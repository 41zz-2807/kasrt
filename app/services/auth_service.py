from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models.user import LOCKOUT_FAILS, LOCKOUT_MINUTES, MIN_PASSWORD_LENGTH, User


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def authenticate(username: str, password: str):
    """Return (user, error). error None means success."""
    user = User.query.filter_by(username=username).first() if username else None
    now = utcnow()

    if user is not None and user.locked_until is not None and user.locked_until > now:
        return None, "account_locked"

    if user is None or not user.check_password(password or ""):
        if user is not None:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= LOCKOUT_FAILS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
            user.updated_at = now
            db.session.commit()
        return None, "invalid_credentials"

    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    db.session.commit()
    return user, None


def change_password(user: User, current_password: str, new_password: str):
    """Return (ok, error)."""
    if not user.check_password(current_password or ""):
        return False, "current_password_incorrect"
    if len(new_password or "") < MIN_PASSWORD_LENGTH:
        return False, "weak_password"
    user.set_password(new_password)
    user.must_change_password = False
    user.updated_at = utcnow()
    db.session.commit()
    return True, None
