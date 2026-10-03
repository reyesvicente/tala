import enum
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import JSON, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


def new_slug() -> str:
    # Unguessable share link: the slug *is* the access token (no accounts).
    return secrets.token_urlsafe(9)


class TranscriptionStatus(enum.StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class TranscriptionTask(enum.StrEnum):
    TRANSCRIBE = "transcribe"
    TRANSLATE = "translate"


class Transcription(Base):
    __tablename__ = "transcriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(32), unique=True, index=True, default=new_slug)
    status: Mapped[TranscriptionStatus] = mapped_column(
        Enum(TranscriptionStatus, name="transcription_status", values_callable=lambda e: [m.value for m in e]),
        default=TranscriptionStatus.PENDING,
    )
    task: Mapped[TranscriptionTask] = mapped_column(
        Enum(TranscriptionTask, name="transcription_task", values_callable=lambda e: [m.value for m in e]),
        default=TranscriptionTask.TRANSCRIBE,
    )
    original_filename: Mapped[str] = mapped_column(String(255))
    audio_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    requested_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    detected_language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    segments: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    @staticmethod
    def expiry_from_now(hours: int) -> datetime:
        return _utcnow() + timedelta(hours=hours)
