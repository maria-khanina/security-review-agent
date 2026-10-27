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
- compliant: a fragment states what the requirement demands, including the \
concrete values it names (limits, periods, counts, algorithms). When the \
requirement itself leaves the measure to the reader, a fragment is enough if \
it states a concrete mechanism or value that the strictest reasonable reading \
of the requirement would accept. A requirement with "should" is a \
requirement like one with "must". A remark that a control exists, without \
the value or mechanism, is not enough. When the requirement is expressed by a \
criterion and not by a value, for example who needs something or what a \
purpose requires, a fragment is enough only if it says who or what meets the \
criterion and why; the bare statement that the criterion is met is not enough.
- violated: a fragment states a decision that contradicts the requirement. \
A sentence that only permits something is not broken by a design that does \
less than it permits. \
When the requirement leaves the measure to the reader or is relaxed by \
another policy sentence, the decision is a violation if it contradicts even \
the most lenient reasonable reading: the control is absent altogether, or a \
stated value lies outside everything the requirement and its exceptions allow.
- unclear: the requirement applies to this design but the fragments do not \
settle it. The design is silent about it, or speaks only in general terms \
that name neither the value nor the mechanism, or the decision breaks only \
the strict reading of a requirement that also has a lenient reading. Do not \
guess; the author has to clarify.
- not_applicable: the requirement does not concern this service, for example \
it is about external callers and the design makes plain that only internal \
services call this one, or it cannot be judged from a design document at all \
because it concerns only settings of the implementation."""

STRICT_VERDICTS_TEXT = """Choose exactly one verdict:
- compliant: a fragment states the concrete content the requirement demands \
(the mechanism, value, scope or prohibition it names). When the requirement \
itself leaves the measure to the reader, a fragment is enough if it states a \
concrete mechanism or value that the strictest reasonable reading would \
accept. A fragment that only mentions the same subject, or is more general \
than the requirement, is not enough. When the requirement is expressed by a \
criterion and not by a value, the fragment has to say who or what meets the \
criterion and why.
- violated: a fragment states a decision that contradicts the requirement \
(a sentence that only permits something is not broken by a design that \
does less than it permits), or, for a requirement that leaves the measure to \
the reader or is relaxed by another policy sentence, contradicts even its most \
lenient reasonable reading.
- unclear: the requirement applies to this design but the fragments do not \
settle it. Either the design is silent or too general about it, or it breaks \
only the strict reading of a requirement that also has a lenient reading. \
Fragments that merely do not mention the subject \
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

REASONED_RULES = """Rules:
1. quote is copied character for character from one fragment, one or two \
consecutive sentences: the sentence that decides compliant or violated. Use an \
empty string for unclear and not_applicable.
2. reason is at most 60 words and comes before the verdict: list what the \
requirement demands (values, mechanism, scope), say for each element whether a \
fragment states it, and name what is missing.
3. severity is judged for violated only; use none for every other verdict.
4. Use only the fragments and the requirement. Do not invent facts."""

SHAPE = """Answer with one JSON object only, with these fields in this order: \
{"quote": "...", "reason": "...", "verdict": \
"compliant|violated|unclear|not_applicable", "severity": \
"none|low|medium|high|critical"}."""


def build_verdict_system_prompt(
    strict: bool,
    with_overview: bool,
    reasoned: bool,
) -> str:
    """Return the system prompt of the per-requirement verdict call."""
    introduction = INTRODUCTION + (OVERVIEW_SENTENCE if with_overview else "")
    verdicts = STRICT_VERDICTS_TEXT if strict else VERDICTS_TEXT
    rules = REASONED_RULES if reasoned else RULES
    return "\n\n".join([introduction, verdicts, SEVERITY_SCALE, rules, SHAPE])


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
