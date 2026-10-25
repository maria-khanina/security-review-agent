"""Tests for the pooled comparison of the finalists."""

import numpy as np

from secreview.evaluation.variant_pooled import (
    Outcome,
    difference_interval,
    draws,
    pool,
    primary_recall,
)
from secreview.evaluation.variant_scores import VariantData
from secreview.evaluation.verdict_stacking import class_verdicts
from secreview.review_settings import REVIEW_SETTINGS


def make_outcome(names: list[str]) -> Outcome:
    violated = class_verdicts().index("violated")
    gold = np.full(len(names), violated, dtype=np.int64)
    data = VariantData(
        run="run",
        rows=[],
        features=np.zeros((len(names), 2)),
        gold=gold,
        documents=np.array(names),
    )
    score = np.linspace(1.0, 0.0, len(names))
    return Outcome(data=data, chosen=gold, score=score)


def test_pooling_joins_the_rows_of_both_sets() -> None:
    joined = pool(make_outcome(["a", "b"]), make_outcome(["c"]))
    assert list(joined.data.documents) == ["a", "b", "c"]
    assert len(joined.score) == len(joined.chosen) == 3


def test_every_resample_draws_as_many_documents_as_there_are() -> None:
    outcome = make_outcome(["a", "b", "c", "d"])
    resamples = draws([outcome])
    assert len(resamples) == REVIEW_SETTINGS.evaluation.table_resamples
    assert all(len(names) == 4 for names in resamples)


def test_recall_of_a_resample_counts_a_drawn_document_once_per_draw() -> None:
    outcome = make_outcome(["a", "b"])
    names = np.array(["a", "a"])
    assert primary_recall(outcome, names) == 1.0


def test_the_difference_of_equal_series_is_zero() -> None:
    series = [0.5, 0.6, 0.7, 0.8]
    mean, low, high = difference_interval(series, series)
    assert mean == low == high == 0.0
