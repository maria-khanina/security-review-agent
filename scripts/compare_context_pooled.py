"""Compares top 10, top 20 and the whole document with intervals on v4 and v5."""

import argparse
from pathlib import Path

from secreview.agents.case_materials import list_case_ids
from secreview.evaluation.context_intervals import (
    format_group,
    load_outcome,
    load_pooled,
    score_contexts,
)
from secreview.evaluation.context_table import length_buckets
from secreview.evaluation.variant_pooled import Outcome
from secreview.evaluation.verdict_run import list_run_case_ids

CONTEXTS = ["top 10", "top 20", "whole document"]
SUFFIXES = ["reasoned800", "top20_reasoned800", "whole_reasoned800"]
BUCKETS = ["shortest third", "middle third", "longest third"]
HEADER = (
    "| Group of designs | Words per design | Designs | Context | "
    "Recall at 2 false alarms per document (95% interval) | "
    "Difference to top 10 (95% interval) | Shown precision |"
)


def parse_arguments() -> argparse.Namespace:
    """Read the file to write."""
    parser = argparse.ArgumentParser()
    parser.add_argument("output_file")
    return parser.parse_args()


def policy_outcomes(prefixes: list[str]) -> dict[str, Outcome]:
    """Load the outcome of every context on one or more sets of designs."""
    outcomes: dict[str, Outcome] = {}
    for context, suffix in zip(CONTEXTS, SUFFIXES, strict=True):
        outcomes[context] = load_pooled([f"{prefix}_{suffix}" for prefix in prefixes])
    return outcomes


def lines_of_set(
    title: str,
    prefixes: list[str],
    cases: list[str],
) -> list[str]:
    """Score the contexts on all designs and on the thirds by length."""
    outcomes = policy_outcomes(prefixes)
    lines = format_group(f"{title}, all", cases, score_contexts(outcomes, cases))
    for name, third in zip(BUCKETS, length_buckets(cases), strict=True):
        scores = score_contexts(outcomes, third)
        lines.extend(format_group(f"{title}, {name}", third, scores))
    return lines


def lines_of_dev() -> list[str]:
    """Score the contexts on the dev designs and on the same designs extended."""
    lines: list[str] = []
    groups: dict[str, tuple[str, str, str]] = {
        "dev, base designs": ("base24_top10", "base24_full", "base24_whole"),
        "dev, same designs extended": ("long", "long_full", "long_whole"),
    }
    for label, prefixes in groups.items():
        outcomes: dict[str, Outcome] = {}
        for context, prefix in zip(CONTEXTS, prefixes, strict=True):
            outcomes[context] = load_outcome(f"{prefix}_reasoned800")
        cases = list_run_case_ids(f"{prefixes[0]}_reasoned800")
        lines.extend(format_group(label, cases, score_contexts(outcomes, cases)))
    return lines


def main() -> None:
    """Write the table."""
    arguments = parse_arguments()
    fourth, fifth = list_case_ids("v4"), list_case_ids("v5")
    lines = lines_of_set("v4", ["v4"], fourth)
    lines.extend(lines_of_set("v5", ["v5"], fifth))
    lines.extend(lines_of_set("v4 and v5", ["v4", "v5"], [*fourth, *fifth]))
    lines.extend(lines_of_dev())
    separator = "|" + "---|" * (HEADER.count("|") - 1)
    text = "\n".join([HEADER, separator, *lines])
    Path(arguments.output_file).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
