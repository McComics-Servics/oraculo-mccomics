"""
Modulo: oraculo.polyglot.injection_detector
Proposito: Detectar patrones de prompt injection en fragmentos (M18 Banking).
"""
from __future__ import annotations
import re

_INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions"),
    re.compile(r"(?i)system\s*:"),
    re.compile(r"<\|im_start\|>"),
    re.compile(r"(?i)you\s+are\s+now\s+"),
    re.compile(r"(?i)forget\s+(everything|all)"),
    re.compile(r"\[INST\]"),
    re.compile(r"(?i)act\s+as\s+"),
]


def detect_injection(text: str) -> list[str]:
    """Retorna lista de patrones detectados. Lista vacia = limpio."""
    found = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            found.append(pattern.pattern)
    return found
