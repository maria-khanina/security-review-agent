"""A yes-or-no check of a verdict whose probability of yes serves as confidence."""

import math
import re
from typing import Literal

from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials
from secreview.agents.policy_requirements import PolicyAnalysis
from secreview.agents.verdict_contexts import list_fragments
from secreview.agents.verdict_review import (
    LogprobClient,
    RequirementRecord,
    VerdictCaseRecord,
)
from secreview.llm.client import LogprobCompletion, TokenLogprobs
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.parsing.vocabulary import COMPLIANT, NOT_APPLICABLE, UNCLEAR, VIOLATED
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

ANSWER_VALUE = re.compile(r'"answer"\s*:\s*"')
YES = "yes"
NO = "no"
QUESTIONS: dict[str, str] = {
    COMPLIANT: (
        "Does the quoted design sentence itself state what the requirement "
        "demands, so that the requirement counts as fulfilled?"
    ),
    VIOLATED: (
        "Does the quoted design sentence state a decision that contradicts "
        "the requirement?"
    ),
    UNCLEAR: (
        "Do the fragments leave the requirement unsettled, being silent or too "
        "general about it, or is the requirement itself too vague to judge?"
    ),
    NOT_APPLICABLE: (
        "Is the requirement about something this service does not have or "
        "do, or can it not be judged from a design document?"
    ),
}
SYSTEM_PROMPT = (
    "You verify the verdict of a security design review on one policy "
    "requirement. You get the requirement, the design fragments shown to the "
    "reviewer, the verdict and the quote. Answer the question with yes or no "
    'as a JSON object {"answer": "yes|no"} and nothing else.'
)


class VerifierReply(BaseModel):
    answer: Literal["yes", "no"]


def build_verifier_schema() -> dict[str, object]:
    """Return the JSON schema that constrains a verifier reply."""
    schema: dict[str, object] = VerifierReply.model_json_schema()
    return schema


def build_verifier_user_prompt(
    requirement: str,
    fragments: list[str],
    record: RequirementRecord,
) -> str:
    """Describe the requirement, the fragments, the verdict and the question."""
    numbered_fragments = enumerate(fragments, 1)
    lines: list[str] = [f"[{number}] {text}" for number, text in numbered_fragments]
    joined = "\n".join(lines)
    return (
        f"<requirement>\n{requirement}\n</requirement>\n\n"
        f"<design_fragments>\n{joined}\n</design_fragments>\n\n"
        f"Verdict: {record.verdict}\nQuote: {record.quote}\n\n"
        f"Question: {QUESTIONS[str(record.verdict)]}"
    )


def find_answer_token(tokens: list[TokenLogprobs]) -> TokenLogprobs | None:
    """Find the token that starts the answer value in the generated text."""
    text = "".join(item.token for item in tokens)
    match = ANSWER_VALUE.search(text)
    if match is None:
        return None
    offset = 0
    for item in tokens:
        if offset == match.end():
            return item
        offset += len(item.token)
    return None


def spread_over_answers(top: dict[str, float]) -> dict[str, float]:
    """Sum the probabilities of the alternative tokens per answer they begin."""
    mass: dict[str, float] = {YES: 0.0, NO: 0.0}
    for token, logprob in top.items():
        piece = token.strip().lower()
        for answer in mass:
            if piece and answer.startswith(piece):
                mass[answer] += math.exp(logprob)
    return mass


def probability_of_yes(tokens: list[TokenLogprobs]) -> float | None:
    """Return the probability of yes among yes and no at the answer position."""
    item = find_answer_token(tokens)
    if item is None:
        return None
    mass = spread_over_answers(item.top)
    total = mass[YES] + mass[NO]
    return mass[YES] / total if total > 0.0 else None


def verify_record(
    client: LogprobClient,
    requirement_text: str,
    fragments: list[str],
    record: RequirementRecord,
) -> tuple[float | None, LogprobCompletion]:
    """Ask the yes-or-no question about one verdict and return P(yes) and the call."""
    completion = client.complete_with_logprobs(
        SYSTEM_PROMPT,
        build_verifier_user_prompt(requirement_text, fragments, record),
        build_verifier_schema(),
        REVIEW_SETTINGS.verdict.top_logprobs,
    )
    try:
        VerifierReply.model_validate_json(extract_json_object(completion.text))
    except (ValueError, ReplyParseError):
        return None, completion
    return probability_of_yes(completion.tokens), completion


def verify_item(
    client: LogprobClient,
    units: list[DesignUnit],
    requirement_text: str,
    item: RequirementRecord,
) -> RequirementRecord:
    """Return the record with the probability of yes as its confidence."""
    if item.verdict is None:
        return item
    fragments = list_fragments(units, item.context_units)
    yes, call = verify_record(client, requirement_text, fragments, item)
    return item.model_copy(
        update={
            "confidence": yes,
            "calls": item.calls + 1,
            "prompt_tokens": item.prompt_tokens + call.prompt_tokens,
            "completion_tokens": item.completion_tokens + call.completion_tokens,
            "seconds": item.seconds + call.seconds,
        }
    )


def verify_case(
    client: LogprobClient,
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    record: VerdictCaseRecord,
) -> VerdictCaseRecord:
    """Replace the confidence of every verdict by the probability of yes."""
    units = split_units(materials.design_text)
    texts: dict[str, str] = {item.id: item.quote for item in analysis.requirements}
    checked: list[RequirementRecord] = []
    for item in record.records:
        checked.append(verify_item(client, units, texts[item.requirement_id], item))
    return VerdictCaseRecord(case_id=record.case_id, records=checked)
