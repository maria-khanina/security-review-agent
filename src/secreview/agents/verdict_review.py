"""One verdict per policy requirement, given the design fragments retrieved for it."""

from typing import Protocol

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.agents.verdict_contexts import (
    Bounds,
    extract_overview,
    guarantee_gold,
    list_fragments,
    union_units,
)
from secreview.agents.verdict_prompts import (
    build_verdict_system_prompt,
    build_verdict_user_prompt,
)
from secreview.agents.verdict_reply import (
    VerdictReply,
    build_verdict_schema,
    compute_confidence,
    compute_distribution,
    parse_verdict_reply,
)
from secreview.agents.verdicts import RequirementVerdict
from secreview.evaluation.verdict_scores import match_truths
from secreview.evaluation.verdict_truth import PairTruth, build_case_truth
from secreview.llm.client import LogprobCompletion
from secreview.parsing.findings import ReplyParseError
from secreview.parsing.grounding import locate_quote
from secreview.parsing.vocabulary import EVIDENCE_VERDICTS, VIOLATED
from secreview.retrieval.requirement_rankings import CaseRankings, name_ranking
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

Span = tuple[int, int]


class LogprobClient(Protocol):
    def complete_with_logprobs(
        self,
        system_prompt: str,
        user_prompt: str,
        response_schema: dict[str, object],
        top_logprobs: int,
    ) -> LogprobCompletion: ...


class ContextChoice(BaseModel):
    method: str
    window: int
    candidates: int
    oracle: bool
    strict: bool
    overview_chars: int


class RequirementRecord(BaseModel):
    requirement_id: str
    verdict: str | None
    quote: str
    design_span: Span | None
    reason: str
    severity: str
    confidence: float | None
    probabilities: dict[str, float] = {}
    context_units: list[int]
    raw_reply: str


class VerdictCaseRecord(BaseModel):
    case_id: str
    records: list[RequirementRecord]


def build_verdict_call(
    client: LogprobClient,
    requirement: str,
    fragments: list[str],
    overview: str,
    choice: ContextChoice,
) -> LogprobCompletion:
    """Ask the model for the verdict on one requirement and the given fragments."""
    return client.complete_with_logprobs(
        build_verdict_system_prompt(choice.strict, bool(overview)),
        build_verdict_user_prompt(requirement, fragments, overview),
        build_verdict_schema(),
        REVIEW_SETTINGS.verdict.top_logprobs,
    )


def ground_quote(materials: CaseMaterials, reply: VerdictReply) -> Span | None:
    """Locate the quote of an evidence verdict in the design text."""
    if reply.verdict not in EVIDENCE_VERDICTS:
        return None
    minimum = REVIEW_SETTINGS.grounding.min_quote_characters
    return locate_quote(materials.design_text, reply.quote, minimum)


def build_record(
    materials: CaseMaterials,
    requirement_id: str,
    indices: list[int],
    completion: LogprobCompletion,
) -> RequirementRecord:
    """Turn the reply of the model into the record of one requirement."""
    try:
        reply = parse_verdict_reply(completion.text)
    except ReplyParseError:
        return RequirementRecord(
            requirement_id=requirement_id,
            verdict=None,
            quote="",
            design_span=None,
            reason="",
            severity=REVIEW_SETTINGS.verdict.no_severity,
            confidence=None,
            probabilities={},
            context_units=indices,
            raw_reply=completion.text,
        )
    return RequirementRecord(
        requirement_id=requirement_id,
        verdict=reply.verdict,
        quote=reply.quote,
        design_span=ground_quote(materials, reply),
        reason=reply.reason,
        severity=reply.severity,
        confidence=compute_confidence(completion.tokens, reply.verdict),
        probabilities=compute_distribution(completion.tokens),
        context_units=indices,
        raw_reply=completion.text,
    )


def find_gold_spans(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
) -> dict[str, list[Span]]:
    """Map each requirement id to the gold design spans of its evidence verdict."""
    truths: list[PairTruth] = build_case_truth(materials)
    matched = match_truths(materials, analysis, truths)
    spans: dict[str, list[Span]] = {}
    for index, requirement_id in matched.items():
        if truths[index].verdict in EVIDENCE_VERDICTS:
            spans[requirement_id] = truths[index].design_spans
    return spans


def choose_bounds(
    requirement: PolicyRequirement,
    rankings: CaseRankings,
    choice: ContextChoice,
    gold: dict[str, list[Span]],
    units: list[DesignUnit],
) -> Bounds:
    """Pick the chunks shown for a requirement, with the gold one when asked."""
    name = name_ranking(choice.method, choice.window)
    ranked: Bounds = [(first, last) for first, last in rankings[requirement.id][name]]
    if choice.oracle and requirement.id in gold:
        return guarantee_gold(ranked, choice.candidates, units, gold[requirement.id])
    return ranked[: choice.candidates]


def review_requirement(
    client: LogprobClient,
    materials: CaseMaterials,
    units: list[DesignUnit],
    requirement: PolicyRequirement,
    indices: list[int],
    overview: str,
    choice: ContextChoice,
) -> RequirementRecord:
    """Give the verdict on one requirement from the fragments with these units."""
    fragments = list_fragments(units, indices)
    completion = build_verdict_call(
        client, requirement.quote, fragments, overview, choice
    )
    return build_record(materials, requirement.id, indices, completion)


def review_case_verdicts(
    client: LogprobClient,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    rankings: CaseRankings,
    choice: ContextChoice,
) -> VerdictCaseRecord:
    """Give a verdict on every requirement of the policy for one design."""
    units = split_units(materials.design_text)
    gold = find_gold_spans(materials, analysis) if choice.oracle else {}
    overview = extract_overview(materials.design_text, choice.overview_chars)
    records: list[RequirementRecord] = []
    for requirement in analysis.requirements:
        bounds = choose_bounds(requirement, rankings, choice, gold, units)
        indices = union_units(bounds, len(bounds))
        records.append(
            review_requirement(
                client, materials, units, requirement, indices, overview, choice
            )
        )
    return VerdictCaseRecord(case_id=materials.case_id, records=records)


def normalized_severity(item: RequirementRecord) -> str:
    """Keep the severity only for the violated verdicts, as the prompt asks."""
    if item.verdict == VIOLATED:
        return item.severity
    return REVIEW_SETTINGS.verdict.no_severity


def to_requirement_verdicts(record: VerdictCaseRecord) -> list[RequirementVerdict]:
    """Convert the records with a valid reply into scorable verdicts."""
    verdicts: list[RequirementVerdict] = []
    for item in record.records:
        if item.verdict is not None:
            verdicts.append(
                RequirementVerdict.model_validate(
                    {
                        "requirement_id": item.requirement_id,
                        "verdict": item.verdict,
                        "design_span": item.design_span,
                        "severity": normalized_severity(item),
                        "confidence": item.confidence,
                    }
                )
            )
    return verdicts
