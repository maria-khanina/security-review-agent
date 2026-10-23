"""Running every ranker and chunking variant over the retrieval items of a split."""

import json

from pydantic import BaseModel

from secreview.agents.case_materials import (
    CaseMaterials,
    list_case_ids,
    load_case_materials,
)
from secreview.datagen.settings import project_path
from secreview.retrieval.gold import RetrievalItem, build_retrieval_items
from secreview.retrieval.metrics import ItemScore, is_reachable, score_ranking
from secreview.retrieval.rankers import (
    Bm25Ranker,
    CrossScorer,
    DenseRanker,
    HybridRanker,
    Ranker,
    RerankRanker,
)
from secreview.retrieval.units import DesignUnit, build_chunks, split_units
from secreview.review_settings import REVIEW_SETTINGS

SEPARATOR = ":"


class ExperimentResult(BaseModel):
    split: str
    skipped_items: int
    scores: dict[str, list[ItemScore]]


def build_rankers() -> dict[str, Ranker]:
    """Create the rankers: BM25, each dense model and each hybrid of the two."""
    settings = REVIEW_SETTINGS.retrieval
    bm25 = Bm25Ranker()
    rankers: dict[str, Ranker] = {settings.bm25_name: bm25}
    for model in settings.dense_models:
        dense = DenseRanker(model.model_id, model.query_prefix)
        rankers[f"{settings.dense_name}{SEPARATOR}{model.name}"] = dense
        hybrid = HybridRanker(bm25, dense)
        rankers[f"{settings.hybrid_name}{SEPARATOR}{model.name}"] = hybrid
    return add_rerankers(rankers)


def add_rerankers(first_stages: dict[str, Ranker]) -> dict[str, Ranker]:
    """Add a cross-encoder second stage on top of every first-stage ranker."""
    settings = REVIEW_SETTINGS.retrieval
    rankers: dict[str, Ranker] = dict(first_stages)
    scorer = CrossScorer(settings.reranker_model_id)
    for name, first_stage in first_stages.items():
        reranked = RerankRanker(first_stage, scorer)
        rankers[f"{name}{settings.rerank_joiner}{settings.rerank_name}"] = reranked
    return rankers


def name_variant(method: str, window: int, with_heading: bool) -> str:
    """Name a ranker and chunking choice, for example hybrid:bge/w1/heading."""
    heading = "heading" if with_heading else "plain"
    return f"{method}/w{window}/{heading}"


def keep_reachable(
    items: list[RetrievalItem],
    units: list[DesignUnit],
) -> list[RetrievalItem]:
    """Drop the items whose gold lies outside every unit."""
    return [item for item in items if is_reachable(item, units)]


def score_variant(
    ranker: Ranker,
    items: list[RetrievalItem],
    units: list[DesignUnit],
    window: int,
    with_heading: bool,
) -> list[ItemScore]:
    """Score one ranker with one chunking on all items of a case."""
    chunks = build_chunks(units, window, with_heading)
    keys: list[str] = [chunk.key for chunk in chunks]
    scores: list[ItemScore] = []
    for item in items:
        ranking = ranker.rank(item.query, keys)
        scores.append(score_ranking(item, units, chunks, ranking))
    return scores


def score_case(
    materials: CaseMaterials,
    rankers: dict[str, Ranker],
    scores: dict[str, list[ItemScore]],
) -> int:
    """Score every variant on one case and return the number of skipped items."""
    units = split_units(materials.design_text)
    items = build_retrieval_items(materials)
    reachable = keep_reachable(items, units)
    settings = REVIEW_SETTINGS.retrieval
    for method, ranker in rankers.items():
        for window in settings.windows:
            for with_heading in settings.heading_options:
                name = name_variant(method, window, with_heading)
                scores.setdefault(name, []).extend(
                    score_variant(ranker, reachable, units, window, with_heading)
                )
    return len(items) - len(reachable)


def run_experiment(split: str) -> ExperimentResult:
    """Score all variants on every case of the split."""
    rankers = build_rankers()
    scores: dict[str, list[ItemScore]] = {}
    skipped = 0
    for case_id in list_case_ids(split):
        skipped += score_case(load_case_materials(case_id), rankers, scores)
    return ExperimentResult(split=split, skipped_items=skipped, scores=scores)


def result_path(split: str) -> str:
    """Return the file name of the stored result of a split."""
    return f"{REVIEW_SETTINGS.retrieval.results_directory}/{split}.json"


def save_result(result: ExperimentResult) -> None:
    """Write the result of an experiment next to the other data files."""
    path = project_path(result_path(result.split))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result.model_dump()), encoding="utf-8")


def load_result(split: str) -> ExperimentResult:
    """Read a stored experiment result."""
    text = project_path(result_path(split)).read_text(encoding="utf-8")
    return ExperimentResult.model_validate_json(text)
