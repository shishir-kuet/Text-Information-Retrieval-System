from flask import Blueprint

from backend.app.services.library_index_service import build_index
from backend.app.services.library_sync_service import LibrarySyncService
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import require_admin, require_auth

bp = Blueprint("library_sync", __name__, url_prefix="/api/admin")


@bp.post("/sync/books")
@require_auth
@require_admin
def sync_books():
    try:
        result = LibrarySyncService().sync_books()
    except Exception as exc:
        return error(str(exc) or "sync failed", status=500)
    return success(result)


@bp.post("/index/build")
@require_auth
@require_admin
def build_index_route():
    try:
        result = build_index(full_rebuild=True)
    except Exception as exc:
        return error(str(exc) or "index build failed", status=500)
    return success(result)
