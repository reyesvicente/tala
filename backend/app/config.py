from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    database_url: str = "postgresql+psycopg://tala:tala@postgres:5432/tala"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        # Hosts like Render hand out postgres:// or postgresql:// URLs; SQLAlchemy needs the driver named.
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url.removeprefix(prefix)
        return url

    # Whisper (open-weight, runs locally via CTranslate2)
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_cpu_threads: int = 0  # 0 = let CTranslate2 decide
    whisper_model_dir: Path = Path("/models")
    # Batched decoding splits audio on speech (VAD) and decodes chunks in parallel:
    # ~6x faster than sequential on CPU. Greedy (beam 1) is as accurate here and a bit faster.
    whisper_batch_size: int = 8
    whisper_beam_size: int = 1
    # Guards against repetition loops (batched decoding has no temperature fallback).
    whisper_repetition_penalty: float = 1.1
    whisper_no_repeat_ngram_size: int = 0  # e.g. 4 blocks loops harder, may clip real repeats

    upload_dir: Path = Path("/data/uploads")
    max_upload_mb: int = 100
    # Transcripts self-destruct after this many hours. Audio is deleted right after transcription.
    retention_hours: int = 72

    # Accounts (optional for users; transcribing never requires one)
    app_url: str = "http://localhost:5173"  # used in password-reset links
    session_days: int = 30
    session_cookie_name: str = "tala_session"
    cookie_secure: bool = True  # set False for plain-http local dev
    password_reset_minutes: int = 60

    # Email via Resend. Without an API key, reset links are logged instead of sent.
    resend_api_key: str | None = None
    email_from: str = "Tala <noreply@rs.vicentereyes.org>"

    # Optional: absolute path to a built frontend (dist/) to serve from the same origin.
    frontend_dist: Path | None = None
    cors_origins: list[str] = []


@lru_cache
def get_settings() -> Settings:
    return Settings()
