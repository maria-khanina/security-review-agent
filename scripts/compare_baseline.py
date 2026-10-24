"""Scores a free-form reviewer run with the verdict scores, on the pilot cases."""

import argparse

from secreview.agents.pilot_sample import load_pilot_sample
from secreview.evaluation.baseline_as_verdicts import score_baseline_run
from secreview.evaluation.verdict_scores import summarize_verdicts


def parse_arguments() -> argparse.Namespace:
    """Read the free-form run to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    return parser.parse_args()


def main() -> None:
    """Print the scores of the findings that are comparable with verdicts."""
    arguments = parse_arguments()
    outcomes = score_baseline_run(arguments.run_name, load_pilot_sample())
    scores = summarize_verdicts(outcomes)
    violated = scores.report.per_class["violated"]
    print(f"defect recall {scores.defect_recall:.3f}")
    print(f"violated recall {violated.recall:.3f} precision {violated.precision:.3f}")
    print(f"recall by subtype {scores.recall_by_subtype}")
    given = sum(row["violated"] for row in scores.report.confusion.values())
    print(f"predicted violated {given}")


if __name__ == "__main__":
    main()
