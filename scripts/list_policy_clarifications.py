"""Writes the requirements to clarify for every policy version of an analysis set."""

import argparse
from pathlib import Path

from secreview.agents.policy_clarifications import (
    list_clarifications,
    render_clarifications,
)
from secreview.agents.policy_requirements import load_policy_analysis
from secreview.datagen.settings import load_settings
from secreview.evaluation.policy_scores import score_policy_analysis


def parse_arguments() -> argparse.Namespace:
    """Read the analysis set and the file to write."""
    parser = argparse.ArgumentParser()
    parser.add_argument("analysis_name")
    parser.add_argument("output_file")
    return parser.parse_args()


def describe_quality(analysis_name: str, version: str) -> str:
    """Write how well the not-clear wording was found, against the gold."""
    analysis = load_policy_analysis(analysis_name, version)
    wording = score_policy_analysis(analysis).wording
    return (
        f"Found {wording.not_clear_recall:.2f} of the requirements to clarify, "
        f"{wording.not_clear_precision:.2f} of the listed ones are right.\n"
    )


def main() -> None:
    """Write the list of every policy version."""
    arguments = parse_arguments()
    settings = load_settings()
    versions: list[str] = [*settings.policy_versions, *settings.new_policy_versions]
    sections: list[str] = []
    for version in versions:
        analysis = load_policy_analysis(arguments.analysis_name, version)
        sections.append(render_clarifications(version, list_clarifications(analysis)))
        sections.append(describe_quality(arguments.analysis_name, version))
    Path(arguments.output_file).write_text("\n".join(sections), encoding="utf-8")


if __name__ == "__main__":
    main()
