"""Extraction of gold character spans from marker-annotated design text.

Authors wrap important passages as ⟦ID|text⟧. Stripping the markers yields the
clean document the agent will see, while the marker positions become the gold
spans of planted flaws and satisfied rules.
"""

import re

MARKER_PATTERN = re.compile(r"⟦([A-Za-z0-9:_-]+)\|(.*?)⟧", re.DOTALL)
MARKER_OPEN = "⟦"
MARKER_CLOSE = "⟧"

MarkerSpans = dict[str, list[list[int]]]


class SpanCollector:
    def __init__(self) -> None:
        self.spans: MarkerSpans = {}
        self.removed_length = 0

    def replace(self, match: re.Match[str]) -> str:
        """Replace one marker by its inner text and record the inner span."""
        inner = match.group(2)
        start = match.start() - self.removed_length
        self.spans.setdefault(match.group(1), []).append([start, start + len(inner)])
        self.removed_length += len(match.group(0)) - len(inner)
        return inner


def strip_markers(marked_text: str) -> tuple[str, MarkerSpans]:
    """Remove markers and return clean text with the spans they enclosed."""
    collector = SpanCollector()
    clean_text = MARKER_PATTERN.sub(collector.replace, marked_text)
    if MARKER_OPEN in clean_text or MARKER_CLOSE in clean_text:
        raise ValueError("unbalanced or nested marker")
    return clean_text, collector.spans
