"""Scores a policy analysis against the gold requirement locations of a policy."""

from pydantic import BaseModel

from secreview.agents.oracle_policy import build_oracle_analysis
from secreview.agents.policy_requirements import PolicyAnalysis, PolicyRequirement
from secreview.datagen.policies import load_policy_versions
from secreview.evaluation.class_report import ClassReport, build_class_report, divide
from secreview.parsing.spans import collect_token_indices, compute_overlap
from secreview.parsing.vocabulary import WORDINGS
from secreview.review_settings import REVIEW_SETTINGS

CLEAR = "clear"
Pair = tuple[PolicyRequirement, PolicyRequirement]


class WordingScores(BaseModel):
    accuracy: float
    report: ClassReport
    not_clear_recall: float
    not_clear_precision: float
    not_clear_f1: float


class TopicScores(BaseModel):
    hit_rate: float
    jaccard: float
    precision: float
    recall: float
    exact_match: float


class PolicyScores(BaseModel):
    policy_version: str
    gold_requirements: int
    predicted_requirements: int
    matched_pairs: int
    recall: float
    precision: float
    wording: WordingScores
    topics: TopicScores


def token_set(text: str, requirement: PolicyRequirement) -> set[int]:
    """Return the token indices covered by a requirement."""
    return collect_token_indices(text, [requirement.span])


def rank_overlaps(
    text: str,
    gold: list[PolicyRequirement],
    predicted: list[PolicyRequirement],
) -> list[tuple[float, int, int]]:
    """List the gold-predicted pairs above the overlap threshold, best first."""
    threshold = REVIEW_SETTINGS.evaluation.iou_threshold
    gold_tokens: list[set[int]] = [token_set(text, item) for item in gold]
    found_tokens: list[set[int]] = [token_set(text, item) for item in predicted]
    ranked: list[tuple[float, int, int]] = []
    for gold_index, expected in enumerate(gold_tokens):
        for found_index, found in enumerate(found_tokens):
            overlap = compute_overlap(expected, found)
            if overlap >= threshold:
                ranked.append((overlap, gold_index, found_index))
    return sorted(ranked, reverse=True)


def match_one_to_one(
    text: str,
    gold: list[PolicyRequirement],
    predicted: list[PolicyRequirement],
) -> list[Pair]:
    """Pair requirements so that each gold and each predicted one is used once."""
    used_gold: set[int] = set()
    used_predicted: set[int] = set()
    pairs: list[Pair] = []
    for _, gold_index, found_index in rank_overlaps(text, gold, predicted):
        if gold_index in used_gold or found_index in used_predicted:
            continue
        used_gold.add(gold_index)
        used_predicted.add(found_index)
        pairs.append((gold[gold_index], predicted[found_index]))
    return pairs


def score_not_clear(
    pairs: list[Pair],
    gold: list[PolicyRequirement],
    predicted: list[PolicyRequirement],
) -> tuple[float, float, float]:
    """Compute recall, precision and F1 of finding the not-clear wording."""
    hits = sum(
        1 for expected, found in pairs if expected.wording != CLEAR != found.wording
    )
    gold_total = sum(1 for item in gold if item.wording != CLEAR)
    found_total = sum(1 for item in predicted if item.wording != CLEAR)
    recall = divide(hits, gold_total)
    precision = divide(hits, found_total)
    return recall, precision, divide(2 * recall * precision, recall + precision)


def score_wording(
    pairs: list[Pair],
    gold: list[PolicyRequirement],
    predicted: list[PolicyRequirement],
) -> WordingScores:
    """Score how well the wording labels of matched requirements agree."""
    labels: list[tuple[str, str]] = []
    for expected, found in pairs:
        labels.append((expected.wording, found.wording))
    report = build_class_report(labels, WORDINGS)
    recall, precision, f1 = score_not_clear(pairs, gold, predicted)
    return WordingScores(
        accuracy=report.accuracy,
        report=report,
        not_clear_recall=recall,
        not_clear_precision=precision,
        not_clear_f1=f1,
    )


def compare_topics(expected: list[str], found: list[str]) -> TopicScores:
    """Compare the topic lists of one matched pair of requirements."""
    shared = set(expected) & set(found)
    union = set(expected) | set(found)
    return TopicScores(
        hit_rate=float(bool(shared)),
        jaccard=divide(len(shared), len(union)),
        precision=divide(len(shared), len(set(found))),
        recall=divide(len(shared), len(set(expected))),
        exact_match=float(set(expected) == set(found)),
    )


def score_topics(pairs: list[Pair]) -> TopicScores:
    """Average the topic comparison over the matched requirement pairs."""
    rows: list[TopicScores] = []
    for expected, found in pairs:
        rows.append(compare_topics(expected.topics, found.topics))
    count = len(rows)
    return TopicScores(
        hit_rate=divide(sum(row.hit_rate for row in rows), count),
        jaccard=divide(sum(row.jaccard for row in rows), count),
        precision=divide(sum(row.precision for row in rows), count),
        recall=divide(sum(row.recall for row in rows), count),
        exact_match=divide(sum(row.exact_match for row in rows), count),
    )


def score_policy_analysis(analysis: PolicyAnalysis) -> PolicyScores:
    """Compare an analysis with the gold requirement list of the same policy."""
    version = analysis.policy_version
    text = load_policy_versions()[version].text
    gold = build_oracle_analysis(version).requirements
    predicted = analysis.requirements
    pairs = match_one_to_one(text, gold, predicted)
    return PolicyScores(
        policy_version=version,
        gold_requirements=len(gold),
        predicted_requirements=len(predicted),
        matched_pairs=len(pairs),
        recall=divide(len(pairs), len(gold)),
        precision=divide(len(pairs), len(predicted)),
        wording=score_wording(pairs, gold, predicted),
        topics=score_topics(pairs),
    )
