"""Tests for the candidate pairs and the marking of contradictory requirements."""

import numpy as np

from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.pair_contradictions import (
    ScoredPair,
    candidate_pairs,
    mark_pairs,
)

POLICY_VERSION = "v5"
NEAREST = 1


def test_the_nearest_sentences_of_each_sentence_form_the_candidate_pairs() -> None:
    vectors = np.array([[1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])
    vectors = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    pairs = candidate_pairs(vectors, NEAREST)
    assert (0, 1) in pairs
    assert all(first < second for first, second in pairs)


def test_only_pairs_above_the_threshold_make_their_requirements_contradictory() -> None:
    analysis = build_oracle_analysis(POLICY_VERSION)
    before: list[str] = [item.wording for item in analysis.requirements]
    marked = mark_pairs(
        analysis,
        [
            ScoredPair(first=0, second=1, score=1.0),
            ScoredPair(first=2, second=len(before) - 1, score=0.0),
        ],
    )
    after: list[str] = [item.wording for item in marked.requirements]
    assert after[:2] == ["contradictory", "contradictory"]
    assert after[2:] == before[2:]
