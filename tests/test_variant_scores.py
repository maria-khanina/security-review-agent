"""Tests for the scores of a variant of the pipeline."""

import numpy as np

from secreview.evaluation.variant_scores import (
    recall_at_budgets,
    shown_classes,
    tolerant_accuracy,
)
from secreview.evaluation.verdict_stacking import class_verdicts
from secreview.review_settings import REVIEW_SETTINGS

DOCUMENTS = len("ab")


def test_the_shown_classes_are_violated_and_unclear() -> None:
    verdicts = class_verdicts()
    assert {verdicts[index] for index in shown_classes()} == {"violated", "unclear"}


def test_recall_is_read_where_the_false_alarms_reach_each_budget() -> None:
    wanted = np.array([True, False, True, False, False, True, False])
    score = np.arange(len(wanted), 0, -1).astype(np.float64)
    recalls = recall_at_budgets(wanted, score, DOCUMENTS)
    budgets = REVIEW_SETTINGS.evaluation.table_budgets
    assert len(recalls) == len(budgets)
    assert recalls == sorted(recalls)
    early = int(wanted[: wanted.size // 2].sum()) / wanted.sum()
    assert recalls[0] == early
    assert recalls[-1] == 1.0


def test_dropped_verdicts_agree_and_a_shown_swap_counts_half() -> None:
    verdicts = class_verdicts()
    compliant, absent = verdicts.index("compliant"), verdicts.index("not_applicable")
    violated, unclear = verdicts.index("violated"), verdicts.index("unclear")
    gold = np.array([compliant, violated, violated, compliant], dtype=np.int64)
    chosen = np.array([absent, unclear, violated, unclear], dtype=np.int64)
    shown = np.isin(chosen, shown_classes())
    wanted = np.isin(gold, shown_classes())
    credit = REVIEW_SETTINGS.evaluation.tolerant_credit
    expected = (1 + credit + 1 + 0) / len(gold)
    assert tolerant_accuracy(gold, chosen, shown, wanted) == expected
