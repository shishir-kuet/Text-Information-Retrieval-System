import pickle
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean

from backend.app.config.database import get_database
from backend.app.config.paths import (
    LIBRARY_BOOK_MANIFEST_FILE,
    SEARCH_INDEX_FILE,
    SEMANTIC_INDEX_FILE,
    SEMANTIC_META_FILE,
    SEMANTIC_PAGE_MAP_FILE,
)
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
    if not LIBRARY_BOOK_MANIFEST_FILE.exists():
        return []

    try:
        with open(LIBRARY_BOOK_MANIFEST_FILE, "rb") as handle:
            manifest = pickle.load(handle) or {}
    except Exception:
        return []

    if isinstance(manifest, dict):
        items = list(manifest.values())
    elif isinstance(manifest, list):
        items = list(manifest)
    else:
        items = []

    items = [item for item in items if isinstance(item, dict)]
    items.sort(key=lambda item: int(item.get("book_id", 0) or 0), reverse=True)
    return items[:limit]


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

    total_search_logs = search_logs.count_documents({})
    total_users = users.count_documents({})

    latency_values = []
    zero_result_searches = 0
    unique_queries = set()
    for log in search_logs.find({}, {"latency_ms": 1, "total_results": 1, "query_text": 1}):
        latency = log.get("latency_ms")
        if isinstance(latency, (int, float)):
            latency_values.append(float(latency))

        if int(log.get("total_results", 0) or 0) == 0:
            zero_result_searches += 1

        query_text = (log.get("query_text") or "").strip().lower()
        if query_text:
            unique_queries.add(query_text)

    average_latency_ms = round(mean(latency_values), 2) if latency_values else 0.0
    zero_result_rate = round((zero_result_searches / total_search_logs) * 100, 2) if total_search_logs else 0.0
    success_rate = round(100.0 - zero_result_rate, 2) if total_search_logs else 0.0

    def _parse_created_at(value):
        if not value:
            return None
        try:
            return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
        except Exception:
            return None

    today = datetime.utcnow().date()
    start_date = today - timedelta(days=6)
    daily_counts = defaultdict(int)
    daily_latency_totals = defaultdict(float)
    daily_latency_counts = defaultdict(int)
    for log in search_logs.find({}, {"latency_ms": 1, "created_at": 1}):
        created_at = _parse_created_at(log.get("created_at"))
        if created_at is None:
            continue
        day = created_at.date()
        if day < start_date or day > today:
            continue

        key = day.isoformat()
        daily_counts[key] += 1

        latency = log.get("latency_ms")
        if isinstance(latency, (int, float)):
            daily_latency_totals[key] += float(latency)
            daily_latency_counts[key] += 1

    recent_search_activity = []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        key = day.isoformat()
        count = daily_counts.get(key, 0)
        latency_count = daily_latency_counts.get(key, 0)
        avg_latency = round(daily_latency_totals.get(key, 0.0) / latency_count, 2) if latency_count else 0.0
        recent_search_activity.append(
            {
                "date": key,
                "searches": count,
                "average_latency_ms": avg_latency,
            }
        )

    synced_books = 0
    synced_books_by_status = {"processed": 0, "uploaded": 0, "indexed": 0, "other": 0}
    if LIBRARY_BOOK_MANIFEST_FILE.exists():
        try:
            with open(LIBRARY_BOOK_MANIFEST_FILE, "rb") as handle:
                manifest = pickle.load(handle) or {}
            if isinstance(manifest, dict):
                manifest_items = list(manifest.values())
            elif isinstance(manifest, list):
                manifest_items = list(manifest)
            else:
                manifest_items = []

            manifest_items = [item for item in manifest_items if isinstance(item, dict)]
            synced_books = len(manifest_items)
            for item in manifest_items:
                status = str(item.get("status") or "").strip().lower()
                if status in synced_books_by_status:
                    synced_books_by_status[status] += 1
                else:
                    synced_books_by_status["other"] += 1
        except Exception:
            synced_books = 0

    return {
        "index_available": exists,
        "index_size_bytes": size,
        "build_date": build_date,
        "semantic_index_available": semantic_exists,
        "semantic_index_size_bytes": semantic_size,
        "total_users": total_users,
        "total_search_logs": total_search_logs,
        "average_latency_ms": average_latency_ms,
        "zero_result_searches": zero_result_searches,
        "zero_result_rate": zero_result_rate,
        "success_rate": success_rate,
        "unique_queries": len(unique_queries),
        "synced_books": synced_books,
        "synced_books_by_status": synced_books_by_status,
        "recent_search_activity": recent_search_activity,
    }

