"""Locating quoted evidence inside a source text as character spans."""

import re

from rapidfuzz import fuzz

from secreview.review_settings import REVIEW_SETTINGS

WHITESPACE = re.compile(r"\s+")


def find_exact_span(text: str, quote: str) -> tuple[int, int] | None:
    """Find the quote allowing any whitespace difference between its words."""
    words = quote.split()
    if not words:
        return None
    pattern = r"\s+".join(re.escape(word) for word in words)
    match = re.search(pattern, text)
    return (match.start(), match.end()) if match else None


def find_fuzzy_span(text: str, quote: str) -> tuple[int, int] | None:
    """Find the best approximate location of the quote when it is close enough."""
    alignment = fuzz.partial_ratio_alignment(quote, text)
    if alignment is None:
        return None
    if alignment.score < REVIEW_SETTINGS.grounding.min_similarity:
        return None
    return alignment.dest_start, alignment.dest_end


def locate_quote(
    text: str,
    quote: str,
    minimum_characters: int,
) -> tuple[int, int] | None:
    """Return the character span of a quote, or None when it is not grounded."""
    cleaned = WHITESPACE.sub(" ", quote).strip()
    if len(cleaned) < minimum_characters:
        return None
    return find_exact_span(text, cleaned) or find_fuzzy_span(text, cleaned)
