"""
Modulo: oraculo.cognitive.reranker
Proposito: Reranker LLM — re-ordena resultados RRF usando el modelo para mejor precision.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 5.2
"""
from __future__ import annotations
import logging
import re
from dataclasses import dataclass

from oraculo.cognitive.provider import LLMProvider, LLMRequest

logger = logging.getLogger(__name__)

RERANK_SYSTEM = (
    "Eres un evaluador de relevancia de fragmentos de codigo. "
    "Dada una QUERY y un FRAGMENTO, evalua la relevancia del fragmento en una escala de 0 a 10. "
    "Responde SOLO con el numero. Nada mas."
)


@dataclass(frozen=True)
class RerankResult:
    fragment_id: str
    original_score: float
    rerank_score: float
    combined_score: float


def rerank_fragments(provider: LLMProvider, query: str,
                     fragments: list[tuple[str, str, float]],
                     weight_rerank: float = 0.6) -> list[RerankResult]:
    """
    Re-ordena fragmentos usando el LLM.

    Args:
        provider: LLM provider.
        query: Query original del usuario.
        fragments: Lista de (fragment_id, content, original_score).
        weight_rerank: Peso del score de reranking vs original (0-1).

    Returns:
        Lista de RerankResult ordenada por combined_score descendente.
    """
    results = []
    weight_orig = 1.0 - weight_rerank

    for frag_id, content, orig_score in fragments:
        rerank_score = _score_fragment(provider, query, content)
        normalized_rerank = rerank_score / 10.0
        combined = (orig_score * weight_orig) + (normalized_rerank * weight_rerank)
        results.append(RerankResult(
            fragment_id=frag_id,
            original_score=orig_score,
            rerank_score=rerank_score,
            combined_score=combined,
        ))

    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results


def _score_fragment(provider: LLMProvider, query: str, content: str) -> float:
    """Pide al LLM que evalúe la relevancia de un fragmento para la query."""
    truncated = content[:500]
    try:
        response = provider.generate(LLMRequest(
            prompt=f"QUERY: {query}\n\nFRAGMENTO:\n{truncated}",
            system_prompt=RERANK_SYSTEM,
            max_tokens=5,
            temperature=0.0,
        ))
        text = response.text.strip()
        numbers = re.findall(r"\d+(?:\.\d+)?", text)
        if numbers:
            score = float(numbers[0])
            return min(10.0, max(0.0, score))
        return 5.0
    except Exception as e:
        logger.warning("Error reranking: %s", e)
        return 5.0


def rerank_with_fallback(provider: LLMProvider | None, query: str,
                         fragments: list[tuple[str, str, float]]) -> list[RerankResult]:
    """Rerank con fallback: si no hay LLM, retorna scores originales normalizados."""
    if provider and provider.is_available:
        return rerank_fragments(provider, query, fragments)

    results = []
    for frag_id, content, orig_score in fragments:
        results.append(RerankResult(
            fragment_id=frag_id,
            original_score=orig_score,
            rerank_score=5.0,
            combined_score=orig_score,
        ))
    results.sort(key=lambda r: r.combined_score, reverse=True)
    return results
