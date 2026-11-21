from argon2 import PasswordHasher
from datetime import datetime, timezone as dt_timezone

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models.user import User
from app.utils import paginate_query, superuser_required

users_bp = Blueprint("users", __name__)

USER_ROLES = ("superuser", "ketua_rt", "bendahara", "warga")
_pwd = PasswordHasher()


def _render(error=None, edit=None, form=None):
    users, page, pages = paginate_query(User.query.order_by(User.id))
    return render_template(
        "users.html", users=users, page=page, pages=pages, error=error, user_form=form, edit=edit
    )


@users_bp.route("/users", methods=["GET"])
@superuser_required
def users():
    return _render()


@users_bp.route("/users", methods=["POST"])
@superuser_required
def users_create():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    role = request.form.get("role") or "warga"
    password = request.form.get("password") or ""
    is_active = request.form.get("is_active") is not None
    must_change = request.form.get("must_change_password") is not None
    form = {"username": username, "email": email, "role": role, "is_active": is_active, "must_change_password": must_change}

    if not username or not password:
        return _render(error="Username dan password wajib diisi.", form=form)
    if User.query.filter_by(username=username).first() is not None:
        return _render(error="Username sudah ada.", form=form)
    if email and User.query.filter_by(email=email).first() is not None:
        return _render(error="Email sudah ada.", form=form)

    db.session.add(
        User(
            username=username,
            email=email or None,
            password_hash=_pwd.hash(password),
            role=role,
            must_change_password=must_change,
            is_active=is_active,
        )
    )
    db.session.commit()
    return redirect(url_for("users.users"))


@users_bp.route("/users/<int:id>/edit", methods=["GET", "POST"])
@superuser_required
def users_edit(id):
    user = db.session.get(User, id)
    if user is None:
        abort(404)
    if request.method == "GET":
        return _render(edit=user)

    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    role = request.form.get("role") or "warga"
    is_active = request.form.get("is_active") is not None
    must_change = request.form.get("must_change_password") is not None

    if not username:
        return _render(error="Username wajib diisi.", edit=user)
    duplicate = User.query.filter_by(username=username).first()
    if duplicate is not None and duplicate.id != id:
        return _render(error="Username sudah ada.", edit=user)
    email_owner = User.query.filter_by(email=email).first() if email else None
    if email_owner is not None and email_owner.id != id:
        return _render(error="Email sudah ada.", edit=user)

    active_superusers = User.query.filter_by(role="superuser", is_active=True).count()
    if user.role == "superuser" and (role != "superuser" or not is_active) and active_superusers <= 1:
        return _render(error="Superuser terakhir tidak boleh dinonaktifkan atau diturunkan.", edit=user)
    if user.id == current_user.id and not is_active:
        return _render(error="Akun sendiri tidak boleh dinonaktifkan.", edit=user)

    user.username = username
    user.email = email or None
    user.role = role
    user.is_active = is_active
    user.must_change_password = must_change
    user.updated_at = datetime.now(dt_timezone.utc).replace(tzinfo=None)
    db.session.commit()
    return redirect(url_for("users.users"))


@users_bp.route("/users/<int:id>/delete", methods=["POST"])
@superuser_required
def users_delete(id):
    user = db.session.get(User, id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        return "Akun sendiri tidak boleh dihapus.", 400
    if user.role == "superuser" and User.query.filter_by(role="superuser", is_active=True).count() <= 1:
        return "Superuser terakhir tidak boleh dihapus.", 400
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("users.users"))


@users_bp.route("/users/<int:id>/toggle", methods=["POST"])
@superuser_required
def users_toggle(id):
    user = db.session.get(User, id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        return "Akun sendiri tidak boleh dinonaktifkan.", 400
    if user.role == "superuser" and user.is_active and User.query.filter_by(role="superuser", is_active=True).count() <= 1:
        return "Superuser terakhir tidak boleh dinonaktifkan.", 400
    user.is_active = not user.is_active
    user.updated_at = datetime.now(dt_timezone.utc).replace(tzinfo=None)
    db.session.commit()
    return redirect(url_for("users.users"))


@users_bp.route("/users/<int:id>/reset-password", methods=["POST"])
@superuser_required
def users_reset_password(id):
    user = db.session.get(User, id)
    if user is None:
        abort(404)
    user.set_password(request.form.get("password") or "kasrt-default-123")
    user.must_change_password = True
    db.session.commit()
    return redirect(url_for("users.users"))
