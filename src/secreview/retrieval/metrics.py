"""Scoring one ranking of chunks against the gold design spans of an item."""

from pydantic import BaseModel

from secreview.retrieval.gold import RetrievalItem, Span
from secreview.retrieval.units import Chunk, DesignUnit
from secreview.review_settings import REVIEW_SETTINGS


class ItemScore(BaseModel):
    case_id: str
    kind: str
    status: str
    values: dict[str, float]


class Trace(BaseModel):
    hit: list[bool]
    full: list[bool]
    characters: list[int]


def overlaps(unit: DesignUnit, span: Span) -> bool:
    """Tell whether the text of a unit shares any character with a span."""
    return unit.start < span[1] and unit.end > span[0]


def find_overlapping_units(units: list[DesignUnit], span: Span) -> set[int]:
    """List the units whose text overlaps a character span."""
    return {index for index, unit in enumerate(units) if overlaps(unit, span)}


def find_gold_units(units: list[DesignUnit], gold_spans: list[Span]) -> list[set[int]]:
    """For every gold span, list the units whose text overlaps it."""
    return [find_overlapping_units(units, span) for span in gold_spans]


def add_chunk(covered: set[int], chunk: Chunk, units: list[DesignUnit]) -> int:
    """Add the units of a chunk to the covered set and return the new characters."""
    added = 0
    for index in range(chunk.first, chunk.last + 1):
        if index not in covered:
            covered.add(index)
            added += len(units[index].text)
    return added


def trace_ranking(
    units: list[DesignUnit],
    chunks: list[Chunk],
    ranking: list[int],
    gold_units: list[set[int]],
) -> Trace:
    """Follow the ranking chunk by chunk and record what the context covers."""
    covered: set[int] = set()
    trace = Trace(hit=[], full=[], characters=[])
    characters = 0
    for position in ranking:
        characters += add_chunk(covered, chunks[position], units)
        trace.hit.append(any(group & covered for group in gold_units))
        trace.full.append(all(group & covered for group in gold_units))
        trace.characters.append(characters)
    return trace


def count_chunks_within(trace: Trace, budget: int) -> int:
    """Count the leading chunks whose merged context fits the character budget."""
    return sum(1 for characters in trace.characters if characters <= budget)


def flag_at(flags: list[bool], count: int) -> float:
    """Tell whether the first count chunks reached the goal, as 1.0 or 0.0."""
    if count == 0:
        return 0.0
    return float(flags[min(count, len(flags)) - 1])


def summarize_cutoffs(trace: Trace) -> dict[str, float]:
    """Record hit and full coverage after the first k chunks."""
    values: dict[str, float] = {}
    for cutoff in REVIEW_SETTINGS.retrieval.cutoffs:
        values[f"hit_at_{cutoff}"] = flag_at(trace.hit, cutoff)
        values[f"full_at_{cutoff}"] = flag_at(trace.full, cutoff)
    return values


def summarize_budgets(trace: Trace) -> dict[str, float]:
    """Record hit and full coverage when the context is limited in characters."""
    values: dict[str, float] = {}
    for budget in REVIEW_SETTINGS.retrieval.context_budgets:
        count = count_chunks_within(trace, budget)
        values[f"hit_within_{budget}"] = flag_at(trace.hit, count)
        values[f"full_within_{budget}"] = flag_at(trace.full, count)
    return values


def summarize_trace(trace: Trace, design_characters: int) -> dict[str, float]:
    """Turn a trace into the metrics of one item."""
    first_hit = trace.hit.index(True) + 1
    full_rank = trace.full.index(True) + 1
    full_characters = trace.characters[full_rank - 1]
    values: dict[str, float] = {
        "reciprocal_rank": 1.0 / first_hit,
        "full_rank": float(full_rank),
        "full_characters": float(full_characters),
        "full_fraction": full_characters / design_characters,
    }
    values.update(summarize_cutoffs(trace))
    values.update(summarize_budgets(trace))
    return values


def score_ranking(
    item: RetrievalItem,
    units: list[DesignUnit],
    chunks: list[Chunk],
    ranking: list[int],
) -> ItemScore:
    """Score the ranking of the chunks for one retrieval item."""
    gold_units = find_gold_units(units, item.gold_spans)
    trace = trace_ranking(units, chunks, ranking, gold_units)
    design_characters = sum(len(unit.text) for unit in units)
    return ItemScore(
        case_id=item.case_id,
        kind=item.kind,
        status=item.status,
        values=summarize_trace(trace, design_characters),
    )


def is_reachable(item: RetrievalItem, units: list[DesignUnit]) -> bool:
    """Tell whether every gold span of the item overlaps some unit."""
    return all(find_gold_units(units, item.gold_spans)) and bool(units)
