"""Rules whose design claim stayed in the prose after drift was removed."""

from functools import cache

from pydantic import BaseModel
import yaml

from secreview.datagen.catalog import read_text
from secreview.datagen.settings import load_settings, project_path


class RemovedClaims(BaseModel):
    removed_claims: dict[str, list[str]]


@cache
def load_removed_claims() -> dict[str, list[str]]:
    """Map a case to the rules that a leftover claim sentence of its design touches."""
    text = read_text(project_path(load_settings().paths.removed_claims_file))
    return RemovedClaims.model_validate(yaml.safe_load(text)).removed_claims


def has_removed_claim(case_id: str, rule_id: str) -> bool:
    """Tell whether the design of the case carries a claim sentence about the rule."""
    return rule_id in load_removed_claims().get(case_id, [])
