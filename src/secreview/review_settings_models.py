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
    quote_coverage: float
    excluded_subtypes: list[str]
    tolerant_credit: float
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


class DenseModelSettings(BaseModel):
    name: str
    model_id: str
    query_prefix: str


class RetrievalSettings(BaseModel):
    dense_models: list[DenseModelSettings]
    device: str
    encode_batch_size: int
    reranker_model_id: str
    rerank_depth: int
    rerank_name: str
    rerank_joiner: str
    windows: list[int]
    heading_options: list[bool]
    cutoffs: list[int]
    context_budgets: list[int]
    rrf_constant: int
    list_marker_pattern: str
    sentence_boundary_pattern: str
    heading_marker: str
    results_directory: str
    ranking_depth: int
    rankings_file_prefix: str
    bm25_name: str
    dense_name: str
    hybrid_name: str


class VerdictSettings(BaseModel):
    runs_directory: str
    analysis_set: str
    ranker: str
    window: int
    candidates: int
    top_logprobs: int
    max_tokens: int
    schema_name: str
    run_config_file: str
    metrics_file_prefix: str
    no_severity: str
    stacking_folds: int
    stacking_steps: int
    stacking_rate: float
    stacking_l2: float
    stacking_class_power: float
    stacking_word_length: int
    stacking_fine: bool
    probability_floor: float


class ReviewSettings(BaseModel):
    llm: LlmSettings
    grounding: GroundingSettings
    evaluation: EvaluationSettings
    policy_analysis: PolicyAnalysisSettings
    pilot: PilotSettings
    retrieval: RetrievalSettings
    verdict: VerdictSettings
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
