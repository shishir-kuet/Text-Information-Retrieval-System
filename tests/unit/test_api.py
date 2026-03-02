"""
Unit tests for Flask API routes (backend/app.py).
Index and DB are mocked — no MongoDB or pkl file required.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


# ── shared fake index payload ─────────────────────────────────────────────────

FAKE_INDEX = {
    "inverted_index": {"war": {"1_1": 5}, "peace": {"1_1": 3}},
    "term_freqs": {"war": 1, "peace": 1},
    "doc_lengths": {"1_1": 100},
    "books_metadata": {
        "1_1": {"book_title": "War and Peace", "page_number": 1, "domain": "Literature"}
    },
    "N": 1,
    "build_date": "2024-01-01",
}

FAKE_SEARCH_RESULTS = [
    {
        "page_id": "1_1",
        "score": 12.5,
        "book_title": "War and Peace",
        "page_number": 1,
        "display_page_number": "i",
        "domain": "Literature",
        "preview": "It was the best of times...",
    }
]


@pytest.fixture
def client():
    """Flask test client with mocked index and DB."""
    with patch("backend.app._get_index", return_value=FAKE_INDEX), \
         patch("backend.app._get_db", return_value=MagicMock(
             **{"__getitem__": lambda self, k: MagicMock(
                 count_documents=lambda _: 30 if k == "books" else 16000
             )}
         )):
        import backend.app as app_module
        app_module.app.config["TESTING"] = True
        with app_module.app.test_client() as c:
            yield c


# ── /api/health ───────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_returns_200(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200

    def test_returns_ok_status(self, client):
        data = client.get("/api/health").get_json()
        assert data["status"] == "ok"


# ── /api/stats ────────────────────────────────────────────────────────────────

class TestStatsEndpoint:
    def test_returns_200(self, client):
        res = client.get("/api/stats")
        assert res.status_code == 200

    def test_has_required_keys(self, client):
        data = client.get("/api/stats").get_json()
        required = {"total_pages_indexed", "unique_terms", "index_built",
                    "total_books", "total_pages_db"}
        assert required.issubset(data.keys())

    def test_pages_indexed_matches_fake_index(self, client):
        data = client.get("/api/stats").get_json()
        assert data["total_pages_indexed"] == FAKE_INDEX["N"]

    def test_unique_terms_matches_fake_index(self, client):
        data = client.get("/api/stats").get_json()
        assert data["unique_terms"] == len(FAKE_INDEX["inverted_index"])


# ── /api/search ───────────────────────────────────────────────────────────────

class TestSearchEndpoint:
    def test_missing_query_returns_400(self, client):
        res = client.post("/api/search", json={})
        assert res.status_code == 400

    def test_empty_query_returns_400(self, client):
        res = client.post("/api/search", json={"query": "   "})
        assert res.status_code == 400

    def test_empty_body_returns_400(self, client):
        res = client.post("/api/search", data="", content_type="application/json")
        assert res.status_code == 400

    def test_valid_query_returns_200(self, client):
        with patch("backend.app.enhanced_search", return_value=FAKE_SEARCH_RESULTS):
            res = client.post("/api/search", json={"query": "war and peace"})
        assert res.status_code == 200

    def test_response_has_required_keys(self, client):
        with patch("backend.app.enhanced_search", return_value=FAKE_SEARCH_RESULTS):
            data = client.post("/api/search", json={"query": "war"}).get_json()
        assert {"query", "total_results", "results"}.issubset(data.keys())

    def test_query_echoed_in_response(self, client):
        with patch("backend.app.enhanced_search", return_value=FAKE_SEARCH_RESULTS):
            data = client.post("/api/search", json={"query": "war"}).get_json()
        assert data["query"] == "war"

    def test_total_results_matches_list_length(self, client):
        with patch("backend.app.enhanced_search", return_value=FAKE_SEARCH_RESULTS):
            data = client.post("/api/search", json={"query": "war"}).get_json()
        assert data["total_results"] == len(data["results"])

    def test_no_results_returns_empty_list(self, client):
        with patch("backend.app.enhanced_search", return_value=[]):
            data = client.post("/api/search", json={"query": "zzznomatch"}).get_json()
        assert data["results"] == []
        assert data["total_results"] == 0

    def test_result_item_has_required_fields(self, client):
        with patch("backend.app.enhanced_search", return_value=FAKE_SEARCH_RESULTS):
            data = client.post("/api/search", json={"query": "war"}).get_json()
        if data["results"]:
            required = {"page_id", "score", "book_title", "page_number",
                        "display_page_number", "domain", "preview"}
            assert required.issubset(data["results"][0].keys())

    def test_punctuation_only_query_returns_400(self, client):
        res = client.post("/api/search", json={"query": "!!! ???"})
        assert res.status_code == 400
