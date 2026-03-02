"""Unit tests for tokenizer_service.tokenize()."""

import pytest
from backend.src.services.tokenizer_service import tokenize


class TestTokenize:
    def test_basic_lowercase(self):
        assert tokenize("Hello World") == ["hello", "world"]

    def test_punctuation_removed(self):
        assert tokenize("hello, world!") == ["hello", "world"]

    def test_numbers_preserved(self):
        result = tokenize("chapter 42 page 7")
        assert "42" in result
        assert "7" in result

    def test_empty_string(self):
        assert tokenize("") == []

    def test_only_punctuation(self):
        assert tokenize("!!! ???") == []

    def test_mixed_case_and_symbols(self):
        result = tokenize("War & Peace: A Novel")
        assert result == ["war", "peace", "a", "novel"]

    def test_multiple_spaces_split_correctly(self):
        result = tokenize("one   two   three")
        assert result == ["one", "two", "three"]

    def test_hyphenated_word(self):
        # Hyphen is non-alphanumeric → split into two tokens
        result = tokenize("well-known")
        assert "well" in result and "known" in result
