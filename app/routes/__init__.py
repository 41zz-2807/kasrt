from app.routes import auth as auth_routes
from app.routes import dashboard as dashboard_routes
from app.routes import health as health_routes

auth_bp = auth_routes.auth_bp
dashboard_bp = dashboard_routes.dashboard_bp
health_bp = health_routes.health_bp
