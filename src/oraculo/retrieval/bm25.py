"""
Modulo: oraculo.retrieval.bm25
Proposito: Wrapper de busqueda BM25 sobre SqliteFtsStore.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 3.1
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from oraculo.index.sqlite_store import SqliteFtsStore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BM25Result:
    fragment_id: str
    score: float
    snippet: str


def search_bm25(store: SqliteFtsStore, query: str, limit: int = 20) -> list[BM25Result]:
    """Busqueda BM25 sobre FTS5. Retorna resultados ordenados por relevancia."""
    raw = store.search_bm25(query, limit=limit)
    results = []
    for frag_id, rank, snippet in raw:
        results.append(BM25Result(fragment_id=frag_id, score=abs(rank), snippet=snippet))
    return results
