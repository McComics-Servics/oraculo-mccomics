"""Modo degradado: registra y reporta funcionalidad reducida."""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DegradedState:
    active: bool = False
    reasons: list[str] = field(default_factory=list)

    def add(self, reason: str) -> None:
        self.active = True
        self.reasons.append(reason)
        logger.warning("MODO DEGRADADO: %s", reason)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"active": self.active, "reasons": self.reasons}, indent=2),
                        encoding="utf-8")

    def summary(self) -> str:
        if not self.active:
            return "Sistema operando normalmente"
        return f"MODO DEGRADADO — {len(self.reasons)} problemas: {'; '.join(self.reasons)}"
