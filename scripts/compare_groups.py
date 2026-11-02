"""Compares the finalists by leaving one policy out of the layer training."""

import argparse
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from secreview.agents.verdict_store import verdict_run_directory
from secreview.evaluation.variant_pooled import (
    Outcome,
    difference_interval,
    draws_over,
    finalist_cost,
    interval,
    outcome_of,
    pool,
    primary_recall,
    run_name,
)
from secreview.evaluation.variant_scores import score_variant
from secreview.review_settings import REVIEW_SETTINGS
from secreview.review_settings_models import FinalistSettings

GROUP_LABELS = {"dev": "v1 to v3"}
COST_PREFIX = "v5"
TABLE_HEADER = (
    "| Variant | Recall at 2 false alarms per document, mean over the policies "
    "(95% interval) | {groups} | Own decisions: recall / precision / "
    "false alarms per document | Prompt tokens |"
)


def group_label(group: str) -> str:
    """Name the policy group of a run prefix for a table."""
    return GROUP_LABELS.get(group, group)


def has_runs(finalist: FinalistSettings) -> bool:
    """Tell whether the finalist has a stored run for every policy group."""
    groups = REVIEW_SETTINGS.evaluation.policy_groups
    names: list[str] = [run_name(group, finalist.configuration) for group in groups]
    return all(verdict_run_directory(name).exists() for name in names)


def available_finalists() -> list[FinalistSettings]:
    """List the finalists that have a run on every policy group."""
    return [item for item in REVIEW_SETTINGS.evaluation.finalists if has_runs(item)]


def leave_one_out(finalist: FinalistSettings) -> dict[str, Outcome]:
    """Train the layer on all other policies and choose on each policy in turn."""
    groups = REVIEW_SETTINGS.evaluation.policy_groups
    outcomes: dict[str, Outcome] = {}
    for group in groups:
        others: list[str] = [other for other in groups if other != group]
        outcomes[group] = outcome_of(finalist, others, group)
    return outcomes


def documents_of(outcome: Outcome) -> NDArray[np.str_]:
    """List the distinct documents of an outcome."""
    return np.unique(outcome.data.documents)


def group_recall(outcome: Outcome) -> float:
    """Compute the recall at the primary budget on all documents of a policy."""
    return primary_recall(outcome, documents_of(outcome))


def mean_recall(outcomes: dict[str, Outcome], groups: list[str]) -> float:
    """Average the recall at the primary budget over the chosen policies."""
    return float(np.mean([group_recall(outcomes[group]) for group in groups]))


def resamples_by_group(
    reference: dict[str, Outcome],
) -> dict[str, list[NDArray[np.str_]]]:
    """Draw the same documents for every finalist, separately in each policy."""
    return {name: draws_over(documents_of(item)) for name, item in reference.items()}


def mean_series(
    outcomes: dict[str, Outcome],
    groups: list[str],
    resamples: dict[str, list[NDArray[np.str_]]],
) -> list[float]:
    """Average the recall over the policies on every resample of the documents."""
    count = len(resamples[groups[0]])
    series: list[float] = []
    for index in range(count):
        values: list[float] = [
            primary_recall(outcomes[group], resamples[group][index])
            for group in groups
        ]
        series.append(float(np.mean(values)))
    return series


def own_decisions(outcomes: dict[str, Outcome]) -> str:
    """Write recall, precision and false alarms of the variant's own decisions."""
    joined = list(outcomes.values())[0]
    for item in list(outcomes.values())[1:]:
        joined = pool(joined, item)
    index = np.arange(len(joined.data.gold))
    metrics = score_variant(joined.data, joined.chosen, joined.score, index)
    return (
        f"{metrics.recall:.2f} / {metrics.precision:.2f} / "
        f"{metrics.false_alarms_per_document:.2f}"
    )


def row_line(
    finalist: FinalistSettings,
    outcomes: dict[str, Outcome],
    groups: list[str],
    series: list[float],
) -> str:
    """Write one table row of a finalist."""
    low, high = interval(series)
    each = " | ".join(f"{group_recall(item):.2f}" for item in outcomes.values())
    cost = finalist_cost(finalist, COST_PREFIX)
    return (
        f"| {finalist.label} | {mean_recall(outcomes, groups):.2f} "
        f"({low:.2f} to {high:.2f}) | {each} | {own_decisions(outcomes)} | "
        f"{cost.prompt_tokens:,.0f} |"
    )


def best_index(means: list[float]) -> int:
    """Find the finalist with the highest mean recall."""
    return int(np.argmax(means))


def difference_lines(
    labels: list[str],
    means: list[float],
    series: list[list[float]],
) -> list[str]:
    """Write the paired differences of every finalist to the best one."""
    best = best_index(means)
    lines: list[str] = [
        f"Best mean recall: {labels[best]}",
        "",
        "| Variant | Difference to the best | 95% interval |",
        "|---|---|---|",
    ]
    for index, label in enumerate(labels):
        if index != best:
            gap, low, high = difference_interval(series[index], series[best])
            lines.append(f"| {label} | {gap:+.3f} | {low:+.3f} to {high:+.3f} |")
    return [*lines, ""]


def table_head(title: str, outcomes: dict[str, Outcome]) -> list[str]:
    """Write the title and the header of a table."""
    names = " | ".join(group_label(group) for group in outcomes)
    header = TABLE_HEADER.format(groups=names)
    divider = "|" + "---|" * (header.count("|") - 1)
    return [f"### {title}", "", header, divider]


def section_lines(
    title: str,
    groups: list[str],
    everything: list[tuple[FinalistSettings, dict[str, Outcome]]],
) -> list[str]:
    """Write the table and the paired differences averaged over some policies."""
    resamples = resamples_by_group(everything[0][1])
    labels: list[str] = [finalist.label for finalist, _ in everything]
    means: list[float] = [mean_recall(item, groups) for _, item in everything]
    series: list[list[float]] = [
        mean_series(item, groups, resamples) for _, item in everything
    ]
    lines: list[str] = table_head(title, everything[0][1])
    for position, (finalist, outcomes) in enumerate(everything):
        lines.append(row_line(finalist, outcomes, groups, series[position]))
    return [*lines, "", *difference_lines(labels, means, series)]


def report_text() -> str:
    """Score the finalists on every policy left out and write the tables."""
    settings = REVIEW_SETTINGS.evaluation
    everything: list[tuple[FinalistSettings, dict[str, Outcome]]] = [
        (item, leave_one_out(item)) for item in available_finalists()
    ]
    lines: list[str] = section_lines(
        "All five policies", settings.policy_groups, everything
    )
    similar = "Policies with similar verdict shares"
    lines += section_lines(similar, settings.matched_groups, everything)
    return "\n".join(lines)


def parse_arguments() -> argparse.Namespace:
    """Read the file to write."""
    parser = argparse.ArgumentParser()
    parser.add_argument("report_file")
    return parser.parse_args()


def main() -> None:
    """Write the report."""
    arguments = parse_arguments()
    Path(arguments.report_file).write_text(report_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
