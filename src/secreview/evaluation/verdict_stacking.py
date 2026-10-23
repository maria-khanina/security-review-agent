"""A calibrated decision layer over the signals of a verdict run.

The model gives a verdict with token probabilities; a verifier gives the
probability of yes. A multinomial logistic regression learns from gold
verdicts how to combine these signals with the wording of the requirement
into the final verdict. It is scored with cross-validation over documents, so
no document of the same service is judged by a model that saw it.
"""

import math

import numpy as np
from numpy.typing import NDArray

from secreview.agents.policy_requirements import PolicyRequirement
from secreview.agents.verdict_review import RequirementRecord
from secreview.parsing.vocabulary import (
    EVIDENCE_VERDICTS,
    TOPICS,
    VERDICTS,
    WORDINGS,
)
from secreview.retrieval.rankers import tokenize
from secreview.review_settings import REVIEW_SETTINGS

Matrix = NDArray[np.float64]
Labels = NDArray[np.int64]
NEUTRAL = 1 / 2


def log_probability(record: RequirementRecord, verdict: str) -> float:
    """Return the log of the probability of a verdict, floored for stability."""
    floor = REVIEW_SETTINGS.verdict.probability_floor
    return math.log(max(record.probabilities.get(verdict, 0.0), floor))


def content_words(text: str) -> set[str]:
    """Collect the distinct words of a text that are long enough to carry meaning."""
    floor = REVIEW_SETTINGS.verdict.stacking_word_length
    return {word for word in tokenize(text) if len(word) > floor}


def overlap_share(requirement: str, other: str) -> float:
    """Share of the content words of the requirement that the other text contains."""
    words = content_words(requirement)
    return len(words & content_words(other)) / len(words) if words else 0.0


def build_features(
    record: RequirementRecord,
    requirement: PolicyRequirement,
    fragments: list[str],
) -> list[float]:
    """Describe a verdict by its signals, the wording and the word overlap."""
    features: list[float] = [log_probability(record, verdict) for verdict in VERDICTS]
    features.append(NEUTRAL if record.confidence is None else record.confidence)
    features.append(float(record.design_span is not None))
    features.extend(float(requirement.wording == wording) for wording in WORDINGS)
    shares: list[float] = [overlap_share(requirement.quote, text) for text in fragments]
    features.append(max(shares, default=0.0))
    features.append(overlap_share(requirement.quote, record.quote))
    features.append(math.log1p(len(content_words(requirement.quote))))
    features.extend(float(topic in requirement.topics) for topic in TOPICS)
    return features


def standardize(train: Matrix, other: Matrix) -> tuple[Matrix, Matrix]:
    """Scale both matrices with the mean and spread of the training one."""
    mean = train.mean(axis=0)
    spread = train.std(axis=0)
    spread[spread == 0.0] = 1.0
    return (train - mean) / spread, (other - mean) / spread


def softmax(scores: Matrix) -> Matrix:
    """Turn scores per class into probabilities, row by row."""
    shifted = scores - scores.max(axis=1, keepdims=True)
    exponents = np.exp(shifted)
    return exponents / exponents.sum(axis=1, keepdims=True)


def add_bias(features: Matrix) -> Matrix:
    """Append a constant column for the intercept."""
    return np.hstack([features, np.ones((features.shape[0], 1))])


def class_weights(labels: Labels) -> Matrix:
    """Weight every row so that rare verdicts count more in the loss."""
    counts = np.bincount(labels, minlength=len(VERDICTS)).astype(np.float64)
    counts[counts == 0.0] = 1.0
    balance = len(labels) / (len(VERDICTS) * counts)
    return balance[labels] ** REVIEW_SETTINGS.verdict.stacking_class_power


def fit_weights(features: Matrix, labels: Labels) -> Matrix:
    """Fit a class-weighted multinomial logistic regression with L2 penalty."""
    settings = REVIEW_SETTINGS.verdict
    inputs = add_bias(features)
    targets = np.eye(len(VERDICTS))[labels]
    importance = class_weights(labels)[:, None]
    weights = np.zeros((inputs.shape[1], len(VERDICTS)))
    for _ in range(settings.stacking_steps):
        error = (softmax(inputs @ weights) - targets) * importance
        gradient = inputs.T @ error / len(labels)
        weights -= settings.stacking_rate * (gradient + settings.stacking_l2 * weights)
    return weights


def predict_classes(weights: Matrix, features: Matrix) -> Labels:
    """Return the index of the most probable verdict for every row."""
    return np.argmax(add_bias(features) @ weights, axis=1).astype(np.int64)


def split_folds(groups: list[str]) -> list[set[str]]:
    """Deal the groups of documents into folds, the same way on every run."""
    ordered = sorted(set(groups))
    count = REVIEW_SETTINGS.verdict.stacking_folds
    folds: list[set[str]] = [set() for _ in range(count)]
    for number, group in enumerate(ordered):
        folds[number % len(folds)].add(group)
    return folds


def cross_validate(
    features: Matrix,
    labels: Labels,
    groups: list[str],
) -> Labels:
    """Predict every row with a model trained on the other folds."""
    predictions = np.zeros(len(labels), dtype=np.int64)
    for fold in split_folds(groups):
        held_out = np.array([group in fold for group in groups])
        train, test = standardize(features[~held_out], features[held_out])
        weights = fit_weights(train, labels[~held_out])
        predictions[held_out] = predict_classes(weights, test)
    return predictions


def keeps_evidence(verdict: str, record: RequirementRecord) -> bool:
    """Tell whether the quote of a record still fits a relabelled verdict."""
    return verdict in EVIDENCE_VERDICTS and verdict == record.verdict
