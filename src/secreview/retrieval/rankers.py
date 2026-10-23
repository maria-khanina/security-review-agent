"""Rankers that order the chunks of a design by relevance to a requirement."""

import re
from typing import Protocol

import numpy as np
from numpy.typing import NDArray
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

from secreview.review_settings import REVIEW_SETTINGS

WORD_PATTERN = re.compile(r"\w+")
Embedding = NDArray[np.float32]


class Ranker(Protocol):
    def rank(self, query: str, keys: list[str]) -> list[int]: ...


def order_by_score(scores: list[float]) -> list[int]:
    """Return the positions sorted from the highest score, earlier ones first."""
    positions: list[int] = list(range(len(scores)))
    return sorted(positions, key=lambda position: (-scores[position], position))


def tokenize(text: str) -> list[str]:
    """Lower-case the text and split it into word tokens."""
    return WORD_PATTERN.findall(text.lower())


class Bm25Ranker:
    def rank(self, query: str, keys: list[str]) -> list[int]:
        """Order the keys by their BM25 score for the query words."""
        corpus: list[list[str]] = [tokenize(key) for key in keys]
        raw_scores = BM25Okapi(corpus).get_scores(tokenize(query))
        scores: list[float] = [float(score) for score in raw_scores]
        return order_by_score(scores)


class DenseRanker:
    def __init__(self, model_id: str, query_prefix: str) -> None:
        self.encoder = SentenceTransformer(
            model_id,
            device=REVIEW_SETTINGS.retrieval.device,
        )
        self.query_prefix = query_prefix
        self.cache: dict[str, Embedding] = {}

    def embed(self, texts: list[str]) -> list[Embedding]:
        """Embed the texts, encoding only those not seen before."""
        unique: list[str] = list(dict.fromkeys(texts))
        missing: list[str] = [text for text in unique if text not in self.cache]
        if missing:
            vectors = self.encoder.encode(
                missing,
                batch_size=REVIEW_SETTINGS.retrieval.encode_batch_size,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )
            self.cache.update(zip(missing, vectors, strict=True))
        return [self.cache[text] for text in texts]

    def rank(self, query: str, keys: list[str]) -> list[int]:
        """Order the keys by cosine similarity of their embeddings to the query."""
        query_vector = self.embed([self.query_prefix + query])[0]
        vectors = self.embed(keys)
        scores: list[float] = [float(vector @ query_vector) for vector in vectors]
        return order_by_score(scores)


class HybridRanker:
    def __init__(self, first: Ranker, second: Ranker) -> None:
        self.first = first
        self.second = second

    def rank(self, query: str, keys: list[str]) -> list[int]:
        """Fuse the two rankings with reciprocal rank fusion."""
        constant = REVIEW_SETTINGS.retrieval.rrf_constant
        scores: list[float] = [0.0] * len(keys)
        for ranker in (self.first, self.second):
            for place, position in enumerate(ranker.rank(query, keys), 1):
                scores[position] += 1.0 / (constant + place)
        return order_by_score(scores)


class CrossScorer:
    def __init__(self, model_id: str) -> None:
        self.model = CrossEncoder(model_id, device=REVIEW_SETTINGS.retrieval.device)
        self.cache: dict[tuple[str, str], float] = {}

    def fill_cache(self, pairs: list[tuple[str, str]]) -> None:
        """Run the cross-encoder on the pairs that have no score yet."""
        unique: list[tuple[str, str]] = list(dict.fromkeys(pairs))
        missing: list[tuple[str, str]] = []
        for pair in unique:
            if pair not in self.cache:
                missing.append(pair)
        if missing:
            batch_size = REVIEW_SETTINGS.retrieval.encode_batch_size
            predicted = self.model.predict(missing, batch_size=batch_size)
            for pair, value in zip(missing, predicted, strict=True):
                self.cache[pair] = float(value)

    def score(self, query: str, keys: list[str]) -> list[float]:
        """Score the query against each key with the cross-encoder."""
        pairs: list[tuple[str, str]] = [(query, key) for key in keys]
        self.fill_cache(pairs)
        return [self.cache[pair] for pair in pairs]


class RerankRanker:
    def __init__(self, first_stage: Ranker, scorer: CrossScorer) -> None:
        self.first_stage = first_stage
        self.scorer = scorer

    def rank(self, query: str, keys: list[str]) -> list[int]:
        """Reorder the best candidates of the first stage by the cross-encoder."""
        ranking = self.first_stage.rank(query, keys)
        depth = REVIEW_SETTINGS.retrieval.rerank_depth
        candidates, rest = ranking[:depth], ranking[depth:]
        texts: list[str] = [keys[position] for position in candidates]
        order = order_by_score(self.scorer.score(query, texts))
        return [candidates[place] for place in order] + rest
