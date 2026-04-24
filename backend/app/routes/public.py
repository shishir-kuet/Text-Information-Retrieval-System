from datetime import datetime
from io import BytesIO
import time

from flask import Blueprint, request, send_file

from backend.app.services.search_log_service import create_search_log
from backend.app.services.library_client import LibraryClient
from backend.app.services.search_service import SearchService
from backend.app.services.ai_summary_service import AiSummaryService
from backend.app.utils.api_response import error, success
from backend.app.utils.auth import decode_token, get_current_user_optional
from pymongo.errors import PyMongoError


bp = Blueprint("public", __name__, url_prefix="/api")
search_service = SearchService()
ai_summary_service = AiSummaryService()
library_client = LibraryClient()


def _highlight_pdf_bytes(pdf_bytes: bytes, query: str) -> bytes:
    query = (query or "").strip()
    if not query:
        return pdf_bytes

    fitz = __import__("fitz")
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if doc.page_count == 0:
            return pdf_bytes

        page = doc[0]
        candidates = [query]
        candidates.extend([part for part in query.split() if len(part) >= 3])

        for needle in candidates:
            for rect in page.search_for(needle):
                annot = page.add_highlight_annot(rect)
                if annot is not None:
                    annot.set_colors(stroke=(1.0, 1.0, 0.0))
                    annot.set_opacity(0.35)
                    annot.update()

        return doc.tobytes()
    finally:
        doc.close()

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


@bp.post("/page/<page_id>/summary")
def summarize_page(page_id):
    page_data = search_service.get_page(page_id)
    if not page_data:
        return error("page not found", status=404)

    data = request.get_json(silent=True) or {}
    max_sentences = data.get("max_sentences", 3)

    try:
        max_sentences = int(max_sentences)
    except (TypeError, ValueError):
        return error("max_sentences must be an integer", status=400)

    if not ai_summary_service.is_configured():
        return error("AI summarization is not configured", status=503)

    text_content = page_data.get("text_content", "")
    try:
        ai_result = ai_summary_service.summarize(text=text_content, max_sentences=max_sentences)
        used_provider = ai_result.get("provider")
        summary_text = (ai_result.get("summary") or "").strip()
    except Exception as exc:
        return error(str(exc) or "AI summarization failed", status=502)

    if not summary_text:
        return error("AI summarization returned empty output", status=502)

    summary = {
        "summary": summary_text,
        "sentence_count": len(ai_summary_service.split_sentences(summary_text)),
        "source_sentence_count": len(ai_summary_service.split_sentences(text_content)),
    }

    return success(
        {
            "page_id": page_id,
            "book_id": page_data.get("book_id"),
            "display_page_number": page_data.get("display_page_number"),
            "provider": used_provider,
            **summary,
        }
    )


@bp.get("/page/<page_id>/pdf")
def open_page_pdf(page_id):
    """Return a single-page PDF for the requested page_id.

    This avoids exposing the full book PDF to unauthenticated users via the browser PDF viewer.
    """
    try:
        pdf_bytes, disposition = library_client.get_page_pdf(page_id)
    except Exception:
        return error("failed to render page pdf", status=502)

    query = (request.args.get("q") or "").strip()
    if query:
        try:
            pdf_bytes = _highlight_pdf_bytes(pdf_bytes, query)
        except Exception:
            pass

    file_name = page_id + ".pdf"
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
        pdf_bytes, disposition = library_client.download_book(book_id)
    except FileNotFoundError:
        return error("pdf file not found", status=404)
    except Exception:
        return error("pdf file not found", status=404)

    if not pdf_bytes:
        return error("book not found", status=404)

    download_name = f"book_{book_id:03d}.pdf"

    return send_file(
        BytesIO(pdf_bytes),
        as_attachment=True,
        download_name=download_name,
        mimetype="application/pdf",
        conditional=False,
    )


