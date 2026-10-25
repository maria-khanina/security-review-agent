"""Scores of the ways to choose the context, by the length of the designs."""

import numpy as np
from numpy.typing import NDArray

from secreview.agents.case_materials import load_case_materials
from secreview.evaluation.variant_scores import (
    VariantData,
    load_variant,
    raw_classes,
    raw_scores,
    score_variant,
)

BUCKET_COUNT = len("abc")


def count_words(case_id: str) -> int:
    """Count the words of the design text of a case."""
    return len(load_case_materials(case_id).design_text.split())


def length_buckets(case_ids: list[str]) -> list[list[str]]:
    """Cut the cases into groups of equal size by the length of their designs."""
    ordered = sorted(case_ids, key=count_words)
    size = -(-len(ordered) // BUCKET_COUNT)
    starts = range(0, len(ordered), size)
    return [ordered[start:][:size] for start in starts]


def rows_of(data: VariantData, case_ids: list[str]) -> NDArray[np.int64]:
    """List the rows that belong to the given cases."""
    return np.where(np.isin(data.documents, case_ids))[0]


def format_context_line(
    label: str,
    context: str,
    data: VariantData,
    cases: list[str],
) -> str:
    """Score one context on a group of cases and write a markdown line."""
    index = rows_of(data, cases)
    metrics = score_variant(data, raw_classes(data), raw_scores(data), index)
    words = int(np.mean([count_words(case) for case in cases]))
    recalls = " / ".join(f"{value:.2f}" for value in metrics.recall_at_budgets)
    return (
        f"| {label} | {words} | {len(cases)} | {context} | {metrics.recall:.2f} | "
        f"{metrics.precision:.2f} | {metrics.false_alarms_per_document:.2f} | "
        f"{recalls} |"
    )


def context_table(lines: list[str]) -> str:
    """Write the lines under the header of the table."""
    names: list[str] = [
        "Group of designs",
        "Words per design",
        "Designs",
        "Context",
        "Shown recall",
        "Shown precision",
        "False alarms per document",
        "Recall at 0.5 / 1 / 2 / 3 false alarms per document",
    ]
    separator = "|" + "---|" * len(names)
    return "\n".join(["| " + " | ".join(names) + " |", separator, *lines])


def lines_for_group(
    label: str,
    runs: dict[str, str],
    cases: list[str],
) -> list[str]:
    """Score every context of a group of designs."""
    return [
        format_context_line(label, context, load_variant(run), cases)
        for context, run in runs.items()
    ]
