"""Judges the wording of every requirement again, one model call per requirement."""

import argparse

import httpx

from secreview.agents.policy_requirements import load_policy_analysis
from secreview.agents.wording_check import store_rechecked
from secreview.datagen.settings import load_settings
from secreview.llm.client import VllmChatClient


def parse_arguments() -> argparse.Namespace:
    """Read the name of the analysis set to improve and the name of the new set."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source_name")
    parser.add_argument("target_name")
    parser.add_argument("--versions", nargs="*", default=None)
    return parser.parse_args()


def main() -> None:
    """Store a copy of the analysis set with the wording judged one by one."""
    arguments = parse_arguments()
    settings = load_settings()
    versions: list[str] = arguments.versions or [
        *settings.policy_versions,
        *settings.new_policy_versions,
    ]
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for version in versions:
            analysis = load_policy_analysis(arguments.source_name, version)
            store_rechecked(arguments.target_name, client, analysis)
            print(version, len(analysis.requirements), flush=True)


if __name__ == "__main__":
    main()
