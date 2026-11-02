"""Costs, helpers and the cascade shared by the comparisons of the variants."""

import shutil

import numpy as np
from pydantic import BaseModel

from secreview.agents.verdict_run_config import (
    load_run_config,
    with_analysis,
    write_run_config,
)
from secreview.agents.verdict_store import verdict_run_directory
from secreview.evaluation.variant_scores import scores_of
from secreview.evaluation.verdict_cost import measured_run_cost
from secreview.evaluation.verdict_stacking import FEATURE_GROUPS, Labels, Matrix
from secreview.review_settings import REVIEW_SETTINGS

PRIOR_GROUPS = ("overlap", "length", "topics")


class Cost(BaseModel):
    calls: float
    prompt_tokens: float
    seconds: float


def cost_per_document(run: str) -> Cost:
    """Measure the calls, the prompt tokens and the seconds per document."""
    measured = measured_run_cost(run)
    documents = measured.documents
    return Cost(
        calls=measured.calls / documents,
        prompt_tokens=measured.prompt_tokens / documents,
        seconds=measured.seconds / documents,
    )


def scale_cost(cost: Cost, share: float) -> Cost:
    """Charge a share of a cost."""
    return Cost(
        calls=cost.calls * share,
        prompt_tokens=cost.prompt_tokens * share,
        seconds=cost.seconds * share,
    )


def with_wording_analysis(run: str) -> str:
    """Copy a run whose policy analysis is the one with the wording per requirement."""
    settings = REVIEW_SETTINGS.verdict
    name = settings.name_separator.join([run, settings.wording_suffix])
    target = verdict_run_directory(name)
    if not target.exists():
        shutil.copytree(verdict_run_directory(run), target)
        config = with_analysis(load_run_config(run), settings.wording_analysis_set)
        write_run_config(name, config)
    return name


def from_probabilities(probabilities: Matrix) -> tuple[Labels, np.ndarray]:
    """Turn class probabilities into chosen classes and scores of being shown."""
    return probabilities.argmax(axis=1).astype(np.int64), scores_of(probabilities)


def group_columns(groups: tuple[str, ...]) -> list[int]:
    """List the feature columns of the named groups."""
    columns: list[int] = []
    start = 0
    for name, width in FEATURE_GROUPS:
        if name in groups:
            columns.extend(range(start, start + width))
        start += width
    return columns


def cascade_outcome(
    pairs: int,
    prior: Matrix,
    full: Matrix,
    share: float,
) -> tuple[Labels, np.ndarray]:
    """Choose classes and scores when the least sure share of pairs gets the model."""
    order = np.argsort(prior.max(axis=1))
    sent = np.zeros(pairs, dtype=bool)
    sent[order[: int(round(share * pairs))]] = True
    return from_probabilities(np.where(sent[:, None], full, prior))
