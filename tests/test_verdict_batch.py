"""Tests for judging a group of requirements in one model call."""

import json

from secreview.agents.policy_requirements import PolicyRequirement
from secreview.agents.verdict_batch import (
    build_batch_schema,
    make_groups,
    parse_batch_reply,
    primary_topic,
)

GROUP_SIZE = len("abc")
REQUIREMENT_COUNT = len("abcdefg")


def make_requirement(index: int, topic: str) -> PolicyRequirement:
    return PolicyRequirement.model_validate(
        {
            "id": f"R{index}",
            "quote": f"Requirement number {index} must hold.",
            "span": (0, 1),
            "wording": "clear",
            "topics": [topic] if topic else [],
        }
    )


def make_requirements() -> list[PolicyRequirement]:
    topics: list[str] = [
        "network",
        "logging",
        "network",
        "",
        "logging",
        "network",
        "secrets",
    ]
    return [make_requirement(index, topic) for index, topic in enumerate(topics)]


def test_groups_keep_topics_together_and_cover_every_requirement() -> None:
    groups = make_groups(make_requirements(), GROUP_SIZE)
    flat: list[str] = [item.id for group in groups for item in group]
    assert sorted(flat) == sorted(f"R{index}" for index in range(REQUIREMENT_COUNT))
    assert all(len(group) <= GROUP_SIZE for group in groups)
    assert [primary_topic(item) for item in groups[0]] == ["", "logging", "logging"]


def test_the_schema_demands_exactly_one_item_per_requirement() -> None:
    schema = build_batch_schema(GROUP_SIZE)
    properties = schema["properties"]
    assert isinstance(properties, dict)
    assert properties["items"]["minItems"] == GROUP_SIZE
    assert properties["items"]["maxItems"] == GROUP_SIZE


def item_json(number: int) -> dict[str, object]:
    return {
        "requirement": number,
        "quote": "",
        "reason": "the fragments are silent",
        "verdict": "unclear",
        "severity": "none",
    }


def test_a_reply_with_the_wrong_number_of_items_is_rejected() -> None:
    reply = json.dumps({"items": [item_json(1), item_json(2)]})
    assert parse_batch_reply(reply, 2) is not None
    assert parse_batch_reply(reply, GROUP_SIZE) is None
    assert parse_batch_reply("no json here", 2) is None
