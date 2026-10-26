"""Finding requirements of one policy that allow less than another one demands."""

from typing import Literal, Protocol

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.agents.verdict_review import LogprobClient
from secreview.agents.verdict_verifier import probability_of_yes
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.review_settings import REVIEW_SETTINGS

Matrix = NDArray[np.float64]
CONTRADICTORY = "contradictory"
THREE_QUESTIONS = len(("weaker", "weaker reversed", "same obligation"))
ANSWER_SHAPE = 'Answer with one JSON object {"answer": "yes"} or {"answer": "no"}.'
WEAKER_PROMPT = f"""You compare two sentences A and B of the same security \
policy. Does sentence B allow less than sentence A demands, for some or all \
cases: an exception, a lower level, a longer period, a later date, or a \
decision left to someone's discretion? {ANSWER_SHAPE}"""
SAME_OBLIGATION_PROMPT = f"""You compare two sentences of the same security policy. \
Do both sentences speak about the same obligation, that is the same control in \
the same situation, while setting different demands, so that following one of \
them means not following the other as written? {ANSWER_SHAPE}"""


class Embedder(Protocol):
    def encode(self, texts: list[str]) -> Matrix: ...


class ScoredPair(BaseModel):
    first: int
    second: int
    score: float


class AnswerReply(BaseModel):
    answer: Literal["yes", "no"]


class SentenceEmbedder:
    def __init__(self) -> None:
        settings = REVIEW_SETTINGS.policy_analysis
        self.model = SentenceTransformer(settings.pair_model_id, device="cpu")

    def encode(self, texts: list[str]) -> Matrix:
        """Embed the texts into unit vectors."""
        vectors = self.model.encode(
            texts,
            batch_size=REVIEW_SETTINGS.retrieval.encode_batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return np.asarray(vectors, dtype=np.float64)


def candidate_pairs(vectors: Matrix, neighbours: int) -> list[tuple[int, int]]:
    """List the pairs in which one sentence is among the nearest of the other."""
    similarity = vectors @ vectors.T
    np.fill_diagonal(similarity, -np.inf)
    pairs: set[tuple[int, int]] = set()
    for index in range(len(vectors)):
        for other in np.argsort(-similarity[index])[:neighbours]:
            pairs.add((min(index, int(other)), max(index, int(other))))
    return sorted(pairs)


def ask_yes(client: LogprobClient, system_prompt: str, user_prompt: str) -> float:
    """Return the probability of yes to a question, or zero when no answer parses."""
    completion = client.complete_with_logprobs(
        system_prompt,
        user_prompt,
        AnswerReply.model_json_schema(),
        REVIEW_SETTINGS.verdict.top_logprobs,
    )
    try:
        AnswerReply.model_validate_json(extract_json_object(completion.text))
    except (ValueError, ReplyParseError):
        return 0.0
    return probability_of_yes(completion.tokens) or 0.0


def pair_prompt(first: str, second: str) -> str:
    """Write the two sentences as the user message of a pair question."""
    return f"Sentence A: {first}\nSentence B: {second}"


def pair_score(client: LogprobClient, first: str, second: str) -> float:
    """Return the mean probability of yes over the three questions about a pair."""
    forward = ask_yes(client, WEAKER_PROMPT, pair_prompt(first, second))
    backward = ask_yes(client, WEAKER_PROMPT, pair_prompt(second, first))
    same = ask_yes(client, SAME_OBLIGATION_PROMPT, pair_prompt(first, second))
    return (forward + backward + same) / THREE_QUESTIONS


def score_pairs(
    client: LogprobClient,
    quotes: list[str],
    pairs: list[tuple[int, int]],
) -> list[ScoredPair]:
    """Ask the questions about every candidate pair."""
    scored: list[ScoredPair] = []
    for first, second in pairs:
        score = pair_score(client, quotes[first], quotes[second])
        scored.append(ScoredPair(first=first, second=second, score=score))
    return scored


def mark_pairs(
    analysis: PolicyAnalysis,
    scored: list[ScoredPair],
) -> PolicyAnalysis:
    """Mark both requirements of every pair above the threshold contradictory."""
    threshold = REVIEW_SETTINGS.policy_analysis.pair_threshold
    flagged: set[int] = set()
    for pair in scored:
        if pair.score >= threshold:
            flagged.update({pair.first, pair.second})
    requirements: list[PolicyRequirement] = []
    for index, item in enumerate(analysis.requirements):
        wording = CONTRADICTORY if index in flagged else item.wording
        requirements.append(item.model_copy(update={"wording": wording}))
    return analysis.model_copy(update={"requirements": requirements})


def detect_contradictions(
    client: LogprobClient,
    embedder: Embedder,
    analysis: PolicyAnalysis,
) -> PolicyAnalysis:
    """Mark the requirements that are in a pair of which one allows less."""
    quotes: list[str] = [item.quote for item in analysis.requirements]
    neighbours = REVIEW_SETTINGS.policy_analysis.pair_neighbours
    pairs = candidate_pairs(embedder.encode(quotes), neighbours)
    return mark_pairs(analysis, score_pairs(client, quotes, pairs))
