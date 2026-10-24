"""Reviews the requirements of each design in groups, one model call per group."""

import argparse
import json

import httpx

from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.agents.policy_requirements import load_policy_analysis
from secreview.agents.verdict_batch import review_case_batched
from secreview.agents.verdict_review import ContextChoice
from secreview.agents.verdict_store import (
    has_verdict_record,
    save_verdict_record,
    verdict_run_directory,
)
from secreview.llm.client import VllmChatClient
from secreview.retrieval.requirement_rankings import SplitRankings, load_rankings
from secreview.review_settings import REVIEW_SETTINGS


def parse_arguments() -> argparse.Namespace:
    """Read the run name, the group size and the context options."""
    settings = REVIEW_SETTINGS.verdict
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    parser.add_argument("--size", type=int, required=True)
    parser.add_argument("--split", type=str, default="dev")
    parser.add_argument("--cases", nargs="*", default=[])
    parser.add_argument("--overview", type=int, default=0)
    parser.add_argument("--candidates", type=int, default=settings.candidates)
    parser.add_argument("--analysis", type=str, default=settings.analysis_set)
    return parser.parse_args()


def build_choice(arguments: argparse.Namespace) -> ContextChoice:
    """Collect the context options of the run."""
    return ContextChoice(
        method=REVIEW_SETTINGS.verdict.ranker,
        window=REVIEW_SETTINGS.verdict.window,
        candidates=arguments.candidates,
        oracle=False,
        strict=False,
        overview_chars=arguments.overview,
        reasoned=False,
    )


def write_run_config(arguments: argparse.Namespace, choice: ContextChoice) -> None:
    """Store what defines the run next to its records."""
    directory = verdict_run_directory(arguments.run_name)
    directory.mkdir(parents=True, exist_ok=True)
    config: dict[str, object] = {
        "choice": choice.model_dump(),
        "analysis": arguments.analysis,
        "split": arguments.split,
        "pilot": False,
        "batch_size": arguments.size,
        "model": REVIEW_SETTINGS.llm.model,
        "temperature": REVIEW_SETTINGS.llm.temperature,
    }
    path = directory / REVIEW_SETTINGS.verdict.run_config_file
    path.write_text(json.dumps(config, indent=1), encoding="utf-8")


def review_one(
    client: VllmChatClient,
    arguments: argparse.Namespace,
    choice: ContextChoice,
    rankings: SplitRankings,
    case_id: str,
) -> None:
    """Review one case in groups and store its record."""
    materials = load_case_materials(case_id)
    version = materials.labels.policy_version
    analysis = load_policy_analysis(arguments.analysis, version)
    record = review_case_batched(
        client, materials, analysis, rankings[case_id], choice, arguments.size
    )
    save_verdict_record(arguments.run_name, record)
    print(f"done {case_id}", flush=True)


def main() -> None:
    """Review every selected case that has no stored record yet."""
    arguments = parse_arguments()
    choice = build_choice(arguments)
    write_run_config(arguments, choice)
    rankings = load_rankings(arguments.split, arguments.analysis)
    case_ids = arguments.cases or list_case_ids(arguments.split)
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for case_id in case_ids:
            if not has_verdict_record(arguments.run_name, case_id):
                review_one(client, arguments, choice, rankings, case_id)


if __name__ == "__main__":
    main()
