"""Build and load the BM25 inverted index from MongoDB."""

import pickle
from datetime import datetime
from pathlib import Path

from backend.src.services.tokenizer_service import tokenize

DEFAULT_INDEX_PATH = Path(__file__).resolve().parents[3] / "data" / "search_index.pkl"


def build_index(db, index_path: Path = DEFAULT_INDEX_PATH) -> dict:
    """
    Read all pages from MongoDB, build the inverted index, and save to disk.
    Returns the index payload dict.
    """
    from backend.src.utils.logger import get_logger

    logger = get_logger(__name__)
    pages_col = db["pages"]
    books_col = db["books"]

    # Build books metadata map
    books_metadata = {}
    for book in books_col.find():
        book_id = book.get("book_id")
        book_title = book.get("title", "Unknown")
        domain = book.get("domain", "Unknown")
        for pg in pages_col.find({"book_id": book_id}, {"page_id": 1, "page_number": 1}):
            books_metadata[pg["page_id"]] = {
                "book_title": book_title,
                "page_number": pg.get("page_number"),
                "domain": domain,
            }

    logger.info(f"Building index for {pages_col.count_documents({})} pages...")

    inverted_index: dict[str, dict] = {}
    term_freqs: dict[str, int] = {}
    doc_lengths: dict[str, int] = {}

    cursor = pages_col.find(
        {"text_content": {"$exists": True, "$ne": ""}},
        {"page_id": 1, "text_content": 1},
    )

    for i, page in enumerate(cursor):
        page_id = page["page_id"]
        tokens = tokenize(page.get("text_content", ""))
        doc_lengths[page_id] = len(tokens)

        tf_map: dict[str, int] = {}
        for token in tokens:
            tf_map[token] = tf_map.get(token, 0) + 1

        for token, tf in tf_map.items():
            inverted_index.setdefault(token, {})[page_id] = tf
            term_freqs[token] = term_freqs.get(token, 0) + 1

        if (i + 1) % 1000 == 0:
            logger.info(f"  Processed {i + 1} pages...")

    N = len(doc_lengths)
    logger.info(f"Index built: {N} pages, {len(inverted_index)} unique terms")

    payload = {
        "books_metadata": books_metadata,
        "inverted_index": inverted_index,
        "term_freqs": term_freqs,
        "doc_lengths": doc_lengths,
        "N": N,
        "build_date": datetime.now().isoformat(),
    }

    index_path.parent.mkdir(parents=True, exist_ok=True)
    with open(index_path, "wb") as f:
        pickle.dump(payload, f)

    logger.info(f"Saved index to {index_path}")
    return payload


def load_index(index_path: Path = DEFAULT_INDEX_PATH) -> dict:
    """Load the pre-built index from disk."""
    if not index_path.exists():
        raise FileNotFoundError(
            f"Search index not found at {index_path}. "
            "Run scripts/build_index.py first."
        )
    with open(index_path, "rb") as f:
        return pickle.load(f)
