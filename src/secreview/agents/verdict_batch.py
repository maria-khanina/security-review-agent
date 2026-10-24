"""One model call for a group of requirements of the same topic."""

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.agents.prompts import SEVERITY_SCALE
from secreview.agents.verdict_contexts import (
    Bounds,
    extract_overview,
    list_fragments,
    union_units,
)
from secreview.agents.verdict_prompts import (
    INTRODUCTION,
    OVERVIEW_SENTENCE,
    VERDICTS_TEXT,
    build_overview_block,
)
from secreview.agents.verdict_reply import VerdictReply, VerdictSeverity
from secreview.agents.verdict_review import (
    ContextChoice,
    LogprobClient,
    RequirementRecord,
    VerdictCaseRecord,
    ground_quote,
)
from secreview.llm.client import LogprobCompletion
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.parsing.vocabulary import Verdict
from secreview.retrieval.requirement_rankings import CaseRankings, name_ranking
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

NO_TOPIC = ""
BATCH_RULES = """Rules:
1. Judge each requirement on its own. The fragments are shown once for the \
whole group; a requirement is settled only by a fragment that really concerns it.
2. quote is copied character for character from one fragment, one or two \
consecutive sentences: the sentence that decides compliant or violated. Use an \
empty string for unclear and not_applicable.
3. reason is at most 25 words: what the fragments say or leave out.
4. severity is judged for violated only; use none for every other verdict.
5. Use only the fragments and the requirements. Do not invent facts."""
BATCH_SHAPE = """Answer with one JSON object only, {"items": [...]}, with one \
item for every requirement, in the order of the requirements. Each item has \
these fields in this order: {"requirement": 1, "quote": "...", "reason": "...", \
"verdict": "compliant|violated|unclear|not_applicable", "severity": \
"none|low|medium|high|critical"}."""


class BatchItem(BaseModel):
    requirement: int
    quote: str
    reason: str
    verdict: Verdict
    severity: VerdictSeverity


class BatchReply(BaseModel):
    items: list[BatchItem]


def build_batch_system_prompt(with_overview: bool) -> str:
    """Return the system prompt of a call that judges a group of requirements."""
    introduction = INTRODUCTION + (OVERVIEW_SENTENCE if with_overview else "")
    parts: list[str] = [
        introduction,
        VERDICTS_TEXT,
        SEVERITY_SCALE,
        BATCH_RULES,
        BATCH_SHAPE,
    ]
    return "\n\n".join(parts)


def build_batch_schema(size: int) -> dict[str, object]:
    """Return the JSON schema of a reply with exactly one item per requirement."""
    schema: dict[str, object] = BatchReply.model_json_schema()
    properties = schema["properties"]
    if isinstance(properties, dict):
        properties["items"]["minItems"] = size
        properties["items"]["maxItems"] = size
    return schema


def primary_topic(requirement: PolicyRequirement) -> str:
    """Return the first topic of a requirement, or an empty string."""
    return requirement.topics[0] if requirement.topics else NO_TOPIC


def make_groups(
    requirements: list[PolicyRequirement],
    size: int,
) -> list[list[PolicyRequirement]]:
    """Order the requirements by their first topic and cut them into groups."""
    ordered = sorted(requirements, key=primary_topic)
    starts = range(0, len(ordered), size)
    return [ordered[start:][:size] for start in starts]


def number_lines(texts: list[str]) -> str:
    """Put a number in square brackets before every text, one per line."""
    return "\n".join(f"[{number}] {text}" for number, text in enumerate(texts, 1))


def build_batch_user_prompt(
    group: list[PolicyRequirement],
    fragments: list[str],
    overview: str,
) -> str:
    """Wrap the numbered requirements and the numbered fragments into one message."""
    requirements = number_lines([item.quote for item in group])
    return (
        f"{build_overview_block(overview)}"
        f"<requirements>\n{requirements}\n</requirements>\n\n"
        f"<design_fragments>\n{number_lines(fragments)}\n</design_fragments>\n\n"
        "Give the verdicts now and answer with the JSON object."
    )


def group_indices(
    group: list[PolicyRequirement],
    rankings: CaseRankings,
    choice: ContextChoice,
) -> list[int]:
    """List, in document order, the units shown for any requirement of the group."""
    name = name_ranking(choice.method, choice.window)
    bounds: Bounds = []
    for item in group:
        ranked = rankings[item.id][name][: choice.candidates]
        bounds.extend((first, last) for first, last in ranked)
    return union_units(bounds, len(bounds))


def failed_record(requirement_id: str, indices: list[int]) -> RequirementRecord:
    """Describe a requirement whose group reply could not be read."""
    return RequirementRecord(
        requirement_id=requirement_id,
        verdict=None,
        quote="",
        design_span=None,
        reason="",
        severity=REVIEW_SETTINGS.verdict.no_severity,
        confidence=None,
        context_units=indices,
        raw_reply="",
        calls=0,
    )


def parse_batch_reply(text: str, size: int) -> list[BatchItem] | None:
    """Parse a group reply, or return nothing when it is malformed."""
    try:
        reply = BatchReply.model_validate_json(extract_json_object(text))
    except (ValueError, ReplyParseError):
        return None
    return reply.items if len(reply.items) == size else None


def item_record(
    materials: CaseMaterials,
    requirement_id: str,
    item: BatchItem,
    indices: list[int],
) -> RequirementRecord:
    """Turn one item of a group reply into the record of its requirement."""
    reply = VerdictReply(
        quote=item.quote,
        reason=item.reason,
        verdict=item.verdict,
        severity=item.severity,
    )
    return RequirementRecord(
        requirement_id=requirement_id,
        verdict=item.verdict,
        quote=item.quote,
        design_span=ground_quote(materials, reply),
        reason=item.reason,
        severity=item.severity,
        confidence=None,
        context_units=indices,
        raw_reply="",
        calls=0,
    )


def assign_cost(
    records: list[RequirementRecord],
    completion: LogprobCompletion,
) -> list[RequirementRecord]:
    """Charge the cost of the call to the first record of the group."""
    first = records[0].model_copy(
        update={
            "calls": 1,
            "raw_reply": completion.text,
            "prompt_tokens": completion.prompt_tokens,
            "completion_tokens": completion.completion_tokens,
            "seconds": completion.seconds,
        }
    )
    return [first, *records[1:]]


def review_group(
    client: LogprobClient,
    materials: CaseMaterials,
    units: list[DesignUnit],
    group: list[PolicyRequirement],
    overview: str,
    indices: list[int],
) -> list[RequirementRecord]:
    """Ask for the verdicts on a group of requirements in one call."""
    completion = client.complete_with_logprobs(
        build_batch_system_prompt(bool(overview)),
        build_batch_user_prompt(group, list_fragments(units, indices), overview),
        build_batch_schema(len(group)),
        REVIEW_SETTINGS.verdict.top_logprobs,
    )
    items = parse_batch_reply(completion.text, len(group))
    if items is None:
        failed: list[RequirementRecord] = [
            failed_record(item.id, indices) for item in group
        ]
        return assign_cost(failed, completion)
    pairs = zip(group, items, strict=True)
    records: list[RequirementRecord] = [
        item_record(materials, one.id, two, indices) for one, two in pairs
    ]
    return assign_cost(records, completion)


def review_case_batched(
    client: LogprobClient,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    rankings: CaseRankings,
    choice: ContextChoice,
    size: int,
) -> VerdictCaseRecord:
    """Give a verdict on every requirement, size requirements per model call."""
    units = split_units(materials.design_text)
    overview = extract_overview(materials.design_text, choice.overview_chars)
    records: list[RequirementRecord] = []
    for group in make_groups(analysis.requirements, size):
        indices = group_indices(group, rankings, choice)
        records.extend(review_group(client, materials, units, group, overview, indices))
    return VerdictCaseRecord(case_id=materials.case_id, records=records)
