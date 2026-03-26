import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.config.database import get_database
from backend.app.models import ensure_book_document, ensure_page_document, ensure_schema_indexes


def _backfill_collection(collection, ensure_fn, *, id_field):
    updated = 0
    scanned = 0
    for doc in collection.find():
        scanned += 1
        new_doc = ensure_fn(doc)
        if new_doc != doc:
            collection.update_one({id_field: doc.get(id_field)}, {"$set": new_doc})
            updated += 1
    return scanned, updated


def main():
    ensure_schema_indexes()
    db = get_database()

    books = db["books"]
    pages = db["pages"]

    books_scanned, books_updated = _backfill_collection(books, ensure_book_document, id_field="book_id")
    pages_scanned, pages_updated = _backfill_collection(pages, ensure_page_document, id_field="page_id")

    print(f"Books scanned: {books_scanned}, updated: {books_updated}")
    print(f"Pages scanned: {pages_scanned}, updated: {pages_updated}")


if __name__ == "__main__":
    main()
