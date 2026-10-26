"""Tests for the list of requirements that the policy owner has to clarify."""

from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.policy_clarifications import (
    list_clarifications,
    render_clarifications,
)
from secreview.datagen.policies import is_firm, load_policy_versions

POLICY_VERSION = "v5"


def test_only_requirements_with_loose_or_conflicting_wording_are_listed() -> None:
    analysis = build_oracle_analysis(POLICY_VERSION)
    items = list_clarifications(analysis)
    assert items
    assert all(item.wording != "clear" for item in items)
    assert len(items) < len(analysis.requirements)


def test_the_gold_list_follows_the_firm_statuses_of_the_rules() -> None:
    policy = load_policy_versions()[POLICY_VERSION]
    spans = 0
    for rule in policy.rules.values():
        if not is_firm(rule.status):
            spans += len(rule.spans)
    assert len(list_clarifications(build_oracle_analysis(POLICY_VERSION))) == spans


def test_the_rendered_section_names_every_listed_requirement() -> None:
    items = list_clarifications(build_oracle_analysis(POLICY_VERSION))
    text = render_clarifications(POLICY_VERSION, items)
    assert all(item.requirement_id in text for item in items)
