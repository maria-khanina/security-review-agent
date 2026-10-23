"""Typed structure of the dataset generator's configuration values."""

from pydantic import BaseModel


class PathSettings(BaseModel):
    raw_directory: str
    processed_directory: str
    policies_directory: str
    configs_directory: str
    rules_file: str
    policy_maps_file: str
    rule_couplings_file: str


class NoiseSettings(BaseModel):
    low_typo_english: list[str]
    low_typo_rates: list[float]
    high_typo_rates: list[float]
    heavy_markdown_structures: list[str]
    heavy_markdown_choices: list[str]
    light_markdown_choices: list[str]
    no_staleness_label: str
    stale_reference_choices: list[int]
    fresh_reference_choices: list[int]
    high_hedging_label: str
    high_hedging_marker_choices: list[int]
    default_marker_choices: list[int]


class OpenApiSettings(BaseModel):
    openapi_version: str
    api_version: str
    server_url: str
    plaintext_server_url: str
    string_max_length: int
    path_parameter_max_length: int
    query_parameter_max_length: int
    pii_parameter_max_length: int
    base64_max_length: int
    pan_max_length: int
    integer_minimum: int
    create_status: str
    default_success_status: str
    error_statuses: list[str]
    rate_limit_status: str
    debug_path: str
    admin_path: str
    api_key_header: str
    bearer_format: str
    hardcoded_secret: str


class TerraformSettings(BaseModel):
    required_version: str
    engine: str
    instance_class: str
    allocated_storage: int
    subnet_group: str
    parameter_group_family: str
    backup_retention_period: int
    kafka_version: str
    broker_node_count: int
    key_deletion_window_days: int
    short_retention_days: int
    minimum_audit_retention_days: int
    hardcoded_password: str
    public_cidr: str
    bucket_prefix: str
    bucket_suffix: str
    overbroad_wildcard: str


class QualityGates(BaseModel):
    min_design_checkable_rules: int
    min_implementation_checkable_rules: int
    min_drift_mutations: int
    min_applicable_rules_per_documented_service: int
    min_violable_rules_per_policy_version: int
    min_flaws_per_type: int
    min_non_clear_flaw_share: float
    min_high_or_critical_flaws: int
    max_flaws_per_case: int
    min_required_rules_for_clean_case: int
    min_rule_sentence_words: int
    min_drift_claim_words: int


class GenerationSettings(BaseModel):
    seed: int
    flaw_seed_offset: int
    quote_preview_length: int
    max_base_severity: int
    policy_versions: list[str]
    flaw_count_weights: dict[int, float]
    non_clear_flaw_share: float
    data_sensitivity_order: list[str]
    secret_pattern: str
    yaml_line_width: int
    mutation_conflict_groups: dict[str, str]
    functional_sections: list[str]
    quality_gates: QualityGates
    paths: PathSettings
    noise: NoiseSettings
    openapi: OpenApiSettings
    terraform: TerraformSettings
