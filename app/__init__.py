import logging
import time
from flask import Flask, redirect, request, session, url_for
from flask_migrate import Migrate
from flask_login import current_user, logout_user
from werkzeug.middleware.proxy_fix import ProxyFix

from app.config import Config
from app.extensions import csrf, db, limiter, login_manager
from app.models.user import User
from app.routes import auth as auth_routes
from app.routes import dashboard as dashboard_routes
from app.routes import health as health_routes
from app.routes import houses as houses_routes
from app.routes import dues as dues_routes
from app.routes import categories as categories_routes
from app.routes import users as users_routes
from app.routes import settings as settings_routes

migrate = Migrate()
log = logging.getLogger("kasrt")

PUBLIC_ENDPOINTS = {"health.healthz", "auth.login", "auth.logout"}


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_app(config_object=None):
    app = Flask(__name__)
    if isinstance(config_object, dict):
        app.config.update(config_object)
    else:
        app.config.from_object(config_object or Config)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Silakan login terlebih dahulu."

    @app.context_processor
    def inject_idle_globals():
        timeouts = app.config.get("IDLE_TIMEOUT_SECONDS") or {}
        timeout_seconds = timeouts.get("warga", app.config.get("DEFAULT_IDLE_TIMEOUT_SECONDS", 1800))
        if current_user.is_authenticated and current_user.is_active:
            timeout_seconds = timeouts.get(current_user.role, app.config.get("DEFAULT_IDLE_TIMEOUT_SECONDS", 1800))
        return {
            "idle_timeout_seconds": timeout_seconds,
            "idle_warning_seconds": 60,
        }

    @app.before_request
    def check_session():
        endpoint = request.endpoint or ""
        if endpoint in PUBLIC_ENDPOINTS or endpoint.startswith("static."):
            return None
        if not current_user.is_authenticated:
            return redirect(url_for("auth.login"))
        user = current_user
        if user.must_change_password and endpoint != "auth.change_password":
            return redirect(url_for("auth.change_password"))
        last_activity = session.get("last_activity")
        now = time.time()
        if last_activity is not None:
            last = float(last_activity)
            timeout_seconds = app.config.get("IDLE_TIMEOUT_SECONDS", {}).get(
                user.role, app.config.get("DEFAULT_IDLE_TIMEOUT_SECONDS", 1800)
            )
            if now - last > float(timeout_seconds):
                session.clear()
                logout_user()
                return redirect(url_for("auth.login"))
        session["last_activity"] = now
        return None

    @app.after_request
    def add_security_headers(response):
        if app.config.get("SECURITY_HEADERS", True):
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Referrer-Policy"] = "no-referrer"
            response.headers["Content-Security-Policy"] = app.config.get(
                "CSP", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:"
            )
        return response

    @app.errorhandler(404)
    def handle_not_found(_e):
        return "Not Found", 404

    @app.errorhandler(403)
    def handle_forbidden(_e):
        return "Forbidden", 403

    @app.errorhandler(500)
    def handle_server_error(_e):
        log.exception("internal server error")
        return "Internal Server Error", 500

    app.register_blueprint(health_routes.health_bp)
    app.register_blueprint(auth_routes.auth_bp)
    app.register_blueprint(dashboard_routes.dashboard_bp)
    app.register_blueprint(houses_routes.houses_bp)
    app.register_blueprint(dues_routes.dues_bp)
    app.register_blueprint(categories_routes.categories_bp)
    app.register_blueprint(users_routes.users_bp)
    app.register_blueprint(settings_routes.settings_bp)
    return app
