"""One-to-one matching of reviewer findings to planted flaws by token overlap."""

from secreview.agents.baseline import GroundedFinding, ReviewRecord
from secreview.agents.case_materials import CaseMaterials
from secreview.datagen.labels import FlawLabel
from secreview.evaluation.evidence import (
    expected_action,
    is_evidence_correct,
    is_in_scope,
)
from secreview.evaluation.outcomes import CaseOutcome, GoldOutcome, PredictionOutcome
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.review_settings import REVIEW_SETTINGS


def gold_tokens(materials: CaseMaterials, flaw: FlawLabel) -> set[int]:
    """Collect the design tokens of the gold evidence of an in-scope flaw."""
    if not is_in_scope(flaw):
        return set()
    spans: list[tuple[int, int]] = [(start, end) for start, end in flaw.design_spans]
    return collect_token_indices(materials.design_text, spans)


def collect_finding_tokens(
    materials: CaseMaterials,
    grounded: GroundedFinding,
) -> set[int]:
    """Collect the design tokens covered by the quote of a finding."""
    spans: list[tuple[int, int]] = []
    if grounded.design_span:
        spans.append(grounded.design_span)
    return collect_token_indices(materials.design_text, spans)


def rank_candidate_pairs(
    materials: CaseMaterials,
    findings: list[GroundedFinding],
) -> list[tuple[float, int, int]]:
    """List finding-flaw pairs above the overlap threshold, best overlap first."""
    pairs: list[tuple[float, int, int]] = []
    threshold = REVIEW_SETTINGS.evaluation.iou_threshold
    flaw_tokens: list[set[int]] = [
        gold_tokens(materials, flaw) for flaw in materials.labels.flaws
    ]
    for finding_index, grounded in enumerate(findings):
        predicted = collect_finding_tokens(materials, grounded)
        for flaw_index, tokens in enumerate(flaw_tokens):
            overlap = compute_overlap(predicted, tokens)
            if overlap >= threshold:
                pairs.append((overlap, finding_index, flaw_index))
    return sorted(pairs, reverse=True)


def assign_pairs(pairs: list[tuple[float, int, int]]) -> dict[int, int]:
    """Greedily pick one flaw per finding and one finding per flaw."""
    flaw_by_finding: dict[int, int] = {}
    used_flaws: set[int] = set()
    for _, finding_index, flaw_index in pairs:
        if finding_index in flaw_by_finding or flaw_index in used_flaws:
            continue
        flaw_by_finding[finding_index] = flaw_index
        used_flaws.add(flaw_index)
    return flaw_by_finding


def build_gold_outcome(
    materials: CaseMaterials,
    flaw: FlawLabel,
    grounded: GroundedFinding | None,
) -> GoldOutcome:
    """Compare one planted flaw with the finding matched to it, if any."""
    reported = grounded
    correct = bool(grounded and is_evidence_correct(materials, flaw, grounded))
    return GoldOutcome(
        case_id=materials.case_id,
        flaw_id=flaw.flaw_id,
        flaw_type=flaw.type,
        severity=flaw.severity,
        policy_status=flaw.policy_status,
        expected_action=expected_action(flaw),
        scorable=is_in_scope(flaw),
        matched=reported is not None,
        evidence_correct=correct,
        confidence=reported.confidence if reported else 0,
        predicted_type=reported.finding_type if reported else "",
        predicted_action=reported.action if reported else "",
        predicted_severity=reported.severity if reported else "",
    )


def build_gold_outcomes(
    materials: CaseMaterials,
    findings: list[GroundedFinding],
    flaw_by_finding: dict[int, int],
) -> list[GoldOutcome]:
    """Build the per-flaw outcomes of a case from the chosen assignment."""
    finding_by_flaw: dict[int, int] = {}
    for finding_index, flaw_index in flaw_by_finding.items():
        finding_by_flaw[flaw_index] = finding_index
    outcomes: list[GoldOutcome] = []
    for index, flaw in enumerate(materials.labels.flaws):
        finding_index = finding_by_flaw.get(index)
        finding = findings[finding_index] if finding_index is not None else None
        outcomes.append(build_gold_outcome(materials, flaw, finding))
    return outcomes


def build_prediction_outcomes(
    materials: CaseMaterials,
    findings: list[GroundedFinding],
    flaw_by_finding: dict[int, int],
) -> list[PredictionOutcome]:
    """Build the per-finding outcomes of a case from the chosen assignment."""
    flaws = materials.labels.flaws
    outcomes: list[PredictionOutcome] = []
    for index, grounded in enumerate(findings):
        flaw_index = flaw_by_finding.get(index)
        flaw = flaws[flaw_index] if flaw_index is not None else None
        strict = bool(flaw and is_evidence_correct(materials, flaw, grounded))
        outcomes.append(
            PredictionOutcome(
                case_id=materials.case_id,
                confidence=grounded.confidence,
                matched_flaw_id=flaw.flaw_id if flaw else None,
                strict_matched=strict,
            )
        )
    return outcomes


def match_case(materials: CaseMaterials, record: ReviewRecord) -> CaseOutcome:
    """Match the findings of one review record against the planted flaws."""
    pairs = rank_candidate_pairs(materials, record.findings)
    flaw_by_finding = assign_pairs(pairs)
    findings = record.findings
    return CaseOutcome(
        case_id=materials.case_id,
        golds=build_gold_outcomes(materials, findings, flaw_by_finding),
        predictions=build_prediction_outcomes(materials, findings, flaw_by_finding),
        parse_failed=record.parse_error is not None,
        recovered=record.recovered,
        rejected_hallucinations=record.rejected_hallucinations,
    )
