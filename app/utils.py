from functools import wraps

from flask import abort
from flask_login import current_user

from app.models.user import STAFF_ROLES, WRITE_ROLES


def staff_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user.role not in STAFF_ROLES:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def write_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user.role not in WRITE_ROLES:
            abort(403)
        return view(*args, **kwargs)
    return wrapper


def superuser_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user.role != "superuser":
            abort(403)
        return view(*args, **kwargs)
    return wrapper
