"""Ranks the design chunks for every requirement of a policy analysis."""

import argparse

from secreview.retrieval.requirement_rankings import (
    rank_split,
    save_rankings,
)


def parse_arguments() -> argparse.Namespace:
    """Read the split and the name of the stored policy analysis set."""
    parser = argparse.ArgumentParser()
    parser.add_argument("split")
    parser.add_argument("analysis_name")
    return parser.parse_args()


def main() -> None:
    """Compute and store the rankings; this needs the GPU, not the language model."""
    arguments = parse_arguments()
    rankings = rank_split(arguments.split, arguments.analysis_name)
    save_rankings(arguments.split, arguments.analysis_name, rankings)
    print(f"{len(rankings)} cases ranked")


if __name__ == "__main__":
    main()
