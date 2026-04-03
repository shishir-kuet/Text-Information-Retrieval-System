from flask import Blueprint, request

from backend.app.services.admin_service import (
    build_index_and_update,
    index_stats,
    list_domains,
    list_books,
    process_uploaded_books,
    upload_book,
)
from backend.app.services.job_service import list_jobs, submit_job
from backend.app.services.search_log_service import get_admin_search_logs
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import require_admin, require_auth


bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _serialize(doc: dict):
    out = dict(doc)
    out.pop("_id", None)
    return out


def _is_wait_mode() -> bool:
    value = (request.args.get("wait") or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _is_full_rebuild_mode() -> bool:
    value = (request.args.get("full") or "").strip().lower()
    return value in {"1", "true", "yes", "on"}


@bp.post("/upload")
@require_auth
@require_admin
def upload():
    file_storage = request.files.get("file")
    domain = (request.form.get("domain") or "").strip()
    title = (request.form.get("title") or "").strip()
    author = (request.form.get("author") or "").strip()
    year = (request.form.get("year") or "").strip()

    book_doc, err = upload_book(file_storage, domain, title, author, year)
    if err == "missing file":
        return error("file is required", status=400)
    if err == "missing domain":
        return error("domain is required", status=400)
    if err == "missing title":
        return error("title is required", status=400)
    if err == "missing author":
        return error("author is required", status=400)
    if err == "invalid year":
        return error("year must be a number", status=400)
    if err:
        return error(err, status=400)

    return success(_serialize(book_doc), status=201)


@bp.get("/domains")
@require_auth
@require_admin
def domains():
    items = list_domains()
    return success({"count": len(items), "items": items})


@bp.post("/process-books")
@require_auth
@require_admin
def process_books_route():
    if _is_wait_mode():
        result, run_err = process_uploaded_books()
        if run_err:
            return error(run_err, status=400)
        return success(result)

    job = submit_job("process_books", process_uploaded_books, meta={"mode": "uploaded"})
    return success(
        {
            "job_id": job.get("job_id"),
            "job_type": job.get("job_type"),
            "status": job.get("status"),
            "mode": "uploaded",
        },
        message="job accepted",
        status=202,
    )


@bp.post("/index/build")
@require_auth
@require_admin
def build_index_route():
    full_rebuild = _is_full_rebuild_mode()

    if _is_wait_mode():
        result = build_index_and_update(full_rebuild=full_rebuild)
        return success(result)

    job = submit_job("index_build", build_index_and_update, full_rebuild=full_rebuild, meta={"full_rebuild": full_rebuild})
    return success(
        {
            "job_id": job.get("job_id"),
            "job_type": job.get("job_type"),
            "status": job.get("status"),
            "full_rebuild": full_rebuild,
        },
        message="job accepted",
        status=202,
    )


@bp.get("/jobs")
@require_auth
@require_admin
def list_jobs_route():
    limit = request.args.get("limit", 50)
    status = (request.args.get("status") or "").strip() or None

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return error("limit must be an integer", status=400)

    if limit <= 0 or limit > 500:
        return error("limit must be between 1 and 500", status=400)

    if status and status not in {"queued", "running", "completed", "failed"}:
        return error("invalid status filter", status=400)

    items = list_jobs(limit=limit, status=status)
    return success({"count": len(items), "items": items, "limit": limit, "status": status})


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
