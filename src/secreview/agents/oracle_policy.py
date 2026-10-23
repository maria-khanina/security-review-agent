"""Policy analysis built from the gold rule locations, to isolate later stages."""

from typing import cast

from secreview.agents.policy_requirements import (
    PolicyAnalysis,
    RequirementDraft,
    assign_requirements,
)
from secreview.datagen.catalog import load_rules
from secreview.datagen.policies import PolicyVersion, load_policy_versions
from secreview.parsing.vocabulary import Topic, Wording
from secreview.review_settings import REVIEW_SETTINGS


def map_topics(categories: list[str]) -> list[Topic]:
    """Map rule categories onto the fixed topic vocabulary, without repeats."""
    mapping = REVIEW_SETTINGS.policy_analysis.category_topics
    topics: list[str] = []
    for category in categories:
        topic = mapping[category]
        if topic not in topics:
            topics.append(topic)
    limit = REVIEW_SETTINGS.policy_analysis.max_topics
    return cast(list[Topic], topics[:limit])


def build_oracle_drafts(policy: PolicyVersion) -> list[RequirementDraft]:
    """Turn every gold rule location of a policy version into a draft."""
    categories: dict[str, list[str]] = {}
    for rule in load_rules():
        categories[rule.id] = rule.categories
    wordings = REVIEW_SETTINGS.policy_analysis.status_wording
    drafts: list[RequirementDraft] = []
    for rule_id, rule_span in policy.rules.items():
        for start, end in rule_span.spans:
            drafts.append(
                RequirementDraft(
                    quote=policy.text[start:end],
                    wording=cast(Wording, wordings[rule_span.status]),
                    topics=map_topics(categories[rule_id]),
                )
            )
    return drafts


def build_oracle_analysis(policy_version: str) -> PolicyAnalysis:
    """Return the gold requirement list of a policy version, numbered by code."""
    policy = load_policy_versions()[policy_version]
    drafts = build_oracle_drafts(policy)
    return assign_requirements(policy_version, policy.text, drafts)
