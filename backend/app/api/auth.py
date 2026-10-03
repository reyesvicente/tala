from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import RequiredUser
from app.config import get_settings
from app.db import get_session, get_session_factory
from app.schemas import Credentials, Envelope, ForgotPasswordIn, LoginIn, ResetPasswordIn, UserOut
from app.services import auth, ratelimit
from app.services.ratelimit import RateLimiter

router = APIRouter(prefix="/api/auth")

SessionDep = Annotated[Session, Depends(get_session)]


def _client_ip(request: Request) -> str:
    # Behind Render's proxy, uvicorn --proxy-headers puts the real client IP here.
    return request.client.host if request.client else "unknown"


def _enforce(limiter: RateLimiter, key: str, *, record: bool = True) -> None:
    wait = limiter.retry_after(key)
    if wait:
        minutes = max(1, round(wait / 60))
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Too many attempts. Try again in {minutes} minute{'s' if minutes != 1 else ''}.",
            headers={"Retry-After": str(wait)},
        )
    if record:
        limiter.hit(key)


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        path="/",
    )


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=Envelope[UserOut])
def register(body: Credentials, request: Request, response: Response, session: SessionDep) -> Envelope[UserOut]:
    _enforce(ratelimit.register_by_ip, _client_ip(request))
    try:
        user = auth.register(session, body.email, body.password)
    except auth.EmailTaken as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "An account with that email already exists.") from exc
    _set_session_cookie(response, auth.create_session(session, user))
    return Envelope(data=UserOut.model_validate(user), message="Account created.")


@router.post("/login", response_model=Envelope[UserOut])
def login(body: LoginIn, request: Request, response: Response, session: SessionDep) -> Envelope[UserOut]:
    email_key = auth.normalize_email(body.email)
    _enforce(ratelimit.login_by_ip, _client_ip(request))
    # Only failures count per email, so normal logins never lock anyone out.
    _enforce(ratelimit.login_failures_by_email, email_key, record=False)
    user = auth.authenticate(session, body.email, body.password)
    if user is None:
        ratelimit.login_failures_by_email.hit(email_key)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong email or password.")
    ratelimit.login_failures_by_email.reset(email_key)
    _set_session_cookie(response, auth.create_session(session, user))
    return Envelope(data=UserOut.model_validate(user), message="Logged in.")


@router.post("/logout", response_model=Envelope[None])
def logout(request: Request, response: Response, session: SessionDep) -> Envelope[None]:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        auth.end_session(session, token)
    response.delete_cookie(settings.session_cookie_name, path="/")
    return Envelope(message="Logged out.")


@router.get("/me", response_model=Envelope[UserOut])
def me(user: RequiredUser) -> Envelope[UserOut]:
    return Envelope(data=UserOut.model_validate(user))


@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED, response_model=Envelope[None])
def forgot_password(
    body: ForgotPasswordIn,
    request: Request,
    background: BackgroundTasks,
    session_factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
) -> Envelope[None]:
    _enforce(ratelimit.forgot_by_ip, _client_ip(request))
    # Run after the response so timing doesn't reveal whether the account exists.
    background.add_task(_send_reset, session_factory, body.email)
    return Envelope(message="If that email has an account, a reset link is on its way.")


def _send_reset(session_factory: sessionmaker[Session], email: str) -> None:
    with session_factory() as session:
        auth.request_password_reset(session, email)


@router.post("/reset-password", response_model=Envelope[UserOut])
def reset_password(
    body: ResetPasswordIn, request: Request, response: Response, session: SessionDep
) -> Envelope[UserOut]:
    _enforce(ratelimit.reset_by_ip, _client_ip(request))
    try:
        user = auth.reset_password(session, body.token, body.password)
    except auth.InvalidResetToken as exc:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "This reset link is invalid or has expired. Request a new one."
        ) from exc
    _set_session_cookie(response, auth.create_session(session, user))
    return Envelope(data=UserOut.model_validate(user), message="Password updated. You're logged in.")
