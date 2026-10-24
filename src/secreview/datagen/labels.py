"""Gold label structures written next to every processed case."""

from pydantic import BaseModel

from secreview.datagen.markers import MarkerSpans
from secreview.datagen.models import Case, Flaw, NoiseProfile
from secreview.datagen.overlaps import find_co_violations
from secreview.datagen.policies import CLEAR_STATUS, PolicyVersion

SATISFIED_PREFIX = "S:"
SpanList = list[list[int]]


class FlawLabel(BaseModel):
    flaw_id: str
    type: str
    rule_id: str | None
    drift_id: str | None
    severity: str
    cwe: list[str]
    component: str
    data_class: str
    manifest: str
    implementation_anchor: str | None
    remediation_options: list[list[str]]
    clarification_needed: str | None
    related_rules: list[str]
    policy_status: str
    needs_policy_review: bool
    design_spans: SpanList
    policy_spans: dict[str, SpanList]
    implementation_spans: SpanList
    also_violates: list[str] = []


class SatisfiedLabel(BaseModel):
    rule_id: str
    design_spans: SpanList
    policy_spans: SpanList


class CaseLabels(BaseModel):
    case_id: str
    split: str
    documented_service: str
    implementation_format: str
    implementation_file: str
    policy_version: str
    author_profile: str
    noise: NoiseProfile
    clean: bool
    flaws: list[FlawLabel]
    satisfied: list[SatisfiedLabel]


def policy_spans_of(policy: PolicyVersion, rule_ids: list[str]) -> dict[str, SpanList]:
    """Collect the policy-text spans of the rules the policy version covers."""
    spans: dict[str, SpanList] = {}
    for rule_id in rule_ids:
        if rule_id in policy.rules:
            spans[rule_id] = [list(span) for span in policy.rules[rule_id].spans]
    return spans


def build_flaw_label(
    flaw: Flaw,
    related_rules: list[str],
    marker_spans: MarkerSpans,
    policy: PolicyVersion,
    implementation_spans: SpanList,
) -> FlawLabel:
    """Create the gold label of one planted flaw."""
    policy_status = policy.review_status(related_rules)
    return FlawLabel(
        flaw_id=flaw.flaw_id,
        type=flaw.type,
        rule_id=flaw.rule_id,
        drift_id=flaw.drift_id,
        severity=flaw.severity,
        cwe=flaw.cwe,
        component=flaw.component,
        data_class=flaw.data_class,
        manifest=flaw.manifest,
        implementation_anchor=flaw.implementation_anchor,
        remediation_options=flaw.remediation_options,
        clarification_needed=flaw.clarification_needed,
        related_rules=related_rules,
        policy_status=policy_status,
        needs_policy_review=policy_status != CLEAR_STATUS,
        design_spans=marker_spans.get(flaw.flaw_id, []),
        policy_spans=policy_spans_of(policy, related_rules),
        implementation_spans=implementation_spans,
        also_violates=find_co_violations(flaw),
    )


def build_satisfied_label(
    rule_id: str,
    marker_spans: MarkerSpans,
    policy: PolicyVersion,
) -> SatisfiedLabel:
    """Create the gold label of one rule the design satisfies."""
    policy_spans = policy_spans_of(policy, [rule_id]).get(rule_id, [])
    return SatisfiedLabel(
        rule_id=rule_id,
        design_spans=marker_spans[f"{SATISFIED_PREFIX}{rule_id}"],
        policy_spans=policy_spans,
    )


def build_case_labels(
    case: Case,
    implementation_file: str,
    flaw_labels: list[FlawLabel],
    satisfied_labels: list[SatisfiedLabel],
) -> CaseLabels:
    """Assemble the complete gold labels of a processed case."""
    return CaseLabels(
        case_id=case.case_id,
        split=case.split,
        documented_service=case.documented_service,
        implementation_format=case.implementation_format,
        implementation_file=implementation_file,
        policy_version=case.policy_version,
        author_profile=case.author_profile,
        noise=case.noise,
        clean=not case.flaws,
        flaws=flaw_labels,
        satisfied=satisfied_labels,
    )
