from argon2 import PasswordHasher
from datetime import datetime, timezone as dt_timezone

from flask import Blueprint, abort, redirect, render_template, request, url_for

from app.extensions import db
from app.models.user import User
from app.utils import superuser_required

users_bp = Blueprint("users", __name__)

USER_ROLES = ("superuser", "ketua_rt", "bendahara", "warga")
_pwd = PasswordHasher()


@users_bp.route("/users", methods=["GET"])
@superuser_required
def users():
    users = User.query.order_by(User.id).all()
    return render_template("users.html", users=users, error=None, user_form=None)


@users_bp.route("/users", methods=["POST"])
@superuser_required
def users_create():
    error = None
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    role = request.form.get("role") or "warga"
    password = request.form.get("password") or ""
    is_active = request.form.get("is_active") is not None
    must_change = request.form.get("must_change_password") is not None

    if not username or not password:
        error = "Username dan password wajib diisi."
    elif User.query.filter_by(username=username).first() is not None:
        error = "Username sudah ada."
    elif email and User.query.filter_by(email=email).first() is not None:
        error = "Email sudah ada."
    else:
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

    users = User.query.order_by(User.id).all()
    return render_template("users.html", users=users, error=error, user_form={"username": username, "email": email, "role": role, "is_active": is_active, "must_change_password": must_change})


@users_bp.route("/users/<int:id>/toggle", methods=["POST"])
@superuser_required
def users_toggle(id):
    user = db.session.get(User, id)
    if user is None:
        abort(404)
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
