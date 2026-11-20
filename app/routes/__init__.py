from app.routes import auth as auth_routes
from app.routes import dashboard as dashboard_routes
from app.routes import dues as dues_routes
from app.routes import houses as houses_routes
from app.routes import categories as categories_routes
from app.routes import settings as settings_routes
from app.routes import users as users_routes
from app.routes import payments as payments_routes
from app.routes import health as health_routes

auth_bp = auth_routes.auth_bp
dashboard_bp = dashboard_routes.dashboard_bp
dues_bp = dues_routes.dues_bp
houses_bp = houses_routes.houses_bp
categories_bp = categories_routes.categories_bp
settings_bp = settings_routes.settings_bp
users_bp = users_routes.users_bp
payments_bp = payments_routes.payments_bp
health_bp = health_routes.health_bp
