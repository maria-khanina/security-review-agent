"""Strict parsing of a reviewer model reply into typed findings."""

import json
from typing import Literal, cast
from typing import get_args as list_literal_values

from pydantic import BaseModel, Field, ValidationError

from secreview.parsing.vocabulary import Topic
from secreview.review_settings import REVIEW_SETTINGS

SEPARATORS = ", \n\t\r"
FINDINGS_KEY = '"findings"'


class ReplyParseError(ValueError):
    """Raised when a model reply cannot be turned into valid findings."""


FindingType = Literal["violation", "ambiguity"]
ReplyFindingType = Literal["violation", "ambiguity", "compliant"]
COMPLIANT = "compliant"
Severity = Literal["low", "medium", "high", "critical"]
FINDING_TYPES: tuple[str, ...] = list_literal_values(FindingType)
SEVERITIES: tuple[str, ...] = list_literal_values(Severity)
ACTIONS: tuple[str, ...] = (
    REVIEW_SETTINGS.evaluation.fix_action,
    REVIEW_SETTINGS.evaluation.clarify_action,
    REVIEW_SETTINGS.evaluation.review_action,
)


class Finding(BaseModel):
    design_quote: str
    observation: str
    requirement_id: str
    finding_type: ReplyFindingType
    severity: Severity
    confidence: int = Field(
        ge=REVIEW_SETTINGS.confidence_minimum,
        le=REVIEW_SETTINGS.confidence_maximum,
    )


class TopicFinding(BaseModel):
    design_quote: str
    topics: list[Topic]
    observation: str
    requirement_id: str
    finding_type: ReplyFindingType
    severity: Severity
    confidence: int = Field(
        ge=REVIEW_SETTINGS.confidence_minimum,
        le=REVIEW_SETTINGS.confidence_maximum,
    )


class FindingsReply(BaseModel):
    findings: list[Finding]


class TopicFindingsReply(BaseModel):
    findings: list[TopicFinding]


class ParsedReply(BaseModel):
    findings: list[Finding | TopicFinding]
    recovered: bool


def strip_reasoning(reply: str) -> str:
    """Drop a leading reasoning block that ends with the closing think tag."""
    closing_tag = REVIEW_SETTINGS.think_close_tag
    if closing_tag in reply:
        return reply.split(closing_tag, 1)[1]
    return reply


def extract_json_object(reply: str) -> str:
    """Cut the outermost JSON object out of a reply, ignoring fences and prose."""
    text = strip_reasoning(reply)
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        raise ReplyParseError("no JSON object in reply")
    stop = end + 1
    return text[start:stop]


def skip_separators(text: str, position: int) -> int:
    """Move past commas and whitespace."""
    while position < len(text) and text[position] in SEPARATORS:
        position += 1
    return position


def validate_item(
    item_model: type[Finding] | type[TopicFinding],
    document: object,
) -> Finding | TopicFinding | None:
    """Validate one decoded item, returning None for an invalid one."""
    try:
        return item_model.model_validate(document)
    except ValidationError:
        return None


def find_findings_start(text: str) -> int | None:
    """Return the position just after the opening bracket of the findings list."""
    key = text.find(FINDINGS_KEY)
    opening = text.find("[", key) if key >= 0 else -1
    return opening + 1 if opening >= 0 else None


def read_item(
    text: str,
    position: int,
    item_model: type[Finding] | type[TopicFinding],
) -> tuple[Finding | TopicFinding | None, int] | None:
    """Decode and validate the object at the position, or None when it is cut off."""
    try:
        document, end = json.JSONDecoder().raw_decode(text, position)
    except json.JSONDecodeError:
        return None
    return validate_item(item_model, document), skip_separators(text, end)


def collect_items(
    text: str,
    start: int,
    item_model: type[Finding] | type[TopicFinding],
) -> list[Finding | TopicFinding]:
    """Read consecutive finding objects from the position until one is cut off."""
    items: list[Finding | TopicFinding] = []
    position = skip_separators(text, start)
    while position < len(text) and text[position] == "{":
        read = read_item(text, position, item_model)
        if read is None:
            break
        item, position = read
        if item is not None:
            items.append(item)
    return items


def recover_findings(
    reply: str,
    use_topics: bool,
) -> list[Finding | TopicFinding] | None:
    """Collect every complete, valid finding object from a damaged reply."""
    text = strip_reasoning(reply)
    start = find_findings_start(text)
    if start is None:
        return None
    return collect_items(text, start, TopicFinding if use_topics else Finding)


def parse_reply(reply: str, use_topics: bool) -> ParsedReply:
    """Parse a reply into findings, salvaging complete findings of a damaged one."""
    reply_model = TopicFindingsReply if use_topics else FindingsReply
    try:
        document = reply_model.model_validate_json(extract_json_object(reply))
        return ParsedReply(findings=list(document.findings), recovered=False)
    except (ReplyParseError, ValidationError) as error:
        recovered = recover_findings(reply, use_topics)
        if recovered is None:
            raise ReplyParseError(str(error)) from error
        return ParsedReply(findings=recovered, recovered=True)


def restrict_requirement_ids(
    schema: dict[str, object],
    finding_name: str,
    requirement_ids: list[str],
) -> None:
    """Limit the requirement_id values of the schema to the known ids."""
    definitions = cast(dict[str, object], schema["$defs"])
    finding = cast(dict[str, object], definitions[finding_name])
    properties = cast(dict[str, object], finding["properties"])
    properties["requirement_id"] = {"type": "string", "enum": requirement_ids}


def restrict_finding_types(
    schema: dict[str, object],
    finding_name: str,
    finding_types: list[str],
) -> None:
    """Limit the finding_type values of the schema to the allowed ones."""
    definitions = cast(dict[str, object], schema["$defs"])
    finding = cast(dict[str, object], definitions[finding_name])
    properties = cast(dict[str, object], finding["properties"])
    properties["finding_type"] = {"type": "string", "enum": finding_types}


def build_reply_schema(
    use_topics: bool,
    requirement_ids: list[str],
    allow_compliant: bool,
) -> dict[str, object]:
    """Return the JSON schema that constrains the model's reply format."""
    reply_model = TopicFindingsReply if use_topics else FindingsReply
    schema = cast(dict[str, object], reply_model.model_json_schema())
    finding_name = TopicFinding.__name__ if use_topics else Finding.__name__
    if requirement_ids:
        restrict_requirement_ids(schema, finding_name, requirement_ids)
    if not allow_compliant:
        restrict_finding_types(schema, finding_name, list(FINDING_TYPES))
    return schema
