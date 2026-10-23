"""Builds and stores the requirement lists of all policy versions."""

import argparse

import httpx

from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.policy_analysis import analyze_policy
from secreview.agents.policy_requirements import PolicyAnalysis, save_policy_analysis
from secreview.datagen.settings import load_settings
from secreview.evaluation.policy_scores import score_policy_analysis
from secreview.llm.client import VllmChatClient


def parse_arguments() -> argparse.Namespace:
    """Read the name of the analysis set and whether to use the gold locations."""
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis_name")
    parser.add_argument("--oracle", action="store_true")
    return parser.parse_args()


def report(analysis: PolicyAnalysis) -> None:
    """Print how many requirements were found and how they score."""
    print(analysis.policy_version, len(analysis.requirements))
    print(score_policy_analysis(analysis).model_dump_json(indent=2))


def analyze_with_model(analysis_name: str) -> None:
    """Ask the model for the requirements of every policy version and store them."""
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for version in load_settings().policy_versions:
            analysis = analyze_policy(client, version)
            save_policy_analysis(analysis_name, analysis)
            report(analysis)


def analyze_with_gold(analysis_name: str) -> None:
    """Store the gold requirement lists as an analysis set."""
    for version in load_settings().policy_versions:
        analysis = build_oracle_analysis(version)
        save_policy_analysis(analysis_name, analysis)
        print(version, len(analysis.requirements))


def main() -> None:
    """Store the analysis set by the chosen method."""
    arguments = parse_arguments()
    if arguments.oracle:
        analyze_with_gold(arguments.analysis_name)
    else:
        analyze_with_model(arguments.analysis_name)


if __name__ == "__main__":
    main()
