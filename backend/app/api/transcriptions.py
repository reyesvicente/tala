from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, RequiredUser, get_job_runner
from app.config import get_settings
from app.db import get_session
from app.models import Transcription, TranscriptionTask, User
from app.schemas import Envelope, Page, ServiceInfo, TranscriptionOut, TranscriptionSummary
from app.services import transcriptions
from app.services.exporters import EXPORTERS
from app.services.jobs import JobRunner
from app.services.languages import LANGUAGES

router = APIRouter(prefix="/api")

SessionDep = Annotated[Session, Depends(get_session)]
RunnerDep = Annotated[JobRunner, Depends(get_job_runner)]


def _get_or_404(session: Session, slug: str, user: User | None) -> Transcription:
    transcription = transcriptions.get_by_slug(session, slug)
    # Someone else's private transcript looks exactly like a missing one.
    if transcription is None or not transcriptions.can_access(transcription, user):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Transcript not found. It may have expired or been deleted. If it's yours, log in to see it.",
        )
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
    user: CurrentUser,
    file: Annotated[UploadFile, File()],
    language: Annotated[str | None, Form()] = None,
    task: Annotated[TranscriptionTask, Form()] = TranscriptionTask.TRANSCRIBE,
) -> Envelope[TranscriptionOut]:
    if language and language not in LANGUAGES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Unsupported language: {language}")
    try:
        transcription = transcriptions.create_transcription(session, file, language, task, user=user)
    except transcriptions.UploadTooLarge as exc:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"File is larger than {exc.args[0]} MB.") from exc
    except transcriptions.UnsupportedMedia as exc:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "That doesn't look like an audio or video file."
        ) from exc
    runner.submit(transcription.id)
    return Envelope(data=TranscriptionOut.model_validate(transcription), message="Queued for transcription.")


@router.get("/transcriptions", response_model=Envelope[Page[TranscriptionSummary]])
def list_my_transcriptions(
    session: SessionDep,
    user: RequiredUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    q: Annotated[str | None, Query(max_length=100, description="Search by file name")] = None,
) -> Envelope[Page[TranscriptionSummary]]:
    items, total = transcriptions.list_for_user(session, user, page=page, page_size=page_size, query=q)
    return Envelope(
        data=Page(
            items=[TranscriptionSummary.model_validate(t) for t in items],
            total=total,
            page=page,
            page_size=page_size,
        )
    )


@router.get("/transcriptions/{slug}", response_model=Envelope[TranscriptionOut])
def get_transcription(slug: str, session: SessionDep, user: CurrentUser) -> Envelope[TranscriptionOut]:
    return Envelope(data=TranscriptionOut.model_validate(_get_or_404(session, slug, user)))


@router.get("/transcriptions/{slug}/export/{fmt}")
def export_transcription(
    slug: str, fmt: Literal["txt", "srt", "vtt"], session: SessionDep, user: CurrentUser
) -> Response:
    transcription = _get_or_404(session, slug, user)
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
def delete_transcription(slug: str, session: SessionDep, user: CurrentUser) -> Envelope[None]:
    transcriptions.delete_transcription(session, _get_or_404(session, slug, user))
    return Envelope(message="Deleted.")
