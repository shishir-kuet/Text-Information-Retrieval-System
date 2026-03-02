"""Tokenizer shared across search and index services."""

import re


def tokenize(text: str) -> list:
    """Lowercase and split text into alphanumeric tokens."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return text.split()
