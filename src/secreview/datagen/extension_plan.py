"""Plans the extension cases: hand-targeted flaws that fill coverage gaps.

The core plan draws flaws at random. The extension plan lists, for every added
case, the exact flaws it must contain, so rare combinations of flaw type and
policy status, rarely flawed rules and the held-out services are covered on
purpose. Core cases are never touched; extension cases continue their numbering.
"""

from collections.abc import Callable
from functools import cache
import random

from pydantic import BaseModel
import yaml

from secreview.datagen.case_plan import sample_noise
from secreview.datagen.catalog import (
    config_path,
    load_author_profiles,
    load_company,
    read_text,
)
from secreview.datagen.flaw_sampling import (
    SamplingContext,
    add_ambiguity,
    add_violation,
    build_context,
    build_violation_option,
    find_ambiguity_options,
    find_documented_service,
    finish_case,
)
from secreview.datagen.models import Case, PlannedCase
from secreview.datagen.settings import load_settings

EXTENSION_PLAN_FILE = "extension_plan.yaml"
REQUEST_SEPARATOR = ":"


class ExtensionCaseSpecification(BaseModel):
    index: int
    service: str
    author_profile: str
    policy_version: str
    flaws: list[str]
    split: str | None = None
    silent: list[str] = []


class ExtensionPlan(BaseModel):
    cases: list[ExtensionCaseSpecification]


@cache
def load_extension_plan() -> ExtensionPlan:
    """Load the hand-written list of extension cases."""
    text = read_text(config_path(EXTENSION_PLAN_FILE))
    return ExtensionPlan.model_validate(yaml.safe_load(text))


def build_empty_case(specification: ExtensionCaseSpecification) -> Case:
    """Create the case of a specification before any flaw is planted."""
    documented_service = find_documented_service(specification.service)
    holdout = specification.service in load_company().split.holdout_documented_services
    generator = random.Random(f"{load_settings().seed}:{specification.index}")
    profile = load_author_profiles()[specification.author_profile]
    return Case(
        case_id=f"c{specification.index:03d}_{specification.service}",
        documented_service=specification.service,
        implementation_format=documented_service.implementation_format,
        split=specification.split or ("test" if holdout else "dev"),
        policy_version=specification.policy_version,
        author_profile=specification.author_profile,
        noise=sample_noise(generator, profile),
        flaws=[],
        required_rules=[],
    )


def plant_violation_of(context: SamplingContext, rule_id: str) -> bool:
    """Plant a violation of the rule when it is viable, else report failure."""
    option = build_violation_option(context, rule_id)
    if option is None:
        return False
    add_violation(context, option[0], option[1])
    return True


def plant_ambiguity_of(context: SamplingContext, rule_id: str) -> bool:
    """Plant an ambiguity about the rule when it is viable, else report failure."""
    for rule in find_ambiguity_options(context):
        if rule.id == rule_id:
            add_ambiguity(context, rule)
            return True
    return False


PLANTERS: dict[str, Callable[[SamplingContext, str], bool]] = {
    "violation": plant_violation_of,
    "ambiguity": plant_ambiguity_of,
}


def plant_requested_flaw(context: SamplingContext, requested: str) -> None:
    """Plant one requested flaw, failing loudly when it cannot be realized."""
    kind, identifier = requested.split(REQUEST_SEPARATOR)
    if not PLANTERS[kind](context, identifier):
        raise ValueError(f"{context.case.case_id}: cannot plant {requested}")


def leave_silent(case: Case, silent: list[str]) -> None:
    """Drop the rules that the design is planned not to mention."""
    unknown = set(silent) - set(case.required_rules)
    if unknown:
        raise ValueError(f"{case.case_id}: cannot leave {sorted(unknown)} silent")
    case.required_rules = [
        rule_id for rule_id in case.required_rules if rule_id not in silent
    ]


def plan_extension_case(specification: ExtensionCaseSpecification) -> PlannedCase:
    """Build one extension case with its requested flaws and required rules."""
    case = build_empty_case(specification)
    context = build_context(case)
    for requested in specification.flaws:
        plant_requested_flaw(context, requested)
    finish_case(context)
    leave_silent(case, specification.silent)
    return PlannedCase(case=case, defective=bool(specification.flaws))


def plan_extension_cases() -> list[PlannedCase]:
    """Plan every extension case from the hand-written list."""
    planned: list[PlannedCase] = []
    for specification in load_extension_plan().cases:
        planned.append(plan_extension_case(specification))
    return planned
