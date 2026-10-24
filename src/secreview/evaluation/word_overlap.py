"""Overlap of the meaningful words of two texts."""

from secreview.retrieval.rankers import tokenize
from secreview.review_settings import REVIEW_SETTINGS


def content_words(text: str) -> set[str]:
    """Collect the distinct words of a text that are long enough to carry meaning."""
    floor = REVIEW_SETTINGS.verdict.stacking_word_length
    return {word for word in tokenize(text) if len(word) > floor}


def overlap_share(requirement: str, other: str) -> float:
    """Share of the content words of the requirement that the other text contains."""
    words = content_words(requirement)
    return len(words & content_words(other)) / len(words) if words else 0.0
