"""Frozen configuration of a baseline run, stored next to its records."""

from pydantic import BaseModel

from secreview.agents.baseline import ReviewVariant
from secreview.agents.policy_requirements import digest_analysis_set
from secreview.agents.prompts import build_system_prompt
from secreview.agents.run_store import run_directory
from secreview.parsing.findings import build_reply_schema
from secreview.review_settings import REVIEW_SETTINGS


class RunConfig(BaseModel):
    variant: ReviewVariant
    system_prompt: str
    response_schema: dict[str, object]
    policy_analysis_digest: str
    model: str
    temperature: float
    max_tokens: int
    enable_thinking: bool
    min_similarity: float
    min_quote_characters: int
    duplicate_overlap: float
    iou_threshold: float


def build_run_config(variant: ReviewVariant) -> RunConfig:
    """Collect the prompt, schema and settings that shape a run's results."""
    llm = REVIEW_SETTINGS.llm
    grounding = REVIEW_SETTINGS.grounding
    return RunConfig(
        variant=variant,
        system_prompt=build_system_prompt(
            variant.use_topics,
            variant.ask_for_silence,
            variant.allow_compliant,
        ),
        response_schema=build_reply_schema(
            variant.use_topics,
            [],
            variant.allow_compliant,
        ),
        policy_analysis_digest=digest_analysis_set(variant.policy_analysis),
        model=llm.model,
        temperature=llm.temperature,
        max_tokens=llm.max_tokens,
        enable_thinking=llm.enable_thinking,
        min_similarity=grounding.min_similarity,
        min_quote_characters=grounding.min_quote_characters,
        duplicate_overlap=grounding.duplicate_overlap,
        iou_threshold=REVIEW_SETTINGS.evaluation.iou_threshold,
    )


def save_run_config(run_name: str, variant: ReviewVariant) -> None:
    """Store the run configuration, refusing to mix two configurations in a run."""
    path = run_directory(run_name) / REVIEW_SETTINGS.run_config_file
    config = build_run_config(variant)
    if path.exists():
        stored = RunConfig.model_validate_json(path.read_text(encoding="utf-8"))
        if stored != config:
            raise ValueError(f"run {run_name} was started with another configuration")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(config.model_dump_json(indent=2), encoding="utf-8")
