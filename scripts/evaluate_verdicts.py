"""Scores a stored verdict run, or compares it with a second run."""

import argparse
import json

from secreview.datagen.settings import project_path
from secreview.evaluation.verdict_run import (
    bootstrap_verdict_difference,
    bootstrap_verdict_run,
    score_run_cases,
    shared_outcomes,
)
from secreview.evaluation.verdict_scores import (
    CaseVerdictOutcome,
    VerdictScores,
    summarize_verdicts,
)
from secreview.review_settings import REVIEW_SETTINGS


def parse_arguments() -> argparse.Namespace:
    """Read the run, the split label and the optional run to compare against."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    parser.add_argument("--split", type=str, default="dev")
    parser.add_argument("--against", type=str, default="")
    return parser.parse_args()


def print_classes(scores: VerdictScores) -> None:
    """Print precision, recall and F1 of every verdict."""
    for verdict, item in scores.report.per_class.items():
        line = f"  {verdict:15} P {item.precision:.3f} R {item.recall:.3f}"
        print(f"{line} F1 {item.f1:.3f} n {item.support}")


def print_summary(scores: VerdictScores) -> None:
    """Print the verdict table, the defect scores and the quote scores."""
    print(f"pairs {scores.pairs}, missing {scores.missing_pairs}")
    with_quote = scores.accuracy_with_evidence
    print(f"accuracy {scores.accuracy:.3f}, with quote {with_quote:.3f}")
    print_classes(scores)
    print(f"defect recall {scores.defect_recall:.3f}")
    precision = scores.violated_precision_with_evidence
    print(f"violated precision with quote {precision:.3f}")
    print(f"quote rate {scores.evidence_rate}")
    print(f"recall by subtype {scores.recall_by_subtype}")
    print(f"confidence AUROC {scores.confidence_auroc}")


def save_metrics(arguments: argparse.Namespace, scores: VerdictScores) -> None:
    """Store the scores and their intervals next to the records of the run."""
    outcomes: list[CaseVerdictOutcome] = list(
        score_run_cases(arguments.run_name).values()
    )
    intervals = bootstrap_verdict_run(outcomes)
    path = project_path(REVIEW_SETTINGS.verdict.runs_directory) / arguments.run_name
    name = f"{REVIEW_SETTINGS.verdict.metrics_file_prefix}{arguments.split}.json"
    payload: dict[str, object] = {
        "scores": scores.model_dump(),
        "intervals": {key: item.model_dump() for key, item in intervals.items()},
    }
    (path / name).write_text(json.dumps(payload, indent=1), encoding="utf-8")
    for key, item in intervals.items():
        print(f"{key:34} {item.estimate:7.3f} [{item.low:7.3f}, {item.high:7.3f}]")


def print_difference(arguments: argparse.Namespace) -> None:
    """Print the paired difference second run minus first run."""
    first, second = shared_outcomes(
        score_run_cases(arguments.run_name),
        score_run_cases(arguments.against),
    )
    for key, item in bootstrap_verdict_difference(first, second).items():
        flag = "SIGNIFICANT" if item.significant else ""
        gap = item.difference
        change = f"{item.first:7.3f} -> {item.second:7.3f}"
        bounds = f"[{gap.low:+7.3f}, {gap.high:+7.3f}]"
        print(f"{key:34} {change}  diff {gap.estimate:+7.3f} {bounds} {flag}")


def main() -> None:
    """Score one run, or compare two runs on the cases they share."""
    arguments = parse_arguments()
    if arguments.against:
        print_difference(arguments)
        return
    outcomes: list[CaseVerdictOutcome] = list(
        score_run_cases(arguments.run_name).values()
    )
    scores = summarize_verdicts(outcomes)
    print_summary(scores)
    save_metrics(arguments, scores)


if __name__ == "__main__":
    main()
