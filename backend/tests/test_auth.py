import re

from app.config import get_settings

EMAIL = "paolo@example.com"
PASSWORD = "correct horse battery"


def _register(client, email=EMAIL, password=PASSWORD):
    return client.post("/api/auth/register", json={"email": email, "password": password})


def _reset_token(outbox) -> str:
    match = re.search(r"reset-password\?token=(\S+)", outbox[-1]["text"])
    assert match
    return match.group(1)


def test_register_logs_in(client):
    res = _register(client, email="  Paolo@Example.com ")
    assert res.status_code == 201
    assert res.json()["data"]["email"] == EMAIL
    cookie = res.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert client.get("/api/auth/me").json()["data"]["email"] == EMAIL


def test_register_rejects_duplicates_and_short_passwords(client):
    _register(client)
    assert _register(client).status_code == 409
    assert _register(client, email="b@example.com", password="short").status_code == 422


def test_login_logout(client):
    _register(client)
    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").status_code == 401

    assert client.post("/api/auth/login", json={"email": EMAIL, "password": "nope-nope"}).status_code == 401
    assert client.post("/api/auth/login", json={"email": "who@example.com", "password": PASSWORD}).status_code == 401
    assert client.post("/api/auth/login", json={"email": EMAIL.upper(), "password": PASSWORD}).status_code == 200
    assert client.get("/api/auth/me").status_code == 200


def test_logout_invalidates_session_server_side(client):
    _register(client)
    token = client.cookies.get(get_settings().session_cookie_name)
    client.post("/api/auth/logout")
    # Replaying the old cookie must not work.
    client.cookies.set(get_settings().session_cookie_name, token)
    assert client.get("/api/auth/me").status_code == 401


def test_forgot_password_does_not_reveal_accounts(client, outbox):
    _register(client)
    known = client.post("/api/auth/forgot-password", json={"email": EMAIL})
    unknown = client.post("/api/auth/forgot-password", json={"email": "nobody@example.com"})
    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert [m["to"] for m in outbox] == [EMAIL]


def test_forgot_password_is_throttled(client, outbox):
    _register(client)
    client.post("/api/auth/forgot-password", json={"email": EMAIL})
    client.post("/api/auth/forgot-password", json={"email": EMAIL})
    assert len(outbox) == 1


def test_reset_password_flow(client, outbox):
    _register(client)
    old_cookie = client.cookies.get(get_settings().session_cookie_name)
    client.post("/api/auth/forgot-password", json={"email": EMAIL})
    token = _reset_token(outbox)

    res = client.post("/api/auth/reset-password", json={"token": token, "password": "a brand new password"})
    assert res.status_code == 200
    assert client.get("/api/auth/me").status_code == 200  # logged in with a fresh session

    # Old sessions are revoked, the link is single-use, and only the new password works.
    client.cookies.set(get_settings().session_cookie_name, old_cookie)
    assert client.get("/api/auth/me").status_code == 401
    again = client.post("/api/auth/reset-password", json={"token": token, "password": "another password!"})
    assert again.status_code == 400
    assert client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD}).status_code == 401
    login = client.post("/api/auth/login", json={"email": EMAIL, "password": "a brand new password"})
    assert login.status_code == 200


def test_reset_password_rejects_bad_token(client):
    res = client.post("/api/auth/reset-password", json={"token": "x" * 40, "password": "whatever123"})
    assert res.status_code == 400


def _upload(client, name="memo.m4a"):
    return client.post("/api/transcriptions", files={"file": (name, b"\x00fake", "audio/mp4")})


def test_anonymous_upload_still_works(client):
    assert _upload(client).status_code == 202
    assert client.get("/api/transcriptions").status_code == 401


def test_history_lists_only_my_transcripts(client):
    _upload(client, "anonymous.m4a")
    _register(client)
    _upload(client, "client-call.m4a")
    _upload(client, "voice-memo.m4a")

    data = client.get("/api/transcriptions").json()["data"]
    assert data["total"] == 2
    assert [i["original_filename"] for i in data["items"]] == ["voice-memo.m4a", "client-call.m4a"]

    searched = client.get("/api/transcriptions", params={"q": "CLIENT"}).json()["data"]
    assert [i["original_filename"] for i in searched["items"]] == ["client-call.m4a"]

    paged = client.get("/api/transcriptions", params={"page": 2, "page_size": 1}).json()["data"]
    assert paged["total"] == 2 and len(paged["items"]) == 1

    client.post("/api/auth/logout")
    _register(client, email="someone@example.com")
    assert client.get("/api/transcriptions").json()["data"]["total"] == 0


def test_account_transcripts_are_owner_only(client):
    _register(client)
    slug = _upload(client, "private-call.m4a").json()["data"]["slug"]
    mine = client.get(f"/api/transcriptions/{slug}").json()["data"]
    assert mine["private"] is True
    assert client.get(f"/api/transcriptions/{slug}/export/txt").status_code == 200

    # Logged out: looks exactly like a missing transcript.
    client.post("/api/auth/logout")
    for method, path in [
        ("get", f"/api/transcriptions/{slug}"),
        ("get", f"/api/transcriptions/{slug}/export/txt"),
        ("delete", f"/api/transcriptions/{slug}"),
    ]:
        assert getattr(client, method)(path).status_code == 404

    # Another account can't see or delete it either.
    _register(client, email="someone-else@example.com")
    assert client.get(f"/api/transcriptions/{slug}").status_code == 404
    assert client.delete(f"/api/transcriptions/{slug}").status_code == 404

    # The owner still can.
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    assert client.delete(f"/api/transcriptions/{slug}").status_code == 200


def test_anonymous_transcripts_stay_link_shareable(client):
    slug = _upload(client).json()["data"]["slug"]
    assert client.get(f"/api/transcriptions/{slug}").json()["data"]["private"] is False
    _register(client)
    assert client.get(f"/api/transcriptions/{slug}").status_code == 200
