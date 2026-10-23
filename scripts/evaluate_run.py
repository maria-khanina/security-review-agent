"""Scores the stored records of a baseline run against the gold labels."""

import argparse

from pydantic import TypeAdapter

from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.agents.run_store import has_record, load_record, run_directory
from secreview.evaluation.matching import CaseOutcome, match_case
from secreview.evaluation.summary import summarize
from secreview.review_settings import REVIEW_SETTINGS


def parse_arguments() -> argparse.Namespace:
    """Read the run name and the split to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    parser.add_argument("split")
    return parser.parse_args()


def save_results(
    run_name: str,
    split: str,
    outcomes: list[CaseOutcome],
) -> None:
    """Write the summary metrics and the per-case outcomes next to the records."""
    directory = run_directory(run_name)
    suffix = REVIEW_SETTINGS.reply_file_suffix
    metrics_name = f"{REVIEW_SETTINGS.metrics_file_prefix}{split}{suffix}"
    outcomes_name = f"{REVIEW_SETTINGS.outcomes_file_prefix}{split}{suffix}"
    summary = summarize(outcomes)
    (directory / metrics_name).write_text(summary.model_dump_json(indent=2), "utf-8")
    outcomes_json = TypeAdapter(list[CaseOutcome]).dump_json(outcomes, indent=2)
    (directory / outcomes_name).write_bytes(outcomes_json)
    print(summary.model_dump_json(indent=2))


def main() -> None:
    """Score the run on the split, print the metrics and save them."""
    arguments = parse_arguments()
    outcomes: list[CaseOutcome] = []
    for case_id in list_case_ids(arguments.split):
        if not has_record(arguments.run_name, case_id):
            continue
        record = load_record(arguments.run_name, case_id)
        outcomes.append(match_case(load_case_materials(case_id), record))
    save_results(arguments.run_name, arguments.split, outcomes)


if __name__ == "__main__":
    main()
