"""
Modulo: oraculo.assembler.pipeline
Proposito: Pipeline completo de ensamblado de contexto: query -> retrieve -> fuse -> dedup -> budget -> payload.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 4
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any

from oraculo.index.sqlite_store import SqliteFtsStore
from oraculo.index.duckdb_store import DuckDbStore
from oraculo.retrieval.bm25 import search_bm25
from oraculo.retrieval.rrf_fusion import rrf_fuse
from oraculo.retrieval.simhash_dedup import dedup_fragments
from oraculo.assembler.budget_allocator import BudgetAllocator
from oraculo.assembler.trust_tier import assign_tier, TRUST_CANON, TRUST_HIGH
from oraculo.assembler.payload_builder import PayloadBuilder, FragmentPayload, AssemblyPayload

logger = logging.getLogger(__name__)


def estimate_tokens(text: str) -> int:
    """Estimacion rapida de tokens: ~4 chars por token."""
    return max(1, len(text) // 4)


class AssemblyPipeline:
    """Pipeline completo: query -> BM25 -> fuse -> dedup -> budget -> payload."""

    def __init__(self, fts_store: SqliteFtsStore, duck_store: DuckDbStore,
                 profile: str = "enterprise", total_budget: int = 4096,
                 rrf_weights: dict[str, float] | None = None):
        self._fts = fts_store
        self._duck = duck_store
        self._profile = profile
        self._total_budget = total_budget
        self._rrf_weights = rrf_weights

    def assemble(self, query: str, limit: int = 10) -> AssemblyPayload:
        builder = PayloadBuilder(query=query, profile=self._profile)
        budget = BudgetAllocator(total_budget=self._total_budget)

        bm25_results = search_bm25(self._fts, query, limit=limit * 3)
        bm25_ids = [r.fragment_id for r in bm25_results]

        symbol_results = self._duck.search_symbols(query, limit=limit)
        symbol_ids = [s["symbol_id"] for s in symbol_results]

        rankings = {"bm25": bm25_ids}
        if symbol_ids:
            rankings["ast"] = symbol_ids

        fused = rrf_fuse(rankings, weights=self._rrf_weights)

        frag_texts = self._load_fragment_texts([item.fragment_id for item in fused[:limit * 2]])
        dedup_pairs = [(fid, frag_texts.get(fid, "")) for fid in [i.fragment_id for i in fused] if fid in frag_texts]
        unique_ids = set(dedup_fragments(dedup_pairs))
        dedup_count = len(dedup_pairs) - len(unique_ids)
        builder.set_dedup_removed(dedup_count)

        fused_map = {item.fragment_id: item for item in fused}
        added = 0
        for item in fused:
            if added >= limit:
                break
            if item.fragment_id not in unique_ids:
                continue

            text = frag_texts.get(item.fragment_id, "")
            if not text:
                continue

            tokens_needed = estimate_tokens(text)
            tier_info = assign_tier(item.fragment_id, "project_code", "L1_treesitter")
            layer = self._tier_to_layer(tier_info.tier)
            consumed = budget.consume(layer, tokens_needed)
            if consumed == 0:
                continue

            meta = self._get_fragment_meta(item.fragment_id)
            builder.add_fragment(FragmentPayload(
                fragment_id=item.fragment_id,
                file_path=meta.get("file_path", "unknown"),
                start_line=meta.get("start_line", 0),
                end_line=meta.get("end_line", 0),
                content=text[:consumed * 4],
                trust_tier=tier_info.tier,
                rrf_score=item.score,
                sources=list(item.sources),
                language=meta.get("language", "unknown"),
                parser_level=meta.get("parser_level", "unknown"),
            ))
            added += 1

        builder.set_budget_summary(budget.summary())
        return builder.build()

    def _load_fragment_texts(self, fragment_ids: list[str]) -> dict[str, str]:
        """Carga contenido de fragmentos desde SQLite."""
        result = {}
        if not fragment_ids:
            return result
        placeholders = ",".join("?" * len(fragment_ids))
        rows = self._fts._conn.execute(
            f"SELECT fragment_id, content FROM fragments WHERE fragment_id IN ({placeholders})",
            fragment_ids,
        ).fetchall()
        for fid, content in rows:
            result[fid] = content
        return result

    def _get_fragment_meta(self, fragment_id: str) -> dict[str, Any]:
        row = self._fts._conn.execute(
            "SELECT file_path, start_line, end_line, language, parser_level FROM fragments WHERE fragment_id = ?",
            (fragment_id,),
        ).fetchone()
        if row:
            return {"file_path": row[0], "start_line": row[1], "end_line": row[2],
                    "language": row[3], "parser_level": row[4]}
        return {}

    def _tier_to_layer(self, tier: int) -> str:
        if tier == TRUST_CANON:
            return "L2_canon"
        if tier == TRUST_HIGH:
            return "L3_high_confidence"
        return "L4_contextual"
