"""Plans which cases the dataset contains, before any flaw is sampled.

The plan fixes, for every case: the service documented service, the implementation
format, the dev or test split, the policy version, the author profile, the
noise level of the design document, and whether the case is clean.
"""

import random

from secreview.datagen.catalog import load_author_profiles, load_company
from secreview.datagen.models import AuthorProfile, Case, NoiseProfile, PlannedCase
from secreview.datagen.settings import load_settings


def implementation_groups() -> dict[str, list[str]]:
    """Group documented service ids by implementation format, in configured order."""
    company = load_company()
    groups: dict[str, list[str]] = {}
    for implementation_format in company.split.implementation_share:
        groups[implementation_format] = []
    for documented_service in company.documented_services:
        groups[documented_service.implementation_format].append(documented_service.id)
    return groups


def slots_for_format(
    random_generator: random.Random,
    implementation_format: str,
    documented_service_ids: list[str],
) -> list[str]:
    """Spread the cases of one implementation format over its documented services."""
    split = load_company().split
    share = split.implementation_share[implementation_format]
    total = round(split.dataset_size * share)
    order: list[str] = list(documented_service_ids)
    random_generator.shuffle(order)
    slots: list[str] = []
    for position in range(total):
        slots.append(order[position % len(order)])
    return slots


def allocate_slots(random_generator: random.Random) -> list[str]:
    """Assign an documented service to every case slot, balanced within each format."""
    slots: list[str] = []
    groups = implementation_groups()
    for implementation_format, documented_service_ids in groups.items():
        slots += slots_for_format(
            random_generator,
            implementation_format,
            documented_service_ids,
        )
    random_generator.shuffle(slots)
    return slots


def group_positions(slots: list[str]) -> dict[str, list[int]]:
    """Collect the slot positions of every documented service."""
    positions: dict[str, list[int]] = {}
    for position, documented_service in enumerate(slots):
        positions.setdefault(documented_service, []).append(position)
    return positions


def rebalance_clean_flags(
    random_generator: random.Random,
    clean_flags: list[bool],
) -> None:
    """Flip random flags until the clean-case total matches the target."""
    split = load_company().split
    difference = sum(clean_flags) - split.clean_cases
    candidates: list[int] = []
    for position, is_clean in enumerate(clean_flags):
        if is_clean == (difference > 0):
            candidates.append(position)
    random_generator.shuffle(candidates)
    for position in candidates[: abs(difference)]:
        clean_flags[position] = not clean_flags[position]


def assign_clean_flags(
    random_generator: random.Random,
    slots: list[str],
) -> list[bool]:
    """Mark which slots hold clean cases, stratified by documented service."""
    split = load_company().split
    clean_flags = [False] * len(slots)
    for positions in group_positions(slots).values():
        clean_count = round(len(positions) * split.clean_cases / split.dataset_size)
        for position in random_generator.sample(positions, clean_count):
            clean_flags[position] = True
    rebalance_clean_flags(random_generator, clean_flags)
    return clean_flags


def typo_rates_for(author_profile: AuthorProfile) -> list[float]:
    """Pick the typo rate choices that fit the author's English."""
    noise = load_settings().noise
    if author_profile.english in noise.low_typo_english:
        return noise.low_typo_rates
    return noise.high_typo_rates


def markdown_choices_for(author_profile: AuthorProfile) -> list[str]:
    """Pick the markdown breakage choices that fit the document structure."""
    noise = load_settings().noise
    if author_profile.structure in noise.heavy_markdown_structures:
        return noise.heavy_markdown_choices
    return noise.light_markdown_choices


def reference_choices_for(author_profile: AuthorProfile) -> list[int]:
    """Pick the dangling-reference choices that fit the author's staleness."""
    noise = load_settings().noise
    if author_profile.staleness == noise.no_staleness_label:
        return noise.fresh_reference_choices
    return noise.stale_reference_choices


def marker_choices_for(author_profile: AuthorProfile) -> list[int]:
    """Pick the TBD-marker choices that fit the author's hedging."""
    noise = load_settings().noise
    if author_profile.hedging == noise.high_hedging_label:
        return noise.high_hedging_marker_choices
    return noise.default_marker_choices


def sample_noise(
    random_generator: random.Random,
    author_profile: AuthorProfile,
) -> NoiseProfile:
    """Draw the noise knobs of one design document from its author profile."""
    return NoiseProfile(
        typo_rate=random_generator.choice(typo_rates_for(author_profile)),
        markdown_breakage=random_generator.choice(markdown_choices_for(author_profile)),
        dangling_references=random_generator.choice(
            reference_choices_for(author_profile)
        ),
        tbd_markers=random_generator.choice(marker_choices_for(author_profile)),
    )


def build_planned_case(
    random_generator: random.Random,
    index: int,
    documented_service_id: str,
    is_clean: bool,
) -> PlannedCase:
    """Create one planned case, drawing its profile, policy and noise."""
    company = load_company()
    documented_service = next(
        item for item in company.documented_services if item.id == documented_service_id
    )
    author_profiles = load_author_profiles()
    author_profile_id = random_generator.choice(list(author_profiles))
    policy_version = random_generator.choice(load_settings().policy_versions)
    noise = sample_noise(random_generator, author_profiles[author_profile_id])
    holdout = documented_service_id in company.split.holdout_documented_services
    case = Case(
        case_id=f"c{index:03d}_{documented_service_id}",
        documented_service=documented_service_id,
        implementation_format=documented_service.implementation_format,
        split="test" if holdout else "dev",
        policy_version=policy_version,
        author_profile=author_profile_id,
        noise=noise,
        flaws=[],
        required_rules=[],
    )
    return PlannedCase(case=case, defective=not is_clean)


def plan_cases() -> list[PlannedCase]:
    """Plan every case of the dataset deterministically from the seed."""
    random_generator = random.Random(load_settings().seed)
    slots = allocate_slots(random_generator)
    clean_flags = assign_clean_flags(random_generator, slots)
    planned: list[PlannedCase] = []
    for index, (documented_service_id, is_clean) in enumerate(zip(slots, clean_flags)):
        planned.append(
            build_planned_case(random_generator, index, documented_service_id, is_clean)
        )
    return planned
