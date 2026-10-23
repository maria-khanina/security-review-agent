"""Aggregate metrics of a baseline run over the evaluated cases."""

from collections import defaultdict

from pydantic import BaseModel

from secreview.evaluation.class_report import (
    ClassReport,
    OrdinalReport,
    build_class_report,
    build_ordinal_report,
    divide,
)
from secreview.evaluation.froc import (
    compute_recall_at_budget,
    is_found,
    list_scored_golds,
)
from secreview.evaluation.outcomes import CaseOutcome, GoldOutcome
from secreview.parsing.findings import ACTIONS, FINDING_TYPES, SEVERITIES
from secreview.review_settings import REVIEW_SETTINGS


class DetectionScores(BaseModel):
    precision: float
    false_alarms_per_document: float
    recall_all_scorable: float
    recall_important: float
    recall_important_at_budget: dict[str, float]
    recall_by_type: dict[str, float]
    recall_by_policy_status: dict[str, float]


class Summary(BaseModel):
    documents: int
    parse_failures: int
    recovered_replies: int
    rejected_hallucinations: int
    out_of_scope_flaws: int
    loose: DetectionScores
    strict: DetectionScores
    loose_on_parsed_documents: DetectionScores
    strict_on_parsed_documents: DetectionScores
    policy_evidence_accuracy: float
    type_report: ClassReport
    action_report: ClassReport
    severity_report: ClassReport
    severity_ordinal: OrdinalReport


def list_golds(outcomes: list[CaseOutcome]) -> list[GoldOutcome]:
    """Flatten the planted-flaw outcomes of all cases."""
    golds: list[GoldOutcome] = []
    for outcome in outcomes:
        golds.extend(outcome.golds)
    return golds


def compute_recall_by(
    golds: list[GoldOutcome],
    attribute: str,
    strict: bool,
) -> dict[str, float]:
    """Compute recall of scorable flaws grouped by one of their attributes."""
    totals: dict[str, int] = defaultdict(int)
    found: dict[str, int] = defaultdict(int)
    for gold in golds:
        if not gold.scorable:
            continue
        key = str(getattr(gold, attribute))
        totals[key] += 1
        found[key] += int(is_found(gold, strict))
    return {key: divide(found[key], totals[key]) for key in totals}


def count_predictions(outcomes: list[CaseOutcome], strict: bool) -> tuple[int, int]:
    """Count all findings and the findings that count as correct."""
    total = 0
    correct = 0
    for outcome in outcomes:
        total += len(outcome.predictions)
        for prediction in outcome.predictions:
            matched = prediction.matched_flaw_id is not None
            correct += int(prediction.strict_matched if strict else matched)
    return total, correct


def compute_budget_recalls(
    outcomes: list[CaseOutcome],
    strict: bool,
) -> dict[str, float]:
    """Compute important-flaw recall at every configured false-alarm budget."""
    recalls: dict[str, float] = {}
    for budget in REVIEW_SETTINGS.evaluation.false_alarm_budgets:
        recalls[str(budget)] = compute_recall_at_budget(outcomes, budget, strict)
    return recalls


def score_detection(outcomes: list[CaseOutcome], strict: bool) -> DetectionScores:
    """Score how well planted flaws were found under the loose or strict rule."""
    golds = list_golds(outcomes)
    scorable: list[GoldOutcome] = [gold for gold in golds if gold.scorable]
    important = list_scored_golds(outcomes)
    total, correct = count_predictions(outcomes, strict)
    found = sum(1 for gold in scorable if is_found(gold, strict))
    important_found = sum(1 for gold in important if is_found(gold, strict))
    return DetectionScores(
        precision=divide(correct, total),
        false_alarms_per_document=divide(total - correct, len(outcomes)),
        recall_all_scorable=divide(found, len(scorable)),
        recall_important=divide(important_found, len(important)),
        recall_important_at_budget=compute_budget_recalls(outcomes, strict),
        recall_by_type=compute_recall_by(golds, "flaw_type", strict),
        recall_by_policy_status=compute_recall_by(golds, "policy_status", strict),
    )


def count_rejected_hallucinations(outcomes: list[CaseOutcome]) -> int:
    """Count the findings dropped because their design quote is not in the text."""
    return sum(outcome.rejected_hallucinations for outcome in outcomes)


def compute_evidence_accuracy(found: list[GoldOutcome]) -> float:
    """Compute how often a located flaw cites the right policy sentence."""
    return divide(sum(1 for gold in found if gold.evidence_correct), len(found))


def pair_attributes(
    found: list[GoldOutcome],
    gold_attribute: str,
    predicted_attribute: str,
) -> list[tuple[str, str]]:
    """Pair the gold and predicted value of an attribute for each located flaw."""
    pairs: list[tuple[str, str]] = []
    for gold in found:
        expected = str(getattr(gold, gold_attribute))
        reported = str(getattr(gold, predicted_attribute))
        pairs.append((expected, reported))
    return pairs


def select_parsed(outcomes: list[CaseOutcome]) -> list[CaseOutcome]:
    """Keep the cases whose reply could be read at all."""
    parsed: list[CaseOutcome] = []
    for outcome in outcomes:
        if not outcome.parse_failed:
            parsed.append(outcome)
    return parsed


def summarize(outcomes: list[CaseOutcome]) -> Summary:
    """Aggregate the case outcomes into the headline metrics."""
    golds = list_golds(outcomes)
    parsed = select_parsed(outcomes)
    located: list[GoldOutcome] = [gold for gold in golds if gold.scorable]
    found: list[GoldOutcome] = [gold for gold in located if gold.matched]
    severity_pairs = pair_attributes(found, "severity", "predicted_severity")
    return Summary(
        documents=len(outcomes),
        parse_failures=sum(1 for outcome in outcomes if outcome.parse_failed),
        recovered_replies=sum(1 for outcome in outcomes if outcome.recovered),
        rejected_hallucinations=count_rejected_hallucinations(outcomes),
        out_of_scope_flaws=sum(1 for gold in golds if not gold.scorable),
        loose=score_detection(outcomes, False),
        strict=score_detection(outcomes, True),
        loose_on_parsed_documents=score_detection(parsed, False),
        strict_on_parsed_documents=score_detection(parsed, True),
        policy_evidence_accuracy=compute_evidence_accuracy(found),
        type_report=build_class_report(
            pair_attributes(found, "flaw_type", "predicted_type"), FINDING_TYPES
        ),
        action_report=build_class_report(
            pair_attributes(found, "expected_action", "predicted_action"), ACTIONS
        ),
        severity_report=build_class_report(severity_pairs, SEVERITIES),
        severity_ordinal=build_ordinal_report(severity_pairs, SEVERITIES),
    )
