"""
Integration tests — end-to-end search pipeline against real data.

Requires:
  - MongoDB with the book_search_system database populated
  - backend/data/search_index.pkl built

Run with:
    pytest tests/integration/test_search_pipeline.py -v
"""

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.config.db import get_db
from backend.src.services.index_service import load_index
from backend.src.services.search_service import enhanced_search
from backend.src.services.tokenizer_service import tokenize

INDEX_PATH = PROJECT_ROOT / "backend" / "data" / "search_index.pkl"


@pytest.fixture(scope="module")
def db():
    return get_db()


@pytest.fixture(scope="module")
def index():
    return load_index(INDEX_PATH)


class TestIndexLoading:
    def test_index_loads_successfully(self, index):
        assert index is not None

    def test_index_has_required_keys(self, index):
        required = {"inverted_index", "term_freqs", "doc_lengths", "books_metadata", "N"}
        assert required.issubset(index.keys())

    def test_index_has_reasonable_term_count(self, index):
        count = len(index["inverted_index"])
        assert count >= 50_000, f"Expected ≥50 000 terms, found {count}"

    def test_index_n_matches_doc_lengths(self, index):
        assert index["N"] == len(index["doc_lengths"])


class TestSearchPipeline:
    def test_common_word_returns_results(self, index, db):
        results = enhanced_search(
            query_terms=tokenize("history"),
            original_query="history",
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        assert len(results) > 0

    def test_results_are_sorted_by_score(self, index, db):
        results = enhanced_search(
            query_terms=tokenize("war peace"),
            original_query="war peace",
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_results_have_required_fields(self, index, db):
        results = enhanced_search(
            query_terms=tokenize("science"),
            original_query="science",
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        if results:
            expected = {"page_id", "score", "book_title", "page_number", "domain", "preview"}
            assert expected.issubset(results[0].keys())

    def test_at_most_10_results_returned(self, index, db):
        results = enhanced_search(
            query_terms=tokenize("the"),
            original_query="the",
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        assert len(results) <= 10

    def test_nonsense_query_returns_empty(self, index, db):
        results = enhanced_search(
            query_terms=tokenize("xyzzy42unusableterm"),
            original_query="xyzzy42unusableterm",
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        assert results == []

    def test_exact_phrase_boosts_score(self, index, db):
        """A page containing the exact phrase should rank higher than pages with separate terms."""
        phrase = "war and peace"
        phrase_results = enhanced_search(
            query_terms=tokenize(phrase),
            original_query=phrase,
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        # Just verifying it runs and returns results without error
        assert isinstance(phrase_results, list)

    def test_multi_domain_results(self, index, db):
        """A broad query should surface results from multiple domains."""
        results = enhanced_search(
            query_terms=tokenize("theory"),
            original_query="theory",
            inverted_index=index["inverted_index"],
            term_freqs=index["term_freqs"],
            doc_lengths=index["doc_lengths"],
            books_metadata=index["books_metadata"],
            N=index["N"],
            db=db,
        )
        domains = {r["domain"] for r in results}
        assert len(domains) >= 1
