"""Samples the planted flaws of a case under compatibility constraints.

Flaws must not duplicate a rule, must not edit the same implementation spot
twice and must leave every other applicable rule satisfied in the design.
"""

from collections.abc import Callable
from dataclasses import dataclass
import random
from typing import TypeVar

from secreview.datagen.catalog import (
    load_all_documented_services,
    load_architecture,
    load_author_profiles,
    load_rules,
    load_severity,
    load_suppressed_rules,
)
from secreview.datagen.flaw_factory import (
    IMPLEMENTATION_ONLY,
    build_ambiguity_flaw,
    build_violation_flaw,
    pick_violation_scenario,
    rule_applies,
)
from secreview.datagen.implementation import conflict_group, is_mutation_available
from secreview.datagen.models import (
    ArchitectureFacts,
    AuthorProfile,
    Case,
    DocumentedServiceDefinition,
    Flaw,
    Rule,
)
from secreview.datagen.policies import is_firm, load_policy_versions
from secreview.datagen.settings import load_settings

FLAW_TYPES = ("violation", "ambiguity")
Candidate = TypeVar("Candidate")


@dataclass
class SamplingContext:
    case: Case
    documented_service: DocumentedServiceDefinition
    facts: ArchitectureFacts
    rules: dict[str, Rule]
    applicable: list[str]
    statuses: dict[str, str]
    author_profile: AuthorProfile
    used_rules: set[str]
    used_mutations: set[str]
    used_groups: set[str]
    flaws: list[Flaw]


@dataclass
class FlawOptions:
    violations: list[tuple[Rule, str | None]]
    ambiguities: list[Rule]

    def viable_types(self) -> list[str]:
        """List the flaw types that still have at least one candidate."""
        viable: list[str] = []
        if self.violations:
            viable.append("violation")
        if self.ambiguities:
            viable.append("ambiguity")
        return viable


Planter = Callable[["SamplingContext", random.Random, "FlawOptions"], None]


def find_documented_service(documented_service_id: str) -> DocumentedServiceDefinition:
    """Look up an documented service specification by id."""
    for documented_service in load_all_documented_services():
        if documented_service.id == documented_service_id:
            return documented_service
    raise KeyError(documented_service_id)


def build_context(case: Case) -> SamplingContext:
    """Prepare the lookup tables and empty state for sampling one case."""
    documented_service = find_documented_service(case.documented_service)
    rules: dict[str, Rule] = {rule.id: rule for rule in load_rules()}
    policy = load_policy_versions()[case.policy_version]
    applicable: list[str] = []
    for rule_id in policy.flaggable():
        if rule_applies(rules[rule_id], documented_service):
            applicable.append(rule_id)
    return SamplingContext(
        case=case,
        documented_service=documented_service,
        facts=load_architecture()[case.documented_service],
        rules=rules,
        applicable=applicable,
        statuses={rule_id: span.status for rule_id, span in policy.rules.items()},
        author_profile=load_author_profiles()[case.author_profile],
        used_rules=set(),
        used_mutations=set(),
        used_groups=set(),
        flaws=[],
    )


def mean_affinity() -> dict[str, float]:
    """Average the flaw-type affinity over all author profiles."""
    author_profiles: list[AuthorProfile] = list(load_author_profiles().values())
    averages: dict[str, float] = {}
    for flaw_type in FLAW_TYPES:
        affinities: list[float] = [
            profile.affinity[flaw_type] for profile in author_profiles
        ]
        total = sum(affinities)
        averages[flaw_type] = total / len(author_profiles)
    return averages


def is_mutation_free(context: SamplingContext, mutation: str | None) -> bool:
    """Tell whether a mutation conflicts with an already planted one."""
    if mutation is None:
        return True
    in_use = mutation in context.used_mutations
    return not in_use and conflict_group(mutation) not in context.used_groups


def claim_mutation(context: SamplingContext, mutation: str | None) -> None:
    """Record that a mutation and its conflict group are taken."""
    if mutation:
        context.used_mutations.add(mutation)
        context.used_groups.add(conflict_group(mutation))


def is_rule_available(context: SamplingContext, rule_id: str) -> bool:
    """Tell whether no planted flaw has consumed the rule yet."""
    return rule_id not in context.used_rules


def usable_mutation(context: SamplingContext, rule: Rule) -> str | None:
    """Return the rule's implementation mutation when it can be planted."""
    case = context.case
    mutation = rule.implementation_check
    if not mutation or not is_mutation_free(context, mutation):
        return None
    format_name = case.implementation_format
    if is_mutation_available(format_name, case.documented_service, mutation):
        return mutation
    return None


def conflicts_with_planted(context: SamplingContext, rule: Rule) -> bool:
    """Tell whether the rule's implementation edit clashes with a planted one."""
    case = context.case
    mutation = rule.implementation_check
    if not mutation:
        return False
    available = is_mutation_available(
        case.implementation_format,
        case.documented_service,
        mutation,
    )
    return available and not is_mutation_free(context, mutation)


def build_violation_option(
    context: SamplingContext,
    rule_id: str,
) -> tuple[Rule, str | None] | None:
    """Return the rule with its mutation when the rule can be violated."""
    rule = context.rules[rule_id]
    if not is_rule_available(context, rule_id):
        return None
    if conflicts_with_planted(context, rule):
        return None
    mutation = usable_mutation(context, rule)
    if rule.check_scope == IMPLEMENTATION_ONLY and mutation is None:
        return None
    return rule, mutation


def find_violation_options(
    context: SamplingContext,
) -> list[tuple[Rule, str | None]]:
    """List rules that can be violated, with their implementation mutation."""
    options: list[tuple[Rule, str | None]] = []
    for rule_id in context.applicable:
        option = build_violation_option(context, rule_id)
        if option is not None:
            options.append(option)
    return options


def find_ambiguity_options(context: SamplingContext) -> list[Rule]:
    """List rules whose required information the design can omit."""
    options: list[Rule] = []
    for rule_id in context.applicable:
        rule = context.rules[rule_id]
        designable = rule.check_scope != IMPLEMENTATION_ONLY
        if is_rule_available(context, rule_id) and designable and rule.ambiguity_ok:
            options.append(rule)
    return options


def collect_options(context: SamplingContext) -> FlawOptions:
    """Gather the current candidates of every flaw type."""
    return FlawOptions(
        violations=find_violation_options(context),
        ambiguities=find_ambiguity_options(context),
    )


def choose_flaw_type(
    context: SamplingContext,
    random_generator: random.Random,
    viable_types: list[str],
    affinity_means: dict[str, float],
) -> str:
    """Draw a flaw type weighted by the author profile's affinities."""
    weights: list[float] = []
    for flaw_type in viable_types:
        affinity = context.author_profile.affinity[flaw_type]
        weights.append(affinity / affinity_means[flaw_type])
    return random_generator.choices(viable_types, weights=weights)[0]


def narrow_to_stratum(
    context: SamplingContext,
    random_generator: random.Random,
    candidates: list[Candidate],
    rule_of: Callable[[Candidate], Rule],
) -> list[Candidate]:
    """Keep either the clear or the non-clear candidates, by configured share."""
    clear: list[Candidate] = []
    non_clear: list[Candidate] = []
    for candidate in candidates:
        status = context.statuses[rule_of(candidate).id]
        (clear if is_firm(status) else non_clear).append(candidate)
    if not clear or not non_clear:
        return candidates
    draw = random_generator.random()
    return non_clear if draw < load_settings().non_clear_flaw_share else clear


def add_violation(
    context: SamplingContext,
    rule: Rule,
    mutation: str | None,
) -> None:
    """Record a policy violation of the given rule in the case."""
    flaw_id = f"F{len(context.flaws) + 1}"
    scenario = pick_violation_scenario(
        context.case.case_id,
        flaw_id,
        rule,
        context.case.policy_version,
    )
    context.flaws.append(
        build_violation_flaw(
            flaw_id,
            rule,
            mutation,
            scenario,
            context.documented_service,
            context.facts,
            load_severity(),
        )
    )
    context.used_rules.add(rule.id)
    claim_mutation(context, mutation)


def add_ambiguity(context: SamplingContext, rule: Rule) -> None:
    """Record an ambiguity about the given rule in the case."""
    flaw_id = f"F{len(context.flaws) + 1}"
    context.flaws.append(
        build_ambiguity_flaw(
            flaw_id,
            rule,
            context.documented_service,
            context.facts,
            load_severity(),
        )
    )
    context.used_rules.add(rule.id)


def plant_violation(
    context: SamplingContext,
    random_generator: random.Random,
    options: FlawOptions,
) -> None:
    """Plant one policy violation chosen by rule severity."""
    pool = narrow_to_stratum(
        context, random_generator, options.violations, lambda option: option[0]
    )
    weights: list[int] = [rule.base_severity for rule, _ in pool]
    rule, mutation = random_generator.choices(pool, weights=weights)[0]
    add_violation(context, rule, mutation)


def plant_ambiguity(
    context: SamplingContext,
    random_generator: random.Random,
    options: FlawOptions,
) -> None:
    """Plant one ambiguity chosen by rule severity."""
    pool = narrow_to_stratum(
        context, random_generator, options.ambiguities, lambda option: option
    )
    weights: list[int] = [rule.base_severity for rule in pool]
    add_ambiguity(context, random_generator.choices(pool, weights=weights)[0])


def draw_flaw_count(random_generator: random.Random) -> int:
    """Draw how many flaws a defective case receives."""
    weights = load_settings().flaw_count_weights
    return random_generator.choices(list(weights), weights=list(weights.values()))[0]


def suppressed_by(planted: set[str]) -> set[str]:
    """Collect the rules whose satisfied statement a planted flaw invalidates."""
    suppressed: set[str] = set()
    for rule_id in planted:
        suppressed |= load_suppressed_rules().get(rule_id, set())
    return suppressed


def is_statable(context: SamplingContext, rule_id: str, unavailable: set[str]) -> bool:
    """Tell whether a rule must be stated as satisfied in the design."""
    designable = context.rules[rule_id].check_scope != IMPLEMENTATION_ONLY
    return designable and rule_id not in unavailable


def finish_case(context: SamplingContext) -> None:
    """Store the flaws and the rules that must be stated as satisfied.

    Rules coupled to a planted flaw are left unstated so the text stays coherent.
    """
    planted: set[str] = set(context.used_rules)
    unavailable = planted | suppressed_by(planted)
    context.case.flaws = context.flaws
    context.case.required_rules = [
        rule_id
        for rule_id in context.applicable
        if is_statable(context, rule_id, unavailable)
    ]


PLANTERS: dict[str, Planter] = {
    "violation": plant_violation,
    "ambiguity": plant_ambiguity,
}


def plant_next_flaw(
    context: SamplingContext,
    random_generator: random.Random,
    affinity_means: dict[str, float],
) -> bool:
    """Plant one more flaw, or report that no candidate is left."""
    options = collect_options(context)
    viable = options.viable_types()
    if not viable:
        return False
    flaw_type = choose_flaw_type(context, random_generator, viable, affinity_means)
    PLANTERS[flaw_type](context, random_generator, options)
    return True


def sample_flaws(
    case: Case,
    random_generator: random.Random,
    defective: bool,
) -> None:
    """Fill a case with planted flaws and its required satisfied rules."""
    context = build_context(case)
    count = draw_flaw_count(random_generator) if defective else 0
    affinity_means = mean_affinity()
    while len(context.flaws) < count:
        if not plant_next_flaw(context, random_generator, affinity_means):
            break
    finish_case(context)
