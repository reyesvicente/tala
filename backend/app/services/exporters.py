from collections.abc import Sequence
from typing import Any


def _timestamp(seconds: float, separator: str) -> str:
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def to_txt(text: str | None) -> str:
    return (text or "").strip() + "\n"


def to_srt(segments: Sequence[dict[str, Any]]) -> str:
    blocks = [
        f"{i}\n{_timestamp(s['start'], ',')} --> {_timestamp(s['end'], ',')}\n{s['text']}\n"
        for i, s in enumerate(segments, start=1)
    ]
    return "\n".join(blocks)


def to_vtt(segments: Sequence[dict[str, Any]]) -> str:
    blocks = [f"{_timestamp(s['start'], '.')} --> {_timestamp(s['end'], '.')}\n{s['text']}\n" for s in segments]
    return "WEBVTT\n\n" + "\n".join(blocks)


EXPORTERS = {
    "txt": ("text/plain", lambda t: to_txt(t.text)),
    "srt": ("application/x-subrip", lambda t: to_srt(t.segments or [])),
    "vtt": ("text/vtt", lambda t: to_vtt(t.segments or [])),
}
