from flask import Blueprint, request

from backend.app.services.search_log_service import (
    clear_user_history,
    delete_user_history_item,
    get_user_history,
)
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import require_auth


bp = Blueprint("history", __name__, url_prefix="/api/history")


def _serialize_log(doc: dict):
    out = dict(doc)
    out.pop("_id", None)
    return out


@bp.get("")
@require_auth
def get_history():
    user = request.current_user
    user_id = user.get("user_id")

    limit = request.args.get("limit", 50)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("limit must be an integer", status=400)

    if limit <= 0 or limit > 200:
        return error("limit must be between 1 and 200", status=400)

    items = get_user_history(user_id, limit=limit)
    return success({"count": len(items), "items": [_serialize_log(i) for i in items]})


@bp.delete("/<int:history_id>")
@require_auth
def delete_history_item(history_id: int):
    user = request.current_user
    user_id = user.get("user_id")

    deleted = delete_user_history_item(user_id, history_id)
    if not deleted:
        return error("history item not found", status=404)

    return success({"deleted": 1})


@bp.delete("")
@require_auth
def clear_history():
    user = request.current_user
    user_id = user.get("user_id")

    deleted = clear_user_history(user_id)
    return success({"deleted": deleted})
