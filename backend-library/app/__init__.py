from flask import Flask
from werkzeug.exceptions import HTTPException

from app.config.settings import settings
from app.routes.library import bp as library_bp
from app.utils.api_response import error


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.jwt_secret

    @app.after_request
    def add_dev_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Range, Accept, Origin, X-Requested-With, If-Modified-Since, If-None-Match"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition, Content-Range, Accept-Ranges"
        return response

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return error(exc.description or "request failed", status=exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        return error("internal server error", status=500)

    app.register_blueprint(library_bp)
    return app
