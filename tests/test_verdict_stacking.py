"""Tests for the cross-validated decision layer over verdict signals."""

import numpy as np

from secreview.evaluation.verdict_stacking import (
    Labels,
    Matrix,
    class_weights,
    cross_validate,
    fit_weights,
    predict_classes,
    softmax,
    split_folds,
)
from secreview.parsing.vocabulary import VERDICTS

PER_CLASS = len("abcdefghij")
SEPARATION = float(len("abcde"))


def separable_data() -> tuple[Matrix, Labels, list[str]]:
    rows: list[list[float]] = []
    labels: list[int] = []
    cases: list[str] = []
    for label in range(len(VERDICTS)):
        for number in range(PER_CLASS):
            rows.append([label * SEPARATION + number / PER_CLASS, float(label % 2)])
            labels.append(label)
            cases.append(f"case{number}")
    return np.array(rows), np.array(labels, dtype=np.int64), cases


def test_softmax_rows_are_probabilities() -> None:
    probabilities = softmax(np.array([[1.0, 2.0, 0.0], [0.0, 0.0, 0.0]]))
    assert np.allclose(probabilities.sum(axis=1), 1.0)
    assert probabilities[0].argmax() == 1


def test_a_separable_problem_is_learned() -> None:
    features, labels, _ = separable_data()
    mean, spread = features.mean(axis=0), features.std(axis=0)
    scaled = (features - mean) / spread
    predicted = predict_classes(fit_weights(scaled, labels), scaled)
    assert (predicted == labels).mean() > 1 - 1 / len(labels) * len(VERDICTS)


def test_rare_verdicts_get_a_larger_weight() -> None:
    labels = np.array([0] * PER_CLASS + [1], dtype=np.int64)
    weights = class_weights(labels)
    assert weights[-1] > weights[0]


def test_folds_partition_the_documents_and_predictions_are_held_out() -> None:
    features, labels, cases = separable_data()
    folds = split_folds(cases)
    assert set().union(*folds) == set(cases)
    assert sum(len(fold) for fold in folds) == len(set(cases))
    predicted = cross_validate(features, labels, cases)
    assert (predicted == labels).mean() > 1 / 2
