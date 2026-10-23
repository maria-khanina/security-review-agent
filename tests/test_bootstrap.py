"""Tests for bootstrap intervals and the paired comparison of two runs."""

from secreview.agents.case_materials import list_case_ids
from secreview.evaluation.bootstrap import (
    align_outcomes,
    bootstrap_difference,
    bootstrap_run,
)
from secreview.evaluation.outcomes import (
    CaseOutcome,
    GoldOutcome,
    PredictionOutcome,
)

DOCUMENT_COUNT = len(list_case_ids("dev"))


def build_outcome(index: int, found: bool) -> CaseOutcome:
    case_id = f"case{index:03d}"
    gold = GoldOutcome(
        case_id=case_id,
        flaw_id="F1",
        flaw_type="violation",
        severity="high",
        policy_status="clear",
        expected_action="fix",
        scorable=True,
        matched=found,
        evidence_correct=found,
        confidence=1,
        predicted_type="violation" if found else "",
        predicted_action="fix" if found else "",
        predicted_severity="high" if found else "",
    )
    predictions: list[PredictionOutcome] = []
    if found:
        predictions.append(
            PredictionOutcome(
                case_id=case_id,
                confidence=1,
                matched_flaw_id="F1",
                strict_matched=True,
            )
        )
    return CaseOutcome(
        case_id=case_id,
        golds=[gold],
        predictions=predictions,
        parse_failed=False,
        recovered=False,
        rejected_hallucinations=0,
    )


def build_run(found_every: int) -> list[CaseOutcome]:
    outcomes: list[CaseOutcome] = []
    for index in range(DOCUMENT_COUNT):
        outcomes.append(build_outcome(index, index % found_every != 0))
    return outcomes


def test_interval_contains_the_estimate_and_is_ordered() -> None:
    intervals = bootstrap_run(build_run(2))
    interval = intervals["loose_recall_important"]
    assert interval.low <= interval.estimate <= interval.high
    assert interval.low < interval.high


def test_paired_difference_flags_a_clearly_better_run() -> None:
    weaker = build_run(2)
    stronger = build_run(DOCUMENT_COUNT + 1)
    differences = bootstrap_difference(weaker, stronger)
    assert differences["loose_recall_important"].significant
    assert differences["loose_recall_important"].difference.estimate > 0.0


def test_paired_difference_of_identical_runs_is_zero_and_not_significant() -> None:
    run = build_run(2)
    differences = bootstrap_difference(run, run)
    item = differences["loose_recall_important"]
    assert item.difference.estimate == 0.0
    assert not item.significant


def test_alignment_keeps_only_shared_documents_in_the_same_order() -> None:
    first = build_run(2)
    second: list[CaseOutcome] = list(
        reversed(build_run(DOCUMENT_COUNT + 1)[: DOCUMENT_COUNT // 2])
    )
    aligned_first, aligned_second = align_outcomes(first, second)
    first_ids: list[str] = [item.case_id for item in aligned_first]
    second_ids: list[str] = [item.case_id for item in aligned_second]
    assert first_ids == second_ids == sorted(second_ids)
    assert len(first_ids) == DOCUMENT_COUNT // 2
