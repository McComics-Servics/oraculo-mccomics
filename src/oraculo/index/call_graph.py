"""
Modulo: oraculo.index.call_graph
Proposito: Grafo de llamadas entre simbolos. Tolerante a dispatch dinamico (M14).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DYNAMIC_DISPATCH_MARKERS = {
    "send", "method_missing", "define_method", "__getattr__",
    "getattr", "invoke", "call", "apply", "reflect",
}


@dataclass(frozen=True)
class CallEdge:
    caller_id: str
    callee_id: str
    call_line: int
    dynamic_dispatch: bool = False


def detect_dynamic_dispatch(line: str) -> bool:
    lower = line.lower()
    return any(m in lower for m in DYNAMIC_DISPATCH_MARKERS)
