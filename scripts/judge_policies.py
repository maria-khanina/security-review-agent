"""Judges the wording and the contradictions of the requirements of every policy."""

import argparse

import httpx

from secreview.agents.pair_contradictions import (
    SentenceEmbedder,
    detect_contradictions,
)
from secreview.agents.policy_requirements import (
    load_policy_analysis,
    save_policy_analysis,
)
from secreview.agents.wording_check import recheck_wording
from secreview.datagen.settings import load_settings
from secreview.llm.client import VllmChatClient


def parse_arguments() -> argparse.Namespace:
    """Read the name of the analysis set to improve and the name of the new set."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source_name")
    parser.add_argument("target_name")
    parser.add_argument("--versions", nargs="*", default=None)
    return parser.parse_args()


def judge_version(
    client: VllmChatClient,
    embedder: SentenceEmbedder,
    source_name: str,
    target_name: str,
    version: str,
) -> None:
    """Judge the wording and the contradictions of one policy version and store them."""
    analysis = load_policy_analysis(source_name, version)
    worded = recheck_wording(client, analysis)
    judged = detect_contradictions(client, embedder, worded)
    save_policy_analysis(target_name, judged)
    print(version, len(judged.requirements), flush=True)


def main() -> None:
    """Store a copy of the analysis set with wording and contradictions judged."""
    arguments = parse_arguments()
    settings = load_settings()
    everything: list[str] = [*settings.policy_versions, *settings.new_policy_versions]
    embedder = SentenceEmbedder()
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for version in arguments.versions or everything:
            judge_version(
                client,
                embedder,
                arguments.source_name,
                arguments.target_name,
                version,
            )


if __name__ == "__main__":
    main()
