"""Tests for reply parsing, quote grounding, matching and run metrics."""

from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

import pytest

from secreview.agents import run_config
from secreview.agents.baseline import ReviewRecord, ReviewVariant, review_case
from secreview.agents.case_materials import (
    CaseMaterials,
    list_case_ids,
    load_case_materials,
)
from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.agents.prompts import build_system_prompt
from secreview.agents.run_config import save_run_config
from secreview.datagen.case_files import processed_case_directory
from secreview.datagen.labels import FlawLabel
from secreview.evaluation.class_report import build_class_report, build_ordinal_report
from secreview.evaluation.evidence import is_in_scope
from secreview.evaluation.matching import match_case
from secreview.evaluation.outcomes import CaseOutcome, GoldOutcome
from secreview.evaluation.summary import DetectionScores, summarize
from secreview.parsing.findings import (
    ACTIONS,
    SEVERITIES,
    ReplyParseError,
    build_reply_schema,
    parse_reply,
)
from secreview.parsing.grounding import locate_quote
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.review_settings import REVIEW_SETTINGS

MIN_CHARACTERS = REVIEW_SETTINGS.grounding.min_quote_characters
MAX_CONFIDENCE = REVIEW_SETTINGS.confidence_maximum
ORACLE = "oracle"
PLAIN = ReviewVariant(use_topics=False, ask_for_silence=False, policy_analysis=ORACLE)
WITH_TOPICS = ReviewVariant(
    use_topics=True,
    ask_for_silence=False,
    policy_analysis=ORACLE,
)
SILENCE_TITLE = "Silence about requirements"


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


def build_finding(
    design_quote: str,
    requirement: PolicyRequirement,
    finding_type: str,
    severity: str,
    use_topics: bool,
) -> dict[str, object]:
    finding: dict[str, object] = {"design_quote": design_quote}
    if use_topics:
        finding["topics"] = requirement.topics
    finding.update(
        observation="what the design says",
        requirement_id=requirement.id,
        finding_type=finding_type,
        severity=severity,
        confidence=MAX_CONFIDENCE,
    )
    return finding


def build_reply(findings: list[dict[str, object]]) -> str:
    return json.dumps({"findings": findings})


def first_flaw_case() -> CaseMaterials:
    for case_id in list_case_ids("dev"):
        materials = load_case_materials(case_id)
        if any(is_in_scope(flaw) for flaw in materials.labels.flaws):
            return materials
    raise LookupError("no dev case with an in-scope flaw")


def oracle_for(materials: CaseMaterials) -> PolicyAnalysis:
    return build_oracle_analysis(materials.labels.policy_version)


def requirement_for(flaw: FlawLabel, analysis: PolicyAnalysis) -> PolicyRequirement:
    first, last = next(iter(flaw.policy_spans.values()))[0]
    for requirement in analysis.requirements:
        if requirement.span == (first, last):
            return requirement
    raise LookupError(flaw.flaw_id)


def build_perfect_finding(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    flaw: FlawLabel,
    use_topics: bool,
) -> dict[str, object]:
    start, end = flaw.design_spans[0]
    return build_finding(
        materials.design_text[start:end],
        requirement_for(flaw, analysis),
        flaw.type,
        flaw.severity,
        use_topics,
    )


def pick_in_scope_flaw(materials: CaseMaterials) -> FlawLabel:
    return next(item for item in materials.labels.flaws if is_in_scope(item))


@dataclass(frozen=True)
class PreparedReview:
    materials: CaseMaterials
    analysis: PolicyAnalysis
    flaw: FlawLabel
    finding: dict[str, object]


def prepare_review() -> PreparedReview:
    materials = first_flaw_case()
    analysis = oracle_for(materials)
    flaw = pick_in_scope_flaw(materials)
    finding = build_perfect_finding(materials, analysis, flaw, False)
    return PreparedReview(materials, analysis, flaw, finding)


def review_findings(
    prepared: PreparedReview,
    findings: list[dict[str, object]],
) -> ReviewRecord:
    client = FakeClient(build_reply(findings))
    return review_case(client, prepared.materials, prepared.analysis, PLAIN)


def sample_finding() -> dict[str, object]:
    requirement = oracle_for(first_flaw_case()).requirements[0]
    quote = "a quote of some length"
    return build_finding(quote, requirement, "violation", "high", False)


def test_parse_reply_accepts_fenced_json_after_reasoning() -> None:
    reply = "<think>hmm</think>\n```json\n" + build_reply([sample_finding()]) + "\n```"
    parsed = parse_reply(reply, False)
    assert len(parsed.findings) == 1
    assert not parsed.recovered


def test_parse_reply_without_any_json_is_an_error() -> None:
    with pytest.raises(ReplyParseError):
        parse_reply("no json here", False)


def test_parse_reply_salvages_complete_findings_of_a_truncated_reply() -> None:
    complete = json.dumps(sample_finding())
    cut_item = '{"design_quote": "cut'
    reply = '{"findings": [' + complete + ", " + complete + ", " + cut_item
    parsed = parse_reply(reply, False)
    assert len(parsed.findings) == len([complete, complete])
    assert parsed.recovered


def test_parse_reply_drops_invalid_items_and_flags_the_recovery() -> None:
    good = sample_finding()
    bad: dict[str, object] = {**good, "severity": "extreme"}
    parsed = parse_reply(build_reply([bad, good]), False)
    assert len(parsed.findings) == 1
    assert parsed.recovered


def test_locate_quote_tolerates_whitespace_and_small_typos() -> None:
    text = "Alpha beta.\nThe service stores   all passwords in clear text. Omega."
    exact_quote = "The service stores all passwords in clear text."
    fuzzy_quote = "The service stores all pasword in clear text."
    exact = locate_quote(text, exact_quote, MIN_CHARACTERS)
    fuzzy = locate_quote(text, fuzzy_quote, MIN_CHARACTERS)
    assert exact is not None and fuzzy is not None
    start, end = exact
    assert text[start:end].startswith("The service")
    invented = "Completely unrelated invented sentence here."
    assert locate_quote(text, invented, MIN_CHARACTERS) is None


def test_token_overlap_is_intersection_over_union() -> None:
    text = "one two three four five"
    first = collect_token_indices(text, [(0, text.index(" four"))])
    second = collect_token_indices(text, [(text.index("two"), text.index(" five"))])
    assert first == {0, 1, 2}
    assert compute_overlap(first, second) == len(first & second) / len(first | second)
    assert compute_overlap(set(), set()) == 0.0


def test_exact_gold_quote_is_matched_and_invented_quote_is_dropped() -> None:
    prepared = prepare_review()
    invented: dict[str, object] = {
        **prepared.finding,
        "design_quote": "This sentence is not in the design text.",
    }
    record = review_findings(prepared, [prepared.finding, invented])
    outcome = match_case(prepared.materials, record)
    assert record.rejected_hallucinations == len(record.rejected_findings) == 1
    assert record.rejected_findings[0].reason == REVIEW_SETTINGS.rejection_reason
    assert len(record.findings) == 1
    assert any(gold.matched for gold in outcome.golds)


def test_unknown_requirement_id_is_rejected_with_its_reason() -> None:
    prepared = prepare_review()
    unknown: dict[str, object] = {**prepared.finding, "requirement_id": "R9999"}
    record = review_findings(prepared, [unknown])
    assert not record.findings
    reason = record.rejected_findings[0].reason
    assert reason == REVIEW_SETTINGS.unknown_requirement_reason


def test_duplicate_findings_are_merged() -> None:
    prepared = prepare_review()
    record = review_findings(prepared, [prepared.finding, prepared.finding])
    assert len(record.findings) == 1


def shorten_quote(quote: str) -> str:
    words = quote.split()
    return " ".join(words[: len(words) - 1])


def test_overlapping_quotes_of_one_requirement_are_merged() -> None:
    prepared = prepare_review()
    shorter: dict[str, object] = {
        **prepared.finding,
        "design_quote": shorten_quote(str(prepared.finding["design_quote"])),
    }
    record = review_findings(prepared, [prepared.finding, shorter])
    assert len(record.findings) == 1


def test_the_same_place_cited_for_two_requirements_stays_two_findings() -> None:
    prepared = prepare_review()
    other = pick_other_requirement(prepared.analysis, prepared.flaw)
    second: dict[str, object] = {**prepared.finding, "requirement_id": other.id}
    record = review_findings(prepared, [prepared.finding, second])
    assert len(record.findings) == len([prepared.finding, second])


def test_action_follows_the_wording_of_the_cited_requirement() -> None:
    prepared = prepare_review()
    record = review_findings(prepared, [prepared.finding])
    wording = requirement_for(prepared.flaw, prepared.analysis).wording
    action = record.findings[0].action
    assert (action == REVIEW_SETTINGS.evaluation.review_action) == (wording != "clear")
    assert action in ACTIONS


def test_unparseable_reply_is_recorded_as_parse_failure() -> None:
    materials = first_flaw_case()
    record = review_case(FakeClient("sorry"), materials, oracle_for(materials), PLAIN)
    summary = summarize([match_case(materials, record)])
    assert record.parse_error is not None
    assert summary.parse_failures == 1
    assert summary.loose.recall_all_scorable == 0.0


def review_perfectly(case_id: str, variant: ReviewVariant) -> CaseOutcome:
    materials = load_case_materials(case_id)
    analysis = oracle_for(materials)
    findings: list[dict[str, object]] = []
    for flaw in materials.labels.flaws:
        if is_in_scope(flaw):
            findings.append(
                build_perfect_finding(materials, analysis, flaw, variant.use_topics)
            )
    reply = build_reply(findings)
    record = review_case(FakeClient(reply), materials, analysis, variant)
    return match_case(materials, record)


def assert_perfect_detection(scores: DetectionScores) -> None:
    assert scores.recall_all_scorable >= 1.0
    assert scores.recall_important >= 1.0
    assert all(value >= 1.0 for value in scores.recall_important_at_budget.values())
    assert scores.precision >= 1.0


@pytest.mark.parametrize("variant", [PLAIN, WITH_TOPICS])
def test_perfect_reviewer_reaches_full_loose_and_strict_recall(
    variant: ReviewVariant,
) -> None:
    outcomes: list[CaseOutcome] = []
    for case_id in list_case_ids("test"):
        outcomes.append(review_perfectly(case_id, variant))
    summary = summarize(outcomes)
    assert_perfect_detection(summary.loose)
    assert_perfect_detection(summary.strict)
    assert summary.parse_failures == 0
    assert summary.type_report.accuracy >= 1.0
    assert summary.severity_ordinal.mean_absolute_error == 0.0
    assert summary.action_report.accuracy >= 1.0


def pick_other_requirement(
    analysis: PolicyAnalysis,
    flaw: FlawLabel,
) -> PolicyRequirement:
    gold_spans: set[tuple[int, ...]] = set()
    for spans in flaw.policy_spans.values():
        gold_spans.update(tuple(span) for span in spans)
    for requirement in analysis.requirements:
        if requirement.span not in gold_spans:
            return requirement
    raise LookupError(flaw.flaw_id)


def test_wrong_requirement_fails_only_the_strict_rule() -> None:
    prepared = prepare_review()
    other = pick_other_requirement(prepared.analysis, prepared.flaw)
    finding: dict[str, object] = {**prepared.finding, "requirement_id": other.id}
    record = review_findings(prepared, [finding])
    summary = summarize([match_case(prepared.materials, record)])
    assert summary.rejected_hallucinations == 0
    assert summary.loose.recall_all_scorable > 0.0
    assert summary.strict.recall_all_scorable == 0.0
    assert summary.policy_evidence_accuracy == 0.0


def find_drift_case() -> CaseMaterials:
    for case_id in list_case_ids("dev"):
        materials = load_case_materials(case_id)
        if any(flaw.type == "drift" for flaw in materials.labels.flaws):
            return materials
    raise LookupError("no dev case with a drift")


def build_drift_quote_finding(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    drift: FlawLabel,
) -> dict[str, object]:
    start, end = drift.design_spans[0]
    quote = materials.design_text[start:end]
    return build_finding(quote, analysis.requirements[0], "violation", "high", False)


def test_drift_flaws_are_out_of_scope_and_a_finding_on_them_is_a_false_alarm() -> None:
    materials = find_drift_case()
    analysis = oracle_for(materials)
    drift = next(item for item in materials.labels.flaws if item.type == "drift")
    finding = build_drift_quote_finding(materials, analysis, drift)
    prepared = PreparedReview(materials, analysis, drift, finding)
    outcome = match_case(materials, review_findings(prepared, [finding]))
    golds: dict[str, GoldOutcome] = {item.flaw_id: item for item in outcome.golds}
    assert not golds[drift.flaw_id].scorable
    assert not golds[drift.flaw_id].matched
    assert [item.matched_flaw_id for item in outcome.predictions] == [None]


def test_reply_schema_variants_and_requirement_ids() -> None:
    ids: list[str] = ["R1", "R2"]
    plain = json.dumps(build_reply_schema(False, ids, False))
    topical = json.dumps(build_reply_schema(True, ids, False))
    assert "topics" not in plain
    assert topical.index("design_quote") < topical.index("topics")
    assert topical.index("topics") < topical.index("observation")
    assert '"enum": ["R1", "R2"]' in plain
    assert "implementation" not in plain and "drift" not in plain


def test_prompt_switches_add_only_their_own_instructions() -> None:
    plain = build_system_prompt(False, False, False)
    topical = build_system_prompt(True, False, False)
    silent = build_system_prompt(False, True, False)
    assert "topics" not in plain and SILENCE_TITLE not in plain
    assert "topics" in topical and SILENCE_TITLE not in topical
    assert SILENCE_TITLE in silent and "topics" not in silent
    assert "drift" not in topical.lower()


def fake_digest(name: str) -> str:
    return name


def test_run_config_is_stored_once_and_a_changed_variant_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        monkeypatch.setattr(REVIEW_SETTINGS, "runs_directory", directory)
        monkeypatch.setattr(run_config, "digest_analysis_set", fake_digest)
        save_run_config("sample", PLAIN)
        save_run_config("sample", PLAIN)
        path = Path(directory) / "sample" / REVIEW_SETTINGS.run_config_file
        assert "requirement_id" in path.read_text(encoding="utf-8")
        with pytest.raises(ValueError):
            save_run_config("sample", WITH_TOPICS)


def test_ordinal_report_measures_distance_and_bias() -> None:
    far = SEVERITIES.index("critical") - SEVERITIES.index("low")
    pairs: list[tuple[str, str]] = [
        ("low", "critical"),
        ("high", "high"),
        ("critical", "high"),
    ]
    report = build_ordinal_report(pairs, SEVERITIES)
    assert report.exact_accuracy == 1 / len(pairs)
    assert report.within_one_accuracy == 2 / len(pairs)
    assert report.mean_absolute_error == (far + 0 + 1) / len(pairs)
    assert report.mean_signed_error == (far + 0 - 1) / len(pairs)


def test_class_report_exposes_a_class_the_model_never_predicts() -> None:
    pairs: list[tuple[str, str]] = [
        ("fix", "fix"),
        ("fix", "fix"),
        ("clarify", "fix"),
    ]
    report = build_class_report(pairs, ACTIONS)
    assert report.per_class["clarify"].recall == 0.0
    assert report.per_class["fix"].precision == 2 / len(pairs)
    assert report.confusion["clarify"]["fix"] == 1


def test_gold_implementation_spans_exist_exactly_for_mutated_flaws() -> None:
    for case_id in list_case_ids("dev") + list_case_ids("test"):
        materials = load_case_materials(case_id)
        directory = processed_case_directory(case_id)
        implementation = directory / materials.labels.implementation_file
        length = len(implementation.read_text(encoding="utf-8"))
        for flaw in materials.labels.flaws:
            has_mutation = flaw.manifest != "design"
            assert bool(flaw.implementation_spans) == has_mutation, case_id
            for start, end in flaw.implementation_spans:
                assert 0 <= start < end <= length


COMPLIANCE_TITLE = "Compliance:"
COMPLIANT_VARIANT = ReviewVariant(
    use_topics=False,
    ask_for_silence=False,
    policy_analysis=ORACLE,
    allow_compliant=True,
)


def test_compliant_findings_are_dropped_and_counted() -> None:
    prepared = prepare_review()
    compliant: dict[str, object] = {**prepared.finding, "finding_type": "compliant"}
    client = FakeClient(build_reply([compliant, prepared.finding]))
    record = review_case(
        client,
        prepared.materials,
        prepared.analysis,
        COMPLIANT_VARIANT,
    )
    assert len(record.findings) == 1
    assert record.compliant_findings == 1


def test_compliance_switch_changes_the_schema_and_the_prompt() -> None:
    ids: list[str] = ["R1"]
    without = json.dumps(build_reply_schema(False, ids, False))
    with_switch = json.dumps(build_reply_schema(False, ids, True))
    assert "compliant" not in without and "compliant" in with_switch
    assert COMPLIANCE_TITLE not in build_system_prompt(False, False, False)
    assert COMPLIANCE_TITLE in build_system_prompt(False, False, True)
