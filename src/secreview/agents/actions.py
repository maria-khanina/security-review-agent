"""The recommended action of a finding, decided by code from its type and policy."""

from secreview.review_settings import REVIEW_SETTINGS


def derive_action(finding_type: str, requirement_wording: str) -> str:
    """Return review_policy for a loosely worded requirement, else by finding type."""
    evaluation = REVIEW_SETTINGS.evaluation
    if requirement_wording != "clear":
        return evaluation.review_action
    if finding_type == "ambiguity":
        return evaluation.clarify_action
    return evaluation.fix_action
