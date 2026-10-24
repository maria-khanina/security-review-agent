"""Tests for the verdict reply, the confidence and the per-requirement review."""

import json
import math

import pytest

from secreview.agents.case_materials import (
    CaseMaterials,
    list_case_ids,
    load_case_materials,
)
from secreview.agents.policy_requirements import PolicyAnalysis, load_policy_analysis
from secreview.agents.verdict_contexts import guarantee_gold, union_units
from secreview.agents.verdict_prompts import (
    build_verdict_system_prompt,
    build_verdict_user_prompt,
)
from secreview.agents.verdict_reply import compute_confidence, parse_verdict_reply
from secreview.agents.verdict_review import (
    ContextChoice,
    VerdictCaseRecord,
    review_case_verdicts,
    to_requirement_verdicts,
)
from secreview.agents.verdict_verifier import probability_of_yes
from secreview.evaluation.verdict_scores import match_truths
from secreview.evaluation.verdict_truth import build_case_truth
from secreview.llm.client import LogprobCompletion, TokenLogprobs
from secreview.parsing.findings import ReplyParseError
from secreview.parsing.vocabulary import EVIDENCE_VERDICTS, VERDICTS
from secreview.retrieval.requirement_rankings import CaseRankings, load_rankings
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

SETTINGS = REVIEW_SETTINGS.verdict
CANDIDATES = len("abc")
OPENING = '{"quote": "", "reason": "r", "verdict": "'
PREFIX_LENGTH = len("comp")
COMPLIANT_COUNT = len("abcdef")
VIOLATED_COUNT = len("abc")


def reply_text(verdict: str, quote: str) -> str:
    return json.dumps(
        {"quote": quote, "reason": "r", "verdict": verdict, "severity": "none"}
    )


def tokens_for(verdict: str, counts: dict[str, int]) -> list[TokenLogprobs]:
    total = sum(counts.values())
    top: dict[str, float] = {}
    for piece, count in counts.items():
        top[piece] = math.log(count / total)
    first = verdict[:PREFIX_LENGTH]
    return [
        TokenLogprobs(token=OPENING, logprob=0.0, top={}),
        TokenLogprobs(token=first, logprob=top[first], top=top),
        TokenLogprobs(token=verdict[PREFIX_LENGTH:], logprob=0.0, top={}),
        TokenLogprobs(token='", "severity": "none"}', logprob=0.0, top={}),
    ]


class FakeClient:
    def __init__(self, verdict: str) -> None:
        self.verdict = verdict

    def complete_with_logprobs(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
        top_logprobs: int,
    ) -> LogprobCompletion:
        text = reply_text(self.verdict, "")
        return LogprobCompletion(text=text, tokens=[])


def test_the_prompts_define_all_verdicts_and_number_the_fragments() -> None:
    system = build_verdict_system_prompt(False, False, False)
    for verdict in VERDICTS:
        assert verdict in system
    user = build_verdict_user_prompt("Use MFA.", ["First.", "Second."], "")
    assert "[1] First." in user and "[2] Second." in user and "Use MFA." in user


def test_a_valid_reply_is_parsed_and_a_broken_one_is_rejected() -> None:
    parsed = parse_verdict_reply(reply_text("violated", "Quote here."))
    assert parsed.verdict == "violated" and parsed.quote == "Quote here."
    with pytest.raises(ReplyParseError):
        parse_verdict_reply('{"verdict": "maybe"}')


def test_confidence_is_the_normalized_share_of_the_chosen_verdict() -> None:
    counts: dict[str, int] = {"comp": COMPLIANT_COUNT, "viol": VIOLATED_COUNT, "unc": 1}
    total = sum(counts.values())
    tokens = tokens_for("compliant", counts)
    compliant = compute_confidence(tokens, "compliant")
    violated = compute_confidence(tokens, "violated")
    assert compliant is not None and math.isclose(compliant, COMPLIANT_COUNT / total)
    assert violated is not None and math.isclose(violated, VIOLATED_COUNT / total)
    assert compute_confidence([], "compliant") is None


def first_units() -> list[DesignUnit]:
    materials = load_case_materials(list_case_ids("dev")[0])
    return split_units(materials.design_text)


def test_the_gold_fragment_replaces_the_last_candidate_only_when_missing() -> None:
    units = first_units()
    far = len(units) - 1
    ranked: list[tuple[int, int]] = [(index, index) for index in range(CANDIDATES + 1)]
    near_gold: list[tuple[int, int]] = [(units[0].start, units[0].end)]
    assert guarantee_gold(ranked, CANDIDATES, units, near_gold) == ranked[:CANDIDATES]
    far_gold: list[tuple[int, int]] = [(units[far].start, units[far].end)]
    swapped = guarantee_gold(ranked, CANDIDATES, units, far_gold)
    assert len(swapped) == CANDIDATES
    assert swapped[:-1] == ranked[: CANDIDATES - 1] and swapped[-1] == (far, far)
    assert union_units(swapped, CANDIDATES) == sorted({0, 1, far})


def find_case_with_violation() -> CaseMaterials:
    for case_id in list_case_ids("dev"):
        materials = load_case_materials(case_id)
        if any(truth.verdict == "violated" for truth in build_case_truth(materials)):
            return materials
    raise LookupError("no case with a violation")


def review(
    materials: CaseMaterials,
    oracle: bool,
) -> tuple[PolicyAnalysis, VerdictCaseRecord]:
    version = materials.labels.policy_version
    analysis = load_policy_analysis(SETTINGS.analysis_set, version)
    rankings: CaseRankings = load_rankings("dev", SETTINGS.analysis_set)[
        materials.case_id
    ]
    choice = ContextChoice(
        method="dense",
        window=0,
        candidates=CANDIDATES,
        oracle=oracle,
        strict=False,
        overview_chars=0,
        reasoned=False,
    )
    record = review_case_verdicts(
        FakeClient("unclear"), materials, analysis, rankings, choice
    )
    return analysis, record


def test_the_review_gives_one_record_per_requirement() -> None:
    analysis, record = review(find_case_with_violation(), False)
    ids: list[str] = [item.requirement_id for item in record.records]
    assert ids == [item.id for item in analysis.requirements]
    assert all(item.context_units for item in record.records)
    assert len(to_requirement_verdicts(record)) == len(analysis.requirements)


def overlapping_units(units: list[DesignUnit], span: tuple[int, int]) -> set[int]:
    start, end = span
    found: set[int] = set()
    for index, unit in enumerate(units):
        if unit.start < end and unit.end > start:
            found.add(index)
    return found


def shown_units(record: VerdictCaseRecord) -> dict[str, set[int]]:
    shown: dict[str, set[int]] = {}
    for item in record.records:
        shown[item.requirement_id] = set(item.context_units)
    return shown


def test_the_oracle_context_always_holds_the_gold_sentence() -> None:
    materials = find_case_with_violation()
    analysis, record = review(materials, True)
    truths = build_case_truth(materials)
    units = split_units(materials.design_text)
    shown = shown_units(record)
    for index, requirement_id in match_truths(materials, analysis, truths).items():
        if truths[index].verdict in EVIDENCE_VERDICTS:
            gold = overlapping_units(units, truths[index].design_spans[0])
            assert gold & shown[requirement_id]


def answer_tokens(counts: dict[str, int]) -> list[TokenLogprobs]:
    total = sum(counts.values())
    top: dict[str, float] = {}
    for piece, count in counts.items():
        top[piece] = math.log(count / total)
    return [
        TokenLogprobs(token='{"answer": "', logprob=0.0, top={}),
        TokenLogprobs(token="yes", logprob=top["yes"], top=top),
        TokenLogprobs(token='"}', logprob=0.0, top={}),
    ]


def test_the_verifier_confidence_is_the_probability_of_yes_among_yes_and_no() -> None:
    yes_count = len("abc")
    tokens = answer_tokens({"yes": yes_count, "no": 1, "maybe": yes_count})
    confidence = probability_of_yes(tokens)
    assert confidence is not None
    assert math.isclose(confidence, yes_count / (yes_count + 1))
    assert probability_of_yes([]) is None
