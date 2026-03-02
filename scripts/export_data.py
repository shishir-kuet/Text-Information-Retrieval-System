"""
scripts/export_data.py
Export MongoDB books/pages collections to CSV files.

Usage (from project root):
    python scripts/export_data.py
"""

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.db import get_db
from backend.src.utils.logger import get_logger

OUTPUT_DIR = PROJECT_ROOT / "dataset"


def export_books(db, output_dir: Path):
    books_col = db["books"]
    out_path = output_dir / "books.csv"
    books = list(books_col.find({}, {"_id": 0}))
    if not books:
        print("[WARN] No books found.")
        return
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=books[0].keys())
        writer.writeheader()
        writer.writerows(books)
    print(f"[OK] Exported {len(books)} books → {out_path}")


def export_pages(db, output_dir: Path):
    pages_col = db["pages"]
    out_path = output_dir / "pages.csv"
    fields = ["page_id", "book_id", "page_number", "word_count", "char_count"]
    count = 0
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for page in pages_col.find({}, {k: 1 for k in fields} | {"_id": 0}):
            writer.writerow({k: page.get(k, "") for k in fields})
            count += 1
    print(f"[OK] Exported {count} pages (metadata only) → {out_path}")


if __name__ == "__main__":
    logger = get_logger(__name__)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    db = get_db()
    export_books(db, OUTPUT_DIR)
    export_pages(db, OUTPUT_DIR)
    logger.info("Export complete.")
