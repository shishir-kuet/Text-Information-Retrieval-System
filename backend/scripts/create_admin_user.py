from __future__ import annotations

import argparse

from backend.app.config.database import get_database
from backend.app.models import ensure_schema_indexes, now_str
from backend.app.utils.auth import hash_password


def _next_user_id() -> int:
    db = get_database()
    last_user = db["users"].find_one(sort=[("user_id", -1)])
    if not last_user or "user_id" not in last_user:
        return 1
    return int(last_user["user_id"]) + 1


def upsert_admin_user(*, name: str, email: str, password: str) -> dict:
    ensure_schema_indexes()

    email = (email or "").strip().lower()
    name = (name or "").strip() or "Admin"
    if not email or not password:
        raise ValueError("email and password are required")

    db = get_database()
    users = db["users"]

    existing = users.find_one({"email": email})
    ts = now_str()
    password_hash = hash_password(password)

    if existing:
        users.update_one(
            {"email": email},
            {
                "$set": {
                    "name": name,
                    "password_hash": password_hash,
                    "role": "admin",
                    "updated_at": ts,
                }
            },
        )
        user_id = int(existing.get("user_id") or 0)
        return {"created": False, "user_id": user_id, "email": email, "role": "admin"}

    user_id = _next_user_id()
    users.insert_one(
        {
            "user_id": user_id,
            "name": name,
            "email": email,
            "password_hash": password_hash,
            "role": "admin",
            "created_at": ts,
            "updated_at": ts,
        }
    )
    return {"created": True, "user_id": user_id, "email": email, "role": "admin"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create/update an admin user for TIRS.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Shishir")
    args = parser.parse_args()

    result = upsert_admin_user(name=args.name, email=args.email, password=args.password)
    # Do not print the password.
    print(result)


if __name__ == "__main__":
    main()

