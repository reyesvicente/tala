from app.services.cleanup import clean_segments, clean_text


def test_collapses_repeated_word():
    assert clean_text("sabi niya ngayon ngayon ngayon ngayon ngayon ngayon ngay") == "sabi niya ngayon ngay"


def test_collapses_repeated_phrase():
    assert clean_text("Lai niya. Lai niya. Lai niya. Lai niya. Ang sila") == "Lai niya. Ang sila"


def test_collapses_character_loop():
    assert clean_text("Malang kakakakakakakakakakakakaka") == "Malang ka"


def test_collapses_hyphenated_loop():
    assert clean_text("distri-stri-stri-stri-stri-stri-stri-str") == "distri-str"
    assert clean_text("sa-ma-ma-ma-ma-ma-ma-ma") == "sa-ma"


def test_keeps_normal_repetition():
    text = "haha talaga, oo oo sige. Hello hello hello?"
    assert clean_text(text) == text


def test_drops_empty_and_merges_duplicate_segments():
    segments = [
        {"start": 0.0, "end": 1.0, "text": "..."},
        {"start": 1.0, "end": 2.0, "text": "Kumusta?"},
        {"start": 2.0, "end": 3.0, "text": "Kumusta?"},
        {"start": 3.0, "end": 4.0, "text": "…"},
        {"start": 4.0, "end": 5.0, "text": "Okay na."},
    ]
    assert clean_segments(segments) == [
        {"start": 1.0, "end": 3.0, "text": "Kumusta?"},
        {"start": 4.0, "end": 5.0, "text": "Okay na."},
    ]
