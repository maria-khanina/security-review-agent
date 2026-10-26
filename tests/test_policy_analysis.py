"""Tests for the policy analysis, requirement numbering and the pilot sample."""

import json

from secreview.agents.case_materials import list_case_ids
from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.pilot_sample import build_pilot_sample, load_pilot_sample
from secreview.agents.policy_analysis import analyze_policy
from secreview.agents.policy_requirements import (
    PolicyAnalysis,
    PolicyRequirement,
    RequirementDraft,
    assign_requirements,
    find_requirement,
    render_tagged_policy,
)
from secreview.datagen.policies import load_policy_versions
from secreview.datagen.settings import load_settings
from secreview.evaluation.policy_scores import compare_topics, score_policy_analysis
from secreview.parsing.vocabulary import TOPICS, WORDINGS
from secreview.review_settings import REVIEW_SETTINGS

POLICY_VERSION = load_settings().policy_versions[0]
INVENTED = "An invented requirement that is nowhere."
LOOSE = "vague"
MAX_TOPICS = REVIEW_SETTINGS.policy_analysis.max_topics
PREFIX = REVIEW_SETTINGS.policy_analysis.requirement_prefix
THREE = len("abc")


class FakeClient:
    def __init__(self, reply: str) -> None:
        self.reply = reply

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
    ) -> str:
        return self.reply


def first_sentence(text: str) -> str:
    return text.split(". ")[1] + "."


def build_drafts(earlier: str, later: str) -> list[RequirementDraft]:
    return [
        RequirementDraft(quote=later, wording="clear", topics=["network"]),
        RequirementDraft(quote=INVENTED, wording="clear", topics=[]),
        RequirementDraft(quote=earlier, wording=LOOSE, topics=["secrets"]),
        RequirementDraft(quote=earlier, wording="clear", topics=["secrets"]),
    ]


def numbered_analysis() -> tuple[PolicyAnalysis, str]:
    policy = load_policy_versions()[POLICY_VERSION]
    earlier = first_sentence(policy.text)
    middle = len(policy.text) // 2
    later = first_sentence(policy.text[middle:])
    drafts = build_drafts(earlier, later)
    return assign_requirements(POLICY_VERSION, policy.text, drafts), earlier


def test_ids_follow_text_order_and_unverifiable_quotes_are_dropped() -> None:
    analysis, earlier = numbered_analysis()
    ids: list[str] = [item.id for item in analysis.requirements]
    assert ids == [f"{PREFIX}1", f"{PREFIX}2"]
    assert analysis.requirements[0].quote == earlier
    assert analysis.requirements[0].wording == LOOSE
    assert analysis.requirements[0].span[0] < analysis.requirements[1].span[0]


def test_requirements_can_be_found_by_id() -> None:
    analysis, _ = numbered_analysis()
    assert find_requirement(analysis, f"{PREFIX}2") is not None
    assert find_requirement(analysis, "R9999") is None


def test_tagged_policy_only_adds_the_tags() -> None:
    analysis = build_oracle_analysis(POLICY_VERSION)
    text = load_policy_versions()[POLICY_VERSION].text
    tagged = render_tagged_policy(text, analysis)
    for requirement in analysis.requirements:
        tagged = tagged.replace(f"[{requirement.id}] ", "", 1)
    assert tagged == text


def test_oracle_analysis_matches_the_gold_and_uses_the_fixed_vocabularies() -> None:
    for version in load_settings().policy_versions:
        analysis = build_oracle_analysis(version)
        scores = score_policy_analysis(analysis)
        assert scores.recall == 1.0
        assert scores.wording.accuracy == 1.0
        assert scores.topics.hit_rate == 1.0
        for requirement in analysis.requirements:
            assert requirement.wording in WORDINGS
            assert 0 < len(requirement.topics) <= MAX_TOPICS
            assert set(requirement.topics) <= set(TOPICS)


def evidence_item(quote: str, relaxed_by: str) -> dict[str, object]:
    return {
        "quote": quote,
        "relaxed_by": relaxed_by,
        "topics": ["network"],
    }


def analyze_items(items: list[dict[str, object]]) -> PolicyAnalysis:
    reply = json.dumps({"requirements": items})
    return analyze_policy(FakeClient(reply), POLICY_VERSION)


def first_quotes() -> list[str]:
    requirements = build_oracle_analysis(POLICY_VERSION).requirements
    return [item.quote for item in requirements[:THREE]]


def test_a_verified_relaxation_marks_both_sentences_and_adds_the_missing_one() -> None:
    first, second, third = first_quotes()
    analysis = analyze_items(
        [evidence_item(first, third), evidence_item(second, "")]
    )
    wordings: list[str] = [item.wording for item in analysis.requirements]
    assert wordings == ["contradictory", "clear", "contradictory"]
    assert analysis.requirements[2].quote == third


def test_unverifiable_or_self_referencing_relaxations_are_ignored() -> None:
    first, _, _ = first_quotes()
    analysis = analyze_items(
        [
            evidence_item(first, INVENTED),
            evidence_item(first, first),
        ]
    )
    assert [item.wording for item in analysis.requirements] == ["clear"]


def test_a_complete_model_reply_gives_a_full_numbered_analysis() -> None:
    gold = build_oracle_analysis(POLICY_VERSION)
    items: list[dict[str, object]] = []
    for item in gold.requirements:
        items.append(evidence_item(item.quote, ""))
    analysis = analyze_items(items)
    assert [item.span for item in analysis.requirements] == [
        item.span for item in gold.requirements
    ]
    assert score_policy_analysis(analysis).recall == 1.0


def service_of(case_id: str) -> str:
    return case_id.split("_", 1)[1]


def test_pilot_sample_is_deterministic_stratified_and_inside_dev() -> None:
    first = build_pilot_sample()
    assert first == build_pilot_sample()
    assert len(first.case_ids) == REVIEW_SETTINGS.pilot.sample_size
    assert set(first.case_ids) <= set(list_case_ids("dev"))
    chosen: set[str] = {service_of(case_id) for case_id in first.case_ids}
    available: set[str] = {service_of(case_id) for case_id in list_case_ids("dev")}
    assert len(chosen) >= len(available) - 1


def test_stored_pilot_sample_is_a_dev_sample_of_the_configured_size() -> None:
    stored = load_pilot_sample()
    assert len(stored) == REVIEW_SETTINGS.pilot.sample_size
    assert set(stored) <= set(list_case_ids("dev"))


def merged_span_analysis() -> PolicyAnalysis:
    text = load_policy_versions()[POLICY_VERSION].text
    first, second = build_oracle_analysis(POLICY_VERSION).requirements[:2]
    start, end = first.span[0], second.span[1]
    quote = text[start:end]
    draft = RequirementDraft(quote=quote, wording="clear", topics=["secrets"])
    return assign_requirements(POLICY_VERSION, text, [draft])


def test_one_merged_requirement_counts_for_one_gold_requirement_only() -> None:
    gold_count = len(build_oracle_analysis(POLICY_VERSION).requirements)
    scores = score_policy_analysis(merged_span_analysis())
    assert scores.matched_pairs == 1
    assert scores.recall == 1 / gold_count
    assert scores.precision == 1.0


def flip_to_clear(analysis: PolicyAnalysis) -> PolicyAnalysis:
    flipped: list[PolicyRequirement] = []
    for item in analysis.requirements:
        flipped.append(item.model_copy(update={"wording": "clear"}))
    return analysis.model_copy(update={"requirements": flipped})


def test_wording_metrics_expose_a_model_that_calls_everything_clear() -> None:
    oracle = build_oracle_analysis(POLICY_VERSION)
    perfect = score_policy_analysis(oracle).wording
    all_clear = score_policy_analysis(flip_to_clear(oracle)).wording
    assert perfect.not_clear_recall == 1.0 and perfect.not_clear_f1 == 1.0
    assert all_clear.not_clear_recall == 0.0
    assert all_clear.accuracy < perfect.accuracy
    assert all_clear.report.per_class[LOOSE].recall == 0.0


def test_topic_metrics_distinguish_extra_and_missing_topics() -> None:
    expected: list[str] = ["network", "secrets"]
    found: list[str] = ["network", "logging", "cryptography"]
    scores = compare_topics(expected, found)
    shared: set[str] = {"network"}
    assert scores.hit_rate == 1.0 and scores.exact_match == 0.0
    assert scores.jaccard == len(shared) / len(set(expected) | set(found))
    assert scores.precision == len(shared) / len(found)
    assert scores.recall == len(shared) / len(expected)
