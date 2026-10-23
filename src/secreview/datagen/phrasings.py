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


@cache
def load_phrasings() -> dict[str, list[str]]:
    """Load the alternative wordings of every rule, keyed by rule id."""
    text = read_text(project_path(load_settings().paths.phrasings_file))
    return PhrasingsFile.model_validate(yaml.safe_load(text)).phrasings


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


def rephrase_statement(case_id: str, rule_id: str, text: str) -> str:
    """Return a varied wording for a near copy of a rule, else the same text."""
    swappable = is_standalone_sentence(text)
    if not swappable or not copies_statement(text, load_statements()[rule_id]):
        return text
    options = load_phrasings()[rule_id]
    choice = choose_option(case_id, rule_id, len(options) + 1)
    if choice == load_settings().phrasing.keep_original_choice:
        return text
    return options[choice - 1]


def rephrase_design(case_id: str, marked_text: str) -> str:
    """Vary the wording of the satisfied statements in a marked design."""

    def replace(match: re.Match[str]) -> str:
        marker, text = match.group(1), match.group(2)
        if not marker.startswith(SATISFIED_PREFIX):
            return match.group(0)
        rule_id = marker[len(SATISFIED_PREFIX):]
        new_text = rephrase_statement(case_id, rule_id, text)
        return f"{MARKER_OPEN}{marker}|{new_text}{MARKER_CLOSE}"

    return MARKER_PATTERN.sub(replace, marked_text)
