from flask import Blueprint, request

from backend.app.services.admin_service import (
    build_index_and_update,
    index_stats,
    list_books,
)
from backend.app.services.library_sync_service import LibrarySyncService
from backend.app.services.search_log_service import get_admin_search_logs
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import require_admin, require_auth


bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _serialize(doc: dict):
    out = dict(doc)
    out.pop("_id", None)
    return out


def _is_full_rebuild_mode() -> bool:
    value = (request.args.get("full") or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


@bp.post("/upload")
@require_auth
@require_admin
def upload():
    return error("upload is handled by the library system", status=410)


@bp.get("/domains")
@require_auth
@require_admin
def domains():
    return error("domains are handled by the library system", status=410)


@bp.post("/process-books")
@require_auth
@require_admin
def process_books_route():
    return error("processing is handled by the library system", status=410)


@bp.post("/sync/books")
@require_auth
@require_admin
def sync_books_route():
    try:
        result = LibrarySyncService().sync_books()
    except Exception as exc:
        return error(str(exc) or "sync failed", status=500)
    return success(result)


@bp.post("/index/build")
@require_auth
@require_admin
def build_index_route():
    full_rebuild = _is_full_rebuild_mode()
    try:
        result = build_index_and_update(full_rebuild=full_rebuild)
    except Exception as exc:
        return error(str(exc) or "index build failed", status=500)
    return success(result)


@bp.get("/books")
@require_auth
@require_admin
def list_books_route():
    limit = request.args.get("limit", 200)
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("limit must be an integer", status=400)

    if limit <= 0 or limit > 500:
        return error("limit must be between 1 and 500", status=400)

    books = list_books(limit=limit)
    return success({"count": len(books), "items": [_serialize(b) for b in books]})


@bp.get("/index/stats")
@require_auth
@require_admin
def index_stats_route():
    stats = index_stats()
    return success(stats)


@bp.get("/logs/search")
@require_auth
@require_admin
def get_search_logs():
    limit = request.args.get("limit", 100)
    skip = request.args.get("skip", 0)

    try:
        limit = int(limit)
        skip = int(skip)
    except (TypeError, ValueError):
        return error("limit/skip must be integers", status=400)

    if limit <= 0 or limit > 500:
        return error("limit must be between 1 and 500", status=400)

    if skip < 0:
        return error("skip must be >= 0", status=400)

    items = get_admin_search_logs(limit=limit, skip=skip)
    return success({"count": len(items), "items": [_serialize(i) for i in items], "limit": limit, "skip": skip})
