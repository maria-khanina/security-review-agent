"""Alternative wordings of satisfied rules, substituted into authored designs."""

from functools import cache
import random
import re

from pydantic import BaseModel
from rapidfuzz import fuzz
import yaml

from secreview.datagen.catalog import load_rules, read_text
from secreview.datagen.markers import MARKER_CLOSE, MARKER_OPEN, MARKER_PATTERN
from secreview.datagen.settings import load_settings, project_path

SATISFIED_PREFIX = "S:"
SENTENCE_END = "."


class PhrasingsFile(BaseModel):
    phrasings: dict[str, list[str]]
    strict_phrasings: dict[str, dict[str, list[str]]]
    required_terms: dict[str, dict[str, list[str]]]


@cache
def load_phrasings_file() -> PhrasingsFile:
    """Load the file with the wordings of every rule."""
    text = read_text(project_path(load_settings().paths.phrasings_file))
    return PhrasingsFile.model_validate(yaml.safe_load(text))


def load_phrasings() -> dict[str, list[str]]:
    """Load the alternative wordings of every rule, keyed by rule id."""
    return load_phrasings_file().phrasings


def load_strict_phrasings() -> dict[str, dict[str, list[str]]]:
    """Load the wordings that meet the extra demands of one policy version."""
    return load_phrasings_file().strict_phrasings


@cache
def load_statements() -> dict[str, str]:
    """Map every rule id to its statement."""
    return {rule.id: rule.statement for rule in load_rules()}


def is_standalone_sentence(text: str) -> bool:
    """Tell whether a marked text is a whole sentence that can be swapped."""
    stripped = text.strip()
    return bool(stripped) and stripped[0].isupper() and stripped.endswith(SENTENCE_END)


def copies_statement(text: str, statement: str) -> bool:
    """Tell whether a marked text is a near copy of the rule statement."""
    similarity = fuzz.ratio(text.lower(), statement.lower())
    return similarity >= load_settings().phrasing.minimum_similarity


def choose_option(case_id: str, rule_id: str, option_count: int) -> int:
    """Pick the same option for the same case and rule on every run."""
    seed = f"{load_settings().phrasing.seed}:{case_id}:{rule_id}"
    return random.Random(seed).randrange(option_count)


def is_known_wording(text: str, rule_id: str) -> bool:
    """Tell whether a text is the statement of a rule or one of its wordings."""
    known: list[str] = [load_statements()[rule_id], *load_phrasings()[rule_id]]
    for versions in load_strict_phrasings().get(rule_id, {}).values():
        known.extend(versions)
    return any(copies_statement(text, wording) for wording in known)


def has_required_terms(text: str, rule_id: str, policy_version: str) -> bool:
    """Tell whether a text names everything the policy version adds to the rule."""
    terms = load_phrasings_file().required_terms.get(rule_id, {})
    return all(
        re.search(rf"\b(?:{term})\b", text, re.IGNORECASE)
        for term in terms.get(policy_version, [])
    )


def is_weaker_wording(text: str, rule_id: str, policy_version: str) -> bool:
    """Tell whether a statement of a rule leaves out what its version adds."""
    strict = load_strict_phrasings().get(rule_id, {}).get(policy_version)
    if strict is None or any(copies_statement(text, option) for option in strict):
        return False
    return not has_required_terms(text, rule_id, policy_version)


def pick_wording(case_id: str, rule_id: str, policy_version: str, text: str) -> str:
    """Pick the wording that replaces a known text of a rule in one policy version."""
    strict = load_strict_phrasings().get(rule_id, {}).get(policy_version)
    if strict is not None:
        return strict[choose_option(case_id, rule_id, len(strict))]
    options = load_phrasings()[rule_id]
    choice = choose_option(case_id, rule_id, len(options) + 1)
    if choice == load_settings().phrasing.keep_original_choice:
        return text
    return options[choice - 1]


def rephrase_statement(
    case_id: str,
    rule_id: str,
    policy_version: str,
    text: str,
) -> str:
    """Return a varied wording for a known text of a rule, else the same text."""
    if not is_standalone_sentence(text) or not is_known_wording(text, rule_id):
        return text
    if (rule_id, policy_version) not in strict_pairs():
        statement = load_statements()[rule_id]
        if not copies_statement(text, statement):
            return text
    return pick_wording(case_id, rule_id, policy_version, text)


def strict_pairs() -> set[tuple[str, str]]:
    """List the rule and policy version pairs that have their own wordings."""
    return {
        (rule_id, version)
        for rule_id, versions in load_strict_phrasings().items()
        for version in versions
    }


def rephrase_design(case_id: str, policy_version: str, marked_text: str) -> str:
    """Vary the wording of the satisfied statements in a marked design."""

    def replace(match: re.Match[str]) -> str:
        marker, text = match.group(1), match.group(2)
        if not marker.startswith(SATISFIED_PREFIX):
            return match.group(0)
        rule_id = marker[len(SATISFIED_PREFIX):]
        new_text = rephrase_statement(case_id, rule_id, policy_version, text)
        return f"{MARKER_OPEN}{marker}|{new_text}{MARKER_CLOSE}"

    return MARKER_PATTERN.sub(replace, marked_text)
