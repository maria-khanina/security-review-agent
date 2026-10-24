"""Prints the cost per document of verdict runs: calls, tokens and seconds."""

import argparse

from secreview.evaluation.verdict_cost import (
    CostSummary,
    estimate_run_cost,
    measured_run_cost,
)


def parse_arguments() -> argparse.Namespace:
    """Read the runs and whether their verifier calls should be counted."""
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--verifier", action="store_true")
    parser.add_argument("--estimate", action="store_true")
    return parser.parse_args()


def describe(name: str, cost: CostSummary) -> str:
    """Format the cost per document of one run."""
    per = cost.documents
    kind = "estimated" if cost.estimated else "measured"
    return (
        f"{name:30} {kind:9} calls {cost.calls / per:6.1f}  "
        f"prompt tokens {cost.prompt_tokens / per:8.0f}  "
        f"generated tokens {cost.completion_tokens / per:7.0f}  "
        f"seconds {cost.seconds / per:6.1f}"
    )


def main() -> None:
    """Print one line per run."""
    arguments = parse_arguments()
    for run in arguments.runs:
        if arguments.estimate:
            cost = estimate_run_cost(run, arguments.verifier)
        else:
            cost = measured_run_cost(run)
        print(describe(run, cost))


if __name__ == "__main__":
    main()
