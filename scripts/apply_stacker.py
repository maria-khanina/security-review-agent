"""Trains the decision layer on one verdict run and relabels another run with it."""

import argparse

from secreview.evaluation.verdict_stack_apply import apply_run


def parse_arguments() -> argparse.Namespace:
    """Read the training run, the run to relabel and the name of the result."""
    parser = argparse.ArgumentParser()
    parser.add_argument("train_run")
    parser.add_argument("apply_run")
    parser.add_argument("target_run")
    return parser.parse_args()


def main() -> None:
    """Train on the first run, relabel the second and store the third."""
    arguments = parse_arguments()
    apply_run(arguments.train_run, arguments.apply_run, arguments.target_run)
    print(f"relabelled {arguments.apply_run} into {arguments.target_run}")


if __name__ == "__main__":
    main()
