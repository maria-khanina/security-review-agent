"""Compares top 10, top 20 and the whole document by the length of the designs."""

import argparse
from pathlib import Path

from secreview.agents.case_materials import list_case_ids
from secreview.evaluation.context_table import (
    context_table,
    length_buckets,
    lines_for_group,
)
from secreview.evaluation.verdict_run import list_run_case_ids

V4_RUNS = {
    "top 10": "v4_reasoned800",
    "top 20": "v4_top20_reasoned800",
    "whole document": "v4_whole_reasoned800",
}
SHORT_RUNS = {
    "top 10": "base24_top10_reasoned800",
    "top 20": "base24_full_reasoned800",
    "whole document": "base24_whole_reasoned800",
}
LONG_RUNS = {
    "top 10": "long_reasoned800",
    "top 20": "long_full_reasoned800",
    "whole document": "long_whole_reasoned800",
}
BUCKET_NAMES = ["v4, shortest third", "v4, middle third", "v4, longest third"]


def parse_arguments() -> argparse.Namespace:
    """Read the file to write."""
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file")
    return parser.parse_args()


def main() -> None:
    """Score the contexts on the thirds of v4 and on the short and long dev designs."""
    arguments = parse_arguments()
    lines: list[str] = []
    thirds = length_buckets(list_case_ids("v4"))
    for name, cases in zip(BUCKET_NAMES, thirds, strict=True):
        lines.extend(lines_for_group(name, V4_RUNS, cases))
    short_cases = list_run_case_ids(SHORT_RUNS["top 20"])
    lines.extend(lines_for_group("dev, base designs", SHORT_RUNS, short_cases))
    long_cases = list_run_case_ids(LONG_RUNS["top 10"])
    lines.extend(lines_for_group("dev, same designs extended", LONG_RUNS, long_cases))
    Path(arguments.output_file).write_text(context_table(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
