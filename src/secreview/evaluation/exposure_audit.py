"""Which internal documents make plain that the service has no external callers."""

from functools import cache

from pydantic import BaseModel
import yaml

from secreview.datagen.catalog import read_text
from secreview.datagen.settings import load_settings, project_path

EVIDENT = "evident"
NOT_STATED = "not_stated"
CONTRADICTED = "contradicted"
UNAUDITED = "unaudited"


class ExposureAudit(BaseModel):
    evident_internal_only: list[str]
    audience_not_stated: list[str]
    audience_contradicted: list[str]


@cache
def load_exposure_audit() -> ExposureAudit:
    """Load the audit of the internal documents."""
    text = read_text(project_path(load_settings().paths.exposure_audit_file))
    return ExposureAudit.model_validate(yaml.safe_load(text))


def audience_reading(case_id: str) -> str:
    """Tell what a careful reader learns from a document about who calls the service."""
    audit = load_exposure_audit()
    if case_id in audit.evident_internal_only:
        return EVIDENT
    if case_id in audit.audience_not_stated:
        return NOT_STATED
    if case_id in audit.audience_contradicted:
        return CONTRADICTED
    return UNAUDITED
