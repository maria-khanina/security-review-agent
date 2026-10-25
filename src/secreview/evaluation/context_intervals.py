"""Recall of the ways to choose the context with intervals over documents."""

import numpy as np
from pydantic import BaseModel

from secreview.agents.case_materials import load_case_materials
from secreview.evaluation.variant_pooled import (
    Outcome,
    difference_interval,
    draws_over,
    interval,
    pool,
    primary_recall,
)
from secreview.evaluation.variant_scores import (
    load_variant,
    raw_classes,
    raw_scores,
    score_variant,
)


class ContextScore(BaseModel):
    context: str
    recall_at_budget: float
    interval: tuple[float, float]
    difference: tuple[float, float, float]
    shown_precision: float


def load_outcome(run: str) -> Outcome:
    """Load the raw answers of a run as an outcome."""
    data = load_variant(run)
    return Outcome(data=data, chosen=raw_classes(data), score=raw_scores(data))


def load_pooled(runs: list[str]) -> Outcome:
    """Load the raw answers of runs on several sets of designs as one outcome."""
    outcomes: list[Outcome] = [load_outcome(run) for run in runs]
    pooled = outcomes[0]
    for later in outcomes[1:]:
        pooled = pool(pooled, later)
    return pooled


def mean_words(cases: list[str]) -> int:
    """Count the words of an average design of the cases."""
    counts: list[int] = []
    for case in cases:
        counts.append(len(load_case_materials(case).design_text.split()))
    return int(np.mean(counts))


def series_of(outcome: Outcome, cases: list[str]) -> list[float]:
    """Compute the recall at the budget on every resample of the cases."""
    resamples = draws_over(np.array(cases))
    return [primary_recall(outcome, names) for names in resamples]


def score_contexts(
    outcomes: dict[str, Outcome],
    cases: list[str],
) -> list[ContextScore]:
    """Score every context on the cases, paired with the first context."""
    names: list[str] = list(outcomes)
    series: dict[str, list[float]] = {}
    for name in names:
        series[name] = series_of(outcomes[name], cases)
    scores: list[ContextScore] = []
    for name in names:
        scores.append(score_one(name, outcomes[name], cases, series, names[0]))
    return scores


def score_one(
    name: str,
    outcome: Outcome,
    cases: list[str],
    series: dict[str, list[float]],
    reference: str,
) -> ContextScore:
    """Score one context on the cases with its interval and the paired difference."""
    rows = np.where(np.isin(outcome.data.documents, cases))[0]
    metrics = score_variant(outcome.data, outcome.chosen, outcome.score, rows)
    return ContextScore(
        context=name,
        recall_at_budget=primary_recall(outcome, np.array(cases)),
        interval=interval(series[name]),
        difference=difference_interval(series[name], series[reference]),
        shown_precision=metrics.precision,
    )


def format_group(
    label: str,
    cases: list[str],
    scores: list[ContextScore],
) -> list[str]:
    """Write the lines of one group of designs."""
    lines: list[str] = []
    words = mean_words(cases)
    for item in scores:
        low, high = item.interval
        mean, gap_low, gap_high = item.difference
        lines.append(
            f"| {label} | {words} | {len(cases)} | {item.context} | "
            f"{item.recall_at_budget:.2f} ({low:.2f} to {high:.2f}) | "
            f"{mean:+.3f} ({gap_low:+.3f} to {gap_high:+.3f}) | "
            f"{item.shown_precision:.2f} |"
        )
    return lines
