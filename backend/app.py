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


if __name__ == "__main__":
    logger.info("Starting Flask API — http://localhost:5000")
    app.run(debug=True, port=5000)
