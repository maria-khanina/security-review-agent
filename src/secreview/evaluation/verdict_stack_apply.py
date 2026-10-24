"""Training the decision layer on one run and applying it to another."""

import numpy as np

from secreview.agents.case_materials import load_case_materials
from secreview.agents.policy_requirements import PolicyRequirement, load_policy_analysis
from secreview.agents.verdict_contexts import list_fragments
from secreview.agents.verdict_review import RequirementRecord
from secreview.agents.verdict_store import load_verdict_record, save_verdict_record
from secreview.evaluation.verdict_run import list_run_case_ids, read_analysis_name
from secreview.evaluation.verdict_stack_run import (
    Key,
    Row,
    collect_case_rows,
    copy_config,
    index_requirements,
    relabel_case,
)
from secreview.evaluation.verdict_stacking import (
    Labels,
    Matrix,
    build_features,
    choose_verdicts,
    class_labels,
    fit_weights,
    predict_probabilities,
    preset_columns,
    standardize,
)
from secreview.retrieval.units import DesignUnit, split_units

Described = list[tuple[Key, list[float]]]


def describe_item(
    case_id: str,
    item: RequirementRecord,
    requirements: dict[str, PolicyRequirement],
    units: list[DesignUnit],
) -> tuple[Key, list[float]]:
    """Describe one judged requirement by its signals."""
    fragments = list_fragments(units, item.context_units)
    features = build_features(item, requirements[item.requirement_id], fragments)
    return (case_id, item.requirement_id), features


def describe_case(run_name: str, analysis_name: str, case_id: str) -> Described:
    """Describe every judged requirement of a stored case, without gold labels."""
    materials = load_case_materials(case_id)
    analysis = load_policy_analysis(analysis_name, materials.labels.policy_version)
    requirements = index_requirements(analysis.requirements)
    units = split_units(materials.design_text)
    records = load_verdict_record(run_name, case_id).records
    return [
        describe_item(case_id, item, requirements, units)
        for item in records
        if item.verdict is not None
    ]


def describe_run(run_name: str) -> Described:
    """Describe every judged requirement of a stored run."""
    analysis_name = read_analysis_name(run_name)
    described: Described = []
    for case_id in list_run_case_ids(run_name):
        described.extend(describe_case(run_name, analysis_name, case_id))
    return described


def train_rows(run_name: str) -> list[Row]:
    """Collect the labelled rows of a stored run for training."""
    analysis_name = read_analysis_name(run_name)
    rows: list[Row] = []
    for case_id in list_run_case_ids(run_name):
        rows.extend(collect_case_rows(run_name, analysis_name, case_id))
    return rows


def design_matrices(
    rows: list[Row],
    described: Described,
    preset: str,
) -> tuple[Matrix, Labels, Matrix]:
    """Build the training matrix, its labels and the matrix to predict."""
    columns = preset_columns(preset)
    full: Matrix = np.array([row.features for row in rows], dtype=np.float64)
    labels: Labels = np.array([row.gold for row in rows], dtype=np.int64)
    every: Matrix = np.array(
        [features for _, features in described],
        dtype=np.float64,
    )
    return full[:, columns], labels, every[:, columns]


def predict_described(
    rows: list[Row],
    described: Described,
    preset: str,
) -> dict[Key, str]:
    """Train on the labelled rows and predict the verdict of the described ones."""
    train, labels, other = design_matrices(rows, described, preset)
    scaled_train, scaled_other = standardize(train, other)
    weights = fit_weights(scaled_train, labels, len(class_labels()))
    chosen = choose_verdicts(predict_probabilities(weights, scaled_other))
    verdicts: dict[Key, str] = {}
    for (key, _), verdict in zip(described, chosen, strict=True):
        verdicts[key] = verdict
    return verdicts


def apply_run(
    train_run: str,
    apply_run: str,
    target_run: str,
    preset: str,
) -> None:
    """Relabel the apply run with a decision layer trained on the train run."""
    described = describe_run(apply_run)
    verdicts = predict_described(train_rows(train_run), described, preset)
    copy_config(apply_run, target_run)
    for case_id in list_run_case_ids(apply_run):
        source = load_verdict_record(apply_run, case_id)
        save_verdict_record(target_run, relabel_case(case_id, source, verdicts))
