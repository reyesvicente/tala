from pathlib import Path

from app.config import get_settings


def _upload(client, **form):
    return client.post(
        "/api/transcriptions",
        files={"file": ("memo.m4a", b"\x00fake-audio", "audio/mp4")},
        data=form,
    )


def test_info(client):
    body = client.get("/api/info").json()
    assert body["errors"] is None
    assert "tl" in body["data"]["languages"]


def test_upload_transcribes_and_deletes_audio(client):
    res = _upload(client, language="en")
    assert res.status_code == 202
    slug = res.json()["data"]["slug"]

    body = client.get(f"/api/transcriptions/{slug}").json()
    data = body["data"]
    assert data["status"] == "done"
    assert data["text"] == "Hello Paolo.\nNo signup needed."
    assert data["detected_language"] == "en"
    assert data["progress"] == 1.0
    # Privacy: the audio file is gone once the transcript exists.
    assert list(Path(get_settings().upload_dir).iterdir()) == []


def test_exports(client):
    slug = _upload(client).json()["data"]["slug"]

    srt = client.get(f"/api/transcriptions/{slug}/export/srt")
    assert srt.status_code == 200
    assert 'filename="memo.srt"' in srt.headers["content-disposition"]
    assert "00:00:01,500 --> 00:00:03,250" in srt.text

    assert client.get(f"/api/transcriptions/{slug}/export/txt").text.startswith("Hello Paolo.")
    assert client.get(f"/api/transcriptions/{slug}/export/pdf").status_code == 422


def test_delete(client):
    slug = _upload(client).json()["data"]["slug"]
    assert client.delete(f"/api/transcriptions/{slug}").status_code == 200
    res = client.get(f"/api/transcriptions/{slug}")
    assert res.status_code == 404
    assert res.json() == {"data": None, "message": res.json()["message"], "errors": None}


def test_rejects_non_audio(client):
    res = client.post("/api/transcriptions", files={"file": ("notes.pdf", b"%PDF", "application/pdf")})
    assert res.status_code == 415


def test_rejects_unknown_language(client):
    assert _upload(client, language="xx").status_code == 422


def test_rejects_oversized(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 0)
    assert _upload(client).status_code == 413


def test_missing_audio_fails_with_friendly_message(client, session_factory):
    from app.models import Transcription
    from app.services.jobs import AUDIO_LOST_MESSAGE

    runner = client.app.state.job_runner
    runner.submit = lambda job_id: None  # queue it without processing
    slug = _upload(client).json()["data"]["slug"]
    with session_factory() as session:
        job = session.query(Transcription).filter_by(slug=slug).one()
        Path(job.audio_path).unlink()  # simulate a redeploy wiping local disk
        job_id = job.id

    runner.process(job_id)
    data = client.get(f"/api/transcriptions/{slug}").json()["data"]
    assert data["status"] == "failed"
    assert data["error"] == AUDIO_LOST_MESSAGE


def test_unreadable_audio_gets_friendly_message(client, monkeypatch):
    import av

    from app.services.jobs import UNREADABLE_MESSAGE

    def broken(*args, **kwargs):
        raise av.error.InvalidDataError(1094995529, "Invalid data found when processing input", "/data/uploads/x.webm")

    monkeypatch.setattr(client.app.state.job_runner, "_transcribe", broken)
    slug = _upload(client).json()["data"]["slug"]
    data = client.get(f"/api/transcriptions/{slug}").json()["data"]
    assert data["status"] == "failed"
    assert data["error"] == UNREADABLE_MESSAGE
    assert "/data/uploads" not in data["error"]
