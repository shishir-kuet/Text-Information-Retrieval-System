"""
tests/conftest.py
Shared pytest fixtures used by both unit and integration tests.
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_inverted_index():
    return {
        "war": {"1_1": 5, "2_3": 2},
        "peace": {"1_1": 3, "3_7": 1},
        "napoleon": {"2_3": 4, "3_7": 6},
    }


@pytest.fixture
def sample_doc_lengths():
    return {"1_1": 200, "2_3": 150, "3_7": 180}


@pytest.fixture
def sample_term_freqs():
    return {"war": 3, "peace": 2, "napoleon": 2}


@pytest.fixture
def sample_books_metadata():
    return {
        "1_1": {"book_title": "War and Peace", "page_number": 1, "domain": "Literature"},
        "2_3": {"book_title": "Napoleon", "page_number": 3, "domain": "History"},
        "3_7": {"book_title": "The Campaign", "page_number": 7, "domain": "History"},
    }


@pytest.fixture
def mock_db():
    """A MagicMock database with pages and books collections."""
    db = MagicMock()
    db["pages"].find.return_value = []
    db["pages"].find_one.return_value = None
    db["pages"].count_documents.return_value = 0
    db["books"].find.return_value = []
    db["books"].find_one.return_value = None
    db["books"].count_documents.return_value = 0
    return db
