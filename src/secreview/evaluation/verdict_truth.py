"""Gold verdicts for every requirement of a policy version in a design document.

For each requirement sentence of the policy version of a case the generator
knows what a design review should answer: the requirement does not concern the
service or cannot be judged from a design, the design satisfies it, the design
breaks it, or nothing in the design settles it.
"""

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.datagen.catalog import load_rules, load_suppressed_rules
from secreview.datagen.flaw_factory import rule_applies, service_data_classes
from secreview.datagen.flaw_sampling import find_documented_service
from secreview.datagen.labels import CaseLabels, FlawLabel
from secreview.datagen.models import (
    IMPLEMENTATION_ONLY,
    DocumentedServiceDefinition,
    Rule,
)
from secreview.datagen.phrasings import is_weaker_wording
from secreview.datagen.policies import RuleSpan, is_firm, load_policy_versions
from secreview.evaluation.claims_audit import has_removed_claim
from secreview.evaluation.exposure_audit import EVIDENT, NOT_STATED, audience_reading
from secreview.evaluation.word_overlap import overlap_share
from secreview.parsing.vocabulary import COMPLIANT, NOT_APPLICABLE, UNCLEAR, VIOLATED
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

Span = tuple[int, int]
EXPOSURES = ("external", "internal", "admin")

NOT_IN_SERVICE = "not_in_service"
NOT_IN_SERVICE_EXPOSURE = "not_in_service_exposure"
NO_EXTERNAL_CALLERS = "no_external_callers"
EXPOSURE_SILENCE = "exposure_silence"
IMPLEMENTATION_ONLY_RULE = "implementation_only"
PLANTED_VIOLATION = "planted_violation"
PLANTED_AMBIGUITY = "planted_ambiguity"
STATED = "stated"
VAGUE_POLICY = "vague_policy"
COUPLED_SILENCE = "coupled_silence"
UNPLANNED_APPLICABLE = "unplanned_applicable"
SOFT_VIOLATION = "soft_violation"
PARTIAL_STATEMENT = "partial_statement"
SILENT_SUBTYPES = (COUPLED_SILENCE, UNPLANNED_APPLICABLE, EXPOSURE_SILENCE)
CLAIM_SENSITIVE_SUBTYPES = (*SILENT_SUBTYPES, VAGUE_POLICY)
CO_VIOLATION = "co_violation"
CONTESTABLE = (
    STATED,
    NOT_IN_SERVICE,
    NOT_IN_SERVICE_EXPOSURE,
    IMPLEMENTATION_ONLY_RULE,
)


SUBTYPE_VERDICTS: dict[str, str] = {
    NOT_IN_SERVICE: NOT_APPLICABLE,
    NOT_IN_SERVICE_EXPOSURE: NOT_APPLICABLE,
    NO_EXTERNAL_CALLERS: NOT_APPLICABLE,
    EXPOSURE_SILENCE: UNCLEAR,
    IMPLEMENTATION_ONLY_RULE: NOT_APPLICABLE,
    PLANTED_VIOLATION: VIOLATED,
    PLANTED_AMBIGUITY: UNCLEAR,
    STATED: COMPLIANT,
    VAGUE_POLICY: UNCLEAR,
    COUPLED_SILENCE: UNCLEAR,
    UNPLANNED_APPLICABLE: UNCLEAR,
    SOFT_VIOLATION: UNCLEAR,
    PARTIAL_STATEMENT: UNCLEAR,
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
    if not rule.applies_to.covers_service(service.id):
        return False
    data_classes = service_data_classes(service)
    for kind in service.components:
        for exposure in EXPOSURES:
            if rule.applies_to.matches(
                kind,
                data_classes,
                exposure,
                service.accepts_requests,
            ):
                return True
    return False


def classify_exposure(
    rule: Rule,
    service: DocumentedServiceDefinition,
    case_id: str,
) -> Classification:
    """Classify a rule that only the exposure of the service makes inapplicable."""
    reading = audience_reading(case_id)
    surface = "external" in rule.applies_to.exposure
    silent = Classification(verdict=UNCLEAR, subtype=EXPOSURE_SILENCE, design_spans=[])
    if service.exposure != "internal" or not surface:
        return silent
    if reading == EVIDENT and "third_party" not in service.components:
        return Classification(
            verdict=NOT_APPLICABLE,
            subtype=NO_EXTERNAL_CALLERS,
            design_spans=[],
        )
    if reading == NOT_STATED or "third_party" in service.components:
        return silent
    return Classification(
        verdict=NOT_APPLICABLE,
        subtype=NOT_IN_SERVICE_EXPOSURE,
        design_spans=[],
    )


def classify_scope(
    rule: Rule,
    service: DocumentedServiceDefinition,
    case_id: str,
) -> Classification | None:
    """Return the not-applicable classification when the rule is out of scope."""
    if not rule_applies(rule, service):
        if applies_ignoring_exposure(rule, service):
            return classify_exposure(rule, service, case_id)
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


def is_weak_statement(
    materials: CaseMaterials,
    rule_id: str,
    spans: list[Span],
) -> bool:
    """Tell whether a statement is a general wording of a rule its version tightens."""
    version = materials.labels.policy_version
    return any(
        is_weaker_wording(materials.design_text[start:end], rule_id, version)
        for start, end in spans
    )


def classify_stated(materials: CaseMaterials, rule_id: str) -> Classification | None:
    """Return the compliant classification when the design states the rule."""
    for statement in materials.labels.satisfied:
        if statement.rule_id == rule_id:
            spans = to_spans(statement.design_spans)
            if is_weak_statement(materials, rule_id, spans):
                return Classification(
                    verdict=UNCLEAR,
                    subtype=PARTIAL_STATEMENT,
                    design_spans=spans,
                )
            return Classification(verdict=COMPLIANT, subtype=STATED, design_spans=spans)
    return None


def classify_violation(
    violation: FlawLabel,
    rule_span: RuleSpan,
    version: str,
) -> Classification:
    """Return the classification of a planted violation of a rule."""
    spans = to_spans(violation.design_spans)
    if not is_firm(rule_span.status):
        return Classification(
            verdict=UNCLEAR,
            subtype=SOFT_VIOLATION,
            design_spans=spans,
            severity=violation.severity,
        )
    return Classification(
        verdict=VIOLATED,
        subtype=PLANTED_VIOLATION,
        design_spans=spans,
        severity=violation.severity,
        contested=version in violation.misfit_versions,
    )


def classify_planted(
    labels: CaseLabels,
    rule_span: RuleSpan,
    rule_id: str,
) -> Classification | None:
    """Return the classification of a planted violation or ambiguity on the rule."""
    violation = find_flaw(labels, rule_id, "violation")
    if violation is not None:
        return classify_violation(violation, rule_span, labels.policy_version)
    if find_flaw(labels, rule_id, "ambiguity") is not None:
        return Classification(
            verdict=UNCLEAR,
            subtype=PLANTED_AMBIGUITY,
            design_spans=[],
        )
    return None


def is_silence_planned(labels: CaseLabels, rule_id: str) -> bool:
    """Tell whether the generator left the rule unstated because of a flaw."""
    planted: set[str] = set()
    for flaw in labels.flaws:
        planted.update(flaw.related_rules)
        if flaw.rule_id is not None:
            planted.add(flaw.rule_id)
    suppressed = load_suppressed_rules()
    return any(rule_id in suppressed.get(other, set()) for other in planted)


def classify_unlabeled(
    rule_span: RuleSpan,
    labels: CaseLabels,
    rule_id: str,
) -> Classification:
    """Classify a rule that has no planted flaw and no stated compliance."""
    if not is_firm(rule_span.status):
        return Classification(verdict=UNCLEAR, subtype=VAGUE_POLICY, design_spans=[])
    planned = is_silence_planned(labels, rule_id)
    subtype = COUPLED_SILENCE if planned else UNPLANNED_APPLICABLE
    return Classification(verdict=UNCLEAR, subtype=subtype, design_spans=[])


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


def classify_labeled(
    rule: Rule,
    rule_span: RuleSpan,
    service: DocumentedServiceDefinition,
    materials: CaseMaterials,
) -> Classification | None:
    """Classify a rule by its scope, its planted flaw or its stated compliance."""
    found = classify_scope(rule, service, materials.case_id)
    found = found or classify_planted(materials.labels, rule_span, rule.id)
    return found or classify_stated(materials, rule.id)


def classify_rule(
    rule: Rule,
    rule_span: RuleSpan,
    service: DocumentedServiceDefinition,
    materials: CaseMaterials,
) -> Classification:
    """Decide the gold verdict of a rule for the design of a case."""
    labels = materials.labels
    co_violation = find_co_violation(labels, rule.id)
    found = classify_labeled(rule, rule_span, service, materials)
    if found is not None:
        contested = co_violation is not None and found.subtype in CONTESTABLE
        return found.model_copy(update={"contested": contested or found.contested})
    if co_violation is not None:
        return classify_co_violation(co_violation)
    return classify_unlabeled(rule_span, labels, rule.id)


def is_excluded(found: Classification) -> bool:
    """Tell whether a pair is left out of scoring: contested or unreliable."""
    excluded_subtypes = REVIEW_SETTINGS.evaluation.excluded_subtypes
    return found.contested or found.subtype in excluded_subtypes


def breaks_silence(units: list[DesignUnit], requirement: str, subtype: str) -> bool:
    """Tell whether a design sentence nearly restates a requirement left unstated."""
    if subtype not in SILENT_SUBTYPES:
        return False
    limit = REVIEW_SETTINGS.evaluation.silence_overlap
    return any(overlap_share(requirement, unit.text) >= limit for unit in units)


def build_pair_truth(
    materials: CaseMaterials,
    units: list[DesignUnit],
    found: Classification,
    pair: tuple[str, Span, str],
) -> PairTruth:
    """Build the gold verdict of one requirement sentence."""
    rule_id, span, requirement = pair
    claimed = found.subtype in CLAIM_SENSITIVE_SUBTYPES
    claimed = claimed and has_removed_claim(materials.case_id, rule_id)
    loud = claimed or breaks_silence(units, requirement, found.subtype)
    return PairTruth(
        case_id=materials.case_id,
        rule_id=rule_id,
        requirement_span=span,
        verdict=found.verdict,
        subtype=found.subtype,
        design_spans=found.design_spans,
        severity=found.severity,
        excluded=is_excluded(found) or loud,
    )


def build_rule_truths(
    materials: CaseMaterials,
    units: list[DesignUnit],
    rule_id: str,
    found: Classification,
) -> list[PairTruth]:
    """Build the gold verdict of every requirement sentence of one rule."""
    policy = load_policy_versions()[materials.labels.policy_version]
    truths: list[PairTruth] = []
    for start, end in policy.rules[rule_id].spans:
        pair = (rule_id, (start, end), policy.text[start:end])
        truths.append(build_pair_truth(materials, units, found, pair))
    return truths


def build_case_truth(materials: CaseMaterials) -> list[PairTruth]:
    """List the gold verdict of every requirement sentence of the case's policy."""
    version = materials.labels.policy_version
    policy = load_policy_versions()[version]
    service = find_documented_service(materials.labels.documented_service)
    rules: dict[str, Rule] = {rule.id: rule for rule in load_rules()}
    units = split_units(materials.design_text)
    truths: list[PairTruth] = []
    for rule_id, rule_span in policy.rules.items():
        found = classify_rule(rules[rule_id], rule_span, service, materials)
        truths.extend(build_rule_truths(materials, units, rule_id, found))
    return truths
