"""Domain models shared by the dataset generator.

They describe the security rule catalog, the fictional company and its service
documented services, author profiles, and the planted flaws that make up a test case.
"""

from pydantic import BaseModel, Field, model_validator

from secreview.datagen.settings import load_settings

CHECK_SCOPES = {"design", "impl", "both"}
IMPLEMENTATION_ONLY = "impl"
IMPLEMENTATION_SCOPES = {"impl", "both"}
CWE_PREFIX = "CWE-"


def check_scope_and_checker(rule: "Rule") -> None:
    """Ensure the check scope is known and implementation rules have a checker."""
    if rule.check_scope not in CHECK_SCOPES:
        raise ValueError(f"{rule.id}: bad check scope {rule.check_scope}")
    if rule.check_scope in IMPLEMENTATION_SCOPES and not rule.implementation_check:
        raise ValueError(f"{rule.id}: rule needs implementation_check")


def check_scenarios_and_scale(rule: "Rule") -> None:
    """Ensure design rules have violation scenarios and severity is on scale."""
    if rule.check_scope != IMPLEMENTATION_ONLY and not rule.violation_scenarios:
        raise ValueError(f"{rule.id}: design rule needs violation scenarios")
    if rule.base_severity > load_settings().max_base_severity:
        raise ValueError(f"{rule.id}: base severity above the scale")


def check_cwe_ids(rule: "Rule") -> None:
    """Ensure every CWE id has the expected prefix."""
    for cwe_id in rule.cwe_ids:
        if not cwe_id.startswith(CWE_PREFIX):
            raise ValueError(f"{rule.id}: bad CWE id {cwe_id}")


class AppliesTo(BaseModel):
    kind: list[str] = Field(default_factory=list)
    data: list[str] = Field(default_factory=list)
    exposure: list[str] = Field(default_factory=list)
    requests: bool = False

    def matches(
        self,
        kind: str,
        data_classes: set[str],
        exposure: str,
        accepts_requests: bool,
    ) -> bool:
        """Tell whether a component of this kind falls under the rule."""
        if self.kind and kind not in self.kind:
            return False
        if self.data and not data_classes & set(self.data):
            return False
        if self.requests and not accepts_requests:
            return False
        return not self.exposure or exposure in self.exposure


class Rule(BaseModel):
    id: str
    title: str
    statement: str
    categories: list[str]
    applies_to: AppliesTo
    check_scope: str
    base_severity: int = Field(ge=1)
    cwe_ids: list[str]
    violation_scenarios: list[str]
    how_to_omit: str
    remediation_options: list[list[str]]
    implementation_check: str | None
    ambiguity_ok: bool

    @model_validator(mode="after")
    def validate_consistency(self) -> "Rule":
        """Reject rules whose scope, checker, scenarios or CWE ids disagree."""
        check_scope_and_checker(self)
        check_scenarios_and_scale(self)
        check_cwe_ids(self)
        return self


class RuleCoupling(BaseModel):
    when_flawed: str
    suppress: list[str]
    reason: str


class DocumentedServiceDefinition(BaseModel):
    id: str
    implementation_format: str
    components: list[str]
    data: list[str]
    exposure: str
    accepts_requests: bool
    summary: str


class SplitSettings(BaseModel):
    dataset_size: int
    clean_cases: int
    holdout_documented_services: list[str]
    implementation_share: dict[str, float]


class CompanyConfig(BaseModel):
    vocabulary: dict[str, list[str]]
    documented_services: list[DocumentedServiceDefinition]
    extension_documented_services: list[DocumentedServiceDefinition]
    split: SplitSettings


class ComponentFact(BaseModel):
    kind: str
    name: str


class FlowFact(BaseModel):
    source: str
    target: str
    data: str


class ArchitectureFacts(BaseModel):
    components: list[ComponentFact]
    flows: list[FlowFact]


class AuthorProfile(BaseModel):
    id: str
    summary: str
    structure: str
    english: str
    hedging: str
    terminology: str
    staleness: str
    length_words: list[int]
    typical_gaps: list[str]
    affinity: dict[str, float]


class NoiseProfile(BaseModel):
    typo_rate: float
    markdown_breakage: str
    dangling_references: int
    tbd_markers: int


class Flaw(BaseModel):
    flaw_id: str
    type: str
    rule_id: str | None
    component: str
    data_class: str
    exposure: str
    severity: str
    cwe: list[str]
    manifest: str
    implementation_mutation: str | None
    implementation_anchor: str | None
    remediation_options: list[list[str]]
    clarification_needed: str | None
    instruction: str


class Case(BaseModel):
    case_id: str
    documented_service: str
    implementation_format: str
    split: str
    policy_version: str
    author_profile: str
    noise: NoiseProfile
    flaws: list[Flaw]
    required_rules: list[str]


class PlannedCase(BaseModel):
    case: Case
    defective: bool
