"""Company policy corpus: versions of the policy text with located rules.

Each policy version is a hand-written document. A map file lists, for every
rule the version covers, its status and the exact quotes that express it.
Quotes are located in the text to obtain gold character spans.
"""

from dataclasses import dataclass
from functools import cache

from pydantic import BaseModel
import yaml

from secreview.datagen.catalog import load_rules, read_text
from secreview.datagen.settings import load_settings, project_path

RULE_STATUSES = {"clear", "vague", "advisory", "conflicting"}
CLEAR_STATUS = "clear"
FIRM_STATUSES = (CLEAR_STATUS, "advisory")


class PolicyMapRule(BaseModel):
    status: str
    quotes: list[str]


class PolicyMapVersion(BaseModel):
    file: str
    rules: dict[str, PolicyMapRule]


class PolicyMaps(BaseModel):
    versions: dict[str, PolicyMapVersion]


@dataclass(frozen=True)
class RuleSpan:
    rule_id: str
    status: str
    spans: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class PolicyVersion:
    version: str
    text: str
    rules: dict[str, RuleSpan]
    absent: tuple[str, ...]

    def flaggable(self) -> list[str]:
        """List every rule the version covers, whatever its status."""
        return list(self.rules)

    def review_status(self, rule_ids: list[str]) -> str:
        """Return the first non-clear status among the rules, else clear."""
        for rule_id in rule_ids:
            status = self.rules[rule_id].status if rule_id in self.rules else None
            if status and status != CLEAR_STATUS:
                return status
        return CLEAR_STATUS

    def violable(self) -> list[str]:
        """List rules stated clearly enough to be violated unambiguously."""
        clear_rules: list[str] = []
        for rule_span in self.rules.values():
            if is_firm(rule_span.status):
                clear_rules.append(rule_span.rule_id)
        return clear_rules


def is_firm(status: str) -> bool:
    """Tell whether a wording is a requirement, whether or not it says "should"."""
    return status in FIRM_STATUSES


def locate_quote(text: str, quote: str) -> tuple[int, int]:
    """Find the unique character span of a quote inside a policy text."""
    preview = quote[: load_settings().quote_preview_length]
    start = text.find(quote)
    if start < 0:
        raise ValueError(f"quote not found: {preview}")
    if text.find(quote, start + 1) >= 0:
        raise ValueError(f"quote not unique: {preview}")
    return start, start + len(quote)


def build_rule_span(text: str, rule_id: str, entry: PolicyMapRule) -> RuleSpan:
    """Convert one map entry into a rule with located character spans."""
    if entry.status not in RULE_STATUSES:
        raise ValueError(f"{rule_id}: bad status {entry.status}")
    spans: list[tuple[int, int]] = []
    for quote in entry.quotes:
        spans.append(locate_quote(text, quote))
    return RuleSpan(rule_id, entry.status, tuple(spans))


def build_policy_version(
    version: str,
    entry: PolicyMapVersion,
    all_rule_ids: list[str],
) -> PolicyVersion:
    """Assemble one policy version with spans and the list of absent rules."""
    policies_directory = project_path(load_settings().paths.policies_directory)
    text = read_text(policies_directory / entry.file)
    rules: dict[str, RuleSpan] = {}
    for rule_id, rule_entry in entry.rules.items():
        rules[rule_id] = build_rule_span(text, rule_id, rule_entry)
    absent = tuple(rule_id for rule_id in all_rule_ids if rule_id not in rules)
    return PolicyVersion(version, text, rules, absent)


@cache
def load_policy_versions() -> dict[str, PolicyVersion]:
    """Load every policy version with located rules."""
    maps_path = project_path(load_settings().paths.policy_maps_file)
    maps = PolicyMaps.model_validate(yaml.safe_load(read_text(maps_path)))
    all_rule_ids: list[str] = [rule.id for rule in load_rules()]
    versions: dict[str, PolicyVersion] = {}
    for version, entry in maps.versions.items():
        versions[version] = build_policy_version(version, entry, all_rule_ids)
    return versions
