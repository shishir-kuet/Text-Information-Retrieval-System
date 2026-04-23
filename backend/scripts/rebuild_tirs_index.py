from __future__ import annotations

import argparse

from backend.app.config.paths import (
    LIBRARY_BOOK_MANIFEST_FILE,
    SEARCH_INDEX_FILE,
    SEMANTIC_INDEX_FILE,
    SEMANTIC_META_FILE,
    SEMANTIC_PAGE_MAP_FILE,
)
from backend.app.models import ensure_schema_indexes
from backend.app.services.admin_service import build_index_and_update


def _safe_unlink(path) -> bool:
    try:
        if path.exists():
            path.unlink()
            return True
    except Exception:
        return False
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild TIRS local search + semantic index artifacts.")
    parser.add_argument("--clean-artifacts", action="store_true", help="Delete existing index artifacts before rebuilding.")
    args = parser.parse_args()

    ensure_schema_indexes()

    cleaned = {}
    if args.clean_artifacts:
        cleaned = {
            "search_index_deleted": _safe_unlink(SEARCH_INDEX_FILE),
            "semantic_index_deleted": _safe_unlink(SEMANTIC_INDEX_FILE),
            "semantic_meta_deleted": _safe_unlink(SEMANTIC_META_FILE),
            "semantic_page_map_deleted": _safe_unlink(SEMANTIC_PAGE_MAP_FILE),
            "library_manifest_deleted": _safe_unlink(LIBRARY_BOOK_MANIFEST_FILE),
        }

    result = build_index_and_update(full_rebuild=True)
    print({"cleaned": cleaned, "result": result})


if __name__ == "__main__":
    main()

