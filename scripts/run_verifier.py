"""Runs a follow-up call on a stored verdict run."""

import argparse
import json
import shutil

import httpx

from secreview.agents.case_materials import load_case_materials
from secreview.agents.policy_requirements import load_policy_analysis
from secreview.agents.verdict_followups import followup_case
from secreview.agents.verdict_store import (
    has_verdict_record,
    load_verdict_record,
    save_verdict_record,
    verdict_run_directory,
)
from secreview.agents.verdict_verifier import verify_case
from secreview.evaluation.verdict_run import list_run_case_ids, read_analysis_name
from secreview.llm.client import VllmChatClient
from secreview.review_settings import REVIEW_SETTINGS


def parse_arguments() -> argparse.Namespace:
    """Read the source run and the name of the run that gets the new confidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("source_run")
    parser.add_argument("target_run")
    modes: list[str] = ["verify", "severity", "verbal"]
    parser.add_argument("--mode", choices=modes, default="verify")
    return parser.parse_args()


def copy_config(arguments: argparse.Namespace) -> None:
    """Copy the run configuration and note that a verifier produced the confidence."""
    target = verdict_run_directory(arguments.target_run)
    target.mkdir(parents=True, exist_ok=True)
    config_name = REVIEW_SETTINGS.verdict.run_config_file
    source = verdict_run_directory(arguments.source_run) / config_name
    shutil.copy(source, target / config_name)
    config = json.loads((target / config_name).read_text(encoding="utf-8"))
    config["followup"] = f"{arguments.mode} on {arguments.source_run}"
    (target / config_name).write_text(json.dumps(config, indent=1), encoding="utf-8")


def verify_one(
    client: VllmChatClient,
    arguments: argparse.Namespace,
    analysis_name: str,
    case_id: str,
) -> None:
    """Verify the verdicts of one case and store the new record."""
    materials = load_case_materials(case_id)
    version = materials.labels.policy_version
    analysis = load_policy_analysis(analysis_name, version)
    record = load_verdict_record(arguments.source_run, case_id)
    if arguments.mode == "verify":
        checked = verify_case(client, materials, analysis, record)
    else:
        checked = followup_case(client, materials, analysis, record, arguments.mode)
    save_verdict_record(arguments.target_run, checked)
    print(f"done {case_id}", flush=True)


def main() -> None:
    """Verify every stored case of the source run that the target lacks."""
    arguments = parse_arguments()
    copy_config(arguments)
    analysis_name = read_analysis_name(arguments.source_run)
    with httpx.Client() as http_client:
        client = VllmChatClient(http_client)
        for case_id in list_run_case_ids(arguments.source_run):
            if not has_verdict_record(arguments.target_run, case_id):
                verify_one(client, arguments, analysis_name, case_id)


if __name__ == "__main__":
    main()
