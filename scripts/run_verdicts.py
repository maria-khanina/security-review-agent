"""Runs the per-requirement verdict review on the cases of a split."""

import argparse
import json

import httpx

from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.agents.pilot_sample import load_pilot_sample
from secreview.agents.policy_requirements import load_policy_analysis
from secreview.agents.verdict_prompts import build_verdict_system_prompt
from secreview.agents.verdict_review import ContextChoice, review_case_verdicts
from secreview.agents.verdict_store import (
    has_verdict_record,
    save_verdict_record,
    verdict_run_directory,
)
from secreview.llm.client import VllmChatClient
from secreview.retrieval.requirement_rankings import SplitRankings, load_rankings
from secreview.review_settings import REVIEW_SETTINGS


def add_context_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the options that choose the design fragments shown to the model."""
    settings = REVIEW_SETTINGS.verdict
    parser.add_argument("--oracle", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--overview", type=int, default=0)
    parser.add_argument("--method", type=str, default=settings.ranker)
    parser.add_argument("--window", type=int, default=settings.window)
    parser.add_argument("--candidates", type=int, default=settings.candidates)
    parser.add_argument("--analysis", type=str, default=settings.analysis_set)


def parse_arguments() -> argparse.Namespace:
    """Read the run name, the split, the case selection and the context choice."""
    parser = argparse.ArgumentParser()
    parser.add_argument("run_name")
    parser.add_argument("--split", type=str, default="dev")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--limit", type=int, default=0)
    add_context_arguments(parser)
    return parser.parse_args()


def build_choice(arguments: argparse.Namespace) -> ContextChoice:
    """Collect the context and prompt options of the run."""
    return ContextChoice(
        method=arguments.method,
        window=arguments.window,
        candidates=arguments.candidates,
        oracle=arguments.oracle,
        strict=arguments.strict,
        overview_chars=arguments.overview,
    )


def select_case_ids(arguments: argparse.Namespace) -> list[str]:
    """List the cases to review: the pilot sample or the whole split, limited."""
    if arguments.pilot:
        case_ids = load_pilot_sample()
    else:
        case_ids = list_case_ids(arguments.split)
    return case_ids[: arguments.limit] if arguments.limit else case_ids


def write_run_config(arguments: argparse.Namespace, choice: ContextChoice) -> None:
    """Store what defines the run next to its records."""
    directory = verdict_run_directory(arguments.run_name)
    directory.mkdir(parents=True, exist_ok=True)
    config: dict[str, object] = {
        "choice": choice.model_dump(),
        "analysis": arguments.analysis,
        "split": arguments.split,
        "pilot": arguments.pilot,
        "system_prompt": build_verdict_system_prompt(
            arguments.strict, arguments.overview > 0
        ),
        "model": REVIEW_SETTINGS.llm.model,
        "temperature": REVIEW_SETTINGS.llm.temperature,
    }
    path = directory / REVIEW_SETTINGS.verdict.run_config_file
    path.write_text(json.dumps(config, indent=1), encoding="utf-8")


def review_one(
    client: VllmChatClient,
    arguments: argparse.Namespace,
    rankings: SplitRankings,
    case_id: str,
) -> None:
    """Review one case and store its record."""
    materials = load_case_materials(case_id)
    version = materials.labels.policy_version
    analysis = load_policy_analysis(arguments.analysis, version)
    choice = build_choice(arguments)
    case_rankings = rankings[case_id]
    record = review_case_verdicts(client, materials, analysis, case_rankings, choice)
    save_verdict_record(arguments.run_name, record)
    print(f"done {case_id}", flush=True)


def run_cases(arguments: argparse.Namespace) -> None:
    """Review every selected case that has no stored record yet."""
    rankings = load_rankings(arguments.split, arguments.analysis)
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for case_id in select_case_ids(arguments):
            if not has_verdict_record(arguments.run_name, case_id):
                review_one(client, arguments, rankings, case_id)


def main() -> None:
    """Run the verdict review as configured by the command line."""
    arguments = parse_arguments()
    choice = build_choice(arguments)
    write_run_config(arguments, choice)
    run_cases(arguments)


if __name__ == "__main__":
    main()
