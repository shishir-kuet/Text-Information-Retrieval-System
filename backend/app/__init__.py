from flask import Flask
from werkzeug.exceptions import HTTPException

from backend.app.config.settings import settings
from backend.app.routes.admin import bp as admin_bp
from backend.app.routes.auth import bp as auth_bp
from backend.app.routes.history import bp as history_bp
from backend.app.routes.public import bp as public_bp
from backend.app.utils.api_response import error


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.jwt_secret

    @app.after_request
    def add_dev_cors_headers(response):
        # Keep frontend integration easy during local development/testing.
        # Range is commonly used for downloads (206 Partial Content).
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Range, Accept, Origin, X-Requested-With, If-Modified-Since, If-None-Match"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition, Content-Range, Accept-Ranges"
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        # Ensure frontend always receives JSON for errors.
        return error(exc.description or "request failed", status=exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        return error("internal server error", status=500)

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(admin_bp)

    return app
