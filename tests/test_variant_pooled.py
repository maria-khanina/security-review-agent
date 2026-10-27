"""Tests for the pooled comparison of the finalists."""

import numpy as np

from secreview.evaluation.variant_pooled import (
    Outcome,
    difference_interval,
    draws,
    join_variants,
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
    assert len(joined.score) == len(joined.chosen) == len(joined.data.documents)


def test_every_resample_draws_as_many_documents_as_there_are() -> None:
    names: list[str] = ["a", "b", "c", "d"]
    resamples = draws([make_outcome(names)])
    assert len(resamples) == REVIEW_SETTINGS.evaluation.table_resamples
    assert all(len(drawn) == len(names) for drawn in resamples)


def test_recall_of_a_resample_counts_a_drawn_document_once_per_draw() -> None:
    outcome = make_outcome(["a", "b"])
    names = np.array(["a", "a"])
    assert primary_recall(outcome, names) == 1.0


def test_the_difference_of_equal_series_is_zero() -> None:
    series: list[float] = list(np.linspace(0.0, 1.0, len("abcd")))
    mean, low, high = difference_interval(series, series)
    assert mean == low == high == 0.0


def test_joining_variants_concatenates_features_and_documents() -> None:
    joined = join_variants(
        [make_outcome(["a", "b"]).data, make_outcome(["c"]).data]
    )
    assert joined.features.shape == (len(joined.documents), 2)
    assert list(joined.documents) == ["a", "b", "c"]
    assert len(joined.gold) == len(joined.documents)
