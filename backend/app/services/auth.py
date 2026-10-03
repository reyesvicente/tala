"""Accounts: password hashing, cookie sessions, and password resets."""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AuthSession, PasswordResetToken, User
from app.services.email import send_email

_hasher = PasswordHasher()
# Verified against when the email doesn't exist, so login takes the same time either way.
_DUMMY_HASH = _hasher.hash("not-a-real-password")
RESET_THROTTLE = timedelta(seconds=60)


class EmailTaken(Exception):
    pass


class InvalidResetToken(Exception):
    pass


def _now() -> datetime:
    return datetime.now(UTC)


def _expired(moment: datetime) -> bool:
    # SQLite (tests) returns naive datetimes; Postgres returns aware ones. Both are UTC.
    return moment.replace(tzinfo=moment.tzinfo or UTC) < _now()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def _get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == normalize_email(email)))


def register(session: Session, email: str, password: str) -> User:
    if _get_user_by_email(session, email):
        raise EmailTaken
    user = User(email=normalize_email(email), password_hash=_hasher.hash(password))
    session.add(user)
    session.commit()
    return user


def authenticate(session: Session, email: str, password: str) -> User | None:
    user = _get_user_by_email(session, email)
    try:
        _hasher.verify(user.password_hash if user else _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return None
    if user is None:
        return None
    if _hasher.check_needs_rehash(user.password_hash):
        user.password_hash = _hasher.hash(password)
        session.commit()
    return user


def create_session(session: Session, user: User) -> str:
    """Returns the raw token for the cookie; only its hash is stored."""
    token = secrets.token_urlsafe(32)
    session.add(
        AuthSession(
            token_hash=_hash_token(token),
            user_id=user.id,
            expires_at=_now() + timedelta(days=get_settings().session_days),
        )
    )
    session.commit()
    return token


def user_for_session_token(session: Session, token: str) -> User | None:
    auth_session = session.scalar(select(AuthSession).where(AuthSession.token_hash == _hash_token(token)))
    if auth_session is None or _expired(auth_session.expires_at):
        return None
    return session.get(User, auth_session.user_id)


def end_session(session: Session, token: str) -> None:
    session.execute(delete(AuthSession).where(AuthSession.token_hash == _hash_token(token)))
    session.commit()


def request_password_reset(session: Session, email: str) -> None:
    """Emails a reset link if the account exists. Callers respond identically either way."""
    user = _get_user_by_email(session, email)
    if user is None:
        return
    latest = session.scalar(
        select(PasswordResetToken.created_at)
        .where(PasswordResetToken.user_id == user.id)
        .order_by(PasswordResetToken.created_at.desc())
        .limit(1)
    )
    if latest and not _expired(latest + RESET_THROTTLE):
        return  # don't let anyone flood an inbox

    settings = get_settings()
    token = secrets.token_urlsafe(32)
    session.add(
        PasswordResetToken(
            token_hash=_hash_token(token),
            user_id=user.id,
            expires_at=_now() + timedelta(minutes=settings.password_reset_minutes),
        )
    )
    session.commit()

    link = f"{settings.app_url.rstrip('/')}/reset-password?token={token}"
    send_email(
        user.email,
        "Reset your Tala password",
        f"Someone asked to reset the password for your Tala account.\n\n"
        f"Set a new password here (the link works for {settings.password_reset_minutes} minutes, once):\n"
        f"{link}\n\n"
        f"If this wasn't you, ignore this email. Your password won't change.",
    )


def reset_password(session: Session, token: str, new_password: str) -> User:
    reset = session.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == _hash_token(token)))
    if reset is None or reset.used_at is not None or _expired(reset.expires_at):
        raise InvalidResetToken
    user = session.get(User, reset.user_id)
    if user is None:
        raise InvalidResetToken
    user.password_hash = _hasher.hash(new_password)
    reset.used_at = _now()
    # A reset means the old password may be compromised: log out everywhere.
    session.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    session.commit()
    return user


def purge_expired(session: Session) -> None:
    now = _now()
    session.execute(delete(AuthSession).where(AuthSession.expires_at < now))
    session.execute(delete(PasswordResetToken).where(PasswordResetToken.expires_at < now))
    session.commit()
