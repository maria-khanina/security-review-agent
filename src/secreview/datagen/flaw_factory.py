"""Turns sampled rules into labeled planted flaws."""

import random

from secreview.datagen.models import (
    ArchitectureFacts,
    DocumentedServiceDefinition,
    Flaw,
    Rule,
)
from secreview.datagen.overlaps import load_misfits
from secreview.datagen.settings import load_settings
from secreview.datagen.severity import Severity

IMPLEMENTATION_ONLY = "impl"
DESIGN_ONLY = "design"
DESIGN_AND_IMPLEMENTATION = "both"


def service_data_classes(documented_service: DocumentedServiceDefinition) -> set[str]:
    """Collect the data classes of a service, including those they imply."""
    implications = load_settings().data_implications
    data_classes: set[str] = set(documented_service.data)
    for data_class in documented_service.data:
        data_classes.update(implications.get(data_class, []))
    return data_classes


def rule_applies(rule: Rule, documented_service: DocumentedServiceDefinition) -> bool:
    """Tell whether a rule applies to some component of the documented service."""
    if not rule.applies_to.covers_service(documented_service.id):
        return False
    data_classes = service_data_classes(documented_service)
    for kind in documented_service.components:
        if rule.applies_to.matches(
            kind,
            data_classes,
            documented_service.exposure,
            documented_service.accepts_requests,
        ):
            return True
    return False


def pick_component(
    rule_kinds: list[str],
    documented_service: DocumentedServiceDefinition,
    facts: ArchitectureFacts,
) -> str:
    """Pick the named component a flaw is attached to."""
    candidates: list[str] = []
    for kind in documented_service.components:
        if not rule_kinds or kind in rule_kinds:
            candidates.append(kind)
    chosen_kind = candidates[0] if candidates else documented_service.components[0]
    for component in facts.components:
        if component.kind == chosen_kind:
            return component.name
    return facts.components[0].name


def pick_data_class(
    rule_data: list[str],
    documented_service: DocumentedServiceDefinition,
) -> str:
    """Pick the most sensitive data class the rule and documented service share."""
    pool: list[str] = []
    for data_class in load_settings().data_sensitivity_order:
        in_documented_service = data_class in documented_service.data
        if in_documented_service and (not rule_data or data_class in rule_data):
            pool.append(data_class)
    return pool[0] if pool else documented_service.data[0]


def pick_violation_scenario(
    case_id: str,
    flaw_id: str,
    rule: Rule,
    policy_version: str,
) -> str:
    """Choose a violation scenario that breaks the wording of the policy version."""
    if not rule.violation_scenarios:
        return ""
    misfits = load_misfits()
    fitting: list[str] = [
        scenario
        for index, scenario in enumerate(rule.violation_scenarios)
        if policy_version not in misfits.get((rule.id, index), [])
    ]
    chooser = random.Random(f"{case_id}:{flaw_id}:{rule.id}")
    return chooser.choice(fitting)


def build_violation_flaw(
    flaw_id: str,
    rule: Rule,
    mutation: str | None,
    scenario: str,
    documented_service: DocumentedServiceDefinition,
    facts: ArchitectureFacts,
    severity: Severity,
) -> Flaw:
    """Create a policy-violation flaw for a rule."""
    data_class = pick_data_class(rule.applies_to.data, documented_service)
    if rule.check_scope == IMPLEMENTATION_ONLY:
        manifest = IMPLEMENTATION_ONLY
        instruction = (
            f"The design must stay silent about: {rule.title}. The issue exists "
            f"only in the implementation. Do not mark any text for {flaw_id}."
        )
    else:
        manifest = DESIGN_AND_IMPLEMENTATION if mutation else DESIGN_ONLY
        instruction = (
            "State, as the author naturally would and believing it acceptable, "
            "a design decision of this kind (use your own words and this "
            f"service's context; do not copy the wording): {scenario}"
        )
    return Flaw(
        flaw_id=flaw_id,
        type="violation",
        rule_id=rule.id,
        component=pick_component(rule.applies_to.kind, documented_service, facts),
        data_class=data_class,
        exposure=documented_service.exposure,
        severity=severity.compute(
            rule.base_severity, documented_service.exposure, data_class, False, False
        ),
        cwe=rule.cwe_ids,
        manifest=manifest,
        implementation_mutation=mutation,
        implementation_anchor=None,
        remediation_options=rule.remediation_options,
        clarification_needed=None,
        instruction=instruction,
    )


def build_ambiguity_flaw(
    flaw_id: str,
    rule: Rule,
    documented_service: DocumentedServiceDefinition,
    facts: ArchitectureFacts,
    severity: Severity,
) -> Flaw:
    """Create an ambiguity flaw: the design omits what a rule needs."""
    data_class = pick_data_class(rule.applies_to.data, documented_service)
    component = pick_component(rule.applies_to.kind, documented_service, facts)
    instruction = (
        f"Mention {component} naturally, but do NOT state: {rule.how_to_omit} "
        f"Wrap the sentence(s) that mention {component} (the place where that "
        f"information should have been) in the {flaw_id} marker."
    )
    return Flaw(
        flaw_id=flaw_id,
        type="ambiguity",
        rule_id=rule.id,
        component=component,
        data_class=data_class,
        exposure=documented_service.exposure,
        severity=severity.compute(
            rule.base_severity, documented_service.exposure, data_class, False, True
        ),
        cwe=rule.cwe_ids,
        manifest=DESIGN_ONLY,
        implementation_mutation=None,
        implementation_anchor=None,
        remediation_options=[],
        clarification_needed=rule.how_to_omit,
        instruction=instruction,
    )
