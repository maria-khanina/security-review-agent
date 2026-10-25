"""Writes the tables that compare the variants of the pipeline on one test set."""

import argparse
from pathlib import Path

from secreview.evaluation.variant_table import (
    TableRow,
    cascade_rows,
    configuration_rows,
    decision_row,
    render_table,
)

CONFIGURATIONS = [
    ("A short reason, no overview", "dev2_base", "v4_base"),
    ("B short reason, overview", "dev2_overview800", "v4_overview800"),
    ("C reasoning, no overview", "dev2_reasoned_nooverview", "v4_reasoned_nooverview"),
    ("D reasoning, overview", "dev2_reasoned800", "v4_reasoned800"),
    ("E reasoning, architecture card", "dev2_card_reasoned", "v4_card_reasoned"),
]
CURVE = [
    ("1 requirement per call (list format)", "v4_batch1"),
    ("2 requirements per call", "v4_batch2"),
    ("4 requirements per call", "v4_batch4"),
    ("8 requirements per call", "v4_batch8"),
    ("top 10 fragments (D)", "v4_reasoned800"),
    ("top 20 fragments", "v4_top20_reasoned800"),
    ("whole document", "v4_whole_reasoned800"),
]


def parse_arguments() -> argparse.Namespace:
    """Read the files to write."""
    parser = argparse.ArgumentParser()
    parser.add_argument("table_file")
    parser.add_argument("curve_file")
    return parser.parse_args()


def main() -> None:
    """Score every variant and write the two tables."""
    arguments = parse_arguments()
    rows: list[TableRow] = []
    for label, dev_run, test_run in CONFIGURATIONS:
        rows.extend(configuration_rows(label, dev_run, test_run))
    rows.extend(cascade_rows("dev2_reasoned800", "v4_reasoned800"))
    Path(arguments.table_file).write_text(render_table(rows), encoding="utf-8")
    curve: list[TableRow] = [decision_row(label, run) for label, run in CURVE]
    Path(arguments.curve_file).write_text(render_table(curve), encoding="utf-8")


if __name__ == "__main__":
    main()
