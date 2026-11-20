import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "kasrt-dev-secret-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///kasrt.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    TESTING = False
    DEBUG = False

    SESSION_COOKIE_NAME = "kasrt_session"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    SESSION_PERMANENT = False

    # idle timeout (detik) per role; default untuk staff
    IDLE_TIMEOUT_SECONDS = {
        "warga": 300,
        "superuser": 1800,
        "ketua_rt": 1800,
        "bendahara": 1800,
    }
    DEFAULT_IDLE_TIMEOUT_SECONDS = 1800

    LOGIN_RATE_LIMIT = "5 per minute"
    GENERAL_RATE_LIMIT = "120 per minute"
    EXPORT_RATE_LIMIT = "5 per minute"
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    SECURITY_HEADERS = True
    CSP = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:"

    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_FROM = os.environ.get("SMTP_FROM", "Kas RT <kasrt@invalid>")
