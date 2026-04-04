import os
import pickle
import re
import threading
from collections import Counter, defaultdict
from datetime import datetime

from backend.app.config.database import get_database
from backend.app.config.paths import SEARCH_INDEX_FILE
from backend.app.models import (
    BOOK_STATUS_INDEXED,
    BOOK_STATUS_PROCESSED,
    ensure_book_document,
    ensure_page_document,
    ensure_schema_indexes,
)


db = get_database()
books_collection = db["books"]
pages_collection = db["pages"]
INDEX_FILE = SEARCH_INDEX_FILE
INDEX_BUILD_LOCK = threading.Lock()


def tokenize(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()


def _now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _book_ids_by_status(statuses):
    cursor = books_collection.find({"status": {"$in": list(statuses)}}, {"book_id": 1})
    return [b.get("book_id") for b in cursor if b.get("book_id") is not None]


def _blank_index_data():
    return {
        "books_metadata": {},
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


def _remove_books_from_index(index_data, book_ids):
    if not book_ids:
        return 0

    book_id_set = set(book_ids)
    term_freqs = index_data["term_freqs"]
    term_positions = index_data["term_positions"]
    doc_lengths = index_data["doc_lengths"]
    inverted_index = index_data["inverted_index"]

    removed_doc_ids = [doc_id for doc_id in list(term_freqs.keys()) if doc_id[0] in book_id_set]
    for doc_id in removed_doc_ids:
        freq = term_freqs.pop(doc_id, None)
        doc_lengths.pop(doc_id, None)

        if not freq:
            continue

        for term in list(freq.keys()):
            postings = inverted_index.get(term)
            if not postings:
                continue
            new_postings = [d for d in postings if d != doc_id]
            if new_postings:
                inverted_index[term] = new_postings
            else:
                inverted_index.pop(term, None)

            per_term_positions = term_positions.get(term)
            if per_term_positions and doc_id in per_term_positions:
                per_term_positions.pop(doc_id, None)
                if not per_term_positions:
                    term_positions.pop(term, None)

    for bid in book_id_set:
        index_data["books_metadata"].pop(bid, None)

    return len(removed_doc_ids)


def _index_pages_for_books(index_data, book_ids):
    if not book_ids:
        return {"indexed_pages": 0, "empty_pages": 0}

    term_freqs = index_data["term_freqs"]
    term_positions = index_data["term_positions"]
    doc_lengths = index_data["doc_lengths"]
    inverted_index = index_data["inverted_index"]

    indexed_pages = 0
    empty_pages = 0

    cursor = pages_collection.find(
        {"book_id": {"$in": list(book_ids)}},
        {"book_id": 1, "page_number": 1, "text_content": 1},
    )

    for raw_page in cursor:
        page_doc = ensure_page_document(raw_page)
        book_id = page_doc.get("book_id")
        page_number = page_doc.get("page_number")
        text = page_doc.get("text_content", "")

        if book_id is None or page_number is None:
            continue

        doc_id = (book_id, page_number)
        if not text or not text.strip():
            empty_pages += 1
            continue

        tokens = tokenize(text)
        freq = Counter(tokens)
        positions = defaultdict(list)
        for pos, term in enumerate(tokens):
            positions[term].append(pos)

        term_freqs[doc_id] = freq
        doc_lengths[doc_id] = sum(freq.values())

        for term in freq.keys():
            inverted_index.setdefault(term, []).append(doc_id)
            term_positions.setdefault(term, {})[doc_id] = positions[term]

        indexed_pages += 1

    for raw_book in books_collection.find(
        {"book_id": {"$in": list(book_ids)}},
        {"book_id": 1, "title": 1, "domain": 1, "num_pages": 1},
    ):
        book = ensure_book_document(raw_book)
        book_id = book.get("book_id")
        if book_id is None:
            continue
        index_data["books_metadata"][book_id] = {
            "title": book.get("title", "Unknown"),
            "domain": book.get("domain", "Unknown"),
            "num_pages": book.get("num_pages", 0),
        }

    return {"indexed_pages": indexed_pages, "empty_pages": empty_pages}


def _finalize_index(index_data):
    index_data["N"] = len(index_data["doc_lengths"])
    index_data["build_date"] = _now_str()


def _build_full_index():
    eligible_ids = _book_ids_by_status([BOOK_STATUS_PROCESSED, BOOK_STATUS_INDEXED])
    index_data = _blank_index_data()

    add_stats = _index_pages_for_books(index_data, eligible_ids)
    _finalize_index(index_data)
    _save_index_data_atomic(index_data)

    return {
        "mode": "full",
        "eligible_books": len(eligible_ids),
        "indexed_books": len(eligible_ids),
        "indexed_pages": add_stats["indexed_pages"],
        "empty_pages": add_stats["empty_pages"],
        "total_docs": index_data["N"],
        "unique_terms": len(index_data["inverted_index"]),
        "build_date": index_data["build_date"],
    }


def _build_incremental_index():
    processed_ids = _book_ids_by_status([BOOK_STATUS_PROCESSED])
    if not processed_ids:
        data = _load_index_data()
        return {
            "mode": "incremental",
            "indexed_books": 0,
            "indexed_pages": 0,
            "empty_pages": 0,
            "total_docs": len(data.get("doc_lengths", {})),
            "unique_terms": len(data.get("inverted_index", {})),
            "build_date": data.get("build_date"),
            "skipped": True,
            "message": "No processed books to index",
        }

    index_data = _load_index_data()
    removed_docs = _remove_books_from_index(index_data, processed_ids)
    add_stats = _index_pages_for_books(index_data, processed_ids)
    _finalize_index(index_data)
    _save_index_data_atomic(index_data)

    return {
        "mode": "incremental",
        "indexed_books": len(processed_ids),
        "indexed_pages": add_stats["indexed_pages"],
        "empty_pages": add_stats["empty_pages"],
        "removed_docs": removed_docs,
        "total_docs": index_data["N"],
        "unique_terms": len(index_data["inverted_index"]),
        "build_date": index_data["build_date"],
    }


def build_index(full_rebuild: bool = False):
    """Build index in full or incremental mode.

    - full_rebuild=True: rebuild from all eligible books (processed + indexed)
    - full_rebuild=False: only re-index books currently in processed status
    """
    ensure_schema_indexes()

    acquired = INDEX_BUILD_LOCK.acquire(blocking=False)
    if not acquired:
        # Avoid 500s when a second build request arrives while one is running.
        # Caller can treat this as a no-op.
        data = _load_index_data()
        return {
            "mode": "incremental" if not full_rebuild else "full",
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
        if full_rebuild or not INDEX_FILE.exists():
            return _build_full_index()
        return _build_incremental_index()
    finally:
        INDEX_BUILD_LOCK.release()


if __name__ == "__main__":
    stats = build_index(full_rebuild=False)
    print(stats)

