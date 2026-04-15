"""
Modulo: oraculo.retrieval.vector_search
Proposito: Busqueda vectorial por similitud coseno sobre embeddings en DuckDB.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 3.2
"""
from __future__ import annotations
import logging
import math
from dataclasses import dataclass

from oraculo.index.duckdb_store import DuckDbStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VectorResult:
    fragment_id: str
    score: float
    trust_tier: int


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Similitud coseno entre dos vectores. Retorna 0.0 si alguno es cero."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def search_vectors(store: DuckDbStore, query_embedding: list[float],
                   limit: int = 20) -> list[VectorResult]:
    """Busqueda por similitud coseno sobre la tabla embeddings de DuckDB."""
    rows = store._conn.execute(
        "SELECT fragment_id, embedding, trust_tier FROM embeddings"
    ).fetchall()

    scored = []
    for frag_id, emb, tier in rows:
        if emb is None:
            continue
        sim = cosine_similarity(query_embedding, list(emb))
        scored.append(VectorResult(fragment_id=frag_id, score=sim, trust_tier=tier))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:limit]
