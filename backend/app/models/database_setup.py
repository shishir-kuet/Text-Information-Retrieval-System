from pymongo import ASCENDING
from pymongo.errors import OperationFailure

from backend.app.config.database import get_database


def _safe_create_index(collection, keys, *, unique: bool = False, name: str | None = None):
    try:
        kwargs = {"unique": unique}
        if name:
            kwargs["name"] = name
        collection.create_index(keys, **kwargs)
    except OperationFailure as exc:
        print(f"Warning: could not create index {name or keys} on {collection.name}: {exc}")


def ensure_schema_indexes() -> None:
    db = get_database()

    existing = set(db.list_collection_names())
    for coll_name in ("books", "pages", "users", "search_logs"):
        if coll_name not in existing:
            db.create_collection(coll_name)

    books = db["books"]
    pages = db["pages"]
    users = db["users"]
    search_logs = db["search_logs"]

    _safe_create_index(books, [("book_id", ASCENDING)], unique=True, name="uq_book_id")
    _safe_create_index(books, [("title", ASCENDING)], name="ix_book_title")
    _safe_create_index(books, [("domain", ASCENDING)], name="ix_book_domain")
    _safe_create_index(books, [("status", ASCENDING)], name="ix_book_status")

    _safe_create_index(pages, [("page_id", ASCENDING)], unique=True, name="uq_page_id")
    _safe_create_index(pages, [("book_id", ASCENDING), ("page_number", ASCENDING)], unique=True, name="uq_book_page")
    _safe_create_index(pages, [("book_id", ASCENDING)], name="ix_page_book_id")

    _safe_create_index(users, [("user_id", ASCENDING)], unique=True, name="uq_user_id")
    _safe_create_index(users, [("email", ASCENDING)], unique=True, name="uq_user_email")
    _safe_create_index(users, [("role", ASCENDING)], name="ix_user_role")

    _safe_create_index(search_logs, [("log_id", ASCENDING)], unique=True, name="uq_log_id")
    _safe_create_index(search_logs, [("user_id", ASCENDING)], name="ix_log_user_id")
    _safe_create_index(search_logs, [("created_at", ASCENDING)], name="ix_log_created_at")
    _safe_create_index(search_logs, [("query_text", ASCENDING)], name="ix_log_query_text")


def inspect_collections() -> dict:
    db = get_database()
    summary = {}
    for coll_name in db.list_collection_names():
        collection = db[coll_name]
        summary[coll_name] = {
            "count": collection.count_documents({}),
            "indexes": list(collection.index_information().keys()),
        }
    return summary
