"""Frozen configuration of a verdict run and the check against mixing two runs."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

from pydantic import BaseModel

from secreview.agents.case_materials import DESIGN_FILE, list_case_ids
from secreview.agents.policy_requirements import digest_analysis_set
from secreview.agents.verdict_prompts import (
    build_verdict_system_prompt,
    build_verdict_user_prompt,
)
from secreview.agents.verdict_reply import build_verdict_schema
from secreview.agents.verdict_review import ContextChoice
from secreview.agents.verdict_store import verdict_run_directory
from secreview.datagen.case_files import LABELS_FILE, processed_case_directory
from secreview.datagen.settings import PROJECT_ROOT, project_path
from secreview.retrieval.requirement_rankings import rankings_path
from secreview.review_settings import REVIEW_SETTINGS

NO_BATCH = 0
TEMPLATE_SAMPLE = ("requirement", ["fragment"], "overview")
VOLATILE_FIELDS = {"created_at", "commit", "decision", "note"}


class VerdictRunConfig(BaseModel):
    choice: dict[str, object]
    analysis: str
    split: str
    pilot: bool
    batch_size: int
    system_prompt: str
    user_prompt_digest: str
    schema_digest: str
    model: str
    temperature: float
    max_tokens: int
    top_logprobs: int
    analysis_digest: str
    rankings_digest: str
    data_digest: str
    data_version: str
    created_at: str
    commit: str
    decision: str
    note: str


def text_digest(text: str) -> str:
    """Return the digest of a text."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def files_digest(paths: list[Path]) -> str:
    """Return one digest of the bytes of several files in the given order."""
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.read_bytes())
    return digest.hexdigest()


def data_digest(split: str) -> str:
    """Return a digest of the designs and the gold labels of a split."""
    paths: list[Path] = []
    for case_id in list_case_ids(split):
        directory = processed_case_directory(case_id)
        paths += [directory / DESIGN_FILE, directory / LABELS_FILE]
    return files_digest(paths)


def current_commit() -> str:
    """Return the commit that the code was started from."""
    unknown = REVIEW_SETTINGS.verdict.unknown_commit
    command: list[str] = ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"]
    try:
        done = subprocess.run(command, capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return unknown
    return done.stdout.strip()


def build_verdict_run_config(
    choice: ContextChoice,
    analysis: str,
    split: str,
    pilot: bool,
    batch_size: int,
) -> VerdictRunConfig:
    """Collect everything that shapes the verdicts of a run."""
    settings = REVIEW_SETTINGS.verdict
    overview = choice.overview_chars > 0 or bool(choice.card_name)
    schema = json.dumps(build_verdict_schema(), sort_keys=True)
    sample = build_verdict_user_prompt(*TEMPLATE_SAMPLE)
    rankings = project_path(rankings_path(split, analysis))
    return VerdictRunConfig(
        choice=choice.model_dump(),
        analysis=analysis,
        split=split,
        pilot=pilot,
        batch_size=batch_size,
        system_prompt=build_verdict_system_prompt(
            choice.strict, overview, choice.reasoned
        ),
        user_prompt_digest=text_digest(sample),
        schema_digest=text_digest(schema),
        model=REVIEW_SETTINGS.llm.model,
        temperature=REVIEW_SETTINGS.llm.temperature,
        max_tokens=settings.max_tokens,
        top_logprobs=settings.top_logprobs,
        analysis_digest=digest_analysis_set(analysis),
        rankings_digest=files_digest([rankings]),
        data_digest=data_digest(split),
        data_version=settings.data_version,
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        commit=current_commit(),
        decision="",
        note="",
    )


def fingerprint(config: VerdictRunConfig) -> str:
    """Return the digest of the fields that decide the verdicts of a run."""
    fields = config.model_dump(exclude=VOLATILE_FIELDS)
    return text_digest(json.dumps(fields, sort_keys=True))


def config_path(run_name: str) -> Path:
    """Return the file with the configuration of a run."""
    return verdict_run_directory(run_name) / REVIEW_SETTINGS.verdict.run_config_file


def has_records(run_name: str) -> bool:
    """Tell whether the run directory holds any stored case."""
    suffix = REVIEW_SETTINGS.reply_file_suffix
    return any(verdict_run_directory(run_name).glob(f"c*{suffix}"))


def load_run_config(run_name: str) -> VerdictRunConfig:
    """Read the stored configuration of a run."""
    text = config_path(run_name).read_text(encoding="utf-8")
    return VerdictRunConfig.model_validate_json(text)


def write_run_config(run_name: str, config: VerdictRunConfig) -> None:
    """Store a configuration, creating the run directory when needed."""
    path = config_path(run_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=1), encoding="utf-8")


def store_run_config(run_name: str, config: VerdictRunConfig) -> None:
    """Store the configuration, refusing to continue a run made with another one."""
    if has_records(run_name):
        if fingerprint(load_run_config(run_name)) != fingerprint(config):
            raise ValueError(f"run {run_name} was made with another configuration")
        return
    write_run_config(run_name, config)


def with_analysis(config: VerdictRunConfig, analysis: str) -> VerdictRunConfig:
    """Return the configuration of the same run read with another analysis set."""
    changes: dict[str, str] = {
        "analysis": analysis,
        "analysis_digest": digest_analysis_set(analysis),
    }
    return config.model_copy(update=changes)
