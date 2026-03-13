"""
backend/app.py — Flask REST API for the book search system.

Endpoints:
  GET  /api/health          — liveness check
  GET  /api/stats           — index + DB stats
  POST /api/search          — BM25 search  { "query": "..." }

Run from project root:
    python backend/app.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request
from flask_cors import CORS

from backend.src.config.db import get_db
from backend.src.services.index_service import load_index
from backend.src.services.search_service import enhanced_search
from backend.src.services.tokenizer_service import tokenize
from backend.src.utils.logger import get_logger
from backend.src.models.page import PageModel
from backend.src.models.book import BookModel

INDEX_PATH = Path(__file__).resolve().parent / "data" / "search_index.pkl"

app = Flask(__name__)
CORS(app)  # allow React dev-server (localhost:5173) to call this API

logger = get_logger(__name__)

# ── load index + db once at startup ──────────────────────────────────────────
_index = None
_db = None


def _get_index():
    global _index
    if _index is None:
        _index = load_index(INDEX_PATH)
    return _index


def _get_db():
    global _db
    if _db is None:
        _db = get_db()
    return _db


# ── routes ────────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/api/stats", methods=["GET"])
def stats():
    idx = _get_index()
    db = _get_db()
    return jsonify({
        "total_pages_indexed": idx["N"],
        "unique_terms": len(idx["inverted_index"]),
        "index_built": idx.get("build_date", "N/A"),
        "total_books": db["books"].count_documents({}),
        "total_pages_db": db["pages"].count_documents({}),
    }), 200


@app.route("/api/search", methods=["POST"])
def search():
    body = request.get_json(silent=True) or {}
    query = str(body.get("query", "")).strip()

    if not query:
        return jsonify({"error": "query is required"}), 400

    query_terms = tokenize(query)
    if not query_terms:
        return jsonify({"error": "No valid tokens in query"}), 400

    idx = _get_index()
    db = _get_db()

    results = enhanced_search(
        query_terms=query_terms,
        original_query=query,
        inverted_index=idx["inverted_index"],
        term_freqs=idx["term_freqs"],
        doc_lengths=idx["doc_lengths"],
        books_metadata=idx["books_metadata"],
        N=idx["N"],
        db=db,
    )

    return jsonify({
        "query": query,
        "total_results": len(results),
        "results": results,
    }), 200


@app.route("/api/page/<page_id>", methods=["GET"])
def get_page(page_id):
    db = _get_db()
    idx = _get_index()

    # Fetch the full page document (including book_id)
    page_doc = db["pages"].find_one(
        {"page_id": page_id},
        {"page_id": 1, "text_content": 1, "display_page_number": 1, "book_id": 1, "page_number": 1, "_id": 0}
    )
    if not page_doc:
        return jsonify({"error": "Page not found"}), 404

    book_id = page_doc.get("book_id", "")
    current_page_num = page_doc.get("page_number", 0)

    # Get book metadata (author, year, title, domain) from MongoDB
    book_doc = db["books"].find_one(
        {"book_id": book_id},
        {"book_title": 1, "title": 1, "author": 1, "year": 1, "domain": 1, "_id": 0}
    ) or {}

    # books_metadata in index for display_page_number fallback
    meta = idx["books_metadata"].get(page_id, {})
    book_title = book_doc.get("book_title") or book_doc.get("title") or meta.get("book_title", "Unknown")

    # Find adjacent pages by querying MongoDB pages collection
    prev_page = db["pages"].find_one(
        {"book_id": book_id, "page_number": current_page_num - 1},
        {"page_id": 1, "_id": 0}
    )
    next_page = db["pages"].find_one(
        {"book_id": book_id, "page_number": current_page_num + 1},
        {"page_id": 1, "_id": 0}
    )

    return jsonify({
        "page_id": page_id,
        "text_content": page_doc.get("text_content", ""),
        "display_page_number": page_doc.get("display_page_number") or meta.get("display_page_number", str(current_page_num)),
        "book_title": book_title,
        "author": book_doc.get("author", ""),
        "year": str(book_doc.get("year", "")),
        "domain": book_doc.get("domain") or meta.get("domain", ""),
        "page_number": current_page_num,
        "prev_page_id": prev_page["page_id"] if prev_page else None,
        "next_page_id": next_page["page_id"] if next_page else None,
    }), 200


if __name__ == "__main__":
    logger.info("Starting Flask API — http://localhost:5000")
    app.run(debug=True, port=5000)
