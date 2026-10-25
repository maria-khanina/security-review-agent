"""A separate model call for every requirement to find the words that make it vague."""

from pydantic import BaseModel

from secreview.agents.policy_requirements import (
    PolicyAnalysis,
    PolicyRequirement,
    save_policy_analysis,
)
from secreview.llm.client import ChatClient
from secreview.parsing.findings import ReplyParseError, extract_json_object

CONTRADICTORY = "contradictory"
VAGUE = "vague_or_advisory"
CLEAR = "clear"
MODAL_WORDS = frozenset({"must", "should", "shall", "may", "not", "be", "is"})
WORDING_PROMPT = """You check one sentence of a security policy. Decide whether a \
reviewer can check it against a software design document. List the words or \
short phrases that make it impossible to check because they leave the measure \
to the reader, for example "appropriate", "adequate", "reasonable", \
"regularly", "periodically", "timely", "as needed", "where practicable", \
"industry practice", "long enough", "excessive", "sufficient". The words \
"must", "should" and "shall", numbers, named mechanisms, named systems and \
precise prohibitions are not vague. Copy each phrase exactly from the \
sentence. Use an empty list when the sentence states a concrete criterion. \
Answer with one JSON object {"loose_phrases": ["..."]} and nothing else."""


class WordingReply(BaseModel):
    loose_phrases: list[str]


def build_wording_schema() -> dict[str, object]:
    """Return the JSON schema of the answer about one sentence."""
    schema: dict[str, object] = WordingReply.model_json_schema()
    return schema


def verified_loose_phrases(quote: str, reply: WordingReply) -> list[str]:
    """Keep the phrases that occur in the sentence and are not modal verbs."""
    lowered = quote.lower()
    phrases: list[str] = [phrase.strip().lower() for phrase in reply.loose_phrases]
    return [
        phrase
        for phrase in phrases
        if phrase and phrase in lowered and phrase not in MODAL_WORDS
    ]


def check_requirement(client: ChatClient, requirement: PolicyRequirement) -> str:
    """Judge the wording of one requirement with its own model call."""
    if requirement.wording == CONTRADICTORY:
        return CONTRADICTORY
    reply = client.complete(WORDING_PROMPT, requirement.quote, build_wording_schema())
    try:
        parsed = WordingReply.model_validate_json(extract_json_object(reply))
    except (ValueError, ReplyParseError):
        return requirement.wording
    return VAGUE if verified_loose_phrases(requirement.quote, parsed) else CLEAR


def recheck_wording(client: ChatClient, analysis: PolicyAnalysis) -> PolicyAnalysis:
    """Return the analysis with the wording of every requirement judged again."""
    rechecked: list[PolicyRequirement] = [
        item.model_copy(update={"wording": check_requirement(client, item)})
        for item in analysis.requirements
    ]
    return analysis.model_copy(update={"requirements": rechecked})


def store_rechecked(name: str, client: ChatClient, analysis: PolicyAnalysis) -> None:
    """Judge the wording again and store the result as a new analysis set."""
    save_policy_analysis(name, recheck_wording(client, analysis))
