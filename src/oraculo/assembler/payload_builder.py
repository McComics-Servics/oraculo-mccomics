"""
Modulo: oraculo.assembler.payload_builder
Proposito: Construye el JSON de respuesta con provenance y metadatos completos.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 4.3 + API_CONTRACT_SPEC.md
"""
from __future__ import annotations
import logging
import time
from dataclasses import dataclass, field, asdict
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FragmentPayload:
    fragment_id: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    trust_tier: int
    rrf_score: float
    sources: list[str]
    language: str = "unknown"
    parser_level: str = "unknown"


@dataclass
class AssemblyPayload:
    query: str
    profile: str
    fragments: list[FragmentPayload] = field(default_factory=list)
    budget_summary: dict[str, Any] = field(default_factory=dict)
    total_fragments: int = 0
    dedup_removed: int = 0
    assembly_time_ms: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PayloadBuilder:
    """Construye el payload de respuesta para la API."""

    def __init__(self, query: str, profile: str):
        self._query = query
        self._profile = profile
        self._fragments: list[FragmentPayload] = []
        self._budget_summary: dict[str, Any] = {}
        self._dedup_removed = 0
        self._start = time.monotonic()

    def add_fragment(self, frag: FragmentPayload) -> None:
        self._fragments.append(frag)

    def set_budget_summary(self, summary: dict[str, Any]) -> None:
        self._budget_summary = summary

    def set_dedup_removed(self, count: int) -> None:
        self._dedup_removed = count

    def build(self) -> AssemblyPayload:
        elapsed = (time.monotonic() - self._start) * 1000
        return AssemblyPayload(
            query=self._query,
            profile=self._profile,
            fragments=self._fragments,
            budget_summary=self._budget_summary,
            total_fragments=len(self._fragments),
            dedup_removed=self._dedup_removed,
            assembly_time_ms=round(elapsed, 2),
        )
