from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from requests.exceptions import RequestException

from backend.app.config.settings import settings


@dataclass(frozen=True)
class LibraryClientConfig:
    base_url: str = "http://127.0.0.1:5100"
    timeout_seconds: int = 30


class LibraryClient:
    def __init__(self, base_url: str | None = None, timeout_seconds: int = 30):
        self.base_url = (base_url or getattr(settings, "library_api_base_url", None) or LibraryClientConfig.base_url).rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.get(self._url(path), params=params or {}, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except RequestException as exc:
            raise RuntimeError(f"Cannot reach Library backend at {self.base_url}. Start `backend-library/run.py` and try again.") from exc
        if not payload.get("success"):
            raise RuntimeError(payload.get("message") or "library request failed")
        return payload.get("data")

    def _post(self, path: str, data: dict[str, Any] | None = None, files=None) -> Any:
        try:
            response = requests.post(self._url(path), data=data or {}, files=files, timeout=self.timeout_seconds)
            response.raise_for_status()
            payload = response.json()
        except RequestException as exc:
            raise RuntimeError(f"Cannot reach Library backend at {self.base_url}. Start `backend-library/run.py` and try again.") from exc
        if not payload.get("success"):
            raise RuntimeError(payload.get("message") or "library request failed")
        return payload.get("data")

    def list_books(self, limit: int = 500) -> dict:
        # Library backend enforces 1..500. Clamp here to avoid hard failures.
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 200
        limit = max(1, min(limit, 500))
        return self._get("/api/library/books", {"limit": limit})

    def get_book(self, book_id: int) -> dict:
        return self._get(f"/api/library/books/{book_id}")

    def list_pages(self, book_id: int) -> dict:
        return self._get(f"/api/library/books/{book_id}/pages")

    def get_page(self, page_id: str) -> dict:
        return self._get(f"/api/library/pages/{page_id}")

    def get_page_text(self, page_id: str) -> dict:
        return self._get(f"/api/library/pages/{page_id}/text")

    def get_page_pdf(self, page_id: str):
        response = requests.get(self._url(f"/api/library/pages/{page_id}/pdf"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.content, response.headers.get("Content-Disposition")

    def download_book(self, book_id: int):
        response = requests.get(self._url(f"/api/library/books/{book_id}/download"), timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.content, response.headers.get("Content-Disposition")

    def upload_book(self, file_path: str, title: str, author: str = "", year: str | None = None) -> dict:
        with open(file_path, "rb") as handle:
            files = {"file": handle}
            data = {"title": title, "author": author}
            if year:
                data["year"] = year
            return self._post("/api/library/books/upload", data=data, files=files)

    def process_book(self, book_id: int) -> dict:
        return self._post(f"/api/library/books/{book_id}/process")
