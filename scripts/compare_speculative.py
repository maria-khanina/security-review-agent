"""Compares verdict runs served with and without speculative decoding.

Every run is compared with a baseline run on the cases both contain: seconds
and generated tokens per document, generated tokens per second, and how many
answers stay the same (verdict, whole reply).
"""

import argparse

from pydantic import BaseModel

from secreview.agents.verdict_review import RequirementRecord
from secreview.agents.verdict_store import load_verdict_record
from secreview.evaluation.verdict_run import list_run_case_ids


class RunComparison(BaseModel):
    """Speed and agreement of one run measured against the baseline."""

    documents: int
    seconds: float
    completion_tokens: int
    same_verdicts: int
    same_replies: int
    answers: int


def parse_arguments() -> argparse.Namespace:
    """Read the baseline run and the runs compared with it."""
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline")
    parser.add_argument("runs", nargs="+")
    return parser.parse_args()


def load_records(run_name: str, case_ids: list[str]) -> list[RequirementRecord]:
    """Load the requirement records of the given cases in a fixed order."""
    records: list[RequirementRecord] = []
    for case_id in case_ids:
        case_records = load_verdict_record(run_name, case_id).records
        records.extend(sorted(case_records, key=lambda item: item.requirement_id))
    return records


def compare_run(baseline: str, run_name: str) -> RunComparison:
    """Measure a run on the cases it shares with the baseline."""
    shared = sorted(set(list_run_case_ids(baseline)) & set(list_run_case_ids(run_name)))
    base_records = load_records(baseline, shared)
    run_records = load_records(run_name, shared)
    pairs: list[tuple[RequirementRecord, RequirementRecord]] = list(
        zip(base_records, run_records),
    )
    return RunComparison(
        documents=len(shared),
        seconds=sum(record.seconds for record in run_records),
        completion_tokens=sum(record.completion_tokens for record in run_records),
        same_verdicts=sum(first.verdict == second.verdict for first, second in pairs),
        same_replies=sum(
            first.raw_reply == second.raw_reply for first, second in pairs
        ),
        answers=len(pairs),
    )


def describe(run_name: str, comparison: RunComparison, base_seconds: float) -> str:
    """Format one comparison as a line of the report."""
    per_document = comparison.seconds / comparison.documents
    tokens_per_second = comparison.completion_tokens / comparison.seconds
    return (
        f"{run_name:40} documents {comparison.documents:3}  "
        f"seconds {per_document:6.1f}  "
        f"speed-up {base_seconds / comparison.seconds:5.2f}  "
        f"generated tokens per second {tokens_per_second:6.1f}  "
        f"same verdicts {comparison.same_verdicts}/{comparison.answers}  "
        f"same replies {comparison.same_replies}/{comparison.answers}"
    )


def main() -> None:
    """Print the baseline and every compared run, one line each."""
    arguments = parse_arguments()
    names: list[str] = [arguments.baseline, *arguments.runs]
    comparisons: list[RunComparison] = [
        compare_run(arguments.baseline, name) for name in names
    ]
    for name, comparison in zip(names, comparisons):
        base_seconds = compare_run(name, arguments.baseline).seconds
        print(describe(name, comparison, base_seconds))


if __name__ == "__main__":
    main()
