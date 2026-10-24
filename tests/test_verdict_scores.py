"""Tests for the gold verdicts and the verdict scores."""

from collections import Counter
import json
from pathlib import Path

from secreview.agents.case_materials import (
    CaseMaterials,
    list_case_ids,
    load_case_materials,
)
from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.policy_requirements import PolicyAnalysis
from secreview.agents.verdicts import RequirementVerdict
from secreview.evaluation.verdict_scores import (
    CaseVerdictOutcome,
    VerdictScores,
    score_case_verdicts,
    summarize_verdicts,
)
from secreview.evaluation.verdict_truth import PairTruth, build_case_truth
from secreview.parsing.vocabulary import EVIDENCE_VERDICTS, UNCLEAR, VERDICTS

EXPECTED = json.loads(
    (Path(__file__).parent / "data" / "verdict_truth_dev.json").read_text(
        encoding="utf-8"
    )
)
LOCATED_UNCLEAR = ("soft_violation", "partial_statement")
SHIFT = len("abcdefghij")
FAR_SHIFT = SHIFT * SHIFT * SHIFT * SHIFT


def dev_materials() -> list[CaseMaterials]:
    return [load_case_materials(case_id) for case_id in list_case_ids("dev")]


def make_verdict(
    requirement_id: str,
    verdict: str,
    span: tuple[int, int] | None,
) -> RequirementVerdict:
    return RequirementVerdict.model_validate(
        {"requirement_id": requirement_id, "verdict": verdict, "design_span": span}
    )


def shifted_span(truth: PairTruth, shift: int) -> tuple[int, int] | None:
    if truth.verdict not in EVIDENCE_VERDICTS:
        return None
    start, end = truth.design_spans[0]
    return start + shift, end + shift


def perfect_verdicts(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    shift: int,
) -> list[RequirementVerdict]:
    by_span: dict[tuple[int, int], PairTruth] = {}
    for truth in build_case_truth(materials):
        by_span.setdefault(truth.requirement_span, truth)
    verdicts: list[RequirementVerdict] = []
    for requirement in analysis.requirements:
        truth = by_span[requirement.span]
        span = shifted_span(truth, shift)
        verdicts.append(make_verdict(requirement.id, truth.verdict, span))
    return verdicts


def score_all(
    shift: int,
    keep_every_other: bool,
) -> VerdictScores:
    outcomes: list[CaseVerdictOutcome] = []
    for materials in dev_materials():
        analysis = build_oracle_analysis(materials.labels.policy_version)
        verdicts = perfect_verdicts(materials, analysis, shift)
        if keep_every_other:
            half = analysis.requirements[::2]
            analysis = analysis.model_copy(update={"requirements": half})
        outcomes.append(score_case_verdicts(materials, analysis, verdicts))
    return summarize_verdicts(outcomes)


def test_gold_verdicts_follow_the_agreed_rules() -> None:
    verdicts: Counter[str] = Counter()
    subtypes: Counter[str] = Counter()
    for materials in dev_materials():
        for truth in build_case_truth(materials):
            verdicts[truth.verdict] += 1
            subtypes[truth.subtype] += 1
    assert sum(verdicts.values()) == EXPECTED["total"]
    assert dict(verdicts) == EXPECTED["by_verdict"]
    assert dict(subtypes) == EXPECTED["by_subtype"]


def test_only_compliant_and_violated_truths_have_a_design_location() -> None:
    for materials in dev_materials():
        for truth in build_case_truth(materials):
            has_location = bool(truth.design_spans)
            shows_evidence = truth.verdict in EVIDENCE_VERDICTS
            assert has_location == (shows_evidence or truth.subtype in LOCATED_UNCLEAR)


def test_the_perfect_answer_scores_one_everywhere() -> None:
    scores = score_all(0, False)
    assert scores.accuracy == scores.accuracy_with_evidence == 1.0
    assert scores.violated_precision_with_evidence == 1.0
    assert scores.reportable.recall == scores.reportable.precision == 1.0
    assert scores.reportable.false_alarm_rate == 0.0
    assert scores.reportable.tolerant_accuracy == 1.0
    assert scores.missing_pairs == scores.extra_requirements == 0
    assert scores.report.macro_f1 == 1.0
    assert all(rate == 1.0 for rate in scores.evidence_rate.values())
    assert all(recall == 1.0 for recall in scores.recall_by_subtype.values())


def test_a_wrong_quote_keeps_the_verdict_but_loses_the_evidence() -> None:
    scores = score_all(FAR_SHIFT, False)
    assert scores.accuracy == 1.0
    assert scores.accuracy_with_evidence < scores.accuracy
    assert scores.evidence_rate["violated"] == 0.0
    assert scores.violated_precision_with_evidence < 1.0


def test_requirements_the_analysis_missed_are_counted_as_missing() -> None:
    scores = score_all(0, True)
    assert scores.missing_pairs > 0
    assert scores.accuracy < 1.0
    assert scores.report.confusion["violated"]["missing"] > 0
    assert scores.extra_requirements == 0


def unclear_everywhere(analysis: PolicyAnalysis) -> list[RequirementVerdict]:
    verdicts: list[RequirementVerdict] = []
    for requirement in analysis.requirements:
        verdicts.append(make_verdict(requirement.id, UNCLEAR, None))
    return verdicts


def score_unclear_everywhere() -> VerdictScores:
    outcomes: list[CaseVerdictOutcome] = []
    for materials in dev_materials():
        analysis = build_oracle_analysis(materials.labels.policy_version)
        verdicts = unclear_everywhere(analysis)
        outcomes.append(score_case_verdicts(materials, analysis, verdicts))
    return summarize_verdicts(outcomes)


def test_answering_unclear_everywhere_is_right_only_for_the_unclear_truths() -> None:
    scores = score_unclear_everywhere()
    share = EXPECTED["scored_by_verdict"][UNCLEAR] / EXPECTED["scored_total"]
    assert abs(scores.accuracy - share) < 1 / EXPECTED["scored_total"]
    assert scores.report.per_class[UNCLEAR].recall == 1.0
    assert scores.report.per_class["violated"].recall == 0.0
    assert scores.recall_by_subtype["planted_violation"] == 0.0
    assert scores.reportable.recall == 1.0
    assert scores.reportable.false_alarm_rate == 1.0
    assert set(scores.report.per_class) == set(VERDICTS)
