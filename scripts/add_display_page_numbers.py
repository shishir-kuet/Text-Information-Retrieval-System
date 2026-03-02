"""
scripts/add_display_page_numbers.py
Migration: read PDF page labels and store `display_page_number` for every
page document already in MongoDB.

Run once from project root:
    python scripts/add_display_page_numbers.py

Safe to re-run — uses $set so existing values are just overwritten.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import fitz
from pymongo import UpdateOne

from backend.src.config.db import get_db
from backend.src.services.ingestion_service import _extract_page_num_from_text
from backend.src.utils.logger import get_logger

logger = get_logger(__name__)


def migrate(db) -> None:
    books_col = db["books"]
    pages_col = db["pages"]

    books = list(books_col.find({}, {"book_id": 1, "file_path": 1}))
    logger.info(f"Migrating display_page_number for {len(books)} books…")

    total_updated = 0

    for book in books:
        book_id   = book["book_id"]
        file_path = Path(book["file_path"])

        if not file_path.exists():
            logger.warning(f"  PDF not found: {file_path} — skipping book_id={book_id}")
            continue

        try:
            doc = fitz.open(str(file_path))
        except Exception as exc:
            logger.error(f"  Cannot open {file_path.name}: {exc}")
            continue

        # Pass 1 — collect fitz labels.  Pages without a valid label are
        # queued for text-content extraction from the DB.
        fitz_labels: dict = {}          # physical (1-based) → label string | None
        for i in range(len(doc)):
            physical = i + 1
            raw = doc[i].get_label()
            if raw and not (raw.startswith('<') and raw.endswith('>')):
                fitz_labels[physical] = raw   # valid embedded label
            else:
                fitz_labels[physical] = None  # needs text-based extraction

        doc.close()

        # Pass 2 — for pages that need it, fetch text_content from the DB
        #           and extract the printed page number from the running header.
        pages_needing_text = [p for p, lbl in fitz_labels.items() if lbl is None]
        text_by_physical: dict = {}
        if pages_needing_text:
            page_ids = [f"{book_id}_{p}" for p in pages_needing_text]
            for rec in pages_col.find(
                {"page_id": {"$in": page_ids}},
                {"page_id": 1, "text_content": 1, "_id": 0},
            ):
                phys = int(rec["page_id"].split("_")[1])
                text_by_physical[phys] = rec.get("text_content") or ""

        # Pass 3 — build bulk-write ops
        ops = []
        for physical in sorted(fitz_labels):
            fitz_label = fitz_labels[physical]
            if fitz_label is not None:
                label = fitz_label
            else:
                text  = text_by_physical.get(physical, "")
                label = _extract_page_num_from_text(text) or str(physical)
            ops.append(UpdateOne(
                {"page_id": f"{book_id}_{physical}"},
                {"$set": {"display_page_number": label}},
            ))

        if ops:
            result = pages_col.bulk_write(ops, ordered=False)
            total_updated += result.modified_count
            logger.info(
                f"  [{book_id}] {file_path.name[:50]} — updated {result.modified_count} pages"
            )

    logger.info(f"Migration complete. Total pages updated: {total_updated}")


if __name__ == "__main__":
    db = get_db()
    migrate(db)
