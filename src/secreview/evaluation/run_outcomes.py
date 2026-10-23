"""Loading the matched outcomes of a stored run for scoring."""

from secreview.agents.case_materials import list_case_ids, load_case_materials
from secreview.agents.run_store import has_record, load_record
from secreview.evaluation.matching import match_case
from secreview.evaluation.outcomes import CaseOutcome


def load_run_outcomes(run_name: str, split: str) -> list[CaseOutcome]:
    """Match every stored record of a run on a split against the gold labels."""
    outcomes: list[CaseOutcome] = []
    for case_id in list_case_ids(split):
        if not has_record(run_name, case_id):
            continue
        record = load_record(run_name, case_id)
        outcomes.append(match_case(load_case_materials(case_id), record))
    return outcomes
