"""Scores of one variant of the pipeline on the pairs of one set of designs."""

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel

from secreview.agents.verdict_store import load_verdict_record
from secreview.evaluation.verdict_stack_run import Row, run_rows
from secreview.evaluation.verdict_stacking import (
    Labels,
    Matrix,
    class_verdicts,
    fit_weights,
    predict_probabilities,
    standardize,
)
from secreview.parsing.vocabulary import VERDICTS
from secreview.review_settings import REVIEW_SETTINGS

Flags = NDArray[np.bool_]
Scores = NDArray[np.float64]


class VariantData(BaseModel, arbitrary_types_allowed=True):
    run: str
    rows: list[Row]
    features: Matrix
    gold: Labels
    documents: NDArray[np.str_]


class VariantMetrics(BaseModel):
    recall: float
    precision: float
    false_alarms_per_document: float
    accuracy: float
    tolerant_accuracy: float
    recall_at_budgets: list[float]


def load_variant(run: str) -> VariantData:
    """Load the judged requirements of a run with their features and gold."""
    rows = run_rows(run)
    return VariantData(
        run=run,
        rows=rows,
        features=np.array([row.features for row in rows], dtype=np.float64),
        gold=np.array([row.gold for row in rows], dtype=np.int64),
        documents=np.array([row.case_id for row in rows]),
    )


def shown_classes() -> list[int]:
    """List the classes that the reviewer sees: violated and unclear."""
    verdicts = class_verdicts()
    return [verdicts.index("violated"), verdicts.index("unclear")]


def raw_classes(data: VariantData) -> Labels:
    """Return the class that the model chose for every judged requirement."""
    verdicts = class_verdicts()
    stored: dict[str, dict[str, str]] = {}
    chosen: list[int] = []
    for row in data.rows:
        if row.case_id not in stored:
            records = load_verdict_record(data.run, row.case_id).records
            stored[row.case_id] = {
                item.requirement_id: str(item.verdict) for item in records
            }
        chosen.append(verdicts.index(stored[row.case_id][row.requirement_id]))
    return np.array(chosen, dtype=np.int64)


def raw_scores(data: VariantData) -> Scores:
    """Return the probability that the model gives to violated or unclear."""
    probabilities = np.exp(data.features[:, : len(VERDICTS)])
    columns: list[int] = [VERDICTS.index("violated"), VERDICTS.index("unclear")]
    return probabilities[:, columns].sum(axis=1)


def layer_probabilities(
    train: VariantData,
    test: VariantData,
    columns: list[int],
) -> Matrix:
    """Train the decision layer on one run and give the class probabilities."""
    scaled_train, scaled_test = standardize(
        train.features[:, columns], test.features[:, columns]
    )
    weights = fit_weights(scaled_train, train.gold, len(class_verdicts()))
    return predict_probabilities(weights, scaled_test)


def scores_of(probabilities: Matrix) -> Scores:
    """Return the probability of being shown for every row."""
    return probabilities[:, shown_classes()].sum(axis=1)


def recall_at_budgets(gold: Flags, score: Scores, documents: int) -> list[float]:
    """Read the recall where the false alarms reach each budget per document."""
    order = np.argsort(-score)
    false_alarms = np.cumsum(~gold[order])
    hits = np.cumsum(gold[order])
    recalls: list[float] = []
    for budget in REVIEW_SETTINGS.evaluation.table_budgets:
        within = false_alarms <= budget * documents
        reached = float(hits[within][-1]) if within.any() else 0.0
        recalls.append(reached / max(int(gold.sum()), 1))
    return recalls


def tolerant_accuracy(
    gold: Labels,
    chosen: Labels,
    shown: Flags,
    wanted: Flags,
) -> float:
    """Count right verdicts, any pair of dropped verdicts and half of shown swaps."""
    right = (gold == chosen) | (~wanted & ~shown)
    swapped = wanted & shown & (gold != chosen)
    credit = REVIEW_SETTINGS.evaluation.tolerant_credit
    return float((right.sum() + credit * swapped.sum()) / len(gold))


def score_variant(
    data: VariantData,
    chosen: Labels,
    score: Scores,
    index: NDArray[np.int64],
) -> VariantMetrics:
    """Compute the metrics of the chosen classes on a subset of the rows."""
    gold, picked, ranking = data.gold[index], chosen[index], score[index]
    wanted = np.isin(gold, shown_classes())
    shown = np.isin(picked, shown_classes())
    documents = max(len(set(data.documents[index])), 1)
    hits = float((shown & wanted).sum())
    return VariantMetrics(
        recall=hits / max(wanted.sum(), 1),
        precision=hits / max(shown.sum(), 1),
        false_alarms_per_document=float((shown & ~wanted).sum()) / documents,
        accuracy=float((gold == picked).mean()),
        tolerant_accuracy=tolerant_accuracy(gold, picked, shown, wanted),
        recall_at_budgets=recall_at_budgets(wanted, ranking, documents),
    )


def resample_index(
    data: VariantData,
    generator: np.random.Generator,
) -> NDArray[np.int64]:
    """Draw the documents with replacement and list the rows of the drawn ones."""
    names = np.unique(data.documents)
    drawn = generator.choice(names, size=len(names), replace=True)
    return np.concatenate([np.where(data.documents == name)[0] for name in drawn])


def metric_on_resample(
    data: VariantData,
    chosen: Labels,
    score: Scores,
    metric: str,
    generator: np.random.Generator,
) -> float:
    """Compute one metric on a resample of the documents."""
    index = resample_index(data, generator)
    return float(getattr(score_variant(data, chosen, score, index), metric))


def interval_of(
    data: VariantData,
    chosen: Labels,
    score: Scores,
    metric: str,
) -> tuple[float, float]:
    """Return the interval of a metric over resamples of the documents."""
    settings = REVIEW_SETTINGS.evaluation
    generator = np.random.default_rng(settings.bootstrap_seed)
    values: list[float] = [
        metric_on_resample(data, chosen, score, metric, generator)
        for _ in range(settings.table_resamples)
    ]
    tail = (1.0 - settings.interval_level) / 2.0
    low, high = np.quantile(values, [tail, 1.0 - tail])
    return float(low), float(high)
