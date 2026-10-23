"""Reading and writing the on-disk files of raw and processed cases."""

import json
from pathlib import Path
import random

from secreview.datagen.brief import DESIGN_MARKED_FILE, write_brief
from secreview.datagen.case_plan import plan_cases
from secreview.datagen.flaw_sampling import sample_flaws
from secreview.datagen.implementation import (
    build_implementation_text,
    implementation_file_name,
)
from secreview.datagen.models import Case
from secreview.datagen.settings import load_settings, project_path

CASE_FILE = "case.json"
BRIEF_FILE = "brief.md"
LABELS_FILE = "labels.json"
DESIGN_FILE = "design.md"
JSON_INDENT = 1


def raw_case_directory(case_id: str) -> Path:
    """Return the working directory of a case that is being authored."""
    return project_path(load_settings().paths.raw_directory) / case_id


def processed_case_directory(case_id: str) -> Path:
    """Return the directory of a finished, labeled case."""
    return project_path(load_settings().paths.processed_directory) / case_id


def write_text(path: Path, text: str) -> None:
    """Write UTF-8 text with Unix line endings."""
    path.write_text(text, encoding="utf-8", newline="\n")


def load_raw_case(case_id: str) -> Case:
    """Load the planned case stored in a raw case directory."""
    text = (raw_case_directory(case_id) / CASE_FILE).read_text(encoding="utf-8")
    return Case.model_validate_json(text)


def write_raw_case(case: Case) -> Path:
    """Write implementation, case record and brief of a planned case."""
    directory = raw_case_directory(case.case_id)
    directory.mkdir(parents=True, exist_ok=True)
    file_name = implementation_file_name(case.implementation_format)
    write_text(directory / file_name, build_implementation_text(case))
    case_json = json.dumps(case.model_dump(), indent=JSON_INDENT)
    write_text(directory / CASE_FILE, case_json)
    write_text(directory / BRIEF_FILE, write_brief(case))
    return directory


def is_finished(case_id: str) -> bool:
    """Tell whether a case already has final labels on disk."""
    return (processed_case_directory(case_id) / LABELS_FILE).exists()


def generate_dataset() -> list[Case]:
    """Plan every case, sample flaws, and write unfinished cases to disk."""
    settings = load_settings()
    flaw_generator = random.Random(settings.seed + settings.flaw_seed_offset)
    cases: list[Case] = []
    for planned in plan_cases():
        sample_flaws(planned.case, flaw_generator, planned.defective)
        if not is_finished(planned.case.case_id):
            write_raw_case(planned.case)
        cases.append(planned.case)
    return cases


def marked_design_path(case_id: str) -> Path:
    """Return where the marker-annotated design text of a case lives."""
    return raw_case_directory(case_id) / DESIGN_MARKED_FILE
