"""Prints the retrieval metrics of every variant for one group of items."""

import argparse

from secreview.evaluation.bootstrap import Interval
from secreview.retrieval.experiment import load_result
from secreview.retrieval.metrics import ItemScore
from secreview.retrieval.report import (
    GROUPS,
    compute_differences,
    compute_intervals,
    select_group,
)

COLUMNS = [
    "hit_at_1",
    "hit_at_3",
    "hit_at_5",
    "hit_at_10",
    "full_at_5",
    "reciprocal_rank",
    "full_rank",
    "full_characters",
    "full_fraction",
    "hit_within_600",
    "full_within_600",
    "full_within_1200",
]


def parse_arguments() -> argparse.Namespace:
    """Read the split, the item group and the optional reference variant."""
    parser = argparse.ArgumentParser()
    parser.add_argument("split")
    parser.add_argument("group", choices=GROUPS)
    parser.add_argument("--reference", type=str, default="")
    parser.add_argument("--columns", nargs="*", default=COLUMNS)
    return parser.parse_args()


def format_cell(column: str, interval: Interval, paired: bool) -> str:
    """Format one value, marking paired gaps whose interval excludes zero."""
    mark = "*" if paired and (interval.low > 0.0 or interval.high < 0.0) else " "
    sign = "+" if paired else ""
    return f"{interval.estimate:{sign}{len(column) + 1}.3f}{mark}"


def format_row(
    name: str,
    width: int,
    scores: list[ItemScore],
    reference: list[ItemScore] | None,
    columns: list[str],
) -> str:
    """Format the means of a variant, or its paired gaps to the reference."""
    if reference is None:
        intervals = compute_intervals(scores)
    else:
        intervals = compute_differences(scores, reference)
    cells: list[str] = []
    for column in columns:
        cells.append(format_cell(column, intervals[column], reference is not None))
    return f"{name:{width}} " + " ".join(cells)


def print_table(
    variants: dict[str, list[ItemScore]],
    group: str,
    reference_name: str,
    columns: list[str],
) -> None:
    """Print one row per variant for the items of a group."""
    chosen: dict[str, list[ItemScore]] = {}
    for name, scores in variants.items():
        chosen[name] = select_group(scores, group)
    width = max(len(name) for name in chosen)
    print(f"{'variant':{width}} " + " ".join(f"{column} " for column in columns))
    for name, scores in sorted(chosen.items()):
        print(format_row(name, width, scores, chosen.get(reference_name), columns))


def main() -> None:
    """Load a stored experiment and print its table."""
    arguments = parse_arguments()
    result = load_result(arguments.split)
    print_table(result.scores, arguments.group, arguments.reference, arguments.columns)


if __name__ == "__main__":
    main()
