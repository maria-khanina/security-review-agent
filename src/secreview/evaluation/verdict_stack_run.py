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
    cross_validate,
    keeps_evidence,
)
from secreview.evaluation.verdict_truth import PairTruth, build_case_truth
from secreview.parsing.vocabulary import VERDICTS
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
        gold=VERDICTS.index(truth.verdict),
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
        if record.verdict is not None:
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


def predict_rows(rows: list[Row]) -> dict[Key, str]:
    """Predict the verdict of every row with cross-validation over documents."""
    features: Matrix = np.array([row.features for row in rows], dtype=np.float64)
    labels: Labels = np.array([row.gold for row in rows], dtype=np.int64)
    predicted = cross_validate(features, labels, [row.group for row in rows])
    verdicts: dict[Key, str] = {}
    for row, index in zip(rows, predicted, strict=True):
        verdicts[(row.case_id, row.requirement_id)] = VERDICTS[int(index)]
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


def stack_run(source_run: str, target_run: str) -> None:
    """Write a copy of a run whose verdicts come from the decision layer."""
    analysis_name = read_analysis_name(source_run)
    case_ids = list_run_case_ids(source_run)
    rows: list[Row] = []
    for case_id in case_ids:
        rows.extend(collect_case_rows(source_run, analysis_name, case_id))
    verdicts = predict_rows(rows)
    copy_config(source_run, target_run)
    for case_id in case_ids:
        source = load_verdict_record(source_run, case_id)
        save_verdict_record(target_run, relabel_case(case_id, source, verdicts))
