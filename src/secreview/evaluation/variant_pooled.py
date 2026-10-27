"""The finalists on two unseen policies, with paired intervals of the differences."""

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

from secreview.evaluation.variant_scores import (
    Scores,
    VariantData,
    layer_probabilities,
    load_variant,
    raw_classes,
    raw_scores,
    recall_at_budgets,
    score_variant,
    shown_classes,
)
from secreview.evaluation.variant_table import (
    PRIOR_GROUPS,
    Cost,
    cascade_outcome,
    cost_per_document,
    from_probabilities,
    group_columns,
    scale_cost,
    with_wording_analysis,
)
from secreview.evaluation.verdict_stacking import Labels, Matrix, preset_columns
from secreview.review_settings import REVIEW_SETTINGS
from secreview.review_settings_models import FinalistSettings


class Outcome(BaseModel, arbitrary_types_allowed=True):
    data: VariantData
    chosen: Labels
    score: Scores


class PooledRow(BaseModel):
    label: str
    recall: float
    precision: float
    false_alarms_per_document: float
    recall_at_budgets: list[float]
    primary_interval: tuple[float, float]
    cost: Cost


def run_name(prefix: str, configuration: str) -> str:
    """Name the run of a configuration on a set of designs."""
    return f"{prefix}_{configuration}"


def join_variants(variants: list[VariantData]) -> VariantData:
    """Join the judged requirements of several runs into one training set."""
    return VariantData(
        run="+".join(item.run for item in variants),
        rows=[row for item in variants for row in item.rows],
        features=np.concatenate([item.features for item in variants]),
        gold=np.concatenate([item.gold for item in variants]),
        documents=np.concatenate([item.documents for item in variants]),
    )


def load_training(runs: list[str]) -> VariantData:
    """Load and join the runs on which a layer is trained."""
    return join_variants([load_variant(run) for run in runs])


def worded_outcome(train_runs: list[str], test_run: str) -> Outcome:
    """Choose with the layer that reads the wording judged for each requirement."""
    train = load_training([with_wording_analysis(run) for run in train_runs])
    test = load_variant(with_wording_analysis(test_run))
    probabilities = layer_probabilities(train, test, preset_columns("all"))
    chosen, score = from_probabilities(probabilities)
    return Outcome(data=test, chosen=chosen, score=score)


def probabilities_of(
    dev: VariantData,
    test: VariantData,
) -> tuple[Matrix, Matrix]:
    """Train the layer on the prior features and on the features of the model."""
    prior = layer_probabilities(dev, test, group_columns(PRIOR_GROUPS))
    full = layer_probabilities(dev, test, preset_columns("no_wording"))
    return prior, full


def layered_outcome(kind: str, train_runs: list[str], test_run: str) -> Outcome:
    """Choose with a layer that has no wording, or with the cascade."""
    train, test = load_training(train_runs), load_variant(test_run)
    prior, full = probabilities_of(train, test)
    shares = REVIEW_SETTINGS.evaluation.cascade_shares
    if kind == "prior":
        chosen, score = from_probabilities(prior)
    elif kind == "cascade":
        chosen, score = cascade_outcome(len(test.gold), prior, full, shares[0])
    else:
        chosen, score = from_probabilities(full)
    return Outcome(data=test, chosen=chosen, score=score)


def outcome_of(
    finalist: FinalistSettings,
    train_prefixes: list[str],
    test_prefix: str,
) -> Outcome:
    """Choose the classes and the scores of a finalist on one set of designs."""
    train_runs: list[str] = [
        run_name(prefix, finalist.configuration) for prefix in train_prefixes
    ]
    test_run = run_name(test_prefix, finalist.configuration)
    if finalist.kind == "raw":
        test = load_variant(test_run)
        return Outcome(data=test, chosen=raw_classes(test), score=raw_scores(test))
    if finalist.kind == "worded":
        return worded_outcome(train_runs, test_run)
    return layered_outcome(finalist.kind, train_runs, test_run)


def pool(first: Outcome, second: Outcome) -> Outcome:
    """Join the outcomes on two sets of designs into one."""
    data = VariantData(
        run=f"{first.data.run}+{second.data.run}",
        rows=[*first.data.rows, *second.data.rows],
        features=np.concatenate([first.data.features, second.data.features]),
        gold=np.concatenate([first.data.gold, second.data.gold]),
        documents=np.concatenate([first.data.documents, second.data.documents]),
    )
    return Outcome(
        data=data,
        chosen=np.concatenate([first.chosen, second.chosen]),
        score=np.concatenate([first.score, second.score]),
    )


def rows_of(outcome: Outcome, names: NDArray[np.str_]) -> NDArray[np.int64]:
    """List the rows of the drawn documents, a document once for each draw."""
    parts: list[NDArray[np.int64]] = []
    for name in names:
        parts.append(np.where(outcome.data.documents == name)[0])
    return np.concatenate(parts).astype(np.int64)


def primary_recall(outcome: Outcome, names: NDArray[np.str_]) -> float:
    """Compute the recall at the primary budget on the drawn documents."""
    index = rows_of(outcome, names)
    gold = np.isin(outcome.data.gold[index], shown_classes())
    values = recall_at_budgets(gold, outcome.score[index], len(names))
    return values[REVIEW_SETTINGS.evaluation.primary_budget_position]


def draws_over(names: NDArray[np.str_]) -> list[NDArray[np.str_]]:
    """Draw documents with replacement, the same draws for every variant."""
    settings = REVIEW_SETTINGS.evaluation
    generator = np.random.default_rng(settings.bootstrap_seed)
    resamples: list[NDArray[np.str_]] = []
    for _ in range(settings.table_resamples):
        resamples.append(generator.choice(names, size=len(names), replace=True))
    return resamples


def draws(outcomes: list[Outcome]) -> list[NDArray[np.str_]]:
    """Draw the same documents with replacement for every resample."""
    names = np.unique(np.concatenate([item.data.documents for item in outcomes]))
    return draws_over(names)


def interval(values: list[float]) -> tuple[float, float]:
    """Return the interval of the resampled values."""
    tail = (1.0 - REVIEW_SETTINGS.evaluation.interval_level) / 2.0
    low, high = np.quantile(values, [tail, 1.0 - tail])
    return float(low), float(high)


def pooled_row(
    label: str,
    outcome: Outcome,
    cost: Cost,
    values: list[float],
) -> PooledRow:
    """Score an outcome and attach the interval of its primary recall."""
    index = np.arange(len(outcome.data.gold))
    metrics = score_variant(outcome.data, outcome.chosen, outcome.score, index)
    return PooledRow(
        label=label,
        recall=metrics.recall,
        precision=metrics.precision,
        false_alarms_per_document=metrics.false_alarms_per_document,
        recall_at_budgets=metrics.recall_at_budgets,
        primary_interval=interval(values),
        cost=cost,
    )


def finalist_cost(finalist: FinalistSettings, test_prefix: str) -> Cost:
    """Measure the cost per document of a finalist on one set of designs."""
    cost = cost_per_document(run_name(test_prefix, finalist.configuration))
    if finalist.kind == "prior":
        return scale_cost(cost, 0.0)
    if finalist.kind == "cascade":
        return scale_cost(cost, REVIEW_SETTINGS.evaluation.cascade_shares[0])
    return cost


def difference_interval(
    left: list[float],
    right: list[float],
) -> tuple[float, float, float]:
    """Return the mean difference and its interval over the same resamples."""
    gaps: list[float] = []
    for first, second in zip(left, right, strict=True):
        gaps.append(first - second)
    low, high = interval(gaps)
    return float(np.mean(gaps)), low, high
