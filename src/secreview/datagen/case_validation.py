"""Consistency checks between a case plan, its design text and its artifact."""

from secreview.datagen.implementation import (
    available_check_names,
    conflict_group,
    run_implementation_check,
)
from secreview.datagen.markers import MarkerSpans
from secreview.datagen.models import Case

IMPLEMENTATION_ONLY = "impl"
SATISFIED_PREFIX = "S:"


def expected_marker_ids(case: Case) -> set[str]:
    """List the marker ids the design text must contain."""
    expected: set[str] = set()
    for flaw in case.flaws:
        if flaw.manifest != IMPLEMENTATION_ONLY:
            expected.add(flaw.flaw_id)
    for rule_id in case.required_rules:
        expected.add(f"{SATISFIED_PREFIX}{rule_id}")
    return expected


def validate_markers(case: Case, spans: MarkerSpans) -> list[str]:
    """Report missing and unexpected markers of a design text."""
    expected = expected_marker_ids(case)
    problems: list[str] = []
    for marker_id in sorted(expected - set(spans)):
        problems.append(f"missing marker {marker_id}")
    for marker_id in sorted(set(spans) - expected):
        problems.append(f"unexpected marker {marker_id}")
    return problems


def planted_mutations(case: Case) -> list[str]:
    """List the implementation mutations planted in a case."""
    names: list[str] = []
    for flaw in case.flaws:
        if flaw.implementation_mutation:
            names.append(flaw.implementation_mutation)
    return names


def find_undetected_mutations(case: Case, implementation_text: str) -> list[str]:
    """Report planted mutations that their detector fails to find."""
    problems: list[str] = []
    for name in planted_mutations(case):
        found = run_implementation_check(
            case.implementation_format,
            name,
            implementation_text,
        )
        if not found:
            problems.append(f"planted mutation {name} not detected")
    return problems


def find_unplanted_detections(case: Case, implementation_text: str) -> list[str]:
    """Report detectors that fire although their flaw was never planted."""
    planted = planted_mutations(case)
    planted_groups: set[str] = {conflict_group(name) for name in planted}
    problems: list[str] = []
    for name in available_check_names(case.implementation_format):
        if name in planted or conflict_group(name) in planted_groups:
            continue
        found = run_implementation_check(
            case.implementation_format,
            name,
            implementation_text,
        )
        if found:
            problems.append(f"unplanted checker {name} fires")
    return problems


def validate_implementation(case: Case, implementation_text: str) -> list[str]:
    """Confirm planted flaws are detectable and nothing else fires."""
    problems = find_undetected_mutations(case, implementation_text)
    return problems + find_unplanted_detections(case, implementation_text)
