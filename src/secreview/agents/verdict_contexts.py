"""Choosing the design fragments shown to the model for one requirement."""

from secreview.retrieval.metrics import find_gold_units
from secreview.retrieval.units import DesignUnit

Bounds = list[tuple[int, int]]
Span = tuple[int, int]


def union_units(bounds: Bounds, count: int) -> list[int]:
    """List, in document order, the units of the first count chunks."""
    indices: set[int] = set()
    for first, last in bounds[:count]:
        indices.update(range(first, last + 1))
    return sorted(indices)


def gold_unit_range(units: list[DesignUnit], gold_spans: list[Span]) -> Span | None:
    """Return the first and last unit that overlap the gold spans of a requirement."""
    found: set[int] = set()
    for group in find_gold_units(units, gold_spans):
        found |= group
    return (min(found), max(found)) if found else None


def guarantee_gold(
    bounds: Bounds,
    count: int,
    units: list[DesignUnit],
    gold_spans: list[Span],
) -> Bounds:
    """Swap the last candidate for the gold fragment when the top ones miss it."""
    gold = gold_unit_range(units, gold_spans)
    if gold is None:
        return bounds[:count]
    shown: set[int] = set(union_units(bounds, count))
    if set(range(gold[0], gold[1] + 1)) <= shown:
        return bounds[:count]
    return bounds[: count - 1] + [gold]


def extract_overview(design_text: str, characters: int) -> str:
    """Return the opening of the design, cut at the last full line."""
    if characters <= 0:
        return ""
    opening = design_text[:characters]
    return opening.rsplit("\n", 1)[0] if "\n" in opening else opening


def list_fragments(units: list[DesignUnit], indices: list[int]) -> list[str]:
    """Return the texts of the chosen units."""
    return [units[index].text for index in indices]
