"""Relabelling a stored verdict run with the cross-validated decision layer."""

import json
import shutil

import numpy as np
from pydantic import BaseModel

from secreview.agents.case_materials import CaseMaterials, load_case_materials
from secreview.agents.policy_requirements import (
    PolicyAnalysis,
    PolicyRequirement,
    load_policy_analysis,
)
from secreview.agents.verdict_contexts import list_fragments
from secreview.agents.verdict_review import RequirementRecord, VerdictCaseRecord
from secreview.agents.verdict_store import (
    load_verdict_record,
    save_verdict_record,
    verdict_run_directory,
)
from secreview.evaluation.verdict_run import list_run_case_ids, read_analysis_name
from secreview.evaluation.verdict_scores import match_truths
from secreview.evaluation.verdict_stacking import (
    Labels,
    Matrix,
    build_features,
    choose_verdicts,
    class_labels,
    cross_validate,
    gold_label,
    keeps_evidence,
    preset_columns,
)
from secreview.evaluation.verdict_truth import PairTruth, build_case_truth
from secreview.retrieval.units import DesignUnit, split_units
from secreview.review_settings import REVIEW_SETTINGS

Key = tuple[str, str]


class Row(BaseModel):
    case_id: str
    group: str
    requirement_id: str
    features: list[float]
    gold: int


def index_records(record: VerdictCaseRecord) -> dict[str, RequirementRecord]:
    """Index the records of a case by requirement id."""
    indexed: dict[str, RequirementRecord] = {}
    for item in record.records:
        indexed[item.requirement_id] = item
    return indexed


def index_requirements(
    requirements: list[PolicyRequirement],
) -> dict[str, PolicyRequirement]:
    """Index the requirements of a policy analysis by id."""
    indexed: dict[str, PolicyRequirement] = {}
    for item in requirements:
        indexed[item.id] = item
    return indexed


def make_row(
    case_id: str,
    group: str,
    record: RequirementRecord,
    requirement: PolicyRequirement,
    fragments: list[str],
    truth: PairTruth,
) -> Row:
    """Describe one judged requirement and its gold verdict."""
    return Row(
        case_id=case_id,
        group=group,
        requirement_id=record.requirement_id,
        features=build_features(record, requirement, fragments),
        gold=class_labels().index(gold_label(truth.verdict, truth.subtype)),
    )


def row_for(
    materials: CaseMaterials,
    units: list[DesignUnit],
    record: RequirementRecord,
    requirements: dict[str, PolicyRequirement],
    truth: PairTruth,
) -> Row:
    """Describe a judged requirement with the fragments the model saw."""
    fragments = list_fragments(units, record.context_units)
    requirement = requirements[record.requirement_id]
    service = materials.labels.documented_service
    return make_row(materials.case_id, service, record, requirement, fragments, truth)


def build_rows(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    records: dict[str, RequirementRecord],
) -> list[Row]:
    """Describe every judged requirement of a case that has a gold verdict."""
    truths = build_case_truth(materials)
    units = split_units(materials.design_text)
    requirements = index_requirements(analysis.requirements)
    rows: list[Row] = []
    for index, requirement_id in match_truths(materials, analysis, truths).items():
        record = records[requirement_id]
        if record.verdict is not None and not truths[index].excluded:
            rows.append(row_for(materials, units, record, requirements, truths[index]))
    return rows


def collect_case_rows(run_name: str, analysis_name: str, case_id: str) -> list[Row]:
    """Load a stored case and describe its judged requirements."""
    materials = load_case_materials(case_id)
    analysis = load_policy_analysis(analysis_name, materials.labels.policy_version)
    records = index_records(load_verdict_record(run_name, case_id))
    return build_rows(materials, analysis, records)


def relabel_record(record: RequirementRecord, predicted: str) -> RequirementRecord:
    """Give a record the verdict chosen by the decision layer."""
    quote_kept = keeps_evidence(predicted, record)
    span = record.design_span if quote_kept else None
    return record.model_copy(update={"verdict": predicted, "design_span": span})


def predict_rows(rows: list[Row], preset: str) -> dict[Key, str]:
    """Predict the verdict of every row with cross-validation over documents."""
    everything: Matrix = np.array([row.features for row in rows], dtype=np.float64)
    features = everything[:, preset_columns(preset)]
    labels: Labels = np.array([row.gold for row in rows], dtype=np.int64)
    groups: list[str] = [row.group for row in rows]
    probabilities = cross_validate(features, labels, groups, len(class_labels()))
    verdicts: dict[Key, str] = {}
    for row, verdict in zip(rows, choose_verdicts(probabilities), strict=True):
        verdicts[(row.case_id, row.requirement_id)] = verdict
    return verdicts


def copy_config(source_run: str, target_run: str) -> None:
    """Copy the run configuration and note how the verdicts were decided."""
    target = verdict_run_directory(target_run)
    target.mkdir(parents=True, exist_ok=True)
    name = REVIEW_SETTINGS.verdict.run_config_file
    shutil.copy(verdict_run_directory(source_run) / name, target / name)
    settings = json.loads((target / name).read_text(encoding="utf-8"))
    settings["decision"] = f"cross-validated logistic stacking on {source_run}"
    (target / name).write_text(json.dumps(settings, indent=1), encoding="utf-8")


def relabel_case(
    case_id: str,
    source: VerdictCaseRecord,
    verdicts: dict[Key, str],
) -> VerdictCaseRecord:
    """Relabel the records of a case that have a predicted verdict."""
    records: list[RequirementRecord] = []
    for item in source.records:
        key = (case_id, item.requirement_id)
        records.append(relabel_record(item, verdicts[key]) if key in verdicts else item)
    return VerdictCaseRecord(case_id=case_id, records=records)


def run_rows(run_name: str) -> list[Row]:
    """Collect the labelled rows of every stored case of a run."""
    analysis_name = read_analysis_name(run_name)
    rows: list[Row] = []
    for case_id in list_run_case_ids(run_name):
        rows.extend(collect_case_rows(run_name, analysis_name, case_id))
    return rows


def join_features(rows: list[Row], extra: list[Row]) -> list[Row]:
    """Append the features of the extra rows to the rows with the same key."""
    lookup: dict[Key, Row] = {}
    for row in extra:
        lookup[(row.case_id, row.requirement_id)] = row
    joined: list[Row] = []
    for row in rows:
        other = lookup.get((row.case_id, row.requirement_id))
        if other is not None:
            features = row.features + other.features
            joined.append(row.model_copy(update={"features": features}))
    return joined


def merge_rows(primary: list[Row], extra_runs: list[str]) -> list[Row]:
    """Append the features of other runs to the rows of the primary run."""
    rows: list[Row] = primary
    for run_name in extra_runs:
        rows = join_features(rows, run_rows(run_name))
    return rows


def stack_run(
    source_run: str,
    target_run: str,
    extra_runs: list[str],
    preset: str,
) -> None:
    """Write a copy of a run whose verdicts come from the decision layer."""
    case_ids = list_run_case_ids(source_run)
    verdicts = predict_rows(merge_rows(run_rows(source_run), extra_runs), preset)
    copy_config(source_run, target_run)
    for case_id in case_ids:
        source = load_verdict_record(source_run, case_id)
        save_verdict_record(target_run, relabel_case(case_id, source, verdicts))
