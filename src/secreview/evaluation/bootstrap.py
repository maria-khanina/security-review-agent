"""Bootstrap confidence intervals over documents, plain and paired between runs."""

import random

from pydantic import BaseModel

from secreview.evaluation.outcomes import CaseOutcome
from secreview.evaluation.summary import DetectionScores, Summary, summarize
from secreview.review_settings import REVIEW_SETTINGS


class Interval(BaseModel):
    estimate: float
    low: float
    high: float


class DifferenceInterval(BaseModel):
    first: float
    second: float
    difference: Interval
    significant: bool


def flatten_detection(name: str, scores: DetectionScores) -> dict[str, float]:
    """Flatten the detection scores of the loose or strict rule."""
    metrics: dict[str, float] = {
        f"{name}_precision": scores.precision,
        f"{name}_false_alarms_per_document": scores.false_alarms_per_document,
        f"{name}_recall_all": scores.recall_all_scorable,
        f"{name}_recall_important": scores.recall_important,
    }
    for budget, recall in scores.recall_important_at_budget.items():
        metrics[f"{name}_recall_important_at_{budget}"] = recall
    return metrics


def flatten_summary(summary: Summary) -> dict[str, float]:
    """Pick the headline numbers of a summary into one flat table."""
    metrics = flatten_detection("loose", summary.loose)
    metrics.update(flatten_detection("strict", summary.strict))
    metrics["type_macro_f1"] = summary.type_report.macro_f1
    metrics["action_macro_f1"] = summary.action_report.macro_f1
    metrics["severity_mae"] = summary.severity_ordinal.mean_absolute_error
    return metrics


def compute_metrics(outcomes: list[CaseOutcome]) -> dict[str, float]:
    """Compute the headline metrics of a set of case outcomes."""
    return flatten_summary(summarize(outcomes))


def draw_resample(count: int, generator: random.Random) -> list[int]:
    """Draw document positions with replacement."""
    return generator.choices(range(count), k=count)


def pick_outcomes(
    outcomes: list[CaseOutcome],
    positions: list[int],
) -> list[CaseOutcome]:
    """Select the outcomes at the drawn positions."""
    return [outcomes[position] for position in positions]


def build_interval(estimate: float, values: list[float]) -> Interval:
    """Turn resampled values into a percentile interval around the estimate."""
    ordered = sorted(values)
    tail = (1.0 - REVIEW_SETTINGS.evaluation.interval_level) / 2
    last = len(ordered) - 1
    low = ordered[min(int(tail * len(ordered)), last)]
    high = ordered[min(int((1.0 - tail) * len(ordered)), last)]
    return Interval(estimate=estimate, low=low, high=high)


def collect_samples(
    outcomes: list[CaseOutcome],
    generator: random.Random,
) -> dict[str, list[float]]:
    """Recompute every headline metric on each resample of the documents."""
    samples: dict[str, list[float]] = {}
    for _ in range(REVIEW_SETTINGS.evaluation.bootstrap_resamples):
        positions = draw_resample(len(outcomes), generator)
        metrics = compute_metrics(pick_outcomes(outcomes, positions))
        for name, value in metrics.items():
            samples.setdefault(name, []).append(value)
    return samples


def bootstrap_run(outcomes: list[CaseOutcome]) -> dict[str, Interval]:
    """Compute a bootstrap interval for every headline metric of one run."""
    generator = random.Random(REVIEW_SETTINGS.evaluation.bootstrap_seed)
    samples = collect_samples(outcomes, generator)
    estimates = compute_metrics(outcomes)
    intervals: dict[str, Interval] = {}
    for name, values in samples.items():
        intervals[name] = build_interval(estimates[name], values)
    return intervals


def align_outcomes(
    first: list[CaseOutcome],
    second: list[CaseOutcome],
) -> tuple[list[CaseOutcome], list[CaseOutcome]]:
    """Keep the documents both runs reviewed, in the same order."""
    first_by_case: dict[str, CaseOutcome] = {}
    second_by_case: dict[str, CaseOutcome] = {}
    for outcome in first:
        first_by_case[outcome.case_id] = outcome
    for outcome in second:
        second_by_case[outcome.case_id] = outcome
    shared = sorted(set(first_by_case) & set(second_by_case))
    aligned_first: list[CaseOutcome] = [first_by_case[key] for key in shared]
    aligned_second: list[CaseOutcome] = [second_by_case[key] for key in shared]
    return aligned_first, aligned_second


def summarize_gaps(
    first: dict[str, float],
    second: dict[str, float],
    gaps: dict[str, list[float]],
) -> dict[str, DifferenceInterval]:
    """Wrap resampled differences into intervals with a significance flag."""
    result: dict[str, DifferenceInterval] = {}
    for name, values in gaps.items():
        interval = build_interval(second[name] - first[name], values)
        excludes_zero = interval.low > 0.0 or interval.high < 0.0
        result[name] = DifferenceInterval(
            first=first[name],
            second=second[name],
            difference=interval,
            significant=excludes_zero,
        )
    return result


def collect_gaps(
    first: list[CaseOutcome],
    second: list[CaseOutcome],
    generator: random.Random,
) -> dict[str, list[float]]:
    """Recompute the metric differences on shared resamples of the documents."""
    gaps: dict[str, list[float]] = {}
    for _ in range(REVIEW_SETTINGS.evaluation.bootstrap_resamples):
        positions = draw_resample(len(first), generator)
        one = compute_metrics(pick_outcomes(first, positions))
        two = compute_metrics(pick_outcomes(second, positions))
        for name in one:
            gaps.setdefault(name, []).append(two[name] - one[name])
    return gaps


def bootstrap_difference(
    first: list[CaseOutcome],
    second: list[CaseOutcome],
) -> dict[str, DifferenceInterval]:
    """Compare two runs on the same resampled documents, metric by metric."""
    aligned_first, aligned_second = align_outcomes(first, second)
    generator = random.Random(REVIEW_SETTINGS.evaluation.bootstrap_seed)
    gaps = collect_gaps(aligned_first, aligned_second, generator)
    estimate_first = compute_metrics(aligned_first)
    estimate_second = compute_metrics(aligned_second)
    return summarize_gaps(estimate_first, estimate_second, gaps)
