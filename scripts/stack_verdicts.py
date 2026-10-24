"""Relabels a stored verdict run with the cross-validated decision layer."""

import argparse

from secreview.evaluation.verdict_stack_run import stack_run


def parse_arguments() -> argparse.Namespace:
    """Read the source run and the name of the relabelled run."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source_run")
    parser.add_argument("target_run")
    parser.add_argument("--extra", nargs="*", default=[])
    parser.add_argument("--preset", type=str, default="all")
    return parser.parse_args()


def main() -> None:
    """Stack the signals of the source run and store the result as a new run."""
    arguments = parse_arguments()
    stack_run(
        arguments.source_run,
        arguments.target_run,
        arguments.extra,
        arguments.preset,
    )
    print(f"stacked {arguments.source_run} into {arguments.target_run}")


if __name__ == "__main__":
    main()
