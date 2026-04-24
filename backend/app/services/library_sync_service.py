from __future__ import annotations

import os
import pickle
from dataclasses import dataclass

from backend.app.config.paths import LIBRARY_BOOK_MANIFEST_FILE
from backend.app.models import now_str
from backend.app.services.library_client import LibraryClient


@dataclass
class SyncSummary:
    total_books: int
    new_books: int
    updated_books: int


class LibrarySyncService:
    def __init__(self, client: LibraryClient | None = None):
        self.client = client or LibraryClient()

    def sync_books(self) -> dict:
        # Library API enforces a hard max limit=500.
        payload = self.client.list_books(limit=500)
        items = payload.get("items", []) if isinstance(payload, dict) else []

        existing_manifest: dict[int, dict] = {}
        if LIBRARY_BOOK_MANIFEST_FILE.exists():
            try:
                with open(LIBRARY_BOOK_MANIFEST_FILE, "rb") as handle:
                    existing_manifest = pickle.load(handle) or {}
            except Exception:
                existing_manifest = {}

        new_books = 0
        updated_books = 0
        manifest: dict[int, dict] = dict(existing_manifest)

        for item in items:
            book_id = item.get("book_id")
            if book_id is None:
                continue

            cleaned = dict(item)
            cleaned["book_id"] = int(book_id)
            cleaned.setdefault("synced_at", now_str())
            comparison = dict(cleaned)
            comparison.pop("synced_at", None)

            existing = manifest.get(int(book_id))
            if existing is None:
                new_books += 1
            else:
                existing_comparison = dict(existing)
                existing_comparison.pop("synced_at", None)
                if existing_comparison != comparison:
                    updated_books += 1

            manifest[int(book_id)] = cleaned

        os.makedirs(LIBRARY_BOOK_MANIFEST_FILE.parent, exist_ok=True)
        with open(LIBRARY_BOOK_MANIFEST_FILE, "wb") as handle:
            pickle.dump(manifest, handle)

        return {
            "total_books": len(items),
            "new_books": new_books,
            "updated_books": updated_books,
        }
