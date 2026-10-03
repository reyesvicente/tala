"""Thin wrapper around faster-whisper (OpenAI Whisper weights, CTranslate2 runtime)."""

import math
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from faster_whisper import BatchedInferencePipeline, WhisperModel

from app.config import get_settings
from app.services.cleanup import clean_segments

ProgressCallback = Callable[[float], None]


@dataclass
class TranscriptResult:
    text: str
    segments: list[dict] = field(default_factory=list)
    language: str | None = None
    duration: float | None = None
    model_name: str = ""


def available_cpus() -> int:
    """CPUs this container may actually use.

    os.cpu_count() reports the host's cores, so on a 1-CPU Render instance CTranslate2 would
    start one thread per host core and they'd all fight over a single CPU.
    """
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            return max(1, math.floor(int(quota) / int(period)))
    except (OSError, ValueError):
        pass
    return os.cpu_count() or 1


_pipeline: BatchedInferencePipeline | None = None
_model_lock = threading.Lock()


def get_pipeline() -> BatchedInferencePipeline:
    global _pipeline
    with _model_lock:
        if _pipeline is None:
            settings = get_settings()
            settings.whisper_model_dir.mkdir(parents=True, exist_ok=True)
            model = WhisperModel(
                settings.whisper_model,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
                cpu_threads=settings.whisper_cpu_threads or available_cpus(),
                download_root=str(settings.whisper_model_dir),
            )
            _pipeline = BatchedInferencePipeline(model)
        return _pipeline


def transcribe(
    audio_path: str,
    language: str | None,
    task: str,
    on_progress: ProgressCallback | None = None,
) -> TranscriptResult:
    settings = get_settings()
    segments_iter, info = get_pipeline().transcribe(
        audio_path,
        language=language,
        task=task,
        vad_filter=True,  # skip silence: faster and fewer hallucinations
        batch_size=settings.whisper_batch_size,
        beam_size=settings.whisper_beam_size,
        repetition_penalty=settings.whisper_repetition_penalty,
        no_repeat_ngram_size=settings.whisper_no_repeat_ngram_size,
    )

    segments: list[dict] = []
    last_report = 0.0
    for seg in segments_iter:  # generator: decoding happens as we iterate
        segments.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        now = time.monotonic()
        if on_progress and info.duration and now - last_report > 1.5:
            on_progress(min(seg.end / info.duration, 0.99))
            last_report = now

    segments = clean_segments(segments)
    return TranscriptResult(
        text="\n".join(s["text"] for s in segments if s["text"]),
        segments=segments,
        language=info.language,
        duration=info.duration,
        model_name=settings.whisper_model,
    )
