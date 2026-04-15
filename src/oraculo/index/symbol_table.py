"""
Modulo: oraculo.index.symbol_table
Proposito: Tabla de simbolos multi-lenguaje con resolucion de includes/imports.
"""
from __future__ import annotations
import hashlib
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Symbol:
    symbol_id: str
    file_path: str
    name: str
    kind: str  # function, class, method, variable, module
    start_line: int
    end_line: int
    signature: str = ""
    parent: str | None = None


def make_symbol_id(file_path: str, name: str, start_line: int) -> str:
    raw = f"{file_path}:{name}:{start_line}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
