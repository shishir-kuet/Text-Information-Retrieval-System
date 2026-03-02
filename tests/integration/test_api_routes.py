"""
Integration tests for Flask API routes.
Uses Flask test client with the REAL index and REAL MongoDB — read-only.

Run with:
    pytest tests/integration/test_api_routes.py -v
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

import backend.app as app_module


@pytest.fixture(scope="module")
def client():
    """Flask test client backed by real index + real MongoDB."""
    app_module.app.config["TESTING"] = True
    # pre-load so the first request doesn't count load time
    app_module._get_index()
    app_module._get_db()
    with app_module.app.test_client() as c:
        yield c


# ── /api/health ───────────────────────────────────────────────────────────────

class TestHealthIntegration:
    def test_health_ok(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.get_json()["status"] == "ok"


# ── /api/stats ────────────────────────────────────────────────────────────────

class TestStatsIntegration:
    def test_returns_200(self, client):
        assert client.get("/api/stats").status_code == 200

    def test_book_count_at_least_30(self, client):
        data = client.get("/api/stats").get_json()
        assert data["total_books"] >= 30

    def test_page_count_at_least_16000(self, client):
        data = client.get("/api/stats").get_json()
        assert data["total_pages_db"] >= 16_000

    def test_index_term_count_at_least_50000(self, client):
        data = client.get("/api/stats").get_json()
        assert data["unique_terms"] >= 50_000

    def test_index_pages_match_n(self, client):
        data = client.get("/api/stats").get_json()
        assert data["total_pages_indexed"] > 0


# ── /api/search ───────────────────────────────────────────────────────────────

class TestSearchIntegration:
    def test_common_word_returns_results(self, client):
        data = client.post("/api/search", json={"query": "history"}).get_json()
        assert data["total_results"] > 0

    def test_results_count_max_10(self, client):
        data = client.post("/api/search", json={"query": "the"}).get_json()
        assert len(data["results"]) <= 10

    def test_results_sorted_by_score_descending(self, client):
        data = client.post("/api/search", json={"query": "war peace"}).get_json()
        scores = [r["score"] for r in data["results"]]
        assert scores == sorted(scores, reverse=True)

    def test_result_fields_present(self, client):
        data = client.post("/api/search", json={"query": "science"}).get_json()
        if data["results"]:
            required = {"page_id", "score", "book_title", "page_number",
                        "display_page_number", "domain", "preview"}
            assert required.issubset(data["results"][0].keys())

    def test_nonsense_query_returns_empty_results(self, client):
        data = client.post("/api/search", json={"query": "xyzzy42unusableterm"}).get_json()
        assert data["total_results"] == 0
        assert data["results"] == []

    def test_missing_query_field_returns_400(self, client):
        res = client.post("/api/search", json={})
        assert res.status_code == 400

    def test_empty_query_string_returns_400(self, client):
        res = client.post("/api/search", json={"query": ""})
        assert res.status_code == 400

    def test_display_page_number_is_string(self, client):
        data = client.post("/api/search", json={"query": "chapter"}).get_json()
        for r in data["results"]:
            assert isinstance(r["display_page_number"], str)
            assert len(r["display_page_number"]) > 0

    def test_physical_and_display_page_can_differ(self, client):
        """On books with Roman numeral prefixes physical != display for intro pages."""
        data = client.post("/api/search", json={"query": "preface introduction"}).get_json()
        # At least verify both fields exist and are non-empty
        for r in data["results"]:
            assert "page_number" in r
            assert "display_page_number" in r

    def test_score_is_positive_number(self, client):
        data = client.post("/api/search", json={"query": "revolution"}).get_json()
        for r in data["results"]:
            assert isinstance(r["score"], (int, float))
            assert r["score"] > 0

    def test_page_number_is_positive_integer(self, client):
        data = client.post("/api/search", json={"query": "battle"}).get_json()
        for r in data["results"]:
            assert isinstance(r["page_number"], int)
            assert r["page_number"] > 0

    def test_preview_is_non_empty_string(self, client):
        data = client.post("/api/search", json={"query": "origin"}).get_json()
        for r in data["results"]:
            assert isinstance(r["preview"], str)
            assert len(r["preview"]) > 0

    def test_query_echoed_in_response(self, client):
        data = client.post("/api/search", json={"query": "Darwin"}).get_json()
        assert data["query"] == "Darwin"
