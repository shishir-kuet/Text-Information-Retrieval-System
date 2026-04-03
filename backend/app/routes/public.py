from datetime import datetime
from io import BytesIO
import time

from flask import Blueprint, request, send_file

from backend.app.config.database import get_database
from backend.app.services.search_log_service import create_search_log
from backend.app.services.search_service import SearchService
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import decode_token, get_current_user_optional
from backend.app.utils.storage import resolve_pdf_path
from pymongo.errors import PyMongoError


bp = Blueprint("public", __name__, url_prefix="/api")
search_service = SearchService()


@bp.get("/health")
def health():
    payload = {"status": "ok", "timestamp": datetime.utcnow().isoformat() + "Z"}
    return success(payload)


@bp.post("/search")
def search():
    started = time.perf_counter()

    data = request.get_json(silent=True) or {}
    query = (data.get("query") or "").strip()
    top_k = data.get("top_k", 10)

    if not query:
        return error("query is required", status=400)

    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        return error("top_k must be an integer", status=400)

    if top_k <= 0 or top_k > 100:
        return error("top_k must be between 1 and 100", status=400)

    try:
        results = search_service.search(query=query, top_k=top_k)
    except FileNotFoundError:
        return error("search index not found", status=503)
    except PyMongoError:
        return error("database unavailable", status=503)
    except Exception:
        return error("search failed", status=500)

    latency_ms = int((time.perf_counter() - started) * 1000)

    user = get_current_user_optional()
    user_id = user.get("user_id") if user else None

    normalized_query = search_service.normalize_query(query)
    top_results = [
        {
            "book_id": r["book_id"],
            "page_id": r["page_id"],
            "page_number": r["page_number"],
            "score": r["score"],
        }
        for r in results[: min(len(results), 5)]
    ]

    # Only record history for authenticated users.
    # Search must remain available even if MongoDB/history logging is temporarily unavailable.
    if user_id is not None:
        try:
            create_search_log(
                user_id=user_id,
                query_text=query,
                normalized_query=normalized_query,
                total_results=len(results),
                top_results=top_results,
                latency_ms=latency_ms,
            )
        except Exception:
            pass

    return success({"query": query, "count": len(results), "results": results, "latency_ms": latency_ms})


@bp.get("/page/<page_id>")
def get_page(page_id):
    page_data = search_service.get_page(page_id)
    if not page_data:
        return error("page not found", status=404)
    return success(page_data)


@bp.get("/page/<page_id>/pdf")
def open_page_pdf(page_id):
    """Return a single-page PDF for the requested page_id.

    This avoids exposing the full book PDF to unauthenticated users via the browser PDF viewer.
    """
    db = get_database()

    raw_page = db["pages"].find_one({"page_id": page_id})
    if not raw_page:
        return error("page not found", status=404)

    book_id = raw_page.get("book_id")
    page_number = raw_page.get("page_number")
    if book_id is None or page_number is None:
        return error("page not found", status=404)

    book = db["books"].find_one({"book_id": book_id})
    if not book:
        return error("book not found", status=404)

    abs_path, _ = resolve_pdf_path(book.get("file_path"))
    if abs_path is None or not abs_path.exists():
        return error("pdf file not found", status=404)

    try:
        import fitz

        src = fitz.open(str(abs_path))
        try:
            idx = int(page_number) - 1
            if idx < 0 or idx >= src.page_count:
                return error("page not found", status=404)

            single = fitz.open()
            try:
                single.insert_pdf(src, from_page=idx, to_page=idx)
                pdf_bytes = single.tobytes()
            finally:
                single.close()
        finally:
            src.close()
    except Exception:
        return error("failed to render page pdf", status=500)

    file_name = f"book_{int(book_id):03d}_page_{int(page_number):04d}.pdf"
    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=False,
        download_name=file_name,
        mimetype="application/pdf",
        conditional=False,
    )


@bp.get("/book/<int:book_id>/download")
def download_book(book_id):
    user = get_current_user_optional()
    if not user:
        token = (request.args.get("token") or "").strip()
        if token:
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
                user_id = int(user_id) if user_id is not None else None
                if user_id is not None:
                    db = get_database()
                    user = db["users"].find_one({"user_id": user_id})
            except Exception:
                user = None

    if not user:
        return error("Missing token", status=401)

    try:
        download_data = search_service.get_book_download(book_id)
    except FileNotFoundError:
        return error("pdf file not found", status=404)

    if not download_data:
        return error("book not found", status=404)

    return send_file(
        download_data["file_path"],
        as_attachment=True,
        download_name=download_data["file_name"],
        mimetype="application/pdf",
        conditional=False,
    )


