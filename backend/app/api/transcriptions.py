from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_job_runner
from app.config import get_settings
from app.db import get_session
from app.models import Transcription, TranscriptionTask
from app.schemas import Envelope, ServiceInfo, TranscriptionOut
from app.services import transcriptions
from app.services.exporters import EXPORTERS
from app.services.jobs import JobRunner
from app.services.languages import LANGUAGES

router = APIRouter(prefix="/api")

SessionDep = Annotated[Session, Depends(get_session)]
RunnerDep = Annotated[JobRunner, Depends(get_job_runner)]


def _get_or_404(session: Session, slug: str) -> Transcription:
    transcription = transcriptions.get_by_slug(session, slug)
    if transcription is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transcript not found. It may have expired or been deleted.")
    return transcription


@router.get("/info", response_model=Envelope[ServiceInfo])
def info() -> Envelope[ServiceInfo]:
    settings = get_settings()
    return Envelope(
        data=ServiceInfo(
            model=settings.whisper_model,
            max_upload_mb=settings.max_upload_mb,
            retention_hours=settings.retention_hours,
            languages=LANGUAGES,
        )
    )


@router.post("/transcriptions", status_code=status.HTTP_202_ACCEPTED, response_model=Envelope[TranscriptionOut])
def create_transcription(
    session: SessionDep,
    runner: RunnerDep,
    file: Annotated[UploadFile, File()],
    language: Annotated[str | None, Form()] = None,
    task: Annotated[TranscriptionTask, Form()] = TranscriptionTask.TRANSCRIBE,
) -> Envelope[TranscriptionOut]:
    if language and language not in LANGUAGES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unsupported language: {language}")
    try:
        transcription = transcriptions.create_transcription(session, file, language, task)
    except transcriptions.UploadTooLarge as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"File is larger than {exc.args[0]} MB.") from exc
    except transcriptions.UnsupportedMedia as exc:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "That doesn't look like an audio or video file."
        ) from exc
    runner.submit(transcription.id)
    return Envelope(data=TranscriptionOut.model_validate(transcription), message="Queued for transcription.")


@router.get("/transcriptions/{slug}", response_model=Envelope[TranscriptionOut])
def get_transcription(slug: str, session: SessionDep) -> Envelope[TranscriptionOut]:
    return Envelope(data=TranscriptionOut.model_validate(_get_or_404(session, slug)))


@router.get("/transcriptions/{slug}/export/{fmt}")
def export_transcription(slug: str, fmt: Literal["txt", "srt", "vtt"], session: SessionDep) -> Response:
    transcription = _get_or_404(session, slug)
    if transcription.text is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Transcript isn't ready yet.")
    media_type, render = EXPORTERS[fmt]
    stem = transcription.original_filename.rsplit(".", 1)[0] or "transcript"
    return Response(
        content=render(transcription),
        media_type=f"{media_type}; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{stem}.{fmt}"'},
    )


@router.delete("/transcriptions/{slug}", response_model=Envelope[None])
def delete_transcription(slug: str, session: SessionDep) -> Envelope[None]:
    transcriptions.delete_transcription(session, _get_or_404(session, slug))
    return Envelope(message="Deleted.")
