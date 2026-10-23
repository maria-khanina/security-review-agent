"""Scoring a stored verdict run and bootstrap intervals over its documents."""

import json
import random

from secreview.agents.case_materials import load_case_materials
from secreview.agents.policy_requirements import load_policy_analysis
from secreview.agents.verdict_review import to_requirement_verdicts
from secreview.agents.verdict_store import (
    load_verdict_record,
    verdict_run_directory,
)
from secreview.evaluation.bootstrap import (
    DifferenceInterval,
    Interval,
    build_interval,
    draw_resample,
    summarize_gaps,
)
from secreview.evaluation.verdict_scores import (
    CaseVerdictOutcome,
    VerdictScores,
    score_case_verdicts,
    summarize_verdicts,
)
from secreview.parsing.vocabulary import VERDICTS
from secreview.review_settings import REVIEW_SETTINGS

RECALL_SUBTYPES = (
    "planted_ambiguity",
    "vague_policy",
    "planted_violation",
    "not_in_service",
    "not_in_service_exposure",
    "coupled_silence",
)


def list_run_case_ids(run_name: str) -> list[str]:
    """List the cases that have a stored record in a verdict run."""
    suffix = REVIEW_SETTINGS.reply_file_suffix
    directory = verdict_run_directory(run_name)
    names: list[str] = [path.name for path in directory.glob(f"c*{suffix}")]
    return sorted(name[: -len(suffix)] for name in names)


def read_analysis_name(run_name: str) -> str:
    """Read the name of the policy analysis set a run was made with."""
    path = verdict_run_directory(run_name) / REVIEW_SETTINGS.verdict.run_config_file
    return str(json.loads(path.read_text(encoding="utf-8"))["analysis"])


def score_run_cases(run_name: str) -> dict[str, CaseVerdictOutcome]:
    """Score every stored case of a run against the gold verdicts."""
    analysis_name = read_analysis_name(run_name)
    outcomes: dict[str, CaseVerdictOutcome] = {}
    for case_id in list_run_case_ids(run_name):
        materials = load_case_materials(case_id)
        version = materials.labels.policy_version
        analysis = load_policy_analysis(analysis_name, version)
        verdicts = to_requirement_verdicts(load_verdict_record(run_name, case_id))
        outcomes[case_id] = score_case_verdicts(materials, analysis, verdicts)
    return outcomes


def flatten_class_scores(scores: VerdictScores) -> dict[str, float]:
    """Flatten the per-verdict and per-subtype recalls and precisions."""
    metrics: dict[str, float] = {}
    for verdict in VERDICTS:
        metrics[f"recall_{verdict}"] = scores.report.per_class[verdict].recall
        metrics[f"precision_{verdict}"] = scores.report.per_class[verdict].precision
    for subtype in RECALL_SUBTYPES:
        metrics[f"recall_{subtype}"] = scores.recall_by_subtype.get(subtype, 0.0)
    return metrics


def flatten_scores(scores: VerdictScores) -> dict[str, float]:
    """Pick the headline numbers of the verdict scores into one flat table."""
    metrics: dict[str, float] = {
        "accuracy": scores.accuracy,
        "accuracy_with_evidence": scores.accuracy_with_evidence,
        "defect_recall": scores.defect_recall,
        "violated_precision": scores.violated_precision_with_evidence,
        "macro_f1": scores.report.macro_f1,
    }
    metrics.update(flatten_class_scores(scores))
    if scores.confidence_auroc is not None:
        metrics["confidence_auroc"] = scores.confidence_auroc
    if scores.severity_ordinal is not None:
        metrics["severity_mae"] = scores.severity_ordinal.mean_absolute_error
    return metrics


def resample_scores(
    outcomes: list[CaseVerdictOutcome],
    generator: random.Random,
) -> VerdictScores:
    """Score a resample of the documents drawn with replacement."""
    positions = draw_resample(len(outcomes), generator)
    return summarize_verdicts([outcomes[position] for position in positions])


def collect_samples(outcomes: list[CaseVerdictOutcome]) -> dict[str, list[float]]:
    """Recompute every headline metric on each resample of the documents."""
    evaluation = REVIEW_SETTINGS.evaluation
    generator = random.Random(evaluation.bootstrap_seed)
    samples: dict[str, list[float]] = {}
    for _ in range(evaluation.bootstrap_resamples):
        drawn = flatten_scores(resample_scores(outcomes, generator))
        for name, value in drawn.items():
            samples.setdefault(name, []).append(value)
    return samples


def bootstrap_verdict_run(outcomes: list[CaseVerdictOutcome]) -> dict[str, Interval]:
    """Compute a bootstrap interval for every headline metric of a run."""
    estimates = flatten_scores(summarize_verdicts(outcomes))
    intervals: dict[str, Interval] = {}
    for name, values in collect_samples(outcomes).items():
        intervals[name] = build_interval(estimates[name], values)
    return intervals


def shared_outcomes(
    first: dict[str, CaseVerdictOutcome],
    second: dict[str, CaseVerdictOutcome],
) -> tuple[list[CaseVerdictOutcome], list[CaseVerdictOutcome]]:
    """Keep the cases both runs reviewed, in the same order."""
    shared = sorted(set(first) & set(second))
    first_outcomes: list[CaseVerdictOutcome] = [first[case_id] for case_id in shared]
    return first_outcomes, [second[case_id] for case_id in shared]


def pick_both(
    first: list[CaseVerdictOutcome],
    second: list[CaseVerdictOutcome],
    positions: list[int],
) -> tuple[dict[str, float], dict[str, float]]:
    """Flatten the scores of both runs on the same drawn documents."""
    one = summarize_verdicts([first[position] for position in positions])
    two = summarize_verdicts([second[position] for position in positions])
    return flatten_scores(one), flatten_scores(two)


def collect_gaps(
    first: list[CaseVerdictOutcome],
    second: list[CaseVerdictOutcome],
) -> dict[str, list[float]]:
    """Recompute the metric differences on shared resamples of the documents."""
    evaluation = REVIEW_SETTINGS.evaluation
    generator = random.Random(evaluation.bootstrap_seed)
    gaps: dict[str, list[float]] = {}
    for _ in range(evaluation.bootstrap_resamples):
        positions = draw_resample(len(first), generator)
        one, two = pick_both(first, second, positions)
        for name in set(one) & set(two):
            gaps.setdefault(name, []).append(two[name] - one[name])
    return gaps


def bootstrap_verdict_difference(
    first: list[CaseVerdictOutcome],
    second: list[CaseVerdictOutcome],
) -> dict[str, DifferenceInterval]:
    """Compare two runs on the same resampled documents, metric by metric."""
    gaps = collect_gaps(first, second)
    estimate_first = flatten_scores(summarize_verdicts(first))
    estimate_second = flatten_scores(summarize_verdicts(second))
    return summarize_gaps(estimate_first, estimate_second, gaps)
