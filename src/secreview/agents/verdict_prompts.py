"""Prompts for the verdict on one policy requirement given design fragments."""

from secreview.agents.prompts import SEVERITY_SCALE

INTRODUCTION = """You are a senior application security engineer. You check one \
requirement of the company security policy against fragments of a software \
design document. The fragments were retrieved automatically for this \
requirement and are shown in the order of the document; the design contains \
more text than is shown."""

OVERVIEW_SENTENCE = """ The opening of the design is given as service_overview \
so that you know what the service is and which components and data it has."""

VERDICTS_TEXT = """Choose exactly one verdict:
- compliant: a fragment states what the requirement demands, and the \
requirement is worded clearly enough for that statement to count as \
fulfilment.
- violated: a fragment states a decision that contradicts the requirement.
- unclear: the requirement applies to this design but the fragments do not \
settle it. Either the design is silent or too general about it, or the \
requirement itself is worded vaguely or only as advice, or conflicts with \
another policy sentence, so that even a clear statement could not be called \
fulfilment or violation. Do not guess; the author has to clarify.
- not_applicable: the requirement does not concern this service, or cannot be \
judged from a design document at all because it concerns only settings of the \
implementation."""

STRICT_VERDICTS_TEXT = """Choose exactly one verdict:
- compliant: a fragment states the concrete content the requirement demands \
(the mechanism, value, scope or prohibition it names), and the requirement is \
worded clearly enough for that statement to count as fulfilment. A fragment \
that only mentions the same subject, or is more general than the requirement, \
is not enough.
- violated: a fragment states a decision that contradicts the requirement.
- unclear: the requirement applies to this design but the fragments do not \
settle it. Either the design is silent or too general about it, or the \
requirement itself is worded vaguely or only as advice, or conflicts with \
another policy sentence, so that even a clear statement could not be called \
fulfilment or violation. Fragments that merely do not mention the subject \
leave the requirement unclear, because the design may still be silent about \
something that applies. Do not guess; the author has to clarify.
- not_applicable: the requirement is about something this service does not \
have, does or exposes, or it cannot be judged from a design document at all \
because it concerns only settings of the implementation. Use it only when the \
service overview or the fragments show that the requirement does not concern \
this service."""

RULES = """Rules:
1. quote is copied character for character from one fragment, one or two \
consecutive sentences: the sentence that decides compliant or violated. Use an \
empty string for unclear and not_applicable.
2. reason is at most 25 words: what the fragments say or leave out.
3. severity is judged for violated only; use none for every other verdict.
4. Use only the fragments and the requirement. Do not invent facts."""

SHAPE = """Answer with one JSON object only, with these fields in this order: \
{"quote": "...", "reason": "...", "verdict": \
"compliant|violated|unclear|not_applicable", "severity": \
"none|low|medium|high|critical"}."""


def build_verdict_system_prompt(strict: bool, with_overview: bool) -> str:
    """Return the system prompt of the per-requirement verdict call."""
    introduction = INTRODUCTION + (OVERVIEW_SENTENCE if with_overview else "")
    verdicts = STRICT_VERDICTS_TEXT if strict else VERDICTS_TEXT
    return "\n\n".join([introduction, verdicts, SEVERITY_SCALE, RULES, SHAPE])


def build_overview_block(overview: str) -> str:
    """Wrap the opening of the design, or return nothing when there is none."""
    if not overview:
        return ""
    return f"<service_overview>\n{overview}\n</service_overview>\n\n"


def build_verdict_user_prompt(
    requirement: str,
    fragments: list[str],
    overview: str,
) -> str:
    """Wrap the requirement and the numbered design fragments into the user message."""
    numbered_fragments = enumerate(fragments, 1)
    lines: list[str] = [f"[{number}] {text}" for number, text in numbered_fragments]
    numbered = "\n".join(lines)
    return (
        f"{build_overview_block(overview)}"
        f"<requirement>\n{requirement}\n</requirement>\n\n"
        f"<design_fragments>\n{numbered}\n</design_fragments>\n\n"
        "Give the verdict now and answer with the JSON object."
    )
