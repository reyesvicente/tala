from app.services.ratelimit import RateLimiter

EMAIL = "paolo@example.com"
PASSWORD = "correct horse battery"


def test_limiter_window(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr("app.services.ratelimit.time.monotonic", lambda: now[0])
    limiter = RateLimiter(limit=2, window_seconds=60)
    limiter.hit("a")
    limiter.hit("a")
    assert limiter.retry_after("a") == 60
    assert limiter.retry_after("b") == 0
    now[0] += 61
    assert limiter.retry_after("a") == 0


def _login(client, password):
    return client.post("/api/auth/login", json={"email": EMAIL, "password": password})


def test_login_locks_after_five_failures(client):
    client.post("/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
    client.post("/api/auth/logout")
    for _ in range(5):
        assert _login(client, "wrong-password").status_code == 401

    blocked = _login(client, PASSWORD)  # even the right password waits out the lock
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0
    assert blocked.json()["message"].startswith("Too many attempts")


def test_successful_login_clears_failures(client):
    client.post("/api/auth/register", json={"email": EMAIL, "password": PASSWORD})
    for _ in range(4):
        _login(client, "wrong-password")
    assert _login(client, PASSWORD).status_code == 200
    for _ in range(4):
        assert _login(client, "wrong-password").status_code == 401


def test_register_limited_per_ip(client):
    codes = [
        client.post("/api/auth/register", json={"email": f"u{i}@example.com", "password": PASSWORD}).status_code
        for i in range(6)
    ]
    assert codes == [201] * 5 + [429]


def test_forgot_password_limited_per_ip(client):
    codes = [client.post("/api/auth/forgot-password", json={"email": EMAIL}).status_code for _ in range(6)]
    assert codes == [202] * 5 + [429]
