"""Reading the findings of the free-form reviewer as verdicts on requirements."""

import json

from secreview.agents.baseline import GroundedFinding, ReviewRecord
from secreview.agents.case_materials import load_case_materials
from secreview.agents.policy_requirements import PolicyAnalysis, load_policy_analysis
from secreview.agents.run_store import load_record, run_directory
from secreview.agents.verdicts import RequirementVerdict
from secreview.evaluation.verdict_scores import CaseVerdictOutcome, score_case_verdicts
from secreview.parsing.vocabulary import UNCLEAR, VIOLATED
from secreview.review_settings import REVIEW_SETTINGS


def read_analysis_set(run_name: str) -> str:
    """Read the name of the policy analysis set a baseline run was made with."""
    path = run_directory(run_name) / "run_config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    return str(config["variant"]["policy_analysis"])


def to_verdict(finding: GroundedFinding) -> RequirementVerdict:
    """Read a violation as a violated verdict and an ambiguity as an unclear one."""
    is_violation = finding.finding_type == "violation"
    return RequirementVerdict.model_validate(
        {
            "requirement_id": finding.requirement_id,
            "verdict": VIOLATED if is_violation else UNCLEAR,
            "design_span": finding.design_span if is_violation else None,
            "severity": finding.severity if is_violation else "none",
            "confidence": finding.confidence / REVIEW_SETTINGS.confidence_maximum,
        }
    )


def best_findings(record: ReviewRecord) -> list[RequirementVerdict]:
    """Keep the most confident finding for every requirement."""
    best: dict[str, GroundedFinding] = {}
    for finding in record.findings:
        known = best.get(finding.requirement_id)
        if known is None or finding.confidence > known.confidence:
            best[finding.requirement_id] = finding
    return [to_verdict(finding) for finding in best.values()]


def score_baseline_case(
    run_name: str,
    case_id: str,
    analysis: PolicyAnalysis,
) -> CaseVerdictOutcome:
    """Score the findings of one case of a free-form run as verdicts."""
    materials = load_case_materials(case_id)
    verdicts = best_findings(load_record(run_name, case_id))
    return score_case_verdicts(materials, analysis, verdicts)


def score_baseline_run(run_name: str, case_ids: list[str]) -> list[CaseVerdictOutcome]:
    """Score a free-form run on the given cases with the verdict scores."""
    analysis_set = read_analysis_set(run_name)
    outcomes: list[CaseVerdictOutcome] = []
    for case_id in case_ids:
        version = load_case_materials(case_id).labels.policy_version
        analysis = load_policy_analysis(analysis_set, version)
        outcomes.append(score_baseline_case(run_name, case_id, analysis))
    return outcomes
