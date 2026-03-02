"""Unit tests for index_service (load_index, build_index)."""

import pickle
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.src.services.index_service import load_index


class TestLoadIndex:
    def test_loads_valid_pickle(self, tmp_path):
        payload = {
            "inverted_index": {"word": {"p1": 1}},
            "term_freqs": {"word": 1},
            "doc_lengths": {"p1": 10},
            "books_metadata": {},
            "N": 1,
            "build_date": "2024-01-01",
        }
        index_file = tmp_path / "search_index.pkl"
        with open(index_file, "wb") as f:
            pickle.dump(payload, f)

        result = load_index(index_file)
        assert result["N"] == 1
        assert "inverted_index" in result
        assert "term_freqs" in result

    def test_raises_when_file_missing(self, tmp_path):
        missing = tmp_path / "missing.pkl"
        with pytest.raises(FileNotFoundError):
            load_index(missing)

    def test_preserves_all_keys(self, tmp_path):
        payload = {
            "inverted_index": {},
            "term_freqs": {},
            "doc_lengths": {},
            "books_metadata": {},
            "N": 0,
            "build_date": "2024-01-01",
        }
        index_file = tmp_path / "test.pkl"
        with open(index_file, "wb") as f:
            pickle.dump(payload, f)

        result = load_index(index_file)
        assert set(result.keys()) == set(payload.keys())
