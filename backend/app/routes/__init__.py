from backend.app.routes.admin import bp as admin_bp
from backend.app.routes.auth import bp as auth_bp
from backend.app.routes.history import bp as history_bp
from backend.app.routes.public import bp as public_bp

__all__ = ["admin_bp", "auth_bp", "history_bp", "public_bp"]
