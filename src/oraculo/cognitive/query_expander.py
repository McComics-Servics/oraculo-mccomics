"""
Modulo: oraculo.cognitive.query_expander
Proposito: Expansion de queries usando LLM para mejorar recall.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 5
"""
from __future__ import annotations
import logging
import re

from oraculo.cognitive.provider import LLMProvider, LLMRequest

logger = logging.getLogger(__name__)

EXPANSION_SYSTEM = (
    "Eres un asistente de busqueda de codigo. "
    "Dada una query del usuario, genera 3 variantes de busqueda complementarias "
    "que capturen sinonimos, abreviaciones y conceptos relacionados. "
    "Responde SOLO con las 3 variantes, una por linea, sin numeracion ni explicacion."
)


def expand_query(provider: LLMProvider, original_query: str,
                 max_variants: int = 3) -> list[str]:
    """Genera variantes de busqueda complementarias usando el LLM."""
    try:
        response = provider.generate(LLMRequest(
            prompt=f"Query original: {original_query}",
            system_prompt=EXPANSION_SYSTEM,
            max_tokens=150,
            temperature=0.3,
        ))
        lines = [l.strip() for l in response.text.strip().splitlines() if l.strip()]
        lines = [re.sub(r"^\d+[\.\)\-]\s*", "", l) for l in lines]
        variants = [l for l in lines if len(l) > 2][:max_variants]
        logger.debug("Query expandida: %s -> %s", original_query, variants)
        return variants
    except Exception as e:
        logger.warning("Error expandiendo query: %s", e)
        return []


def expand_with_fallback(provider: LLMProvider | None, original_query: str) -> list[str]:
    """Expansion con fallback: si no hay LLM, retorna solo la query original."""
    variants = [original_query]
    if provider and provider.is_available:
        expanded = expand_query(provider, original_query)
        variants.extend(expanded)
    return variants
