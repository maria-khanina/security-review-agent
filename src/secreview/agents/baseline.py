"""Baseline reviewer: one call per design, numbered policy, grounded quotes."""

from pydantic import BaseModel

from secreview.agents.actions import derive_action
from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import (
    PolicyAnalysis,
    find_requirement,
    list_requirement_ids,
    render_tagged_policy,
)
from secreview.agents.prompts import build_system_prompt, build_user_prompt
from secreview.llm.client import ChatClient
from secreview.parsing.findings import (
    COMPLIANT,
    Finding,
    ReplyParseError,
    TopicFinding,
    build_reply_schema,
    parse_reply,
)
from secreview.parsing.grounding import locate_quote
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.review_settings import REVIEW_SETTINGS


class ReviewVariant(BaseModel):
    use_topics: bool
    ask_for_silence: bool
    policy_analysis: str
    allow_compliant: bool = False


class GroundedFinding(BaseModel):
    design_quote: str
    topics: list[str]
    observation: str
    requirement_id: str
    finding_type: str
    severity: str
    confidence: int
    action: str
    wording: str
    design_span: tuple[int, int]
    policy_span: tuple[int, int]


class RejectedFinding(BaseModel):
    design_quote: str
    requirement_id: str
    finding_type: str
    reason: str


class ReviewRecord(BaseModel):
    case_id: str
    raw_reply: str
    parse_error: str | None
    recovered: bool
    findings: list[GroundedFinding]
    rejected_hallucinations: int
    rejected_findings: list[RejectedFinding]
    compliant_findings: int = 0


def reject(finding: Finding | TopicFinding, reason: str) -> RejectedFinding:
    """Describe a finding that could not be grounded and why."""
    return RejectedFinding(
        design_quote=finding.design_quote,
        requirement_id=finding.requirement_id,
        finding_type=finding.finding_type,
        reason=reason,
    )


def ground_finding(
    finding: Finding | TopicFinding,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
) -> GroundedFinding | RejectedFinding:
    """Check the requirement id and the design quote of a finding."""
    requirement = find_requirement(analysis, finding.requirement_id)
    if requirement is None:
        return reject(finding, REVIEW_SETTINGS.unknown_requirement_reason)
    minimum = REVIEW_SETTINGS.grounding.min_quote_characters
    design_span = locate_quote(materials.design_text, finding.design_quote, minimum)
    if design_span is None:
        return reject(finding, REVIEW_SETTINGS.rejection_reason)
    topics = finding.topics if isinstance(finding, TopicFinding) else []
    return GroundedFinding(
        design_quote=finding.design_quote,
        topics=list(topics),
        observation=finding.observation,
        requirement_id=finding.requirement_id,
        finding_type=finding.finding_type,
        severity=finding.severity,
        confidence=finding.confidence,
        action=derive_action(finding.finding_type, requirement.wording),
        wording=requirement.wording,
        design_span=design_span,
        policy_span=requirement.span,
    )


def is_duplicate(
    finding: GroundedFinding,
    kept: list[GroundedFinding],
    design_text: str,
) -> bool:
    """Tell whether a kept finding cites this requirement at an overlapping place."""
    tokens = collect_token_indices(design_text, [finding.design_span])
    threshold = REVIEW_SETTINGS.grounding.duplicate_overlap
    for other in kept:
        if other.requirement_id != finding.requirement_id:
            continue
        other_tokens = collect_token_indices(design_text, [other.design_span])
        if compute_overlap(tokens, other_tokens) >= threshold:
            return True
    return False


def deduplicate(
    findings: list[GroundedFinding],
    design_text: str,
) -> list[GroundedFinding]:
    """Keep the first of the findings that cite one requirement at one place."""
    unique: list[GroundedFinding] = []
    for finding in findings:
        if not is_duplicate(finding, unique, design_text):
            unique.append(finding)
    return unique


def build_record(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    raw_reply: str,
    findings: list[Finding | TopicFinding],
) -> ReviewRecord:
    """Ground every finding and split off those that cannot be verified."""
    kept: list[GroundedFinding] = []
    rejected: list[RejectedFinding] = []
    for finding in findings:
        grounded = ground_finding(finding, materials, analysis)
        if isinstance(grounded, RejectedFinding):
            rejected.append(grounded)
        else:
            kept.append(grounded)
    return ReviewRecord(
        case_id=materials.case_id,
        raw_reply=raw_reply,
        parse_error=None,
        recovered=False,
        findings=deduplicate(kept, materials.design_text),
        rejected_hallucinations=len(rejected),
        rejected_findings=rejected,
    )


def build_failed_record(case_id: str, raw_reply: str, error: str) -> ReviewRecord:
    """Describe a reply from which no finding could be recovered."""
    return ReviewRecord(
        case_id=case_id,
        raw_reply=raw_reply,
        parse_error=error,
        recovered=False,
        findings=[],
        rejected_hallucinations=0,
        rejected_findings=[],
    )


def ask_model(
    client: ChatClient,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    variant: ReviewVariant,
) -> str:
    """Send the numbered policy and the design to the model, return its reply."""
    system_prompt = build_system_prompt(
        variant.use_topics,
        variant.ask_for_silence,
        variant.allow_compliant,
    )
    tagged_policy = render_tagged_policy(materials.policy_text, analysis)
    user_prompt = build_user_prompt(tagged_policy, materials.design_text)
    ids = list_requirement_ids(analysis)
    schema = build_reply_schema(variant.use_topics, ids, variant.allow_compliant)
    return client.complete(system_prompt, user_prompt, schema)


def review_case(
    client: ChatClient,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    variant: ReviewVariant,
) -> ReviewRecord:
    """Run the baseline reviewer on one case and return the grounded result."""
    raw_reply = ask_model(client, materials, analysis, variant)
    try:
        parsed = parse_reply(raw_reply, variant.use_topics)
    except ReplyParseError as error:
        return build_failed_record(materials.case_id, raw_reply, str(error))
    problems: list[Finding | TopicFinding] = []
    for item in parsed.findings:
        if item.finding_type != COMPLIANT:
            problems.append(item)
    record = build_record(materials, analysis, raw_reply, problems)
    return record.model_copy(
        update={
            "recovered": parsed.recovered,
            "compliant_findings": len(parsed.findings) - len(problems),
        }
    )
