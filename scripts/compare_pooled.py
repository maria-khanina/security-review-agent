"""Compares the pre-registered finalists on v5 and on v4 and v5 together."""

import argparse
from pathlib import Path

from secreview.evaluation.variant_pooled import (
    Outcome,
    PooledRow,
    difference_interval,
    draws,
    finalist_cost,
    outcome_of,
    pool,
    pooled_row,
    primary_recall,
)
from secreview.evaluation.variant_table import Cost
from secreview.review_settings import REVIEW_SETTINGS

DEV_PREFIX = "dev2"
TABLE_HEADER = (
    "| Variant | Shown recall | Shown precision | False alarms per document | "
    "Recall at 0.5 / 1 / 2 / 3 false alarms per document | "
    "Recall at 2 (95% interval) | Calls | Prompt tokens |"
)


def parse_arguments() -> argparse.Namespace:
    """Read the file to write."""
    parser = argparse.ArgumentParser()
    parser.add_argument("report_file")
    return parser.parse_args()


def format_row(row: PooledRow) -> str:
    """Write a row as a line of a markdown table."""
    position = REVIEW_SETTINGS.evaluation.primary_budget_position
    recalls = " / ".join(f"{value:.2f}" for value in row.recall_at_budgets)
    low, high = row.primary_interval
    return (
        f"| {row.label} | {row.recall:.2f} | {row.precision:.2f} | "
        f"{row.false_alarms_per_document:.2f} | {recalls} | "
        f"{row.recall_at_budgets[position]:.2f} ({low:.2f} to {high:.2f}) | "
        f"{row.cost.calls:.1f} | {row.cost.prompt_tokens:,.0f} |"
    )


def table_lines(title: str, rows: list[PooledRow]) -> list[str]:
    """Write one markdown table of the rows."""
    columns = TABLE_HEADER.count("|") - 1
    lines: list[str] = [f"### {title}", "", TABLE_HEADER, "|" + "---|" * columns]
    for row in rows:
        lines.append(format_row(row))
    return [*lines, ""]


def score_finalists(
    outcomes: list[Outcome],
    costs: list[Cost],
) -> tuple[list[PooledRow], list[list[float]]]:
    """Score every finalist and collect its primary recall on shared resamples."""
    resamples = draws(outcomes)
    rows: list[PooledRow] = []
    series: list[list[float]] = []
    finalists = REVIEW_SETTINGS.evaluation.finalists
    for finalist, outcome, cost in zip(finalists, outcomes, costs, strict=True):
        values: list[float] = [
            primary_recall(outcome, names) for names in resamples
        ]
        rows.append(pooled_row(finalist.label, outcome, cost, values))
        series.append(values)
    return rows, series


def pick_best(rows: list[PooledRow]) -> int | None:
    """Find the finalist with the best primary recall among the precise ones."""
    position = REVIEW_SETTINGS.evaluation.primary_budget_position
    minimum = REVIEW_SETTINGS.evaluation.minimum_shown_precision
    best: int | None = None
    best_recall = -1.0
    for index, row in enumerate(rows):
        recall = row.recall_at_budgets[position]
        if row.precision >= minimum and recall > best_recall:
            best, best_recall = index, recall
    return best


def difference_lines(rows: list[PooledRow], series: list[list[float]]) -> list[str]:
    """Write the paired differences of the primary recall against the best one."""
    best = pick_best(rows)
    if best is None:
        return ["No finalist reaches the minimum precision.", ""]
    lines: list[str] = [
        f"Best by the rule: {rows[best].label}",
        "",
        "| Variant | Difference of the recall at 2 against the best | 95% interval |",
        "|---|---|---|",
    ]
    for index, row in enumerate(rows):
        if index != best:
            mean, low, high = difference_interval(series[index], series[best])
            lines.append(f"| {row.label} | {mean:+.3f} | {low:+.3f} to {high:+.3f} |")
    return [*lines, ""]


def collect_outcomes(test_prefix: str) -> list[Outcome]:
    """Choose the classes and scores of every finalist on one set of designs."""
    outcomes: list[Outcome] = []
    for finalist in REVIEW_SETTINGS.evaluation.finalists:
        outcomes.append(outcome_of(finalist, DEV_PREFIX, test_prefix))
    return outcomes


def collect_costs(test_prefix: str) -> list[Cost]:
    """Measure the cost per document of every finalist."""
    costs: list[Cost] = []
    for finalist in REVIEW_SETTINGS.evaluation.finalists:
        costs.append(finalist_cost(finalist, test_prefix))
    return costs


def pool_outcomes(first: list[Outcome], second: list[Outcome]) -> list[Outcome]:
    """Join the outcomes of every finalist on two sets of designs."""
    pooled: list[Outcome] = []
    for left, right in zip(first, second, strict=True):
        pooled.append(pool(left, right))
    return pooled


def section_lines(
    title: str,
    outcomes: list[Outcome],
    costs: list[Cost],
) -> list[str]:
    """Write the table and the paired differences of one set of designs."""
    rows, series = score_finalists(outcomes, costs)
    return [*table_lines(title, rows), *difference_lines(rows, series)]


def report_text() -> str:
    """Score the finalists on v5 and on v4 and v5 together and write the tables."""
    fourth = collect_outcomes("v4")
    fifth = collect_outcomes("v5")
    pooled = pool_outcomes(fourth, fifth)
    costs = collect_costs("v5")
    lines: list[str] = []
    sections = (("v4", fourth), ("v5", fifth), ("v4 and v5 together", pooled))
    for title, outcomes in sections:
        lines.extend(section_lines(title, outcomes, costs))
    return "\n".join(lines)


def main() -> None:
    """Write the report."""
    arguments = parse_arguments()
    Path(arguments.report_file).write_text(report_text(), encoding="utf-8")


if __name__ == "__main__":
    main()
