"""Post-processing for Whisper output.

Small Whisper models (and batched decoding, which has no temperature fallback) can
get stuck in loops on hard audio: "ngayon ngayon ngayon …" or "kakakakaka…". These
rules collapse that noise without touching normal speech.
"""

import re

# A 1-4 word phrase repeated 4+ times in a row -> one occurrence.
_REPEATED_PHRASE = re.compile(r"(?<!\S)(\S+(?:\s+\S+){0,3}?)(?:\s+\1(?!\S)){3,}")
# A 1-6 char chunk repeated 5+ times inside a token ("kakakakaka", "sa-ma-ma-ma-ma-ma") -> one occurrence.
_REPEATED_CHUNK = re.compile(r"(\S{1,6}?)\1{4,}")
# Segments with no actual words, e.g. "...", "…", "-".
_HAS_WORD = re.compile(r"\w")


def clean_text(text: str) -> str:
    text = _REPEATED_CHUNK.sub(r"\1", text)
    previous = None
    while previous != text:  # nested loops can need more than one pass
        previous = text
        text = _REPEATED_PHRASE.sub(r"\1", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def clean_segments(segments: list[dict]) -> list[dict]:
    cleaned = []
    for segment in segments:
        text = clean_text(segment["text"])
        if not _HAS_WORD.search(text):
            continue
        if cleaned and cleaned[-1]["text"] == text:  # same line repeated across segments
            cleaned[-1]["end"] = segment["end"]
            continue
        cleaned.append({**segment, "text": text})
    return cleaned
