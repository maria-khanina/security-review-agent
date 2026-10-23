"""Follow-up calls on stored verdicts: a separate severity and a stated confidence."""

from pydantic import BaseModel, Field

from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import PolicyAnalysis
from secreview.agents.prompts import CONFIDENCE_SCALE, SEVERITY_SCALE
from secreview.agents.verdict_contexts import list_fragments
from secreview.agents.verdict_reply import VerdictSeverity
from secreview.agents.verdict_review import (
    LogprobClient,
    RequirementRecord,
    VerdictCaseRecord,
)
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.parsing.vocabulary import VIOLATED
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

SEVERITY_SYSTEM = (
    "You rate the severity of one confirmed violation of a security policy "
    "requirement by a software design, judged for this service.\n\n"
    + SEVERITY_SCALE
    + '\n\nAnswer with one JSON object {"severity": "low|medium|high|critical"} '
    "and nothing else."
)
CONFIDENCE_SYSTEM = (
    "You review the verdict of a security design review on one policy "
    "requirement. You get the requirement, the design fragments shown to the "
    "reviewer, the verdict and the quote. State how confident you are that the "
    "verdict is right.\n\n"
    + CONFIDENCE_SCALE
    + '\n\nAnswer with one JSON object {"confidence": <integer 1-100>} '
    "and nothing else."
)


class SeverityReply(BaseModel):
    severity: VerdictSeverity


class StatedConfidence(BaseModel):
    confidence: int = Field(
        ge=REVIEW_SETTINGS.confidence_minimum,
        le=REVIEW_SETTINGS.confidence_maximum,
    )


def build_followup_user_prompt(
    requirement: str,
    fragments: list[str],
    record: RequirementRecord,
) -> str:
    """Describe the requirement, the fragments, the verdict and its quote."""
    numbered = enumerate(fragments, 1)
    lines: list[str] = [f"[{number}] {text}" for number, text in numbered]
    joined = "\n".join(lines)
    return (
        f"<requirement>\n{requirement}\n</requirement>\n\n"
        f"<design_fragments>\n{joined}\n</design_fragments>\n\n"
        f"Verdict: {record.verdict}\nQuote: {record.quote}"
    )


def ask_followup(
    client: LogprobClient,
    system: str,
    user: str,
    schema: dict[str, object],
) -> str | None:
    """Send one follow-up call and return the reply text, or None on failure."""
    top = REVIEW_SETTINGS.verdict.top_logprobs
    completion = client.complete_with_logprobs(system, user, schema, top)
    try:
        return extract_json_object(completion.text)
    except ReplyParseError:
        return None


def rate_severity(
    client: LogprobClient,
    requirement: str,
    fragments: list[str],
    record: RequirementRecord,
) -> str:
    """Ask for the severity of one violated verdict; keep the old one on failure."""
    schema: dict[str, object] = SeverityReply.model_json_schema()
    user = build_followup_user_prompt(requirement, fragments, record)
    text = ask_followup(client, SEVERITY_SYSTEM, user, schema)
    if text is None:
        return record.severity
    try:
        return SeverityReply.model_validate_json(text).severity
    except ValueError:
        return record.severity


def state_confidence(
    client: LogprobClient,
    requirement: str,
    fragments: list[str],
    record: RequirementRecord,
) -> float | None:
    """Ask the model to state its confidence in a verdict as a share of one."""
    schema: dict[str, object] = StatedConfidence.model_json_schema()
    user = build_followup_user_prompt(requirement, fragments, record)
    text = ask_followup(client, CONFIDENCE_SYSTEM, user, schema)
    if text is None:
        return None
    try:
        stated = StatedConfidence.model_validate_json(text).confidence
        return stated / REVIEW_SETTINGS.confidence_maximum
    except ValueError:
        return None


def followup_item(
    client: LogprobClient,
    units: list[DesignUnit],
    requirement: str,
    item: RequirementRecord,
    mode: str,
) -> RequirementRecord:
    """Apply the severity or the stated-confidence follow-up to one record."""
    if item.verdict is None:
        return item
    fragments = list_fragments(units, item.context_units)
    if mode == "severity":
        if item.verdict != VIOLATED:
            return item
        severity = rate_severity(client, requirement, fragments, item)
        return item.model_copy(update={"severity": severity})
    stated = state_confidence(client, requirement, fragments, item)
    return item.model_copy(update={"confidence": stated})


def followup_case(
    client: LogprobClient,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    record: VerdictCaseRecord,
    mode: str,
) -> VerdictCaseRecord:
    """Apply a follow-up call to every record of a case."""
    units = split_units(materials.design_text)
    texts: dict[str, str] = {item.id: item.quote for item in analysis.requirements}
    records: list[RequirementRecord] = []
    for item in record.records:
        text = texts[item.requirement_id]
        records.append(followup_item(client, units, text, item, mode))
    return VerdictCaseRecord(case_id=record.case_id, records=records)
