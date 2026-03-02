"""Unit tests for search_service (BM25, proximity, exact phrase)."""

import pytest
from unittest.mock import MagicMock, patch

from backend.src.services.search_service import (
    bm25_score,
    calculate_proximity_score,
    check_exact_phrase,
    enhanced_search,
)


class TestBm25Score:
    def test_returns_dict(self, sample_inverted_index, sample_doc_lengths, sample_term_freqs):
        scores = bm25_score(
            ["war"], sample_inverted_index, sample_term_freqs, sample_doc_lengths, N=3
        )
        assert isinstance(scores, dict)

    def test_matching_pages_scored(self, sample_inverted_index, sample_doc_lengths, sample_term_freqs):
        scores = bm25_score(
            ["war"], sample_inverted_index, sample_term_freqs, sample_doc_lengths, N=3
        )
        assert "1_1" in scores
        assert "2_3" in scores

    def test_non_matching_term_returns_empty(self, sample_inverted_index, sample_doc_lengths, sample_term_freqs):
        scores = bm25_score(
            ["zzznomatch"], sample_inverted_index, sample_term_freqs, sample_doc_lengths, N=3
        )
        assert scores == {}

    def test_scores_are_positive(self, sample_inverted_index, sample_doc_lengths, sample_term_freqs):
        scores = bm25_score(
            ["napoleon"], sample_inverted_index, sample_term_freqs, sample_doc_lengths, N=3
        )
        assert all(v > 0 for v in scores.values())

    def test_multiple_terms_cumulate(self, sample_inverted_index, sample_doc_lengths, sample_term_freqs):
        score_single = bm25_score(
            ["war"], sample_inverted_index, sample_term_freqs, sample_doc_lengths, N=3
        ).get("1_1", 0)
        score_multi = bm25_score(
            ["war", "peace"], sample_inverted_index, sample_term_freqs, sample_doc_lengths, N=3
        ).get("1_1", 0)
        assert score_multi > score_single

    def test_zero_n_does_not_crash(self):
        scores = bm25_score(["word"], {"word": {"p1": 1}}, {"word": 1}, {"p1": 10}, N=0)
        assert isinstance(scores, dict)


class TestCalculateProximityScore:
    def test_close_terms_give_high_bonus(self):
        tokens = ["the", "war", "and", "peace", "treaty"]
        score = calculate_proximity_score(tokens, ["war", "peace"])
        assert score >= 30.0

    def test_adjacent_gives_maximum_bonus(self):
        tokens = ["war", "peace"]
        score = calculate_proximity_score(tokens, ["war", "peace"])
        assert score == 50.0

    def test_single_term_returns_zero(self):
        tokens = ["war", "was", "terrible"]
        score = calculate_proximity_score(tokens, ["war"])
        assert score == 0.0

    def test_terms_not_in_tokens_returns_zero(self):
        tokens = ["the", "quick", "brown", "fox"]
        score = calculate_proximity_score(tokens, ["war", "peace"])
        assert score == 0.0

    def test_distant_terms_give_low_or_no_bonus(self):
        tokens = ["war"] + ["x"] * 50 + ["peace"]
        score = calculate_proximity_score(tokens, ["war", "peace"])
        assert score == 0.0


class TestCheckExactPhrase:
    def test_exact_match(self):
        assert check_exact_phrase("The war and peace agreement", "war and peace") is True

    def test_case_insensitive(self):
        assert check_exact_phrase("WAR AND PEACE", "war and peace") is True

    def test_no_match(self):
        assert check_exact_phrase("The battle of Waterloo", "war and peace") is False

    def test_empty_query(self):
        assert check_exact_phrase("some text", "") is True  # empty string is always in text

    def test_partial_word_match(self):
        assert check_exact_phrase("peaceful war", "war") is True


class TestEnhancedSearch:
    def _make_index_args(self, sample_inverted_index, sample_doc_lengths,
                         sample_term_freqs, sample_books_metadata):
        return dict(
            inverted_index=sample_inverted_index,
            term_freqs=sample_term_freqs,
            doc_lengths=sample_doc_lengths,
            books_metadata=sample_books_metadata,
            N=3,
        )

    def test_returns_list(self, sample_inverted_index, sample_doc_lengths,
                          sample_term_freqs, sample_books_metadata, mock_db):
        mock_db["pages"].find.return_value = [
            {"page_id": "1_1", "text_content": "war and peace text", "display_page_number": "i"},
            {"page_id": "2_3", "text_content": "napoleon invaded", "display_page_number": "3"},
        ]
        results = enhanced_search(
            query_terms=["war"],
            original_query="war",
            db=mock_db,
            **self._make_index_args(
                sample_inverted_index, sample_doc_lengths,
                sample_term_freqs, sample_books_metadata
            ),
        )
        assert isinstance(results, list)

    def test_empty_query_returns_empty(self, sample_inverted_index, sample_doc_lengths,
                                       sample_term_freqs, sample_books_metadata, mock_db):
        results = enhanced_search(
            query_terms=[],
            original_query="",
            db=mock_db,
            **self._make_index_args(
                sample_inverted_index, sample_doc_lengths,
                sample_term_freqs, sample_books_metadata
            ),
        )
        assert results == []

    def test_no_match_returns_empty(self, sample_inverted_index, sample_doc_lengths,
                                    sample_term_freqs, sample_books_metadata, mock_db):
        results = enhanced_search(
            query_terms=["zzznomatch"],
            original_query="zzznomatch",
            db=mock_db,
            **self._make_index_args(
                sample_inverted_index, sample_doc_lengths,
                sample_term_freqs, sample_books_metadata
            ),
        )
        assert results == []

    def test_result_has_required_keys(self, sample_inverted_index, sample_doc_lengths,
                                      sample_term_freqs, sample_books_metadata, mock_db):
        mock_db["pages"].find.return_value = [
            {"page_id": "1_1", "text_content": "war text", "display_page_number": "1"},
        ]
        results = enhanced_search(
            query_terms=["war"],
            original_query="war",
            db=mock_db,
            **self._make_index_args(
                sample_inverted_index, sample_doc_lengths,
                sample_term_freqs, sample_books_metadata
            ),
        )
        if results:
            required = {"page_id", "score", "book_title", "page_number",
                        "display_page_number", "domain", "preview"}
            assert required.issubset(results[0].keys())

    def test_max_10_results(self, mock_db):
        # Build large index with many matching pages
        big_index = {"query": {str(i): 1 for i in range(50)}}
        big_meta = {str(i): {"book_title": f"Book{i}", "page_number": i, "domain": "Test"}
                    for i in range(50)}
        big_lengths = {str(i): 100 for i in range(50)}
        big_freqs = {"query": 50}

        mock_db["pages"].find.return_value = [
            {"page_id": str(i), "text_content": "query text", "display_page_number": str(i)}
            for i in range(50)
        ]
        results = enhanced_search(
            query_terms=["query"],
            original_query="query",
            inverted_index=big_index,
            term_freqs=big_freqs,
            doc_lengths=big_lengths,
            books_metadata=big_meta,
            N=50,
            db=mock_db,
        )
        assert len(results) <= 10
