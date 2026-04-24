from pymongo import ASCENDING
from pymongo.errors import OperationFailure

from app.config.database import get_database


def _safe_create_index(collection, keys, *, unique: bool = False, name: str | None = None):
    try:
        kwargs: dict[str, object] = {"unique": unique}
        if name:
            kwargs["name"] = name
        collection.create_index(keys, **kwargs)
    except OperationFailure as exc:
        print(f"Warning: could not create index {name or keys} on {collection.name}: {exc}")


def ensure_schema_indexes() -> None:
    db = get_database()

    existing = set(db.list_collection_names())
    for coll_name in ("books", "pages", "page_chunks"):
        if coll_name not in existing:
            db.create_collection(coll_name)

    books = db["books"]
    pages = db["pages"]
    page_chunks = db["page_chunks"]

    _safe_create_index(books, [("book_id", ASCENDING)], unique=True, name="uq_book_id")
    _safe_create_index(books, [("title", ASCENDING)], name="ix_book_title")
    _safe_create_index(books, [("status", ASCENDING)], name="ix_book_status")
    _safe_create_index(books, [("updated_at", ASCENDING)], name="ix_book_updated_at")

    _safe_create_index(pages, [("page_id", ASCENDING)], unique=True, name="uq_page_id")
    _safe_create_index(pages, [("book_id", ASCENDING), ("page_number", ASCENDING)], unique=True, name="uq_book_page")
    _safe_create_index(pages, [("book_id", ASCENDING)], name="ix_page_book_id")

    _safe_create_index(page_chunks, [("chunk_id", ASCENDING)], unique=True, name="uq_chunk_id")
    _safe_create_index(page_chunks, [("book_id", ASCENDING), ("page_number", ASCENDING)], name="ix_chunk_book_page")
    _safe_create_index(page_chunks, [("book_id", ASCENDING)], name="ix_chunk_book_id")
