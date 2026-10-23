"""Averages and paired bootstrap intervals of the retrieval scores."""

import numpy as np
from numpy.typing import NDArray

from secreview.evaluation.bootstrap import Interval, build_interval
from secreview.retrieval.gold import SATISFIED
from secreview.retrieval.metrics import ItemScore
from secreview.review_settings import REVIEW_SETTINGS

GROUPS = ["all", "flaws", "violation", "ambiguity", "not_clear", "satisfied"]
Matrix = NDArray[np.float64]
Counts = NDArray[np.intp]


def belongs_to(group: str, score: ItemScore) -> bool:
    """Tell whether an item score is part of a reporting group."""
    is_flaw = score.kind != SATISFIED
    tests: dict[str, bool] = {
        "all": True,
        "flaws": is_flaw,
        "violation": score.kind == "violation",
        "ambiguity": score.kind == "ambiguity",
        "not_clear": is_flaw and score.status != "clear",
        "satisfied": not is_flaw,
    }
    return tests[group]


def select_group(scores: list[ItemScore], group: str) -> list[ItemScore]:
    """Keep the item scores of one reporting group."""
    return [score for score in scores if belongs_to(group, score)]


def list_metric_names(scores: list[ItemScore]) -> list[str]:
    """List the metric names of the scores, in their recorded order."""
    return list(scores[0].values) if scores else []


def read_row(score: ItemScore, metric_names: list[str]) -> list[float]:
    """Read the values of the named metrics from an item score."""
    return [score.values[name] for name in metric_names]


def build_matrix(scores: list[ItemScore], metric_names: list[str]) -> Matrix:
    """Arrange the metric values as a matrix of items by metrics."""
    rows: list[list[float]] = [read_row(score, metric_names) for score in scores]
    return np.array(rows, dtype=np.float64)


def index_cases(scores: list[ItemScore]) -> tuple[NDArray[np.int64], int]:
    """Number the cases of the items and return the case number of every item."""
    case_ids = sorted({score.case_id for score in scores})
    numbers: dict[str, int] = {}
    for number, case_id in enumerate(case_ids):
        numbers[case_id] = number
    indices: list[int] = [numbers[score.case_id] for score in scores]
    return np.array(indices, dtype=np.int64), len(case_ids)


def draw_case_weights(case_count: int) -> Matrix:
    """Draw how often each case enters every resample, the same for all variants."""
    evaluation = REVIEW_SETTINGS.evaluation
    generator = np.random.default_rng(evaluation.bootstrap_seed)
    draws = generator.integers(
        0,
        case_count,
        size=(evaluation.bootstrap_resamples, case_count),
    )
    counts: list[Counts] = [np.bincount(row, minlength=case_count) for row in draws]
    return np.array(counts, dtype=np.float64)


def resample_means(
    matrix: Matrix,
    case_indices: NDArray[np.int64],
    weights: Matrix,
) -> Matrix:
    """Compute the metric means of every resample of the cases."""
    item_weights = weights[:, case_indices]
    totals = item_weights.sum(axis=1, keepdims=True)
    return (item_weights @ matrix) / totals


def to_interval(estimate: float, samples: NDArray[np.float64]) -> Interval:
    """Build the percentile interval of resampled values."""
    return build_interval(estimate, [float(value) for value in samples])


def pair_intervals(
    names: list[str],
    estimates: Matrix,
    samples: Matrix,
) -> dict[str, Interval]:
    """Pair every metric name with the interval of its resampled values."""
    intervals: dict[str, Interval] = {}
    for number, name in enumerate(names):
        intervals[name] = to_interval(float(estimates[number]), samples[:, number])
    return intervals


def compute_intervals(scores: list[ItemScore]) -> dict[str, Interval]:
    """Compute a case-level bootstrap interval for the mean of every metric."""
    names = list_metric_names(scores)
    matrix = build_matrix(scores, names)
    indices, case_count = index_cases(scores)
    samples = resample_means(matrix, indices, draw_case_weights(case_count))
    return pair_intervals(names, matrix.mean(axis=0), samples)


def compute_differences(
    scores: list[ItemScore],
    reference: list[ItemScore],
) -> dict[str, Interval]:
    """Compute the paired interval of the mean difference to a reference variant."""
    names = list_metric_names(scores)
    matrix = build_matrix(scores, names)
    other = build_matrix(reference, names)
    indices, case_count = index_cases(scores)
    weights = draw_case_weights(case_count)
    gaps = resample_means(matrix, indices, weights)
    gaps = gaps - resample_means(other, indices, weights)
    return pair_intervals(names, matrix.mean(axis=0) - other.mean(axis=0), gaps)
