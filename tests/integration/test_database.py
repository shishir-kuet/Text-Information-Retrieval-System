"""
Integration tests — database connectivity and data integrity.

These tests connect to the REAL MongoDB instance (read-only operations).
They verify the database is populated correctly and leave no side effects.

Run with:
    pytest tests/integration/test_database.py -v
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.db import get_db
from backend.src.models.book import BookModel
from backend.src.models.page import PageModel


@pytest.fixture(scope="module")
def db():
    """Shared real MongoDB connection for the test module."""
    return get_db()


@pytest.fixture(scope="module")
def book_model(db):
    return BookModel(db)


@pytest.fixture(scope="module")
def page_model(db):
    return PageModel(db)


class TestDatabaseConnectivity:
    def test_db_is_reachable(self, db):
        """MongoDB client can list collection names without error."""
        names = db.list_collection_names()
        assert isinstance(names, list)

    def test_books_collection_exists(self, db):
        assert "books" in db.list_collection_names()

    def test_pages_collection_exists(self, db):
        assert "pages" in db.list_collection_names()


class TestBooksCollection:
    def test_minimum_book_count(self, book_model):
        """At least 30 books must be present (full ingestion)."""
        count = book_model.count()
        assert count >= 30, f"Expected ≥30 books, found {count}"

    def test_book_document_structure(self, book_model):
        book = book_model.find_all()[0]
        required = {"book_id", "title", "domain", "num_pages", "date_added"}
        assert required.issubset(book.keys()), f"Missing fields: {required - book.keys()}"

    def test_all_domains_present(self, book_model):
        expected_domains = {"Academic", "History", "Literature", "Philosophy", "Science"}
        actual_domains = {b["domain"] for b in book_model.find_all()}
        missing = expected_domains - actual_domains
        assert not missing, f"Missing domains in DB: {missing}"

    def test_book_ids_are_unique(self, book_model):
        ids = [b["book_id"] for b in book_model.find_all()]
        assert len(ids) == len(set(ids)), "Duplicate book_id values found"

    def test_find_by_id_returns_correct_book(self, book_model):
        first = book_model.find_all()[0]
        found = book_model.find_by_id(first["book_id"])
        assert found is not None
        assert found["book_id"] == first["book_id"]


class TestPagesCollection:
    def test_minimum_page_count(self, page_model):
        """At least 16 000 pages must be present."""
        count = page_model.count()
        assert count >= 16_000, f"Expected ≥16 000 pages, found {count}"

    def test_pages_with_text_count(self, page_model):
        """At least 15 000 pages should contain extracted text."""
        count = page_model.count_with_text()
        assert count >= 15_000, f"Expected ≥15 000 pages with text, found {count}"

    def test_page_document_structure(self, page_model, db):
        sample = db["pages"].find_one({})
        assert sample is not None
        required = {"page_id", "book_id", "page_number", "text_content"}
        assert required.issubset(sample.keys()), f"Missing fields: {required - sample.keys()}"

    def test_page_id_format(self, db):
        """page_id must be in '<book_id>_<page_number>' format."""
        sample = db["pages"].find_one({})
        assert "_" in sample["page_id"]
        parts = sample["page_id"].split("_")
        assert len(parts) == 2
        assert parts[0].isdigit() and parts[1].isdigit()

    def test_batch_fetch_by_ids(self, page_model, db):
        ids = [p["page_id"] for p in db["pages"].find({}, {"page_id": 1}).limit(5)]
        pages = page_model.find_by_ids(ids)
        assert len(pages) == len(ids)
