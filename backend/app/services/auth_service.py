from backend.app.config.database import get_database
from backend.app.models import ensure_schema_indexes, now_str
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import create_token, hash_password, verify_password


def _next_user_id() -> int:
    db = get_database()
    last_user = db["users"].find_one(sort=[("user_id", -1)])
    if not last_user or "user_id" not in last_user:
        return 1
    return int(last_user["user_id"]) + 1


def register_user(name: str, email: str, password: str):
    ensure_schema_indexes()

    if not name or not email or not password:
        return error("name, email, password required", status=400)

    db = get_database()
    users = db["users"]

    if users.find_one({"email": email}):
        return error("Email already registered", status=400)

    user_doc = {
        "user_id": _next_user_id(),
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": "user",
        "created_at": now_str(),
        "updated_at": now_str(),
    }

    users.insert_one(user_doc)
    token = create_token(user_doc)

    return success(
        {
            "token": token,
            "user": _user_payload(user_doc),
        },
        status=201,
    )


def login_user(email: str, password: str):
    ensure_schema_indexes()

    if not email or not password:
        return error("email and password required", status=400)

    db = get_database()
    user = db["users"].find_one({"email": email})
    if not user:
        return error("Invalid credentials", status=401)

    if not verify_password(password, user.get("password_hash", "")):
        return error("Invalid credentials", status=401)

    token = create_token(user)
    return success(
        {
            "token": token,
            "user": _user_payload(user),
        },
        status=200,
    )


def me_user(user: dict):
    return success(
        {
            "user_id": user.get("user_id"),
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role"),
            "created_at": user.get("created_at"),
            "updated_at": user.get("updated_at"),
        }
    )


def logout_user(user: dict):
    # JWT is stateless in this project. Server cannot "unset" a token without
    # implementing a revocation list. Frontend should discard the token.
    return success(
        {
            "logged_out": True,
            "user_id": user.get("user_id"),
        }
    )


def _user_payload(user: dict):
    return {
        "user_id": user.get("user_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
    }

