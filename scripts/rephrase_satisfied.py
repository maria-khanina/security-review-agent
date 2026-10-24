"""Varies the wording of satisfied statements in the authored designs."""

from secreview.datagen.case_files import (
    load_raw_case,
    marked_design_path,
    write_text,
)
from secreview.datagen.phrasings import rephrase_design
from secreview.datagen.settings import load_settings, project_path


def list_raw_case_ids() -> list[str]:
    """List the authored cases, in id order."""
    raw = project_path(load_settings().paths.raw_directory)
    return sorted(directory.name for directory in raw.iterdir())


def rephrase_case(case_id: str) -> bool:
    """Rewrite the marked design of a case and report whether it changed."""
    path = marked_design_path(case_id)
    original = path.read_text(encoding="utf-8")
    version = load_raw_case(case_id).policy_version
    varied = rephrase_design(case_id, version, original)
    if varied != original:
        write_text(path, varied)
    return varied != original


def main() -> None:
    """Rephrase every authored case and report how many were changed."""
    case_ids = list_raw_case_ids()
    changed = sum(1 for case_id in case_ids if rephrase_case(case_id))
    print(f"{changed} of {len(case_ids)} designs changed")


if __name__ == "__main__":
    main()
