"""Runs the baseline reviewer on a split and stores one record per case."""

import argparse

import httpx

from secreview.agents.baseline import ReviewVariant, review_case
from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.agents.pilot_sample import load_pilot_sample
from secreview.agents.policy_requirements import PolicyAnalysis, load_policy_analysis
from secreview.agents.run_config import save_run_config
from secreview.agents.run_store import has_record, save_record
from secreview.datagen.settings import load_settings
from secreview.llm.client import VllmChatClient


def parse_arguments() -> argparse.Namespace:
    """Read the run name, the split, the case selection and the prompt variant."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    parser.add_argument("split")
    parser.add_argument("--policy-analysis", required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--topics", action="store_true")
    parser.add_argument("--silence", action="store_true")
    parser.add_argument("--compliant", action="store_true")
    return parser.parse_args()


def select_case_ids(split: str, limit: int, pilot: bool) -> list[str]:
    """List the cases to review: the pilot sample or the split, cut to the limit."""
    case_ids = load_pilot_sample() if pilot else list_case_ids(split)
    return case_ids[:limit] if limit else case_ids


def load_analyses(analysis_name: str) -> dict[str, PolicyAnalysis]:
    """Load the stored policy analysis of every policy version."""
    analyses: dict[str, PolicyAnalysis] = {}
    for version in load_settings().policy_versions:
        analyses[version] = load_policy_analysis(analysis_name, version)
    return analyses


def review_one(
    client: VllmChatClient,
    run_name: str,
    case_id: str,
    context: tuple[dict[str, PolicyAnalysis], ReviewVariant],
) -> None:
    """Review one case that has no record yet and store the record."""
    analyses, variant = context
    materials = load_case_materials(case_id)
    analysis = analyses[materials.labels.policy_version]
    record = review_case(client, materials, analysis, variant)
    save_record(run_name, record)
    print(case_id, len(record.findings), record.parse_error)


def review_cases(run_name: str, case_ids: list[str], variant: ReviewVariant) -> None:
    """Review every case that has no record in the run yet."""
    save_run_config(run_name, variant)
    context = (load_analyses(variant.policy_analysis), variant)
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for case_id in case_ids:
            if not has_record(run_name, case_id):
                review_one(client, run_name, case_id, context)


def main() -> None:
    """Run the baseline reviewer as configured on the command line."""
    arguments = parse_arguments()
    variant = ReviewVariant(
        use_topics=arguments.topics,
        ask_for_silence=arguments.silence,
        allow_compliant=arguments.compliant,
        policy_analysis=arguments.policy_analysis,
    )
    case_ids = select_case_ids(arguments.split, arguments.limit, arguments.pilot)
    review_cases(arguments.run_name, case_ids, variant)


if __name__ == "__main__":
    main()
