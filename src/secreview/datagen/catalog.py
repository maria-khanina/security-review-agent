"""Cached loaders for the static YAML catalogs of the dataset generator."""

from functools import cache
from pathlib import Path

from pydantic import BaseModel, TypeAdapter
import yaml

from secreview.datagen.models import (
    ArchitectureFacts,
    AuthorProfile,
    CompanyConfig,
    DocumentedServiceDefinition,
    Rule,
    RuleCoupling,
)
from secreview.datagen.settings import load_settings, project_path
from secreview.datagen.severity import Severity


class RulesFile(BaseModel):
    rules: list[Rule]


class CouplingsFile(BaseModel):
    couplings: list[RuleCoupling]


class AuthorProfilesFile(BaseModel):
    author_profiles: list[AuthorProfile]


def config_path(file_name: str) -> Path:
    """Locate a file inside the configs directory."""
    return project_path(load_settings().paths.configs_directory) / file_name


def read_text(path: Path) -> str:
    """Read a UTF-8 text file."""
    return path.read_text(encoding="utf-8")


@cache
def load_rules() -> list[Rule]:
    """Load the atomic security rule catalog."""
    text = read_text(project_path(load_settings().paths.rules_file))
    return RulesFile.model_validate(yaml.safe_load(text)).rules


@cache
def load_suppressed_rules() -> dict[str, set[str]]:
    """Map each rule to the rules whose satisfied statement its flaw invalidates."""
    text = read_text(project_path(load_settings().paths.rule_couplings_file))
    couplings = CouplingsFile.model_validate(yaml.safe_load(text)).couplings
    suppressed: dict[str, set[str]] = {}
    for coupling in couplings:
        suppressed.setdefault(coupling.when_flawed, set()).update(coupling.suppress)
    return suppressed


@cache
def load_rule_couplings() -> list[RuleCoupling]:
    """Load the table of rules that cannot be stated as satisfied beside a flaw."""
    text = read_text(project_path(load_settings().paths.rule_couplings_file))
    return CouplingsFile.model_validate(yaml.safe_load(text)).couplings


@cache
def load_company() -> CompanyConfig:
    """Load the fictional company, its service documented services and the split."""
    text = read_text(config_path("company.yaml"))
    return CompanyConfig.model_validate(yaml.safe_load(text))


def load_all_documented_services() -> list[DocumentedServiceDefinition]:
    """List the core documented services followed by the extension ones."""
    company = load_company()
    return company.documented_services + company.extension_documented_services


@cache
def load_architecture() -> dict[str, ArchitectureFacts]:
    """Load components and data flows of every service documented service."""
    text = read_text(config_path("architecture.yaml"))
    adapter = TypeAdapter(dict[str, ArchitectureFacts])
    return adapter.validate_python(yaml.safe_load(text))


@cache
def load_author_profiles() -> dict[str, AuthorProfile]:
    """Load the design-document author profiles keyed by profile id."""
    text = read_text(config_path("author_profiles.yaml"))
    profiles_file = AuthorProfilesFile.model_validate(yaml.safe_load(text))
    author_profiles = profiles_file.author_profiles
    return {author_profile.id: author_profile for author_profile in author_profiles}


@cache
def load_severity() -> Severity:
    """Load the severity formula parameters."""
    text = read_text(config_path("severity.yaml"))
    return Severity.model_validate(yaml.safe_load(text))
