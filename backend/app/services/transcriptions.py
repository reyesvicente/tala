"""Business logic for transcription jobs. Routers stay thin and call into here."""

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import Transcription, TranscriptionStatus, TranscriptionTask, User


class UploadTooLarge(Exception):
    pass


class UnsupportedMedia(Exception):
    pass


CHUNK = 1024 * 1024


def _is_media(upload: UploadFile) -> bool:
    content_type = (upload.content_type or "").split(";")[0].strip()
    return content_type.startswith(("audio/", "video/")) or content_type in {"application/octet-stream", ""}


def save_upload(upload: UploadFile) -> Path:
    """Stream the upload to disk, enforcing the size limit without buffering it all in memory."""
    if not _is_media(upload):
        raise UnsupportedMedia(upload.content_type)

    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(upload.filename or "").suffix[:10]
    dest = settings.upload_dir / f"{uuid.uuid4().hex}{suffix}"
    limit = settings.max_upload_mb * CHUNK

    written = 0
    with dest.open("wb") as out:
        while chunk := upload.file.read(CHUNK):
            written += len(chunk)
            if written > limit:
                out.close()
                dest.unlink(missing_ok=True)
                raise UploadTooLarge(settings.max_upload_mb)
            out.write(chunk)
    return dest


def create_transcription(
    session: Session,
    upload: UploadFile,
    language: str | None,
    task: TranscriptionTask,
    user: User | None = None,
) -> Transcription:
    audio_path = save_upload(upload)
    transcription = Transcription(
        user_id=user.id if user else None,
        original_filename=(upload.filename or "recording")[:255],
        audio_path=str(audio_path),
        requested_language=language or None,
        task=task,
        expires_at=Transcription.expiry_from_now(get_settings().retention_hours),
    )
    session.add(transcription)
    session.commit()
    return transcription


def can_access(transcription: Transcription, user: User | None) -> bool:
    """Anonymous transcripts are shared by link; account transcripts are owner-only."""
    if transcription.user_id is None:
        return True
    return user is not None and user.id == transcription.user_id


def get_by_slug(session: Session, slug: str) -> Transcription | None:
    return session.scalar(select(Transcription).where(Transcription.slug == slug))


def list_for_user(
    session: Session, user: User, *, page: int, page_size: int, query: str | None = None
) -> tuple[list[Transcription], int]:
    stmt = select(Transcription).where(Transcription.user_id == user.id)
    if query:
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(Transcription.original_filename.ilike(f"%{escaped}%", escape="\\"))
    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = session.scalars(
        stmt.order_by(Transcription.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(items), total


def _remove_audio(transcription: Transcription) -> None:
    if transcription.audio_path:
        Path(transcription.audio_path).unlink(missing_ok=True)
        transcription.audio_path = None


def delete_transcription(session: Session, transcription: Transcription) -> None:
    _remove_audio(transcription)
    session.delete(transcription)
    session.commit()


def mark_processing(session: Session, transcription: Transcription) -> None:
    transcription.status = TranscriptionStatus.PROCESSING
    transcription.progress = 0.0
    transcription.started_at = datetime.now(UTC)
    session.commit()


def mark_done(
    session: Session,
    transcription: Transcription,
    *,
    text: str,
    segments: list[dict],
    language: str | None,
    duration: float | None,
    model_name: str,
) -> None:
    transcription.status = TranscriptionStatus.DONE
    transcription.text = text
    transcription.segments = segments
    transcription.detected_language = language
    transcription.duration_seconds = duration
    transcription.model_name = model_name
    transcription.progress = 1.0
    transcription.completed_at = datetime.now(UTC)
    _remove_audio(transcription)
    session.commit()


def mark_failed(session: Session, transcription: Transcription, error: str) -> None:
    transcription.status = TranscriptionStatus.FAILED
    transcription.error = error[:2000]
    _remove_audio(transcription)
    session.commit()


def pending_ids(session: Session) -> list[int]:
    """Jobs that were queued or interrupted mid-run (e.g. container restart)."""
    stmt = (
        select(Transcription.id)
        .where(Transcription.status.in_([TranscriptionStatus.PENDING, TranscriptionStatus.PROCESSING]))
        .order_by(Transcription.created_at)
    )
    return list(session.scalars(stmt))


def purge_expired(session: Session) -> int:
    now = datetime.now(UTC)
    expired = session.scalars(select(Transcription).where(Transcription.expires_at < now)).all()
    for transcription in expired:
        _remove_audio(transcription)
    session.execute(delete(Transcription).where(Transcription.expires_at < now))
    session.commit()
    return len(expired)


def remove_orphan_uploads(session: Session) -> None:
    upload_dir = get_settings().upload_dir
    if not upload_dir.exists():
        return
    known = {p for p in session.scalars(select(Transcription.audio_path)) if p}
    for path in upload_dir.iterdir():
        if str(path) not in known:
            if path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
            else:
                path.unlink(missing_ok=True)
