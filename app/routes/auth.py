from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_user, logout_user
from flask_limiter import Limiter

from app.extensions import limiter
from app.services import auth_service
from app.utils import landing_url

auth_bp = Blueprint("auth", __name__, url_prefix="")


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(landing_url())

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user, err = auth_service.authenticate(username, password)
        if user is None:
            error = err
        else:
            login_user(user, remember=False)
            return redirect(landing_url())

    return render_template("login.html", error=error)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("auth.login"))


@auth_bp.route("/change-password", methods=["GET", "POST"])
def change_password():
    if not current_user.must_change_password and request.method == "GET":
        return redirect(landing_url())

    error = None
    if request.method == "POST":
        ok, err = auth_service.change_password(
            current_user, request.form.get("current_password", ""), request.form.get("new_password", "")
        )
        if not ok:
            error = err
        else:
            flash("Password berhasil diubah.")
            return redirect(landing_url())

    return render_template("change_password.html", error=error)
