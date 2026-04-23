import pickle
from pathlib import Path

from backend.app.config.database import get_database
from backend.app.config.paths import SEARCH_INDEX_FILE, SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE
from backend.app.models import ensure_schema_indexes
from backend.app.services.library_index_service import build_index
from backend.app.services.library_sync_service import LibrarySyncService


def build_index_and_update(full_rebuild: bool = False):
    ensure_schema_indexes()
    sync_result = LibrarySyncService().sync_books()
    build_stats = build_index(full_rebuild=full_rebuild)

    return {
        "status": "indexed",
        "sync": sync_result,
        "mode": build_stats.get("mode"),
        "indexed_books": build_stats.get("indexed_books", 0),
        "indexed_pages": build_stats.get("indexed_pages", 0),
        "empty_pages": build_stats.get("empty_pages", 0),
        "total_docs": build_stats.get("total_docs", 0),
        "unique_terms": build_stats.get("unique_terms", 0),
        "build_date": build_stats.get("build_date"),
        "full_rebuild": full_rebuild,
        "skipped": bool(build_stats.get("skipped", False)),
        "message": build_stats.get("message"),
    }


def list_books(limit: int = 100):
    return LibrarySyncService().client.list_books(limit=limit).get("items", [])


def index_stats():
    idx_path = Path(SEARCH_INDEX_FILE)
    exists = idx_path.exists()
    size = idx_path.stat().st_size if exists else 0

    semantic_exists = all(path.exists() for path in (SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE))
    semantic_size = 0
    if semantic_exists:
        semantic_size = sum(path.stat().st_size for path in (SEMANTIC_INDEX_FILE, SEMANTIC_META_FILE, SEMANTIC_PAGE_MAP_FILE))

    build_date = None
    if exists:
        try:
            with open(idx_path, "rb") as f:
                data = pickle.load(f)
                build_date = data.get("build_date")
        except Exception:
            build_date = None

    db = get_database()
    users = db["users"]
    search_logs = db["search_logs"]

    return {
        "index_available": exists,
        "index_size_bytes": size,
        "build_date": build_date,
        "semantic_index_available": semantic_exists,
        "semantic_index_size_bytes": semantic_size,
        "total_users": users.count_documents({}),
        "total_search_logs": search_logs.count_documents({}),
    }

