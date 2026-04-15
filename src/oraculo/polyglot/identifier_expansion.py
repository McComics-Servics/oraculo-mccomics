"""
Modulo: oraculo.polyglot.identifier_expansion
Proposito: Expandir abreviaturas McComics usando glosario.
"""
from __future__ import annotations
from pathlib import Path

import yaml


def load_glossary(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def expand_query(query: str, glossary: dict[str, str]) -> str:
    """Expande abreviaturas del glosario en la query."""
    tokens = query.split()
    expanded = []
    for t in tokens:
        upper = t.upper()
        if upper in glossary:
            expanded.append(f"{t} {glossary[upper]}")
        else:
            expanded.append(t)
    return " ".join(expanded)
