"""A separate model call for every requirement to judge whether it names its measure."""

import re
from typing import Literal

from pydantic import BaseModel

from secreview.agents.policy_requirements import (
    PolicyAnalysis,
    PolicyRequirement,
    save_policy_analysis,
)
from secreview.agents.verdict_review import LogprobClient
from secreview.agents.verdict_verifier import probability_of_yes
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.review_settings import REVIEW_SETTINGS

CONTRADICTORY = "contradictory"
VAGUE = "vague"
CLEAR = "clear"
SOFT_MODALS = re.compile(r"\b(?:should|shall)\b", re.IGNORECASE)
CLAUSE_BREAK = re.compile(
    r"(?:;|,\s+and)\s+(?=[^,;]{0,60}\b(?:must|may|are|is)\b)",
    re.IGNORECASE,
)
WORDING_PROMPT = """You check one sentence of a security policy. A reviewer reads \
a software design document and must decide whether the design does what the \
sentence demands. Does the sentence itself name the measure the design has to \
meet: a number, a named mechanism, a named system, a named standard, an \
explicit list or an explicit prohibition? Answer "no" when the sentence leaves \
the measure to the reader with a general word that stands for how much, how \
often, how fast, how long or how well. A sentence that states a criterion \
whose application depends on the facts of each service still names the \
measure, because the design then has to state those facts. The obligation \
words "must", "should", "shall" and "may" do not count as general words. \
Answer with one JSON object {"answer": "yes"} or {"answer": "no"} and \
nothing else."""
LOOSE_WORD_PROMPT = """You check one sentence of a security policy. Copy the one \
word or short phrase (at most three words) of the sentence that leaves a \
degree to the reader: a general word of degree, frequency, speed, quantity or \
quality that is used without a number, a mechanism or a criterion. Never copy \
an obligation word, and never copy a verb or a noun that names the demanded \
action or its object. If the sentence has no such word, answer with an empty \
string. Answer with one JSON object {"word": "..."} and nothing else."""
OBLIGATION_WORDS = frozenset(
    {"must", "should", "shall", "may", "not", "be", "is", "never", "only"}
)


class WordingReply(BaseModel):
    answer: Literal["yes", "no"]


class LooseWordReply(BaseModel):
    word: str


def build_wording_schema() -> dict[str, object]:
    """Return the JSON schema of the answer about one sentence."""
    schema: dict[str, object] = WordingReply.model_json_schema()
    return schema


def normalize_modals(sentence: str) -> str:
    """Write "should" and "shall" as "must", which is how the policy reads them."""
    return SOFT_MODALS.sub("must", sentence)


def split_clauses(sentence: str) -> list[str]:
    """Cut a sentence with several obligations into one text per obligation."""
    pieces: list[str] = CLAUSE_BREAK.split(sentence)
    return [piece.strip() for piece in pieces if piece.strip()]


def has_loose_word(client: LogprobClient, text: str) -> bool:
    """Tell whether the model can copy a general word of degree from the text."""
    completion = client.complete_with_logprobs(
        LOOSE_WORD_PROMPT,
        text,
        LooseWordReply.model_json_schema(),
        REVIEW_SETTINGS.verdict.top_logprobs,
    )
    try:
        reply = LooseWordReply.model_validate_json(extract_json_object(completion.text))
    except (ValueError, ReplyParseError):
        return False
    word = reply.word.strip().lower()
    longest = REVIEW_SETTINGS.policy_analysis.loose_word_max_words
    return (
        bool(word)
        and word in text.lower()
        and len(word.split()) <= longest
        and word not in OBLIGATION_WORDS
    )


def probability_of_no(client: LogprobClient, text: str) -> float | None:
    """Ask whether the text names its measure and return the probability of no."""
    completion = client.complete_with_logprobs(
        WORDING_PROMPT,
        text,
        build_wording_schema(),
        REVIEW_SETTINGS.verdict.top_logprobs,
    )
    try:
        WordingReply.model_validate_json(extract_json_object(completion.text))
    except (ValueError, ReplyParseError):
        return None
    names_the_measure = probability_of_yes(completion.tokens)
    return None if names_the_measure is None else 1.0 - names_the_measure


def vagueness_of(client: LogprobClient, quote: str) -> float | None:
    """Return the largest probability of no over the obligations of a sentence."""
    scores: list[float] = []
    normalized = normalize_modals(quote)
    clauses: list[str] = [normalized]
    if REVIEW_SETTINGS.policy_analysis.split_clauses:
        clauses = split_clauses(normalized)
    for clause in clauses:
        score = probability_of_no(client, clause)
        if score is not None:
            scores.append(score)
    return max(scores) if scores else None


def check_requirement(
    client: LogprobClient,
    requirement: PolicyRequirement,
) -> str:
    """Judge the wording of one requirement with a call for each obligation."""
    if requirement.wording == CONTRADICTORY:
        return CONTRADICTORY
    score = vagueness_of(client, requirement.quote)
    if score is None:
        return requirement.wording
    threshold = REVIEW_SETTINGS.policy_analysis.vagueness_threshold
    if score < threshold:
        return CLEAR
    normalized = normalize_modals(requirement.quote)
    return VAGUE if has_loose_word(client, normalized) else CLEAR


def recheck_wording(client: LogprobClient, analysis: PolicyAnalysis) -> PolicyAnalysis:
    """Return the analysis with the wording of every requirement judged again."""
    rechecked: list[PolicyRequirement] = [
        item.model_copy(update={"wording": check_requirement(client, item)})
        for item in analysis.requirements
    ]
    return analysis.model_copy(update={"requirements": rechecked})


def store_rechecked(
    name: str,
    client: LogprobClient,
    analysis: PolicyAnalysis,
) -> None:
    """Judge the wording again and store the result as a new analysis set."""
    save_policy_analysis(name, recheck_wording(client, analysis))
