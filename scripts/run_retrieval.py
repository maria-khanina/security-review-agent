"""Scores every retriever and chunking variant on a split and stores the result."""

import argparse

from secreview.retrieval.experiment import run_experiment, save_result


def parse_arguments() -> argparse.Namespace:
    """Read the split to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("split")
    return parser.parse_args()


def main() -> None:
    """Run the retrieval experiment and report how many items it scored."""
    arguments = parse_arguments()
    result = run_experiment(arguments.split)
    save_result(result)
    variants = len(result.scores)
    print(f"{variants} variants, {result.skipped_items} items without a unit")


if __name__ == "__main__":
    main()
