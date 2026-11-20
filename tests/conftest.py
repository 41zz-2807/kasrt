import pytest
from argon2 import PasswordHasher
from sqlalchemy.pool import StaticPool

from app import create_app, db
from app.config import Config
from app.models.user import User

_pwd = PasswordHasher()


class TestingConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": StaticPool, "connect_args": {"check_same_thread": False}}
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False
    SECURITY_HEADERS = True
    WTF_CSRF_TIME_LIMIT = None
    IDLE_TIMEOUT_SECONDS = {"warga": 300, "superuser": 1800, "ketua_rt": 1800, "bendahara": 1800}


@pytest.fixture()
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def superuser(app):
    with app.app_context():
        user = User(
            username="admin",
            email="admin@kasrt.local",
            password_hash=_pwd.hash("supersecret1"),
            role="superuser",
            must_change_password=False,
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture()
def warga(app):
    with app.app_context():
        user = User(
            username="warga",
            email="warga@kasrt.local",
            password_hash=_pwd.hash("supersecret1"),
            role="warga",
            must_change_password=False,
        )
        db.session.add(user)
        db.session.commit()
        return user
