"""
Unit tests for the page-label extraction helpers in ingestion_service.

These helpers extract visible page numbers from OCR text when a PDF
has no embedded PageLabels dictionary.
"""

import pytest
from backend.src.services.ingestion_service import (
    _extract_page_num_from_text,
    _is_roman,
    _roman_to_int,
)


# ---------------------------------------------------------------------------
# _roman_to_int
# ---------------------------------------------------------------------------
class TestRomanToInt:
    def test_i(self):
        assert _roman_to_int("i") == 1

    def test_viii(self):
        assert _roman_to_int("viii") == 8

    def test_xv(self):
        assert _roman_to_int("xv") == 15

    def test_xxii(self):
        assert _roman_to_int("xxii") == 22

    def test_uppercase(self):
        assert _roman_to_int("XIV") == 14


# ---------------------------------------------------------------------------
# _is_roman
# ---------------------------------------------------------------------------
class TestIsRoman:
    def test_valid_lowercase(self):
        for token in ("i", "iv", "viii", "ix", "xv", "xxii", "xl", "xc"):
            assert _is_roman(token), f"Expected {token!r} to be Roman"

    def test_valid_uppercase(self):
        assert _is_roman("XIV")
        assert _is_roman("XXII")

    def test_empty_string_is_false(self):
        assert not _is_roman("")

    def test_plain_arabic_is_false(self):
        assert not _is_roman("3")
        assert not _is_roman("150")

    def test_non_roman_word_is_false(self):
        # "mix" parses as Roman 1009 which exceeds our 999 ceiling → False
        assert not _is_roman("mix")

    def test_regular_word_is_false(self):
        assert not _is_roman("CHAPTER")
        assert not _is_roman("PREFACE")


# ---------------------------------------------------------------------------
# _extract_page_num_from_text  (step-by-step with realistic headers)
# ---------------------------------------------------------------------------
class TestExtractPageNumFromText:

    # Step 1a — first line is JUST a number
    def test_first_line_only_number(self):
        assert _extract_page_num_from_text("42\nsome page content here") == "42"

    # Step 1b — first line is JUST a Roman numeral
    def test_first_line_only_roman(self):
        assert _extract_page_num_from_text("viii\nsome content") == "viii"

    def test_first_line_roman_uppercase(self):
        # Should normalise to lowercase
        assert _extract_page_num_from_text("XIV\ncontent") == "xiv"

    # Step 2a — leading Arabic: "2 CHAPTER 1 ..."
    def test_leading_arabic_number(self):
        assert _extract_page_num_from_text("2 CHAPTER 1. INTRODUCTION\ntext") == "2"

    def test_leading_arabic_does_not_match_section_ref(self):
        # "1.2. Section" starts with "1." not "1 " → no leading-number hit
        result = _extract_page_num_from_text("1.2. ALGORITHM SPECIFICATION 7\ncontent")
        # Step 3a picks up the trailing "7"
        assert result == "7"

    # Step 2b — leading Roman: "xxii PREFACE"
    def test_leading_roman(self):
        assert _extract_page_num_from_text("xxii PREFACE\nparagraph text") == "xxii"

    def test_leading_roman_mixed_case(self):
        assert _extract_page_num_from_text("Xvi PREFACE\ntext") == "xvi"

    # Step 3a — trailing Arabic: "PREFACE 3" or "WHAT IS AN ALGORITHM? 3"
    def test_trailing_arabic_number(self):
        assert _extract_page_num_from_text("WHAT IS AN ALGORITHM? 3\ntext") == "3"

    def test_chapter_trailing_number(self):
        # "Chapter 1" → trailing "1" matches step 3a
        assert _extract_page_num_from_text("Chapter 1\nbody text") == "1"

    # Step 3b — trailing Roman: "CONTENTS ix" or "PREFACE xv"
    def test_trailing_roman(self):
        assert _extract_page_num_from_text("CONTENTS ix\nmore content") == "ix"

    def test_trailing_roman_preface(self):
        assert _extract_page_num_from_text("PREFACE xvii\ntext") == "xvii"

    # Step 4 — last line is Roman (footer on a Preface page, not a TOC page)
    def test_last_line_roman_on_non_toc_page(self):
        text = "PREFACE\nThis is the preface content spanning.\nxv"
        assert _extract_page_num_from_text(text) == "xv"

    def test_last_line_roman_skipped_on_toc_page(self):
        # "Contents" first line → TOC guard → step 4 should not fire
        text = "Contents\nChapter 1 ... 1\nxv"
        # No earlier step matches; step 4 is suppressed → fallback = None
        assert _extract_page_num_from_text(text) is None

    def test_last_line_plain_number_not_returned(self):
        # Plain Arabic at end of TOC page — "553" should be ignored to avoid
        # picking up TOC page-references as page numbers.
        text = "CONTENTS\nChapter 10 ... 553\n553"
        assert _extract_page_num_from_text(text) is None

    # Edge cases
    def test_empty_string_returns_none(self):
        assert _extract_page_num_from_text("") is None

    def test_none_returns_none(self):
        assert _extract_page_num_from_text(None) is None

    def test_plain_text_no_page_number_returns_none(self):
        assert _extract_page_num_from_text("Just some body text here.") is None

    def test_whitespace_only_returns_none(self):
        assert _extract_page_num_from_text("   \n  \n   ") is None
