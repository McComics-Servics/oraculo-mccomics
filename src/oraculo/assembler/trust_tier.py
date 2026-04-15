"""
Modulo: oraculo.assembler.trust_tier
Proposito: Asignacion de trust tiers a fragmentos segun procedencia y perfil activo.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 4.1 + THREAT_MODEL seccion trust
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from oraculo.core.constants import TRUST_CANON, TRUST_HIGH, TRUST_CONTEXTUAL

logger = logging.getLogger(__name__)

CANON_SOURCES = frozenset({"official_docs", "stdlib", "verified_api"})
HIGH_SOURCES = frozenset({"project_code", "internal_lib", "tested_module"})


@dataclass(frozen=True)
class TierAssignment:
    fragment_id: str
    tier: int
    reason: str


def assign_tier(fragment_id: str, source_type: str, parser_level: str,
                has_tests: bool = False) -> TierAssignment:
    """Asigna trust tier a un fragmento basado en su procedencia."""
    if source_type in CANON_SOURCES:
        return TierAssignment(fragment_id, TRUST_CANON, f"fuente canon: {source_type}")

    if source_type in HIGH_SOURCES or has_tests:
        return TierAssignment(fragment_id, TRUST_HIGH, f"fuente high: {source_type}")

    if parser_level in ("L1_treesitter", "L2_antlr"):
        return TierAssignment(fragment_id, TRUST_HIGH, f"parser nivel alto: {parser_level}")

    return TierAssignment(fragment_id, TRUST_CONTEXTUAL, "fuente contextual — no verificada")


def filter_by_min_tier(assignments: list[TierAssignment], min_tier: int) -> list[TierAssignment]:
    """Filtra fragmentos que no cumplen el tier minimo (menor = mas confiable)."""
    return [a for a in assignments if a.tier <= min_tier]
