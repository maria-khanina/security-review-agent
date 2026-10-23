"""Loading the texts and gold labels of a processed case."""

from pydantic import BaseModel

from secreview.datagen.case_files import LABELS_FILE, processed_case_directory
from secreview.datagen.labels import CaseLabels
from secreview.datagen.policies import load_policy_versions
from secreview.datagen.settings import load_settings, project_path

DESIGN_FILE = "design.md"


class CaseMaterials(BaseModel):
    case_id: str
    design_text: str
    policy_text: str
    labels: CaseLabels


def load_case_materials(case_id: str) -> CaseMaterials:
    """Read the design, policy and labels of one case."""
    directory = processed_case_directory(case_id)
    labels = CaseLabels.model_validate_json(
        (directory / LABELS_FILE).read_text(encoding="utf-8")
    )
    return CaseMaterials(
        case_id=case_id,
        design_text=(directory / DESIGN_FILE).read_text(encoding="utf-8"),
        policy_text=load_policy_versions()[labels.policy_version].text,
        labels=labels,
    )


def list_case_ids(split: str) -> list[str]:
    """List the processed cases that belong to a split, in id order."""
    case_ids: list[str] = []
    processed = project_path(load_settings().paths.processed_directory)
    for directory in sorted(processed.iterdir()):
        materials = load_case_materials(directory.name)
        if materials.labels.split == split:
            case_ids.append(directory.name)
    return case_ids
