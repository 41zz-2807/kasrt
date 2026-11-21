import hashlib
import os
import re
import time

from argon2 import PasswordHasher
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy.pool import StaticPool

from app import create_app, db
from app.models.user import User

_CSRF_FIELD = "csrf_token"
_CSRF_SALT = "wtf-csrf-token"


def _csrf_serializer(client):
    return URLSafeTimedSerializer(client.application.secret_key, salt=_CSRF_SALT)


def csrf_token(client):
    value = hashlib.sha1(os.urandom(64)).hexdigest()
    with client.session_transaction() as sess:
        sess[_CSRF_FIELD] = value
    return _csrf_serializer(client).dumps(value)


def login(client, username, password):
    return client.post(
        "/login",
        data={"username": username, "password": password, "csrf_token": csrf_token(client)},
        follow_redirects=False,
    )


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_security_headers(client):
    resp = client.get("/healthz")
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src" in resp.headers["Content-Security-Policy"]


def test_login_page_uses_cache_busted_assets(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert "/static/dist/app.css?v=" in body
    assert "/static/js/idle.js?v=" in body
    assert "/static/manifest.webmanifest?v=" in body
    assert "/static/favicon-192.png?v=" in body


def test_login_csrf_token_is_hidden(client):
    body = client.get("/login").get_data(as_text=True)
    assert '<input type="hidden" name="csrf_token" value="' in body
    assert not re.search(r">\s*[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\s*<", body)


def test_login_success(client, superuser):
    resp = login(client, "admin", "supersecret1")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]
    assert client.get("/dashboard").status_code == 200


def test_root_redirects_after_login(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/dashboard" in resp.headers["Location"]


def test_root_redirects_warga_to_portal(client, warga):
    assert login(client, "warga", "supersecret1").status_code == 302
    resp = client.get("/")
    assert resp.status_code == 302
    assert "/warga" in resp.headers["Location"]


def test_login_invalid_credentials(client, superuser):
    resp = login(client, "admin", "wrongpassword")
    assert resp.status_code == 200
    assert client.get("/dashboard").status_code == 302


def test_login_csrf_required(client, superuser):
    resp = client.post("/login", data={"username": "admin", "password": "supersecret1"})
    assert resp.status_code == 400


def test_logout(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    resp = client.get("/logout")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_change_password_flow(client, app, superuser):
    user = User(
        username="baru",
        email="baru@kasrt.local",
        password_hash=PasswordHasher().hash("supersecret1"),
        role="superuser",
        must_change_password=True,
    )
    with app.app_context():
        db.session.add(user)
        db.session.commit()
        uid = user.id

    assert login(client, "baru", "supersecret1").status_code == 302
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/change-password" in resp.headers["Location"]

    weak = client.post(
        "/change-password",
        data={"current_password": "supersecret1", "new_password": "short", "csrf_token": csrf_token(client)},
    )
    assert weak.status_code == 200

    ok = client.post(
        "/change-password",
        data={"current_password": "supersecret1", "new_password": "newsecret123", "csrf_token": csrf_token(client)},
        follow_redirects=False,
    )
    assert ok.status_code == 302
    with app.app_context():
        assert db.session.get(User, uid).must_change_password is False


def test_warga_cannot_access_staff_dashboard(client, warga):
    assert login(client, "warga", "supersecret1").status_code == 302
    assert client.get("/dashboard").status_code == 403


def test_warga_idle_timeout_logs_out(client, warga):
    assert login(client, "warga", "supersecret1").status_code == 302
    with client.session_transaction() as sess:
        sess["last_activity"] = time.time() - 400
    resp = client.get("/dashboard")
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_staff_idle_within_timeout(client, superuser):
    assert login(client, "admin", "supersecret1").status_code == 302
    with client.session_transaction() as sess:
        sess["last_activity"] = time.time() - 60
    assert client.get("/dashboard").status_code == 200


def test_login_rate_limit():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": True,
            "SECRET_KEY": "test-secret",
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_ENGINE_OPTIONS": {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}},
            "SESSION_COOKIE_SECURE": False,
            "RATELIMIT_ENABLED": True,
            "SECURITY_HEADERS": True,
            "WTF_CSRF_TIME_LIMIT": None,
            "IDLE_TIMEOUT_SECONDS": {"warga": 300, "superuser": 1800, "ketua_rt": 1800, "bendahara": 1800},
        }
    )
    with app.app_context():
        db.create_all()
    client = app.test_client()
    statuses = []
    for _ in range(6):
        resp = client.post(
            "/login",
            data={"username": "admin", "password": "supersecret1", "csrf_token": csrf_token(client)},
        )
        statuses.append(resp.status_code)
    assert statuses[-1] == 429


def test_account_lockout(client, superuser, app):
    for _ in range(5):
        assert login(client, "admin", "wrongpassword").status_code == 200

    with app.app_context():
        user = User.query.filter_by(username="admin").first()
        assert user.failed_attempts == 5
        assert user.locked_until is not None

    resp = login(client, "admin", "supersecret1")
    assert resp.status_code == 200
    assert client.get("/dashboard").status_code == 302
