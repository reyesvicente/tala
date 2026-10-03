from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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


class Page[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int


class TranscriptionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    status: TranscriptionStatus
    original_filename: str
    detected_language: str | None
    duration_seconds: float | None
    created_at: datetime
    expires_at: datetime


Password = Annotated[str, Field(min_length=8, max_length=128)]


class Credentials(BaseModel):
    email: EmailStr
    password: Password


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    password: Password


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    created_at: datetime
