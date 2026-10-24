"""Scores of requirement verdicts against the gold verdicts of a design."""

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.agents.verdicts import RequirementVerdict
from secreview.evaluation.class_report import (
    ClassReport,
    ClassScores,
    OrdinalReport,
    build_class_report,
    build_ordinal_report,
    count_confusion,
    divide,
    score_class,
)
from secreview.evaluation.policy_scores import match_one_to_one
from secreview.evaluation.verdict_truth import (
    PairTruth,
    build_case_truth,
)
from secreview.parsing.findings import SEVERITIES
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.parsing.vocabulary import (
    EVIDENCE_VERDICTS,
    UNCLEAR,
    VERDICTS,
    VIOLATED,
)
from secreview.review_settings import REVIEW_SETTINGS

Span = tuple[int, int]
MISSING = "missing"
CLASSES: tuple[str, ...] = VERDICTS + (MISSING,)
TRUTH_PREFIX = "T"
TIE_VALUE = 1 / 2


class PairOutcome(BaseModel):
    case_id: str
    rule_id: str
    gold_verdict: str
    subtype: str
    predicted_verdict: str
    evidence_ok: bool
    gold_severity: str
    predicted_severity: str
    confidence: float | None


class ReportScores(BaseModel):
    recall: float
    precision: float
    f1: float
    false_alarm_rate: float
    false_alarms_per_document: float
    tolerant_accuracy: float


class QuoteTally(BaseModel):
    predicted: int
    predicted_hits: int
    gold: int
    gold_hits: int


class CaseVerdictOutcome(BaseModel):
    pairs: list[PairOutcome]
    extra_requirements: int
    quotes: QuoteTally


class VerdictScores(BaseModel):
    pairs: int
    missing_pairs: int
    extra_requirements: int
    accuracy: float
    accuracy_with_evidence: float
    report: ClassReport
    evidence_rate: dict[str, float]
    recall_by_subtype: dict[str, float]
    reportable: ReportScores
    violated_precision_with_evidence: float
    violation_quote_precision: float
    violation_quote_recall: float
    severity_report: ClassReport | None
    severity_ordinal: OrdinalReport | None
    confidence_auroc: float | None


def build_gold_requirements(truths: list[PairTruth]) -> list[PolicyRequirement]:
    """Describe the gold requirement sentences, one per truth, for matching."""
    requirements: list[PolicyRequirement] = []
    for number, truth in enumerate(truths):
        requirements.append(
            PolicyRequirement(
                id=f"{TRUTH_PREFIX}{number}",
                quote="",
                span=truth.requirement_span,
                wording="clear",
                topics=[],
            )
        )
    return requirements


def match_truths(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    truths: list[PairTruth],
) -> dict[int, str]:
    """Map the index of each truth to the id of the requirement matched to it."""
    gold = build_gold_requirements(truths)
    pairs = match_one_to_one(materials.policy_text, gold, analysis.requirements)
    matched: dict[int, str] = {}
    for expected, found in pairs:
        matched[int(expected.id[len(TRUTH_PREFIX):])] = found.id
    return matched


def tokens_match(predicted: set[int], gold: set[int]) -> bool:
    """Accept a quote that overlaps the gold span enough or covers most of it."""
    evaluation = REVIEW_SETTINGS.evaluation
    if compute_overlap(predicted, gold) >= evaluation.iou_threshold:
        return True
    covered = len(predicted & gold) / len(gold) if gold else 0.0
    return covered >= evaluation.quote_coverage


def is_quote_correct(
    materials: CaseMaterials,
    truth: PairTruth,
    verdict: RequirementVerdict | None,
) -> bool:
    """Tell whether the cited design span matches the gold span."""
    if truth.verdict not in EVIDENCE_VERDICTS:
        return True
    if verdict is None or verdict.design_span is None:
        return False
    text = materials.design_text
    predicted = collect_token_indices(text, [verdict.design_span])
    return tokens_match(predicted, collect_token_indices(text, truth.design_spans))


def build_pair_outcome(
    materials: CaseMaterials,
    truth: PairTruth,
    verdict: RequirementVerdict | None,
) -> PairOutcome:
    """Compare the verdict given for one requirement with its gold verdict."""
    return PairOutcome(
        case_id=truth.case_id,
        rule_id=truth.rule_id,
        gold_verdict=truth.verdict,
        subtype=truth.subtype,
        predicted_verdict=verdict.verdict if verdict else MISSING,
        evidence_ok=is_quote_correct(materials, truth, verdict),
        gold_severity=truth.severity,
        predicted_severity=verdict.severity if verdict else "",
        confidence=verdict.confidence if verdict else None,
    )


def spans_match(materials: CaseMaterials, first: Span, others: list[Span]) -> bool:
    """Tell whether a span matches the union of other spans of the design."""
    one = collect_token_indices(materials.design_text, [first])
    return tokens_match(one, collect_token_indices(materials.design_text, others))


def count_hits(
    materials: CaseMaterials,
    spans: list[Span],
    others: list[Span],
) -> int:
    """Count the spans that match the other spans."""
    return sum(1 for span in spans if spans_match(materials, span, others))


def tally_quotes(
    materials: CaseMaterials,
    truths: list[PairTruth],
    verdicts: list[RequirementVerdict],
) -> QuoteTally:
    """Count violated quotes that hit a planted violation, whatever the requirement."""
    gold: list[Span] = []
    for truth in truths:
        if truth.verdict == VIOLATED:
            gold.append(truth.design_spans[0])
    predicted: list[Span] = []
    for verdict in verdicts:
        if verdict.verdict == VIOLATED and verdict.design_span is not None:
            predicted.append(verdict.design_span)
    return QuoteTally(
        predicted=len(predicted),
        predicted_hits=count_hits(materials, predicted, gold),
        gold=len(gold),
        gold_hits=count_hits(materials, gold, predicted),
    )


def index_verdicts(verdicts: list[RequirementVerdict]) -> dict[str, RequirementVerdict]:
    """Index the verdicts of a design by the id of their requirement."""
    by_id: dict[str, RequirementVerdict] = {}
    for verdict in verdicts:
        by_id[verdict.requirement_id] = verdict
    return by_id


def build_pairs(
    materials: CaseMaterials,
    truths: list[PairTruth],
    matched: dict[int, str],
    verdicts: list[RequirementVerdict],
) -> list[PairOutcome]:
    """Compare the verdicts with the gold verdicts of the pairs that are scored."""
    by_id = index_verdicts(verdicts)
    pairs: list[PairOutcome] = []
    for index, truth in enumerate(truths):
        if not truth.excluded:
            verdict = by_id.get(matched.get(index, ""))
            pairs.append(build_pair_outcome(materials, truth, verdict))
    return pairs


def score_case_verdicts(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    verdicts: list[RequirementVerdict],
) -> CaseVerdictOutcome:
    """Score the verdicts of one design against the gold verdicts of its policy."""
    truths = build_case_truth(materials)
    matched = match_truths(materials, analysis, truths)
    pairs = build_pairs(materials, truths, matched, verdicts)
    extra = len(analysis.requirements) - len(matched)
    quotes = tally_quotes(materials, truths, verdicts)
    return CaseVerdictOutcome(pairs=pairs, extra_requirements=extra, quotes=quotes)


def is_right_verdict(pair: PairOutcome) -> bool:
    """Tell whether the verdict equals the gold verdict, whatever the quote."""
    return pair.predicted_verdict == pair.gold_verdict


def is_correct(pair: PairOutcome) -> bool:
    """Tell whether the verdict is right and, where needed, so is the quote."""
    return is_right_verdict(pair) and pair.evidence_ok


def count_correct(pairs: list[PairOutcome]) -> int:
    """Count the pairs whose verdict and quote are both right."""
    return sum(1 for pair in pairs if is_correct(pair))


def build_verdict_report(pairs: list[PairOutcome]) -> ClassReport:
    """Build the confusion table and per-class scores of the four verdicts."""
    labels: list[tuple[str, str]] = []
    for pair in pairs:
        labels.append((pair.gold_verdict, pair.predicted_verdict))
    confusion = count_confusion(labels, CLASSES)
    per_class: dict[str, ClassScores] = {}
    for label in VERDICTS:
        per_class[label] = score_class(confusion, label)
    macro = divide(sum(scores.f1 for scores in per_class.values()), len(VERDICTS))
    correct = sum(confusion[label][label] for label in VERDICTS)
    return ClassReport(
        accuracy=divide(correct, len(pairs)),
        macro_f1=macro,
        per_class=per_class,
        confusion=confusion,
    )


def compute_evidence_rate(pairs: list[PairOutcome]) -> dict[str, float]:
    """Share of right verdicts that also quote the right place, per verdict."""
    rates: dict[str, float] = {}
    for verdict in EVIDENCE_VERDICTS:
        right: list[PairOutcome] = []
        for pair in pairs:
            if pair.gold_verdict == verdict and is_right_verdict(pair):
                right.append(pair)
        rates[verdict] = divide(count_correct(right), len(right))
    return rates


def compute_recall_by_subtype(pairs: list[PairOutcome]) -> dict[str, float]:
    """Recall of the gold verdict within every kind of gold situation."""
    groups: dict[str, list[PairOutcome]] = {}
    for pair in pairs:
        groups.setdefault(pair.subtype, []).append(pair)
    recalls: dict[str, float] = {}
    for subtype, group in groups.items():
        recalls[subtype] = divide(count_correct(group), len(group))
    return recalls


def compute_violated_precision(pairs: list[PairOutcome]) -> float:
    """Share of violated verdicts that are right and quote the right place."""
    given: list[PairOutcome] = []
    for pair in pairs:
        if pair.predicted_verdict == VIOLATED:
            given.append(pair)
    return divide(count_correct(given), len(given))


def build_severity_report(pairs: list[PairOutcome]) -> ClassReport | None:
    """Score the severity of the violated verdicts that are right."""
    labels = collect_severity_pairs(pairs)
    return build_class_report(labels, SEVERITIES) if labels else None


def build_severity_ordinal(pairs: list[PairOutcome]) -> OrdinalReport | None:
    """Measure how far the predicted severity is from the gold severity."""
    labels = collect_severity_pairs(pairs)
    return build_ordinal_report(labels, SEVERITIES) if labels else None


def quote_precision(outcomes: list[CaseVerdictOutcome]) -> float:
    """Share of violated quotes that hit a planted violation, any requirement."""
    hits = sum(case.quotes.predicted_hits for case in outcomes)
    return divide(hits, sum(case.quotes.predicted for case in outcomes))


def quote_recall(outcomes: list[CaseVerdictOutcome]) -> float:
    """Share of planted violations hit by some violated quote."""
    found = sum(case.quotes.gold_hits for case in outcomes)
    return divide(found, sum(case.quotes.gold for case in outcomes))


def is_reported(verdict: str) -> bool:
    """Tell whether a verdict is shown to the user, as opposed to dropped."""
    return verdict in (VIOLATED, UNCLEAR)


def gold_is_reported(pair: PairOutcome) -> bool:
    """Tell whether the gold verdict of a pair is shown to the user."""
    return is_reported(pair.gold_verdict)


def predicted_is_reported(pair: PairOutcome) -> bool:
    """Tell whether the predicted verdict of a pair is shown to the user."""
    return is_reported(pair.predicted_verdict)


def tolerant_credit(pair: PairOutcome) -> float:
    """Full credit for the right group, partial for violated versus unclear."""
    if gold_is_reported(pair) != predicted_is_reported(pair):
        return 0.0
    if not gold_is_reported(pair) or pair.gold_verdict == pair.predicted_verdict:
        return 1.0
    return REVIEW_SETTINGS.evaluation.tolerant_credit


def compute_report_scores(pairs: list[PairOutcome], documents: int) -> ReportScores:
    """Score the decision to show a verdict to the user, ignoring which of the two."""
    wanted: list[PairOutcome] = [pair for pair in pairs if gold_is_reported(pair)]
    dropped: list[PairOutcome] = [pair for pair in pairs if not gold_is_reported(pair)]
    shown: list[PairOutcome] = [pair for pair in pairs if predicted_is_reported(pair)]
    found = sum(1 for pair in wanted if predicted_is_reported(pair))
    right = sum(1 for pair in shown if gold_is_reported(pair))
    alarms = sum(1 for pair in dropped if predicted_is_reported(pair))
    recall, precision = divide(found, len(wanted)), divide(right, len(shown))
    credit = sum(tolerant_credit(pair) for pair in pairs)
    return ReportScores(
        recall=recall,
        precision=precision,
        f1=divide(2 * recall * precision, recall + precision),
        false_alarm_rate=divide(alarms, len(dropped)),
        false_alarms_per_document=divide(alarms, documents),
        tolerant_accuracy=divide(credit, len(pairs)),
    )


def summarize_verdicts(outcomes: list[CaseVerdictOutcome]) -> VerdictScores:
    """Combine the pair outcomes of several designs into the verdict scores."""
    pairs: list[PairOutcome] = []
    for case in outcomes:
        pairs.extend(case.pairs)
    right = sum(1 for pair in pairs if is_right_verdict(pair))
    return VerdictScores(
        pairs=len(pairs),
        missing_pairs=sum(1 for pair in pairs if pair.predicted_verdict == MISSING),
        extra_requirements=sum(case.extra_requirements for case in outcomes),
        accuracy=divide(right, len(pairs)),
        accuracy_with_evidence=divide(count_correct(pairs), len(pairs)),
        report=build_verdict_report(pairs),
        evidence_rate=compute_evidence_rate(pairs),
        recall_by_subtype=compute_recall_by_subtype(pairs),
        reportable=compute_report_scores(pairs, len(outcomes)),
        violated_precision_with_evidence=compute_violated_precision(pairs),
        violation_quote_precision=quote_precision(outcomes),
        violation_quote_recall=quote_recall(outcomes),
        severity_report=build_severity_report(pairs),
        severity_ordinal=build_severity_ordinal(pairs),
        confidence_auroc=compute_auroc(collect_confidence(pairs)),
    )


def clamp_severity(severity: str) -> str:
    """Treat a predicted severity outside the scale as the lowest level."""
    return severity if severity in SEVERITIES else SEVERITIES[0]


def collect_severity_pairs(pairs: list[PairOutcome]) -> list[tuple[str, str]]:
    """Pair gold and predicted severity of the right violated verdicts."""
    labels: list[tuple[str, str]] = []
    for pair in pairs:
        if pair.gold_verdict == VIOLATED and is_correct(pair):
            labels.append((pair.gold_severity, clamp_severity(pair.predicted_severity)))
    return labels


def win_value(first: float, second: float) -> float:
    """Score one comparison of a right and a wrong verdict: win, tie or loss."""
    if first == second:
        return TIE_VALUE
    return 1.0 if first > second else 0.0


def compute_auroc(observations: list[tuple[float, bool]]) -> float | None:
    """Probability that a right verdict has a higher confidence than a wrong one."""
    right: list[float] = [score for score, correct in observations if correct]
    wrong: list[float] = [score for score, correct in observations if not correct]
    if not right or not wrong:
        return None
    wins = sum(win_value(first, second) for first in right for second in wrong)
    return wins / (len(right) * len(wrong))


def collect_confidence(pairs: list[PairOutcome]) -> list[tuple[float, bool]]:
    """List confidence and correctness of every pair that has both."""
    observations: list[tuple[float, bool]] = []
    for pair in pairs:
        if pair.confidence is not None:
            observations.append((pair.confidence, is_correct(pair)))
    return observations
