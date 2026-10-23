"""Prompt texts of the single-call design reviewer and their switchable parts."""

from secreview.parsing.vocabulary import TOPICS

INTRODUCTION = """You are a senior application security engineer. Review a \
software design document against the company security policy. The policy is \
given as numbered reference material: every requirement sentence carries a tag \
such as [R12]. The policy is a reference to check the design against, not a \
list you have to walk through.

Read the design. Wherever it describes how something works, check that against \
the policy. Report every problem you find; there is no limit on their number."""

FINDING_KINDS = """Finding kinds:
- violation: the design states a decision that breaks a policy requirement.
- ambiguity: the design describes a component but is vague or silent about \
something a policy requirement needs in order to be judged. Do not guess; the \
author has to clarify."""

SILENCE_INSTRUCTION = """Silence about requirements: if the design describes a \
component and a requirement of the policy clearly concerns that kind of \
component but the design says nothing about it, report an ambiguity and quote \
the sentence in which the component is named. Do not report silence about a \
topic that has nothing to do with any component the design describes."""

COMPLIANCE_INSTRUCTION = (
    "Compliance: when a sentence of the design states what a requirement "
    "demands, that is not a problem. Report such a sentence with "
    "finding_type compliant instead of violation, so that only real "
    "problems are marked violation or ambiguity. Compliant entries are "
    "discarded afterwards."
)

SEVERITY_SCALE = """Severity scale, judged for this service:
- critical: secrets, card numbers, personal data or control of the service can \
be reached directly by outsiders, with no other weakness, on an \
internet-exposed service or store.
- high: sensitive data or privileged functions are seriously exposed, but \
exploitation needs another condition (an insider, a stolen credential, a \
second weakness).
- medium: a defence-in-depth control is weak or missing, the data is not \
sensitive, or the component is internal only.
- low: hygiene, a documentation gap or a minor deviation with little direct \
impact.
Rate an ambiguity one level below the violation it could hide."""

CONFIDENCE_SCALE = """Confidence scale, 1 to 100, how likely a careful human \
reviewer would confirm the finding: 90-100 no reasonable alternative reading; \
70-89 very likely, one alternative reading; 50-69 plausible, an assumption \
must be checked; 30-49 weak signal; 1-29 speculation, better omitted. Use the \
whole scale; findings of different strength get different values."""

RULES = """Rules:
1. design_quote is copied character for character from the design, one or two \
consecutive sentences. For an ambiguity, quote the sentence that names the \
component.
2. requirement_id is the tag of the policy requirement the finding concerns, \
for example R12. Cite only tags that appear in the policy.
3. observation is at most 25 words: what the design says, or what it leaves \
out.
4. Report only what the two texts show. Do not invent requirements or report \
requirements the design clearly satisfies.
5. If there is nothing to report, return an empty findings list."""


def build_topics_instruction() -> str:
    """Describe the topics field that precedes the observation of a finding."""
    return (
        "topics: before you reason about a finding, name the security topics of "
        "the quoted sentence, one to three, chosen only from: "
        + ", ".join(TOPICS)
        + ". Then choose the requirement among those that share a topic."
    )


def build_shape(use_topics: bool, allow_compliant: bool) -> str:
    """Describe the JSON shape of the reply."""
    topics_part = '"topics": ["..."], ' if use_topics else ""
    types = "violation|ambiguity"
    if allow_compliant:
        types += "|compliant"
    return (
        "Answer with one JSON object only, {\"findings\": [ ... ]}, where every "
        "finding has these fields in this order: "
        '{"design_quote": "...", ' + topics_part + '"observation": "...", '
        '"requirement_id": "R12", "finding_type": "' + types + '", '
        '"severity": "low|medium|high|critical", "confidence": <integer 1-100>}.'
    )


def build_system_prompt(
    use_topics: bool,
    ask_for_silence: bool,
    allow_compliant: bool,
) -> str:
    """Assemble the system prompt for the chosen variant."""
    parts: list[str] = [INTRODUCTION, FINDING_KINDS]
    if ask_for_silence:
        parts.append(SILENCE_INSTRUCTION)
    if allow_compliant:
        parts.append(COMPLIANCE_INSTRUCTION)
    parts.extend([SEVERITY_SCALE, CONFIDENCE_SCALE, RULES])
    if use_topics:
        parts.append(build_topics_instruction())
    parts.append(build_shape(use_topics, allow_compliant))
    return "\n\n".join(parts)


def build_user_prompt(tagged_policy: str, design_text: str) -> str:
    """Join the numbered policy and the design into the user message."""
    return (
        f"<security_policy>\n{tagged_policy}\n</security_policy>\n\n"
        f"<design_document>\n{design_text}\n</design_document>\n\n"
        "Review the design document now and answer with the JSON object."
    )
