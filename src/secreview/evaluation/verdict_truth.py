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
from secreview.review_settings import REVIEW_SETTINGS

Span = tuple[int, int]
EXPOSURES = ("external", "internal", "admin")

NOT_IN_SERVICE = "not_in_service"
NOT_IN_SERVICE_EXPOSURE = "not_in_service_exposure"
IMPLEMENTATION_ONLY_RULE = "implementation_only"
PLANTED_VIOLATION = "planted_violation"
PLANTED_AMBIGUITY = "planted_ambiguity"
STATED = "stated"
DRIFT_CLAIM = "drift_claim"
VAGUE_POLICY = "vague_policy"
COUPLED_SILENCE = "coupled_silence"
CO_VIOLATION = "co_violation"
CONTESTABLE = (STATED, NOT_IN_SERVICE, NOT_IN_SERVICE_EXPOSURE)


SUBTYPE_VERDICTS: dict[str, str] = {
    NOT_IN_SERVICE: NOT_APPLICABLE,
    NOT_IN_SERVICE_EXPOSURE: NOT_APPLICABLE,
    IMPLEMENTATION_ONLY_RULE: NOT_APPLICABLE,
    PLANTED_VIOLATION: VIOLATED,
    PLANTED_AMBIGUITY: UNCLEAR,
    STATED: COMPLIANT,
    DRIFT_CLAIM: COMPLIANT,
    VAGUE_POLICY: UNCLEAR,
    COUPLED_SILENCE: UNCLEAR,
    CO_VIOLATION: VIOLATED,
}
SUBTYPES: tuple[str, ...] = tuple(SUBTYPE_VERDICTS)


class Classification(BaseModel):
    verdict: str
    subtype: str
    design_spans: list[Span]
    severity: str = ""
    contested: bool = False


class PairTruth(BaseModel):
    case_id: str
    rule_id: str
    requirement_span: Span
    verdict: str
    subtype: str
    design_spans: list[Span]
    severity: str = ""
    excluded: bool = False


def to_spans(raw_spans: list[list[int]]) -> list[Span]:
    """Convert label spans into start and end pairs."""
    return [(span[0], span[1]) for span in raw_spans]


def applies_ignoring_exposure(
    rule: Rule,
    service: DocumentedServiceDefinition,
) -> bool:
    """Tell whether the rule would apply to the service under another exposure."""
    data_classes: set[str] = set(service.data)
    for kind in service.components:
        for exposure in EXPOSURES:
            if rule.applies_to.matches(kind, data_classes, exposure):
                return True
    return False


def name_inapplicability(rule: Rule, service: DocumentedServiceDefinition) -> str:
    """Tell whether only the exposure of the service makes the rule inapplicable."""
    if applies_ignoring_exposure(rule, service):
        return NOT_IN_SERVICE_EXPOSURE
    return NOT_IN_SERVICE


def classify_scope(
    rule: Rule,
    service: DocumentedServiceDefinition,
) -> Classification | None:
    """Return the not-applicable classification when the rule is out of scope."""
    if not rule_applies(rule, service):
        return Classification(
            verdict=NOT_APPLICABLE,
            subtype=name_inapplicability(rule, service),
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
            severity=violation.severity,
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


def find_co_violation(labels: CaseLabels, rule_id: str) -> FlawLabel | None:
    """Find a planted violation of another rule whose sentence also breaks this rule."""
    for flaw in labels.flaws:
        co_violates = rule_id in flaw.also_violates
        if flaw.type == "violation" and co_violates and flaw.design_spans:
            return flaw
    return None


def classify_co_violation(flaw: FlawLabel) -> Classification:
    """Return the violated classification of a rule broken by another rule's flaw."""
    spans = to_spans(flaw.design_spans)
    return Classification(
        verdict=VIOLATED,
        subtype=CO_VIOLATION,
        design_spans=spans,
        severity=flaw.severity,
    )


def classify_rule(
    rule: Rule,
    rule_span: RuleSpan,
    service: DocumentedServiceDefinition,
    labels: CaseLabels,
) -> Classification:
    """Decide the gold verdict of a rule for the design of a case."""
    co_violation = find_co_violation(labels, rule.id)
    found = classify_scope(rule, service) or classify_planted(labels, rule.id)
    found = found or classify_stated(labels, rule.id)
    if found is not None:
        contested = co_violation is not None and found.subtype in CONTESTABLE
        return found.model_copy(update={"contested": contested})
    if co_violation is not None:
        return classify_co_violation(co_violation)
    return classify_unlabeled(rule_span, labels, rule.id)


def is_excluded(found: Classification) -> bool:
    """Tell whether a pair is left out of scoring: contested or unreliable."""
    excluded_subtypes = REVIEW_SETTINGS.evaluation.excluded_subtypes
    return found.contested or found.subtype in excluded_subtypes


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
                    severity=found.severity,
                    excluded=is_excluded(found),
                )
            )
    return truths
