"""Tests for the hand-targeted extension cases."""

from secreview.datagen.case_files import load_raw_case
from secreview.datagen.case_plan import plan_cases
from secreview.datagen.catalog import load_suppressed_rules
from secreview.datagen.extension_plan import (
    load_extension_plan,
    plan_extension_cases,
)
from secreview.datagen.policies import is_firm, load_policy_versions
from secreview.datagen.settings import load_settings

REQUIRED_TEST_STATUSES = {"vague", "advisory", "conflicting"}


def test_extension_indices_are_unique_and_follow_the_core_plan() -> None:
    cases = load_extension_plan().cases
    indices: list[int] = [specification.index for specification in cases]
    assert len(indices) == len(set(indices))
    assert min(indices) == len(plan_cases())


def test_every_requested_flaw_can_be_planted() -> None:
    planned = plan_extension_cases()
    assert len(planned) == len(load_extension_plan().cases)
    for item in planned:
        assert item.defective == bool(item.case.flaws)


def collect_coupled_rules(flawed: set[str]) -> set[str]:
    suppressed_by_rule = load_suppressed_rules()
    suppressed: set[str] = set()
    for rule_id in flawed:
        suppressed |= suppressed_by_rule.get(rule_id, set())
    return suppressed


def test_required_rules_are_clear_and_not_coupled_to_a_flaw() -> None:
    for item in plan_extension_cases():
        case = item.case
        policy = load_policy_versions()[case.policy_version]
        flawed: set[str] = {flaw.rule_id for flaw in case.flaws if flaw.rule_id}
        required: set[str] = set(case.required_rules)
        assert not collect_coupled_rules(flawed) & required, case.case_id
        assert not flawed & required, case.case_id
        for rule_id in required:
            assert is_firm(policy.review_status([rule_id])), case.case_id


def test_extension_covers_every_non_clear_status_in_the_test_split() -> None:
    statuses: set[str] = set()
    for item in plan_extension_cases():
        policy = load_policy_versions()[item.case.policy_version]
        if item.case.split != "test":
            continue
        for flaw in item.case.flaws:
            if flaw.rule_id:
                statuses.add(policy.review_status([flaw.rule_id]))
    assert REQUIRED_TEST_STATUSES <= statuses


def test_written_skeletons_match_the_plan() -> None:
    for item in plan_extension_cases():
        stored = load_raw_case(item.case.case_id)
        assert stored.documented_service == item.case.documented_service
        planned: list[str] = [flaw.flaw_id for flaw in item.case.flaws]
        assert [flaw.flaw_id for flaw in stored.flaws][: len(planned)] == planned
        assert load_settings().seed
