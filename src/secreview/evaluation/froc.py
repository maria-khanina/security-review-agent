"""Recall of important flaws at fixed false-alarm budgets per document."""

from secreview.evaluation.outcomes import CaseOutcome, GoldOutcome
from secreview.review_settings import REVIEW_SETTINGS


def is_found(gold: GoldOutcome, strict: bool) -> bool:
    """Tell whether a flaw counts as found under the loose or strict rule."""
    return gold.strict_matched if strict else gold.matched


def list_scored_golds(outcomes: list[CaseOutcome]) -> list[GoldOutcome]:
    """Collect the planted flaws that count towards the important-flaw recall."""
    scored: list[GoldOutcome] = []
    severities = REVIEW_SETTINGS.evaluation.scored_severities
    for outcome in outcomes:
        for gold in outcome.golds:
            if gold.scorable and gold.severity in severities:
                scored.append(gold)
    return scored


def collect_false_alarm_confidences(
    outcomes: list[CaseOutcome],
    strict: bool,
) -> list[int]:
    """Collect the confidence of every finding that counts as a false alarm."""
    confidences: list[int] = []
    for outcome in outcomes:
        for prediction in outcome.predictions:
            matched = prediction.matched_flaw_id is not None
            found = prediction.strict_matched if strict else matched
            if not found:
                confidences.append(prediction.confidence)
    return confidences


def compute_recall_at_threshold(
    scored: list[GoldOutcome],
    threshold: int,
    strict: bool,
) -> float:
    """Compute the share of important flaws found by findings above the threshold."""
    if not scored:
        return 0.0
    found = sum(
        1 for gold in scored if is_found(gold, strict) and gold.confidence >= threshold
    )
    return found / len(scored)


def compute_false_alarms_per_document(
    false_alarm_confidences: list[int],
    threshold: int,
    document_count: int,
) -> float:
    """Compute false alarms per document among findings above the threshold."""
    count = sum(1 for confidence in false_alarm_confidences if confidence >= threshold)
    return count / document_count if document_count else 0.0


def list_thresholds(
    scored: list[GoldOutcome],
    false_alarms: list[int],
) -> list[int]:
    """List the confidence values at which recall or false alarms can change."""
    values: set[int] = {REVIEW_SETTINGS.confidence_minimum}
    values.update(false_alarms)
    values.update(gold.confidence for gold in scored if gold.matched)
    return sorted(values)


def compute_recall_at_budget(
    outcomes: list[CaseOutcome],
    budget: float,
    strict: bool,
) -> float:
    """Return the best important-flaw recall within a false-alarm budget."""
    scored = list_scored_golds(outcomes)
    false_alarms = collect_false_alarm_confidences(outcomes, strict)
    best = 0.0
    for threshold in list_thresholds(scored, false_alarms):
        rate = compute_false_alarms_per_document(false_alarms, threshold, len(outcomes))
        if rate <= budget:
            best = max(best, compute_recall_at_threshold(scored, threshold, strict))
    return best
