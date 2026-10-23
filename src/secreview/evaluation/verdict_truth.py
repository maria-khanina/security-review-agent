"""Gold verdicts for every requirement of a policy version in a design document.

For each requirement sentence of the policy version of a case the generator
knows what a design review should answer: the requirement does not concern the
service or cannot be judged from a design, the design satisfies it, the design
breaks it, or nothing in the design settles it.
"""

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.datagen.catalog import load_rules
from secreview.datagen.flaw_factory import rule_applies
from secreview.datagen.flaw_sampling import find_documented_service
from secreview.datagen.labels import CaseLabels, FlawLabel
from secreview.datagen.models import (
    IMPLEMENTATION_ONLY,
    DocumentedServiceDefinition,
    Rule,
)
from secreview.datagen.policies import CLEAR_STATUS, RuleSpan, load_policy_versions
from secreview.parsing.vocabulary import COMPLIANT, NOT_APPLICABLE, UNCLEAR, VIOLATED

Span = tuple[int, int]

NOT_IN_SERVICE = "not_in_service"
IMPLEMENTATION_ONLY_RULE = "implementation_only"
PLANTED_VIOLATION = "planted_violation"
PLANTED_AMBIGUITY = "planted_ambiguity"
STATED = "stated"
DRIFT_CLAIM = "drift_claim"
VAGUE_POLICY = "vague_policy"
COUPLED_SILENCE = "coupled_silence"


class Classification(BaseModel):
    verdict: str
    subtype: str
    design_spans: list[Span]


class PairTruth(BaseModel):
    case_id: str
    rule_id: str
    requirement_span: Span
    verdict: str
    subtype: str
    design_spans: list[Span]


def to_spans(raw_spans: list[list[int]]) -> list[Span]:
    """Convert label spans into start and end pairs."""
    return [(span[0], span[1]) for span in raw_spans]


def classify_scope(
    rule: Rule,
    service: DocumentedServiceDefinition,
) -> Classification | None:
    """Return the not-applicable classification when the rule is out of scope."""
    if not rule_applies(rule, service):
        return Classification(
            verdict=NOT_APPLICABLE,
            subtype=NOT_IN_SERVICE,
            design_spans=[],
        )
    if rule.check_scope == IMPLEMENTATION_ONLY:
        return Classification(
            verdict=NOT_APPLICABLE,
            subtype=IMPLEMENTATION_ONLY_RULE,
            design_spans=[],
        )
    return None


def find_flaw(labels: CaseLabels, rule_id: str, flaw_type: str) -> FlawLabel | None:
    """Find the planted flaw of a type on a rule that has a design location."""
    for flaw in labels.flaws:
        if flaw.type == flaw_type and flaw.rule_id == rule_id and flaw.design_spans:
            return flaw
    return None


def find_drift_claim(labels: CaseLabels, rule_id: str) -> FlawLabel | None:
    """Find a drift flaw whose design claim concerns the rule."""
    for flaw in labels.flaws:
        if flaw.type == "drift" and rule_id in flaw.related_rules and flaw.design_spans:
            return flaw
    return None


def classify_stated(labels: CaseLabels, rule_id: str) -> Classification | None:
    """Return the compliant classification when the design states the rule."""
    for statement in labels.satisfied:
        if statement.rule_id == rule_id:
            spans = to_spans(statement.design_spans)
            return Classification(verdict=COMPLIANT, subtype=STATED, design_spans=spans)
    return None


def classify_drift_claim(labels: CaseLabels, rule_id: str) -> Classification | None:
    """Return the compliant classification of a design claim made by a drift flaw."""
    drift = find_drift_claim(labels, rule_id)
    if drift is None:
        return None
    spans = to_spans(drift.design_spans)
    return Classification(verdict=COMPLIANT, subtype=DRIFT_CLAIM, design_spans=spans)


def classify_planted(labels: CaseLabels, rule_id: str) -> Classification | None:
    """Return the classification of a planted violation or ambiguity on the rule."""
    violation = find_flaw(labels, rule_id, "violation")
    if violation is not None:
        spans = to_spans(violation.design_spans)
        return Classification(
            verdict=VIOLATED,
            subtype=PLANTED_VIOLATION,
            design_spans=spans,
        )
    if find_flaw(labels, rule_id, "ambiguity") is not None:
        return Classification(
            verdict=UNCLEAR,
            subtype=PLANTED_AMBIGUITY,
            design_spans=[],
        )
    return None


def classify_unlabeled(
    rule_span: RuleSpan,
    labels: CaseLabels,
    rule_id: str,
) -> Classification:
    """Classify a rule that has no planted flaw and no stated compliance."""
    if rule_span.status != CLEAR_STATUS:
        return Classification(verdict=UNCLEAR, subtype=VAGUE_POLICY, design_spans=[])
    claim = classify_drift_claim(labels, rule_id)
    if claim is not None:
        return claim
    return Classification(verdict=UNCLEAR, subtype=COUPLED_SILENCE, design_spans=[])


def classify_rule(
    rule: Rule,
    rule_span: RuleSpan,
    service: DocumentedServiceDefinition,
    labels: CaseLabels,
) -> Classification:
    """Decide the gold verdict of a rule for the design of a case."""
    found = classify_scope(rule, service)
    found = found or classify_planted(labels, rule.id)
    found = found or classify_stated(labels, rule.id)
    return found or classify_unlabeled(rule_span, labels, rule.id)


def build_case_truth(materials: CaseMaterials) -> list[PairTruth]:
    """List the gold verdict of every requirement sentence of the case's policy."""
    labels = materials.labels
    policy = load_policy_versions()[labels.policy_version]
    service = find_documented_service(labels.documented_service)
    rules: dict[str, Rule] = {rule.id: rule for rule in load_rules()}
    truths: list[PairTruth] = []
    for rule_id, rule_span in policy.rules.items():
        found = classify_rule(rules[rule_id], rule_span, service, labels)
        for span in rule_span.spans:
            truths.append(
                PairTruth(
                    case_id=materials.case_id,
                    rule_id=rule_id,
                    requirement_span=span,
                    verdict=found.verdict,
                    subtype=found.subtype,
                    design_spans=found.design_spans,
                )
            )
    return truths
