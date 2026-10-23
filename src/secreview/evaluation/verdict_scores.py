"""Scores of requirement verdicts against the gold verdicts of a design."""

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.agents.verdicts import RequirementVerdict
from secreview.evaluation.class_report import (
    ClassReport,
    ClassScores,
    count_confusion,
    divide,
    score_class,
)
from secreview.evaluation.policy_scores import match_one_to_one
from secreview.evaluation.verdict_truth import (
    PLANTED_AMBIGUITY,
    PairTruth,
    build_case_truth,
)
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.parsing.vocabulary import (
    EVIDENCE_VERDICTS,
    VERDICTS,
    VIOLATED,
)
from secreview.review_settings import REVIEW_SETTINGS

MISSING = "missing"
CLASSES: tuple[str, ...] = VERDICTS + (MISSING,)
TRUTH_PREFIX = "T"


class PairOutcome(BaseModel):
    case_id: str
    rule_id: str
    gold_verdict: str
    subtype: str
    predicted_verdict: str
    evidence_ok: bool


class CaseVerdictOutcome(BaseModel):
    pairs: list[PairOutcome]
    extra_requirements: int


class VerdictScores(BaseModel):
    pairs: int
    missing_pairs: int
    extra_requirements: int
    accuracy: float
    accuracy_with_evidence: float
    report: ClassReport
    evidence_rate: dict[str, float]
    recall_by_subtype: dict[str, float]
    defect_recall: float
    violated_precision_with_evidence: float


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


def is_quote_correct(
    materials: CaseMaterials,
    truth: PairTruth,
    verdict: RequirementVerdict | None,
) -> bool:
    """Tell whether the cited design span overlaps the gold span enough."""
    if truth.verdict not in EVIDENCE_VERDICTS:
        return True
    if verdict is None or verdict.design_span is None:
        return False
    text = materials.design_text
    predicted = collect_token_indices(text, [verdict.design_span])
    gold = collect_token_indices(text, truth.design_spans)
    threshold = REVIEW_SETTINGS.evaluation.iou_threshold
    return compute_overlap(predicted, gold) >= threshold


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
    )


def index_verdicts(verdicts: list[RequirementVerdict]) -> dict[str, RequirementVerdict]:
    """Index the verdicts of a design by the id of their requirement."""
    by_id: dict[str, RequirementVerdict] = {}
    for verdict in verdicts:
        by_id[verdict.requirement_id] = verdict
    return by_id


def score_case_verdicts(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    verdicts: list[RequirementVerdict],
) -> CaseVerdictOutcome:
    """Score the verdicts of one design against the gold verdicts of its policy."""
    truths = build_case_truth(materials)
    matched = match_truths(materials, analysis, truths)
    by_id = index_verdicts(verdicts)
    pairs: list[PairOutcome] = []
    for index, truth in enumerate(truths):
        verdict = by_id.get(matched.get(index, ""))
        pairs.append(build_pair_outcome(materials, truth, verdict))
    extra = len(analysis.requirements) - len(matched)
    return CaseVerdictOutcome(pairs=pairs, extra_requirements=extra)


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


def is_defect(pair: PairOutcome) -> bool:
    """Tell whether the gold of a pair is a planted violation or ambiguity."""
    return pair.gold_verdict == VIOLATED or pair.subtype == PLANTED_AMBIGUITY


def compute_defect_recall(pairs: list[PairOutcome]) -> float:
    """Recall over the planted violations and ambiguities of the designs."""
    defects: list[PairOutcome] = [pair for pair in pairs if is_defect(pair)]
    return divide(count_correct(defects), len(defects))


def compute_violated_precision(pairs: list[PairOutcome]) -> float:
    """Share of violated verdicts that are right and quote the right place."""
    given: list[PairOutcome] = []
    for pair in pairs:
        if pair.predicted_verdict == VIOLATED:
            given.append(pair)
    return divide(count_correct(given), len(given))


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
        defect_recall=compute_defect_recall(pairs),
        violated_precision_with_evidence=compute_violated_precision(pairs),
    )
