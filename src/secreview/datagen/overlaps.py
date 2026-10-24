"""Other rules that a planted violation also breaks, by violation scenario."""

from functools import cache

from pydantic import BaseModel
from rapidfuzz import fuzz
import yaml

from secreview.datagen.catalog import load_rules, read_text
from secreview.datagen.models import Flaw, Rule
from secreview.datagen.settings import load_settings, project_path


class Overlap(BaseModel):
    rule: str
    scenario: int
    also_violates: list[str]


class OverlapsFile(BaseModel):
    overlaps: list[Overlap]


@cache
def load_overlaps() -> dict[tuple[str, int], list[str]]:
    """Map a rule and the index of its violation scenario to the other rules broken."""
    text = read_text(project_path(load_settings().paths.overlaps_file))
    table: dict[tuple[str, int], list[str]] = {}
    for item in OverlapsFile.model_validate(yaml.safe_load(text)).overlaps:
        table[(item.rule, item.scenario)] = item.also_violates
    return table


def locate_scenario(rule: Rule, instruction: str) -> int | None:
    """Find which violation scenario of the rule an instruction to the author used."""
    best: int | None = None
    best_score = load_settings().phrasing.minimum_similarity
    for index, scenario in enumerate(rule.violation_scenarios):
        score = fuzz.partial_ratio(scenario, instruction)
        if score > best_score:
            best, best_score = index, score
    return best


def find_co_violations(flaw: Flaw) -> list[str]:
    """List the other rules that the planted violation also breaks."""
    if flaw.type != "violation" or flaw.rule_id is None:
        return []
    rules: dict[str, Rule] = {rule.id: rule for rule in load_rules()}
    index = locate_scenario(rules[flaw.rule_id], flaw.instruction)
    if index is None:
        return []
    return list(load_overlaps().get((flaw.rule_id, index), []))
