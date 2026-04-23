from __future__ import annotations

import math
import os
import pickle
import re
import threading
from collections import Counter, defaultdict
from datetime import datetime

from backend.app.config.database import get_database
from backend.app.config.paths import SEARCH_INDEX_FILE
from backend.app.models import ensure_schema_indexes
from backend.app.services.library_client import LibraryClient
from backend.app.services.semantic_index_service import build_semantic_index


INDEX_BUILD_LOCK = threading.Lock()
INDEX_FILE = SEARCH_INDEX_FILE


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _blank_index_data():
    return {
        "books_metadata": {},
        "page_records": {},
        "page_texts": {},
        "inverted_index": {},
        "term_freqs": {},
        "term_positions": {},
        "doc_lengths": {},
        "N": 0,
        "build_date": _now_str(),
    }


def _load_index_data():
    if not INDEX_FILE.exists():
        return _blank_index_data()

    with open(INDEX_FILE, "rb") as f:
        data = pickle.load(f)

    data.setdefault("books_metadata", {})
    data.setdefault("page_records", {})
    data.setdefault("page_texts", {})
    data.setdefault("inverted_index", {})
    data.setdefault("term_freqs", {})
    data.setdefault("term_positions", {})
    data.setdefault("doc_lengths", {})
    data.setdefault("N", len(data.get("doc_lengths", {})))
    data.setdefault("build_date", _now_str())
    return data


def _save_index_data_atomic(index_data):
    os.makedirs(INDEX_FILE.parent, exist_ok=True)
    tmp_path = INDEX_FILE.with_suffix(".tmp")
    with open(tmp_path, "wb") as f:
        pickle.dump(index_data, f)
    os.replace(tmp_path, INDEX_FILE)


def _finalize_index(index_data):
    index_data["N"] = len(index_data["doc_lengths"])
    index_data["build_date"] = _now_str()


def _build_full_index(client: LibraryClient):
    # Library API enforces a hard max limit=500.
    payload = client.list_books(limit=500)
    items = payload.get("items", []) if isinstance(payload, dict) else []

    # Cache book metadata from the library list endpoint so search results can show titles/domains
    # even if the page payload doesn't embed full book info.
    book_info_by_id: dict[int, dict] = {}
    for item in items:
        book_id = item.get("book_id")
        if book_id is None:
            continue
        try:
            book_id_int = int(book_id)
        except (TypeError, ValueError):
            continue
        book_info_by_id[book_id_int] = dict(item)

    book_ids = sorted(book_info_by_id.keys())

    index_data = _blank_index_data()
    indexed_pages = 0
    empty_pages = 0

    # Seed books metadata up-front so SearchService can always resolve titles.
    for book_id in book_ids:
        book_payload = book_info_by_id.get(book_id) or {}
        index_data["books_metadata"][book_id] = {
            "title": book_payload.get("title") or "Unknown",
            "domain": book_payload.get("domain") or "Library",
            "num_pages": book_payload.get("num_pages"),
        }

    for book_id in book_ids:
        pages_payload = client.list_pages(book_id)
        pages = pages_payload.get("items", []) if isinstance(pages_payload, dict) else []
        for raw_page in pages:
            page = dict(raw_page)
            page_book_id = page.get("book_id")
            page_number = page.get("page_number")
            text = page.get("text_content", "") or ""
            if page_book_id is None or page_number is None:
                continue
            if not text.strip():
                empty_pages += 1
                continue

            doc_id = (int(page_book_id), int(page_number))
            tokens = tokenize(text)
            freq = Counter(tokens)
            positions = defaultdict(list)
            for pos, term in enumerate(tokens):
                positions[term].append(pos)

            index_data["term_freqs"][doc_id] = freq
            index_data["doc_lengths"][doc_id] = sum(freq.values())
            index_data["page_texts"][doc_id] = text
            index_data["page_records"][f"{int(page_book_id)}_{int(page_number)}"] = {
                "page_id": page.get("page_id") or f"{int(page_book_id)}_{int(page_number)}",
                "book_id": int(page_book_id),
                "page_number": int(page_number),
                "display_page_number": page.get("display_page_number") or str(page_number),
                "text_content": text,
            }
            for term in freq.keys():
                index_data["inverted_index"].setdefault(term, []).append(doc_id)
                index_data["term_positions"].setdefault(term, {})[doc_id] = positions[term]

            indexed_pages += 1

    _finalize_index(index_data)
    _save_index_data_atomic(index_data)
    semantic_stats = build_semantic_index(full_rebuild=True)

    return {
        "mode": "full",
        "indexed_books": len(book_ids),
        "indexed_pages": indexed_pages,
        "empty_pages": empty_pages,
        "total_docs": index_data["N"],
        "unique_terms": len(index_data["inverted_index"]),
        "build_date": index_data["build_date"],
        "semantic": semantic_stats,
    }


def build_index(full_rebuild: bool = False):
    ensure_schema_indexes()
    client = LibraryClient()

    acquired = INDEX_BUILD_LOCK.acquire(blocking=False)
    if not acquired:
        data = _load_index_data()
        return {
            "mode": "full" if full_rebuild else "incremental",
            "indexed_books": 0,
            "indexed_pages": 0,
            "empty_pages": 0,
            "total_docs": len(data.get("doc_lengths", {})),
            "unique_terms": len(data.get("inverted_index", {})),
            "build_date": data.get("build_date"),
            "skipped": True,
            "message": "Index build already running",
        }

    try:
        return _build_full_index(client)
    finally:
        INDEX_BUILD_LOCK.release()
