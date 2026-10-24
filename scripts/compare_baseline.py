"""Scores a free-form reviewer run with the verdict scores, on the pilot cases."""

import argparse

from secreview.agents.pilot_sample import load_pilot_sample
from secreview.evaluation.baseline_as_verdicts import score_baseline_run
from secreview.evaluation.verdict_scores import VerdictScores, summarize_verdicts


def parse_arguments() -> argparse.Namespace:
    """Read the free-form run to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    return parser.parse_args()


def print_scores(scores: VerdictScores) -> None:
    """Print how many verdicts are shown to the user and how many are right."""
    item = scores.reportable
    rate = item.false_alarm_rate
    print(f"shown: recall {item.recall:.3f} false alarm rate {rate:.3f}")
    violated = scores.report.per_class["violated"]
    print(f"violated recall {violated.recall:.3f} precision {violated.precision:.3f}")
    given = sum(row["violated"] for row in scores.report.confusion.values())
    print(f"predicted violated {given}")


def main() -> None:
    """Print the scores of the findings that are comparable with verdicts."""
    arguments = parse_arguments()
    outcomes = score_baseline_run(arguments.run_name, load_pilot_sample())
    print_scores(summarize_verdicts(outcomes))


if __name__ == "__main__":
    main()
