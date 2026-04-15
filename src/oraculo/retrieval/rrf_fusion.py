"""
Modulo: oraculo.retrieval.rrf_fusion
Proposito: Reciprocal Rank Fusion — combina rankings de multiples fuentes (BM25, vector, AST, call_graph).
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 3.3
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_K = 60


@dataclass(frozen=True)
class RankedItem:
    fragment_id: str
    score: float
    sources: tuple[str, ...]


def rrf_fuse(rankings: dict[str, list[str]], k: int = DEFAULT_K,
             weights: dict[str, float] | None = None) -> list[RankedItem]:
    """
    Reciprocal Rank Fusion.

    Args:
        rankings: {"bm25": [id1, id2, ...], "vector": [id3, id1, ...], ...}
                  Cada lista ordenada de mejor a peor.
        k: Constante RRF (default 60).
        weights: Pesos por fuente. Default 1.0 para todas.

    Returns:
        Lista fusionada ordenada por score RRF descendente.
    """
    if weights is None:
        weights = {}

    scores: dict[str, float] = {}
    source_map: dict[str, set[str]] = {}

    for source_name, ranked_ids in rankings.items():
        w = weights.get(source_name, 1.0)
        for rank, frag_id in enumerate(ranked_ids):
            rrf_score = w / (k + rank + 1)
            scores[frag_id] = scores.get(frag_id, 0.0) + rrf_score
            if frag_id not in source_map:
                source_map[frag_id] = set()
            source_map[frag_id].add(source_name)

    items = [
        RankedItem(
            fragment_id=fid,
            score=score,
            sources=tuple(sorted(source_map.get(fid, set()))),
        )
        for fid, score in scores.items()
    ]
    items.sort(key=lambda x: x.score, reverse=True)
    return items
