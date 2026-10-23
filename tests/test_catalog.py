"""Integrity tests for catalogs, documented services, severity and author profiles."""

from collections.abc import Iterator
from pathlib import Path
from typing import cast

from pydantic import BaseModel
import yaml

from secreview.datagen.catalog import (
    load_all_documented_services,
    load_architecture,
    load_author_profiles,
    load_company,
    load_drift_mutations,
    load_rule_couplings,
    load_rules,
    load_severity,
)
from secreview.datagen.flaw_factory import rule_applies
from secreview.datagen.models import Rule
from secreview.datagen.settings import PROJECT_ROOT, load_settings

CONFIG_FILES = [
    "configs/company.yaml",
    "configs/architecture.yaml",
    "configs/documented_service_templates.yaml",
    "configs/drift_mutations.yaml",
    "configs/author_profiles.yaml",
    "configs/severity.yaml",
    "data/policies/rules.yaml",
    "data/policies/policy_maps.yaml",
    "data/policies/rule_couplings.yaml",
]
NULLABLE_KEY = "implementation_check"
SEVERITY_EXAMPLES_FILE = Path(__file__).parent / "data" / "severity_examples.yaml"


class SeverityExample(BaseModel):
    base: int
    exposure: str
    data_class: str
    compensating: bool
    ambiguity: bool
    expected: str


class SeverityExamples(BaseModel):
    examples: list[SeverityExample]


def find_null_values(document: object, path: str) -> Iterator[str]:
    """Yield the path of every null value inside a parsed YAML document."""
    if document is None:
        yield path
    elif isinstance(document, dict):
        for key, value in cast(dict[str, object], document).items():
            yield from find_null_values(value, f"{path}/{key}")
    elif isinstance(document, list):
        for position, value in enumerate(cast(list[object], document)):
            yield from find_null_values(value, f"{path}[{position}]")


def rules_with_scope(rules: list[Rule], scopes: set[str]) -> list[Rule]:
    """Select the rules whose check scope is one of the given scopes."""
    selected: list[Rule] = []
    for rule in rules:
        if rule.check_scope in scopes:
            selected.append(rule)
    return selected


def find_unexpected_nulls(paths: list[str]) -> list[str]:
    """Drop the null paths that are allowed to be null."""
    unexpected: list[str] = []
    for path in paths:
        if not path.endswith(NULLABLE_KEY):
            unexpected.append(path)
    return unexpected


def test_rule_ids_are_unique_and_use_known_vocabulary() -> None:
    vocabulary = load_company().vocabulary
    rules = load_rules()
    assert len({rule.id for rule in rules}) == len(rules)
    for rule in rules:
        assert set(rule.applies_to.kind) <= set(vocabulary["component_kind"])
        assert set(rule.applies_to.data) <= set(vocabulary["data_class"])
        assert set(rule.applies_to.exposure) <= set(vocabulary["exposure"])


def test_drift_mutations_reference_existing_rules() -> None:
    rule_ids: set[str] = {rule.id for rule in load_rules()}
    for drift in load_drift_mutations():
        assert set(drift.related_rules) <= rule_ids, drift.id


def test_rule_couplings_reference_distinct_existing_rules() -> None:
    rule_ids: set[str] = {rule.id for rule in load_rules()}
    sources: list[str] = []
    for coupling in load_rule_couplings():
        sources.append(coupling.when_flawed)
        assert coupling.when_flawed in rule_ids
        assert coupling.suppress
        assert set(coupling.suppress) <= rule_ids
        assert coupling.when_flawed not in coupling.suppress
        assert len(coupling.suppress) == len(set(coupling.suppress))
    assert len(sources) == len(set(sources))


def test_documented_services_use_known_vocabulary() -> None:
    company = load_company()
    vocabulary = company.vocabulary
    for documented_service in load_all_documented_services():
        assert set(documented_service.components) <= set(vocabulary["component_kind"])
        assert set(documented_service.data) <= set(vocabulary["data_class"])
        assert documented_service.exposure in vocabulary["exposure"]
    documented_service_ids: set[str] = {
        documented_service.id for documented_service in load_all_documented_services()
    }
    assert set(company.split.holdout_documented_services) <= documented_service_ids


def test_architecture_covers_every_documented_service() -> None:
    architecture = load_architecture()
    for documented_service in load_all_documented_services():
        components = architecture[documented_service.id].components
        kinds: set[str] = {component.kind for component in components}
        assert kinds == set(documented_service.components), documented_service.id


def test_every_documented_service_has_enough_applicable_rules() -> None:
    minimum = load_settings().quality_gates.min_applicable_rules_per_documented_service
    rules = load_rules()
    for documented_service in load_all_documented_services():
        applicable: list[Rule] = [
            rule for rule in rules if rule_applies(rule, documented_service)
        ]
        assert len(applicable) >= minimum, documented_service.id


def test_catalog_covers_design_and_implementation_checks() -> None:
    gates = load_settings().quality_gates
    rules = load_rules()
    design = rules_with_scope(rules, {"design", "both"})
    implementation = rules_with_scope(rules, {"impl", "both"})
    assert len(design) >= gates.min_design_checkable_rules
    assert len(implementation) >= gates.min_implementation_checkable_rules
    assert len(load_drift_mutations()) >= gates.min_drift_mutations


def test_severity_formula_examples() -> None:
    severity = load_severity()
    text = SEVERITY_EXAMPLES_FILE.read_text(encoding="utf-8")
    examples = SeverityExamples.model_validate(yaml.safe_load(text)).examples
    for example in examples:
        computed = severity.compute(
            example.base,
            example.exposure,
            example.data_class,
            example.compensating,
            example.ambiguity,
        )
        assert computed == example.expected, example


def test_author_profiles_are_well_formed() -> None:
    author_profiles = load_author_profiles()
    assert author_profiles
    for author_profile in author_profiles.values():
        low, high = author_profile.length_words
        assert 0 < low < high, author_profile.id
        assert set(author_profile.affinity) == {"violation", "ambiguity", "drift"}


def test_configs_have_no_accidental_null_values() -> None:
    for relative_path in CONFIG_FILES:
        text = (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")
        paths: list[str] = list(find_null_values(yaml.safe_load(text), ""))
        unexpected = find_unexpected_nulls(paths)
        assert not unexpected, (relative_path, unexpected)


def test_every_rule_has_well_formed_remediation_options() -> None:
    for rule in load_rules():
        assert rule.remediation_options, rule.id
        for option in rule.remediation_options:
            assert option, rule.id
            assert all(step.strip() for step in option), rule.id


def test_rule_texts_are_complete_sentences() -> None:
    gates = load_settings().quality_gates
    for rule in load_rules():
        sentences: list[str] = [
            rule.statement,
            rule.how_to_omit,
            *rule.violation_scenarios,
        ]
        for sentence in sentences:
            assert sentence.endswith("."), rule.id
            assert len(sentence.split()) >= gates.min_rule_sentence_words, rule.id
    for drift in load_drift_mutations():
        assert drift.design_claim.endswith("."), drift.id
        assert len(drift.design_claim.split()) >= gates.min_drift_claim_words
