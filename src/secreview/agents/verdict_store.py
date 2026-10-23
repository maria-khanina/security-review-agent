"""Saving and loading the records of a named verdict run."""

from pathlib import Path

from secreview.agents.verdict_review import VerdictCaseRecord
from secreview.datagen.settings import project_path
from secreview.review_settings import REVIEW_SETTINGS


def verdict_run_directory(run_name: str) -> Path:
    """Return the directory that holds the records of a verdict run."""
    return project_path(REVIEW_SETTINGS.verdict.runs_directory) / run_name


def verdict_record_path(run_name: str, case_id: str) -> Path:
    """Return the file of one case record inside a verdict run."""
    suffix = REVIEW_SETTINGS.reply_file_suffix
    return verdict_run_directory(run_name) / f"{case_id}{suffix}"


def has_verdict_record(run_name: str, case_id: str) -> bool:
    """Tell whether a case was already reviewed in the run."""
    return verdict_record_path(run_name, case_id).exists()


def save_verdict_record(run_name: str, record: VerdictCaseRecord) -> None:
    """Write one case record, creating the run directory when needed."""
    path = verdict_record_path(run_name, record.case_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=1), encoding="utf-8")


def load_verdict_record(run_name: str, case_id: str) -> VerdictCaseRecord:
    """Read the record of a case from a verdict run."""
    text = verdict_record_path(run_name, case_id).read_text(encoding="utf-8")
    return VerdictCaseRecord.model_validate_json(text)
