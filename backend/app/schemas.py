from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import TranscriptionStatus, TranscriptionTask


class Envelope[T](BaseModel):
    data: T | None = None
    message: str = ""
    errors: Any = None


class Segment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    status: TranscriptionStatus
    task: TranscriptionTask
    original_filename: str
    requested_language: str | None
    detected_language: str | None
    duration_seconds: float | None
    progress: float
    text: str | None
    segments: list[Segment] | None
    error: str | None
    model_name: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    expires_at: datetime


class ServiceInfo(BaseModel):
    model: str
    max_upload_mb: int
    retention_hours: int
    languages: dict[str, str]
