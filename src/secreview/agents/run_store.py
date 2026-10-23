"""Saving and loading the review records of a named baseline run."""

from pathlib import Path

from secreview.agents.baseline import ReviewRecord
from secreview.datagen.settings import project_path
from secreview.review_settings import REVIEW_SETTINGS


def run_directory(run_name: str) -> Path:
    """Return the directory that holds the records of a run."""
    return project_path(REVIEW_SETTINGS.runs_directory) / run_name


def record_path(run_name: str, case_id: str) -> Path:
    """Return the file of one case record inside a run."""
    suffix = REVIEW_SETTINGS.reply_file_suffix
    return run_directory(run_name) / f"{case_id}{suffix}"


def has_record(run_name: str, case_id: str) -> bool:
    """Tell whether a case was already reviewed in the run."""
    return record_path(run_name, case_id).exists()


def save_record(run_name: str, record: ReviewRecord) -> None:
    """Write one review record, creating the run directory when needed."""
    path = record_path(run_name, record.case_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(record.model_dump_json(indent=2), encoding="utf-8")


def load_record(run_name: str, case_id: str) -> ReviewRecord:
    """Read the review record of a case from a run."""
    text = record_path(run_name, case_id).read_text(encoding="utf-8")
    return ReviewRecord.model_validate_json(text)
