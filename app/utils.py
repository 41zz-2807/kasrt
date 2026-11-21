from functools import wraps

from flask import abort, request, url_for
from flask_login import current_user

from app.models.user import STAFF_ROLES, WRITE_ROLES


def landing_url():
    """Halaman pertama setelah login, sesuai peran."""
    return url_for("warga.warga" if current_user.role == "warga" else "dashboard.dashboard")


def paginate_query(query, per_page=10, param="page"):
    total = query.count()
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(max(request.args.get(param, 1, type=int) or 1, 1), pages)
    return query.offset((page - 1) * per_page).limit(per_page).all(), page, pages


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
