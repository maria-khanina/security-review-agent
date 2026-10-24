"""Tests for the cross-validated decision layer over verdict signals."""

import numpy as np

from secreview.evaluation.verdict_stacking import (
    Labels,
    Matrix,
    class_weights,
    content_words,
    cross_validate,
    fit_weights,
    overlap_share,
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
    weights = fit_weights(scaled, labels, len(VERDICTS))
    predicted = predict_classes(weights, scaled)
    assert (predicted == labels).mean() > 1 - 1 / len(labels) * len(VERDICTS)


def test_rare_verdicts_get_a_larger_weight() -> None:
    labels = np.array([0] * PER_CLASS + [1], dtype=np.int64)
    weights = class_weights(labels, len(VERDICTS))
    assert weights[-1] > weights[0]


def test_folds_partition_the_documents_and_predictions_are_held_out() -> None:
    features, labels, cases = separable_data()
    folds = split_folds(cases)
    assert set().union(*folds) == set(cases)
    assert sum(len(fold) for fold in folds) == len(set(cases))
    probabilities = cross_validate(features, labels, cases, len(VERDICTS))
    predicted = probabilities.argmax(axis=1)
    assert (predicted == labels).mean() > 1 / 2


def test_word_overlap_counts_only_content_words_of_the_requirement() -> None:
    requirement = "Passwords must be hashed with argon2id or bcrypt"
    assert overlap_share(requirement, "We hash passwords with argon2id") > 0.0
    assert overlap_share(requirement, "Nothing relevant here") == 0.0
    assert overlap_share("", "anything") == 0.0
    assert "bcrypt" in content_words(requirement)
    assert "be" not in content_words(requirement)
