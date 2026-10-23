"""Typed structure of the review pipeline and evaluation configuration."""

from pydantic import BaseModel


class LlmSettings(BaseModel):
    base_url: str
    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float
    enable_thinking: bool


class GroundingSettings(BaseModel):
    min_similarity: float
    min_quote_characters: int
    duplicate_overlap: float


class EvaluationSettings(BaseModel):
    iou_threshold: float
    in_scope_types: list[str]
    scored_severities: list[str]
    false_alarm_budgets: list[float]
    review_action: str
    clarify_action: str
    fix_action: str
    bootstrap_resamples: int
    bootstrap_seed: int
    interval_level: float


class PolicyAnalysisSettings(BaseModel):
    directory: str
    requirement_prefix: str
    max_topics: int
    status_wording: dict[str, str]
    category_topics: dict[str, str]


class PilotSettings(BaseModel):
    sample_file: str
    sample_size: int
    sample_seed: int


class ReviewSettings(BaseModel):
    llm: LlmSettings
    grounding: GroundingSettings
    evaluation: EvaluationSettings
    policy_analysis: PolicyAnalysisSettings
    pilot: PilotSettings
    confidence_minimum: int
    confidence_maximum: int
    runs_directory: str
    reply_file_suffix: str
    think_close_tag: str
    schema_name: str
    metrics_file_prefix: str
    run_config_file: str
    rejection_reason: str
    unknown_requirement_reason: str
    outcomes_file_prefix: str
