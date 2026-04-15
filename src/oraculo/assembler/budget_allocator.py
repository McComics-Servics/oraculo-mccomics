"""
Modulo: oraculo.assembler.budget_allocator
Proposito: Reparte el token budget entre capas jerarquicas (L0-L6) segun perfil activo.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 4.2
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_TOTAL_BUDGET = 4096

LAYER_WEIGHTS = {
    "L0_system_prompt": 0.05,
    "L1_user_query": 0.10,
    "L2_canon": 0.25,
    "L3_high_confidence": 0.30,
    "L4_contextual": 0.15,
    "L5_call_graph": 0.10,
    "L6_history": 0.05,
}


@dataclass
class BudgetAllocation:
    layer: str
    tokens_allocated: int
    tokens_used: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.tokens_allocated - self.tokens_used)


class BudgetAllocator:
    """Distribuye token budget entre capas segun pesos configurables."""

    def __init__(self, total_budget: int = DEFAULT_TOTAL_BUDGET,
                 layer_weights: dict[str, float] | None = None):
        self._total = total_budget
        self._weights = layer_weights or dict(LAYER_WEIGHTS)
        self._allocations: dict[str, BudgetAllocation] = {}
        self._distribute()

    @property
    def total_budget(self) -> int:
        return self._total

    @property
    def allocations(self) -> dict[str, BudgetAllocation]:
        return dict(self._allocations)

    def _distribute(self) -> None:
        total_weight = sum(self._weights.values())
        for layer, weight in self._weights.items():
            tokens = int(self._total * weight / total_weight)
            self._allocations[layer] = BudgetAllocation(layer=layer, tokens_allocated=tokens)

    def consume(self, layer: str, tokens: int) -> int:
        """Consume tokens de una capa. Retorna tokens realmente consumidos."""
        alloc = self._allocations.get(layer)
        if not alloc:
            return 0
        actual = min(tokens, alloc.remaining)
        alloc.tokens_used += actual
        return actual

    def remaining(self, layer: str) -> int:
        alloc = self._allocations.get(layer)
        return alloc.remaining if alloc else 0

    def total_remaining(self) -> int:
        return sum(a.remaining for a in self._allocations.values())

    def summary(self) -> dict[str, dict[str, int]]:
        return {
            layer: {"allocated": a.tokens_allocated, "used": a.tokens_used, "remaining": a.remaining}
            for layer, a in self._allocations.items()
        }
