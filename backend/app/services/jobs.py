"""In-process job queue. One worker thread runs Whisper so the CPU isn't oversubscribed.

Good enough for a single-instance app; jobs survive restarts because pending rows are
re-enqueued on startup.
"""

import logging
import queue
import threading
import time
from collections.abc import Callable
from pathlib import Path

import av
from sqlalchemy.orm import Session, sessionmaker

from app.models import Transcription
from app.services import auth, transcriber, transcriptions

logger = logging.getLogger(__name__)

PURGE_INTERVAL_SECONDS = 600
UNREADABLE_MESSAGE = (
    "This file couldn't be read. It may be empty, damaged, or in an unusual format. "
    "Try converting it to mp3 or m4a, or record it again."
)
GENERIC_FAILURE_MESSAGE = "Something went wrong while transcribing this file. Please try uploading it again."
AUDIO_LOST_MESSAGE = (
    "The server restarted before this file was transcribed, so the upload was lost. Please upload it again."
)


class JobRunner:
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        transcribe: Callable[..., transcriber.TranscriptResult] = transcriber.transcribe,
    ) -> None:
        self._session_factory = session_factory
        self._transcribe = transcribe
        self._queue: queue.Queue[int | None] = queue.Queue()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        with self._session_factory() as session:
            transcriptions.purge_expired(session)
            transcriptions.remove_orphan_uploads(session)
            for job_id in transcriptions.pending_ids(session):
                self._queue.put(job_id)
        self._thread = threading.Thread(target=self._loop, name="whisper-worker", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._thread:
            self._queue.put(None)
            self._thread.join(timeout=5)

    def submit(self, job_id: int) -> None:
        self._queue.put(job_id)

    def queue_position(self) -> int:
        return self._queue.qsize()

    def _loop(self) -> None:
        last_purge = time.monotonic()
        while True:
            try:
                job_id = self._queue.get(timeout=60)
            except queue.Empty:
                job_id = -1
            if job_id is None:
                return
            if job_id >= 0:
                self.process(job_id)
            if time.monotonic() - last_purge > PURGE_INTERVAL_SECONDS:
                with self._session_factory() as session:
                    purged = transcriptions.purge_expired(session)
                    auth.purge_expired(session)
                if purged:
                    logger.info("Purged %d expired transcriptions", purged)
                last_purge = time.monotonic()

    def process(self, job_id: int) -> None:
        with self._session_factory() as session:
            job = session.get(Transcription, job_id)
            if job is None or not job.audio_path:
                return
            if not Path(job.audio_path).exists():
                # Uploads live on local disk; a restart/redeploy without a persistent disk loses them.
                transcriptions.mark_failed(session, job, AUDIO_LOST_MESSAGE)
                return
            transcriptions.mark_processing(session, job)

            def report(progress: float) -> None:
                job.progress = progress
                session.commit()

            try:
                result = self._transcribe(
                    job.audio_path,
                    language=job.requested_language,
                    task=job.task.value,
                    on_progress=report,
                )
            except av.error.FFmpegError:
                logger.exception("Transcription %s: unreadable audio", job.slug)
                transcriptions.mark_failed(session, job, UNREADABLE_MESSAGE)
                return
            except Exception:  # noqa: BLE001 - never leave a job stuck; details go to the logs only
                logger.exception("Transcription %s failed", job.slug)
                transcriptions.mark_failed(session, job, GENERIC_FAILURE_MESSAGE)
                return

            transcriptions.mark_done(
                session,
                job,
                text=result.text,
                segments=result.segments,
                language=result.language,
                duration=result.duration,
                model_name=result.model_name,
            )
