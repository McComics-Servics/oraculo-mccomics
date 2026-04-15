"""
Modulo: oraculo.retrieval.weight_learner
Proposito: Aprendizaje activo de pesos RRF con feedback binario (thumbs up/down). Mejora M5.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 3.5
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {"bm25": 1.0, "vector": 1.0, "ast": 0.8, "call_graph": 0.5}
LEARNING_RATE = 0.05
MIN_WEIGHT = 0.1
MAX_WEIGHT = 3.0


@dataclass
class WeightState:
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    feedback_count: int = 0


class WeightLearner:
    """Ajusta pesos de fuentes RRF basado en feedback del usuario."""

    def __init__(self, state_file: Path | None = None):
        self._state_file = state_file
        self._state = self._load()

    @property
    def weights(self) -> dict[str, float]:
        return dict(self._state.weights)

    @property
    def feedback_count(self) -> int:
        return self._state.feedback_count

    def record_feedback(self, sources_used: list[str], positive: bool) -> None:
        """Registra feedback positivo o negativo para las fuentes usadas en un resultado."""
        delta = LEARNING_RATE if positive else -LEARNING_RATE
        for src in sources_used:
            if src in self._state.weights:
                new_w = self._state.weights[src] + delta
                self._state.weights[src] = max(MIN_WEIGHT, min(MAX_WEIGHT, new_w))
        self._state.feedback_count += 1
        self._save()

    def _load(self) -> WeightState:
        if self._state_file and self._state_file.exists():
            try:
                data = json.loads(self._state_file.read_text(encoding="utf-8"))
                return WeightState(
                    weights=data.get("weights", dict(DEFAULT_WEIGHTS)),
                    feedback_count=data.get("feedback_count", 0),
                )
            except (json.JSONDecodeError, KeyError):
                logger.warning("Archivo de pesos corrupto, usando defaults")
        return WeightState()

    def _save(self) -> None:
        if self._state_file:
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            self._state_file.write_text(
                json.dumps(asdict(self._state), indent=2),
                encoding="utf-8",
            )
