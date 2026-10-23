"""Scope of the evaluation and the check of the cited policy sentence."""

from secreview.agents.baseline import GroundedFinding
from secreview.agents.case_materials import CaseMaterials
from secreview.datagen.labels import FlawLabel
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.review_settings import REVIEW_SETTINGS


def is_in_scope(flaw: FlawLabel) -> bool:
    """Tell whether a planted flaw is a design-versus-policy flaw with evidence."""
    return flaw.type in REVIEW_SETTINGS.evaluation.in_scope_types and bool(
        flaw.design_spans
    )


def expected_action(flaw: FlawLabel) -> str:
    """Return the action a reviewer should recommend for a planted flaw."""
    evaluation = REVIEW_SETTINGS.evaluation
    if flaw.needs_policy_review:
        return evaluation.review_action
    if flaw.type == "ambiguity":
        return evaluation.clarify_action
    return evaluation.fix_action


def list_gold_policy_spans(flaw: FlawLabel) -> list[tuple[int, int]]:
    """List the gold policy spans of the requirements a flaw is judged against."""
    spans: list[tuple[int, int]] = []
    for rule_spans in flaw.policy_spans.values():
        spans.extend((start, end) for start, end in rule_spans)
    return spans


def is_evidence_correct(
    materials: CaseMaterials,
    flaw: FlawLabel,
    grounded: GroundedFinding,
) -> bool:
    """Tell whether the cited policy sentence overlaps a gold span enough."""
    text = materials.policy_text
    predicted = collect_token_indices(text, [grounded.policy_span])
    threshold = REVIEW_SETTINGS.evaluation.iou_threshold
    for gold_span in list_gold_policy_spans(flaw):
        gold = collect_token_indices(text, [gold_span])
        if compute_overlap(predicted, gold) >= threshold:
            return True
    return False
