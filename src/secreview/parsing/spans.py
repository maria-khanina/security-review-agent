"""Token-level overlap between character spans of one text."""

import re

TOKEN_PATTERN = re.compile(r"\w+")


def collect_token_indices(text: str, spans: list[tuple[int, int]]) -> set[int]:
    """Return the indices of the tokens that overlap any of the character spans."""
    indices: set[int] = set()
    for index, match in enumerate(TOKEN_PATTERN.finditer(text)):
        for start, end in spans:
            if match.start() < end and match.end() > start:
                indices.add(index)
                break
    return indices


def compute_overlap(first: set[int], second: set[int]) -> float:
    """Compute the intersection over union of two token index sets."""
    union = first | second
    if not union:
        return 0.0
    return len(first & second) / len(union)
