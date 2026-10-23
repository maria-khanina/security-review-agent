"""Parsing a verdict reply and turning token log-probabilities into a confidence."""

import math
import re
from typing import Literal

from pydantic import BaseModel

from secreview.llm.client import TokenLogprobs
from secreview.parsing.findings import ReplyParseError, extract_json_object
from secreview.parsing.vocabulary import VERDICTS, Verdict

VerdictSeverity = Literal["none", "low", "medium", "high", "critical"]
VERDICT_VALUE = re.compile(r'"verdict"\s*:\s*"')


class VerdictReply(BaseModel):
    quote: str
    reason: str
    verdict: Verdict
    severity: VerdictSeverity


def build_verdict_schema() -> dict[str, object]:
    """Return the JSON schema that constrains a verdict reply."""
    schema: dict[str, object] = VerdictReply.model_json_schema()
    return schema


def parse_verdict_reply(reply: str) -> VerdictReply:
    """Parse a verdict reply, raising ReplyParseError when it is not valid."""
    try:
        return VerdictReply.model_validate_json(extract_json_object(reply))
    except ValueError as error:
        raise ReplyParseError(str(error)) from error


def find_value_token(tokens: list[TokenLogprobs]) -> TokenLogprobs | None:
    """Find the token that starts the verdict value in the generated text."""
    text = "".join(item.token for item in tokens)
    match = VERDICT_VALUE.search(text)
    if match is None:
        return None
    offset = 0
    for item in tokens:
        if offset == match.end():
            return item
        offset += len(item.token)
    return None


def spread_over_verdicts(top: dict[str, float]) -> dict[str, float]:
    """Sum the probabilities of the alternative tokens per verdict they begin."""
    mass: dict[str, float] = {verdict: 0.0 for verdict in VERDICTS}
    for token, logprob in top.items():
        piece = token.strip()
        for verdict in VERDICTS:
            if piece and verdict.startswith(piece):
                mass[verdict] += math.exp(logprob)
    return mass


def compute_distribution(tokens: list[TokenLogprobs]) -> dict[str, float]:
    """Return the probabilities of the four verdicts, or nothing when unknown."""
    item = find_value_token(tokens)
    if item is None:
        return {}
    mass = spread_over_verdicts(item.top)
    total = sum(mass.values())
    if total <= 0.0:
        return {}
    return {verdict: share / total for verdict, share in mass.items()}


def compute_confidence(tokens: list[TokenLogprobs], verdict: str) -> float | None:
    """Return the probability of the chosen verdict among the four verdicts."""
    return compute_distribution(tokens).get(verdict)
