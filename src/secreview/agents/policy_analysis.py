"""One model call per policy version that lists its requirements with evidence.

The model does not label a requirement as clear or vague. It copies the
statement that relaxes a requirement; code checks it against the policy text
and marks both sentences contradictory. The wording of the other requirements
is judged by a separate call for each of them.
"""

from pydantic import BaseModel

from secreview.agents.policy_requirements import (
    LocatedDraft,
    PolicyAnalysis,
    RequirementDraft,
    locate_drafts,
    number_requirements,
)
from secreview.datagen.policies import load_policy_versions
from secreview.llm.client import ChatClient
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.parsing.grounding import locate_quote
from secreview.parsing.vocabulary import TOPICS, Topic, Wording
from secreview.review_settings import REVIEW_SETTINGS

Span = tuple[int, int]
UNJUDGED_WORDING: Wording = "clear"

POLICY_ANALYSIS_PROMPT = f"""You read a company security policy and list its \
requirements, so that a design review can refer to them.

A requirement is one sentence, or one clause of a sentence, that obliges or \
advises the engineers to do or avoid something concerning security. Skip \
purpose statements, scope, definitions, review cycles and disciplinary text. A \
sentence that holds several independent obligations is still one entry; copy \
it whole.

For every requirement give, in this order:
1. quote: copied character for character from the policy, without the section \
number or bullet marker.
2. relaxed_by: when another sentence of the policy allows less than this one \
demands (an exception, a grace period, a permission, or a different value for \
the same limit), copy that other sentence exactly from the policy. Look for \
words like "may", "up to", "until", "unless", "except", "acceptable" anywhere \
in the policy. Otherwise use an empty string.
3. topics: the one or two (at most {REVIEW_SETTINGS.policy_analysis.max_topics}) \
security topics the sentence itself is about, chosen only from: \
{", ".join(TOPICS)}. Do not list a topic the sentence does not mention.

List the requirements in the order they appear. Answer with one JSON object \
{{"requirements": [{{"quote": "...", "relaxed_by": "...", \
"topics": ["..."]}}]}} and nothing else."""


class RequirementEvidence(BaseModel):
    quote: str
    relaxed_by: str
    topics: list[Topic]


class PolicyEvidenceReply(BaseModel):
    requirements: list[RequirementEvidence]


def build_policy_schema() -> dict[str, object]:
    """Return the JSON schema that constrains the policy analysis reply."""
    schema: dict[str, object] = PolicyEvidenceReply.model_json_schema()
    return schema


def build_policy_user_prompt(policy_text: str) -> str:
    """Wrap the policy text into the user message of the analysis call."""
    return (
        f"<security_policy>\n{policy_text}\n</security_policy>\n\n"
        "List the requirements of this policy now and answer with the JSON object."
    )


def parse_policy_reply(reply: str) -> list[RequirementEvidence]:
    """Parse the analysis reply into requirements with their evidence."""
    try:
        text = extract_json_object(reply)
        return PolicyEvidenceReply.model_validate_json(text).requirements
    except ValueError as error:
        raise ReplyParseError(str(error)) from error


def build_base_drafts(items: list[RequirementEvidence]) -> list[RequirementDraft]:
    """Turn the evidence into drafts whose wording is judged by a later step."""
    drafts: list[RequirementDraft] = []
    for item in items:
        drafts.append(
            RequirementDraft(
                quote=item.quote,
                wording=UNJUDGED_WORDING,
                topics=item.topics,
            )
        )
    return drafts


def spans_touch(first: Span, second: Span) -> bool:
    """Tell whether two character spans share any character."""
    return first[0] < second[1] and second[0] < first[1]


def collect_relaxations(
    policy_text: str,
    items: list[RequirementEvidence],
) -> list[tuple[Span, Span, RequirementEvidence]]:
    """Keep the relaxations whose two sentences are both found in the policy."""
    minimum = REVIEW_SETTINGS.grounding.min_quote_characters
    found: list[tuple[Span, Span, RequirementEvidence]] = []
    for item in items:
        own = locate_quote(policy_text, item.quote, minimum)
        other = locate_quote(policy_text, item.relaxed_by, minimum)
        if own is not None and other is not None and own != other:
            found.append((own, other, item))
    return found


def mark_contradictory(
    entries: dict[Span, RequirementDraft],
    policy_text: str,
    span: Span,
    topics: list[Topic],
) -> None:
    """Mark every requirement at the span contradictory, adding it when missing."""
    touching: list[Span] = [key for key in entries if spans_touch(key, span)]
    for key in touching:
        entries[key] = entries[key].model_copy(update={"wording": "contradictory"})
    if not touching:
        quote = policy_text[span[0]:span[1]]
        entries[span] = RequirementDraft(
            quote=quote,
            wording="contradictory",
            topics=topics,
        )


def build_requirement_entries(
    policy_text: str,
    items: list[RequirementEvidence],
) -> list[LocatedDraft]:
    """Locate the requirements and mark both sides of every verified relaxation."""
    entries: dict[Span, RequirementDraft] = dict(
        locate_drafts(policy_text, build_base_drafts(items))
    )
    for own, other, item in collect_relaxations(policy_text, items):
        mark_contradictory(entries, policy_text, own, item.topics)
        mark_contradictory(entries, policy_text, other, item.topics)
    return sorted(entries.items())


def analyze_policy(client: ChatClient, policy_version: str) -> PolicyAnalysis:
    """Ask the model for the requirements of a policy version and number them."""
    policy_text = load_policy_versions()[policy_version].text
    reply = client.complete(
        POLICY_ANALYSIS_PROMPT,
        build_policy_user_prompt(policy_text),
        build_policy_schema(),
    )
    entries = build_requirement_entries(policy_text, parse_policy_reply(reply))
    return number_requirements(policy_version, policy_text, entries)
