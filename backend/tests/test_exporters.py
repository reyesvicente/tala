from app.services.exporters import to_srt, to_txt, to_vtt

SEGMENTS = [
    {"start": 0.0, "end": 1.5, "text": "Hello."},
    {"start": 3661.25, "end": 3662.0, "text": "An hour later."},
]


def test_srt_numbering_and_timestamps():
    assert to_srt(SEGMENTS) == (
        "1\n00:00:00,000 --> 00:00:01,500\nHello.\n\n2\n01:01:01,250 --> 01:01:02,000\nAn hour later.\n"
    )


def test_vtt_header_and_dot_separator():
    out = to_vtt(SEGMENTS)
    assert out.startswith("WEBVTT\n\n")
    assert "01:01:01.250 --> 01:01:02.000" in out


def test_txt_handles_empty():
    assert to_txt(None) == "\n"
    assert to_txt("  hi ") == "hi\n"
