from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.db import Base, get_session, get_session_factory
from app.main import create_app
from app.services import ratelimit
from app.services.jobs import JobRunner
from app.services.transcriber import TranscriptResult


def fake_transcribe(audio_path: str, language: str | None, task: str, on_progress=None) -> TranscriptResult:
    assert Path(audio_path).exists()
    if on_progress:
        on_progress(0.5)
    segments = [
        {"start": 0.0, "end": 1.5, "text": "Hello Paolo."},
        {"start": 1.5, "end": 3.25, "text": "No signup needed."},
    ]
    return TranscriptResult(
        text="Hello Paolo.\nNo signup needed.",
        segments=segments,
        language=language or "en",
        duration=3.25,
        model_name="fake",
    )


class InlineRunner(JobRunner):
    """Processes jobs synchronously so tests are deterministic."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def submit(self, job_id: int) -> None:
        self.process(job_id)


@pytest.fixture
def session_factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> sessionmaker[Session]:
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path / "uploads")
    monkeypatch.setattr(get_settings(), "cookie_secure", False)  # TestClient talks plain http
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, expire_on_commit=False)


@pytest.fixture
def client(session_factory: sessionmaker[Session]) -> Iterator[TestClient]:
    app = create_app()
    app.state.job_runner = InlineRunner(session_factory, transcribe=fake_transcribe)

    def override_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_session
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def outbox(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    sent: list[dict] = []
    monkeypatch.setattr(
        "app.services.auth.send_email",
        lambda to, subject, text: sent.append({"to": to, "subject": subject, "text": text}),
    )
    return sent


@pytest.fixture(autouse=True)
def reset_rate_limits() -> Iterator[None]:
    for limiter in ratelimit.ALL:
        limiter.clear()
    yield
