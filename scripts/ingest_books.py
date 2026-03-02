"""
scripts/ingest_books.py
Ingest all PDFs in the books/ folder into MongoDB.

Usage (from project root):
    python scripts/ingest_books.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.db import get_db
from backend.src.services.ingestion_service import ingest_books
from backend.src.utils.logger import get_logger

BOOKS_FOLDER = PROJECT_ROOT / "books"

if __name__ == "__main__":
    logger = get_logger(__name__)
    db = get_db()
    logger.info(f"Starting ingestion from: {BOOKS_FOLDER}")
    result = ingest_books(db, BOOKS_FOLDER, use_ocr=True, clear_existing=False)
    logger.info(f"Done — {result['books']} books, {result['pages']} pages ingested.")
