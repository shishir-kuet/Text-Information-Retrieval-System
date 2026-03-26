import datetime
from functools import wraps

import jwt
from flask import request
from werkzeug.security import check_password_hash, generate_password_hash

from backend.app.config.database import get_database
from backend.app.config.settings import settings
from backend.app.utils.api_response import error


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


def create_token(user: dict) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": str(user.get("user_id")),
        "email": user.get("email"),
        "role": user.get("role"),
        "name": user.get("name"),
        "iat": now,
        "exp": now + datetime.timedelta(days=7),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])


def _get_bearer_token():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return auth.split(" ", 1)[1].strip()


def _parse_user_id(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def get_current_user_optional():
    """Best-effort auth: returns user dict or None; never errors."""
    token = _get_bearer_token()
    if not token:
        return None

    try:
        payload = decode_token(token)
        user_id = _parse_user_id(payload.get("sub"))
        if user_id is None:
            return None

        db = get_database()
        user = db["users"].find_one({"user_id": user_id})
        if not user:
            return None

        request.current_user = user
        return user
    except Exception:
        return None


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = get_current_user_optional()
        if not user:
            return error("Missing token", status=401)
        return fn(*args, **kwargs)

    return wrapper


def require_admin(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        user = getattr(request, "current_user", None)
        if not user:
            return error("Unauthorized", status=401)
        if user.get("role") != "admin":
            return error("Admin access required", status=403)
        return fn(*args, **kwargs)

    return wrapper
