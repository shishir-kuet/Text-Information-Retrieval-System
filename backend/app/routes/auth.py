from flask import Blueprint, request

from backend.app.services.auth_service import login_user, logout_user, me_user, register_user
from backend.app.utils.auth import require_auth


bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    return register_user(name, email, password)


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    return login_user(email, password)


@bp.get("/me")
@require_auth
def me():
    return me_user(request.current_user)


@bp.post("/logout")
@require_auth
def logout():
    return logout_user(request.current_user)



