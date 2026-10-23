"""Tests for the policy corpus versions and their located rules."""

from secreview.datagen.catalog import load_rules
from secreview.datagen.policies import PolicyVersion, load_policy_versions
from secreview.datagen.settings import load_settings

ALL_STATUSES = {"clear", "vague", "advisory", "conflicting"}


def collect_spans(policy: PolicyVersion) -> list[tuple[int, int]]:
    """Gather all located spans of a policy version in text order."""
    spans: list[tuple[int, int]] = []
    for rule_span in policy.rules.values():
        spans += list(rule_span.spans)
    spans.sort()
    return spans


def test_every_rule_is_mapped_or_absent_exactly_once() -> None:
    rule_ids: set[str] = {rule.id for rule in load_rules()}
    for policy in load_policy_versions().values():
        assert set(policy.rules) | set(policy.absent) == rule_ids
        assert not set(policy.rules) & set(policy.absent)


def test_spans_are_disjoint_and_inside_the_text() -> None:
    for policy in load_policy_versions().values():
        spans = collect_spans(policy)
        for (_, first_end), (second_start, _) in zip(spans, spans[1:]):
            assert first_end <= second_start, policy.version
        for start, end in spans:
            assert 0 <= start < end <= len(policy.text)


def test_versions_differ_in_coverage_and_quality() -> None:
    minimum = load_settings().quality_gates.min_violable_rules_per_policy_version
    versions = load_policy_versions()
    statuses: set[str] = set()
    for policy in versions.values():
        assert len(policy.violable()) >= minimum, policy.version
        statuses |= {rule.status for rule in policy.rules.values()}
    absent_counts: set[int] = {len(policy.absent) for policy in versions.values()}
    assert len(absent_counts) == len(versions)
    assert statuses == ALL_STATUSES


def test_every_rule_can_be_flagged_in_some_version() -> None:
    flaggable: set[str] = set()
    for policy in load_policy_versions().values():
        flaggable |= set(policy.flaggable())
    assert {rule.id for rule in load_rules()} <= flaggable
