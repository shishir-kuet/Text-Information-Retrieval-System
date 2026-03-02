"""
scripts/build_index.py
Build the BM25 search index from MongoDB and save to backend/data/.

Usage (from project root):
    python scripts/build_index.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.db import get_db
from backend.src.services.index_service import build_index
from backend.src.utils.logger import get_logger

INDEX_PATH = PROJECT_ROOT / "backend" / "data" / "search_index.pkl"

if __name__ == "__main__":
    logger = get_logger(__name__)
    db = get_db()
    logger.info("Building search index...")
    payload = build_index(db, index_path=INDEX_PATH)
    logger.info(
        f"Index saved to {INDEX_PATH} -- "
        f"{payload['N']} pages, {len(payload['inverted_index'])} terms."
    )
