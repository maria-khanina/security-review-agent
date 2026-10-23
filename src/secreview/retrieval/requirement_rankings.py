"""Stored rankings of design chunks for every requirement of a policy analysis."""

import json

from secreview.agents.case_materials import (
    CaseMaterials,
    list_case_ids,
    load_case_materials,
)
from secreview.agents.policy_requirements import PolicyAnalysis, load_policy_analysis
from secreview.datagen.settings import project_path
from secreview.retrieval.rankers import Bm25Ranker, DenseRanker, HybridRanker, Ranker
from secreview.retrieval.units import Chunk, build_chunks, split_units
from secreview.review_settings import REVIEW_SETTINGS

Bounds = list[tuple[int, int]]
CaseRankings = dict[str, dict[str, Bounds]]
SplitRankings = dict[str, CaseRankings]
SEPARATOR = "/"


def name_ranking(method: str, window: int) -> str:
    """Name a ranker with a chunk window, for example dense/0."""
    return f"{method}{SEPARATOR}{window}"


def build_first_stage_rankers() -> dict[str, Ranker]:
    """Create the dense ranker of the chosen model and its hybrid with BM25."""
    settings = REVIEW_SETTINGS.retrieval
    model = settings.dense_models[-1]
    dense = DenseRanker(model.model_id, model.query_prefix)
    return {
        settings.dense_name: dense,
        settings.hybrid_name: HybridRanker(Bm25Ranker(), dense),
    }


def rank_requirement(
    ranker: Ranker,
    chunks: list[Chunk],
    query: str,
) -> Bounds:
    """Return the bounds of the best chunks for one requirement text."""
    keys: list[str] = [chunk.key for chunk in chunks]
    order = ranker.rank(query, keys)[: REVIEW_SETTINGS.retrieval.ranking_depth]
    return [(chunks[position].first, chunks[position].last) for position in order]


def rank_case(
    materials: CaseMaterials,
    analysis: PolicyAnalysis,
    rankers: dict[str, Ranker],
) -> CaseRankings:
    """Rank the chunks of a design for every requirement, per ranker and window."""
    units = split_units(materials.design_text)
    rankings: CaseRankings = {item.id: {} for item in analysis.requirements}
    for window in REVIEW_SETTINGS.retrieval.windows:
        chunks = build_chunks(units, window, False)
        for method, ranker in rankers.items():
            for item in analysis.requirements:
                name = name_ranking(method, window)
                rankings[item.id][name] = rank_requirement(ranker, chunks, item.quote)
    return rankings


def rankings_path(split: str, analysis_name: str) -> str:
    """Return the file name of the stored rankings of a split and analysis."""
    settings = REVIEW_SETTINGS.retrieval
    prefix = settings.rankings_file_prefix
    return f"{settings.results_directory}/{prefix}{analysis_name}_{split}.json"


def rank_split(split: str, analysis_name: str) -> SplitRankings:
    """Rank the design chunks of every case of a split for its policy analysis."""
    rankers = build_first_stage_rankers()
    result: SplitRankings = {}
    for case_id in list_case_ids(split):
        materials = load_case_materials(case_id)
        version = materials.labels.policy_version
        analysis = load_policy_analysis(analysis_name, version)
        result[case_id] = rank_case(materials, analysis, rankers)
    return result


def save_rankings(split: str, analysis_name: str, rankings: SplitRankings) -> None:
    """Write the rankings of a split next to the other retrieval results."""
    path = project_path(rankings_path(split, analysis_name))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rankings), encoding="utf-8")


def load_rankings(split: str, analysis_name: str) -> SplitRankings:
    """Read the stored rankings of a split and policy analysis."""
    text = project_path(rankings_path(split, analysis_name)).read_text(encoding="utf-8")
    return json.loads(text)
