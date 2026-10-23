"""Scores a stored policy analysis set against the gold requirements, offline."""

import argparse

from secreview.agents.policy_requirements import load_policy_analysis
from secreview.datagen.settings import load_settings
from secreview.evaluation.policy_scores import score_policy_analysis


def parse_arguments() -> argparse.Namespace:
    """Read the name of the stored analysis set to score."""
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis_name")
    return parser.parse_args()


def main() -> None:
    """Print the scores of every policy version; no model is called."""
    arguments = parse_arguments()
    for version in load_settings().policy_versions:
        analysis = load_policy_analysis(arguments.analysis_name, version)
        print(score_policy_analysis(analysis).model_dump_json(indent=2))


if __name__ == "__main__":
    main()
