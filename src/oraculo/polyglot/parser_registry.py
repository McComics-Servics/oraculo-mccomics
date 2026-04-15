"""
Modulo: oraculo.polyglot.parser_registry
Proposito: Registro central de parsers por nivel. Conecta dispatcher con parsers concretos.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

from oraculo.polyglot.dispatcher import ParserLevel

logger = logging.getLogger(__name__)


def parse_file(path: Path, content: str, level: ParserLevel, language: str) -> Any:
    """Parsea un archivo usando el parser apropiado segun nivel y lenguaje. Retorna resultado tipado."""

    if level == ParserLevel.L2_ANTLR:
        return _parse_l2(content, language)

    if level == ParserLevel.L3_PATTERNS:
        return _parse_l3(content, language)

    if level == ParserLevel.L4_LEXICAL:
        from oraculo.polyglot.lexical_skeleton import extract_skeleton
        is_cobol = language == "cobol"
        return extract_skeleton(content, is_cobol=is_cobol)

    # L1 tree-sitter — placeholder hasta tener bindings
    from oraculo.polyglot.lexical_skeleton import extract_skeleton
    return extract_skeleton(content)


def _parse_l2(content: str, language: str) -> Any:
    """Selecciona parser L2 segun lenguaje."""
    if language == "cobol":
        from oraculo.polyglot.L2_antlr.cobol_parser import parse_cobol
        return parse_cobol(content)

    if language == "pli":
        from oraculo.polyglot.L2_antlr.pli_parser import parse_pli
        return parse_pli(content)

    # Fallback a skeleton para L2 sin parser dedicado
    from oraculo.polyglot.lexical_skeleton import extract_skeleton
    return extract_skeleton(content)


def _parse_l3(content: str, language: str) -> Any:
    """Selecciona parser L3 segun lenguaje."""
    if language == "rpg":
        from oraculo.polyglot.L3_patterns.rpg_parser import parse_rpg
        return parse_rpg(content)

    if language == "jcl":
        from oraculo.polyglot.L3_patterns.jcl_parser import parse_jcl
        return parse_jcl(content)

    if language == "natural":
        from oraculo.polyglot.L3_patterns.natural_parser import parse_natural
        return parse_natural(content)

    from oraculo.polyglot.lexical_skeleton import extract_skeleton
    return extract_skeleton(content)


def supported_languages() -> dict[str, str]:
    """Retorna mapa de lenguaje -> nivel de parser disponible."""
    return {
        "python": "L1", "javascript": "L1", "typescript": "L1", "ruby": "L1",
        "go": "L1", "rust": "L1", "java": "L1", "c": "L1", "cpp": "L1",
        "c_sharp": "L1", "php": "L1", "kotlin": "L1", "swift": "L1",
        "scala": "L1", "lua": "L1", "bash": "L1", "sql": "L1",
        "cobol": "L2", "pli": "L2", "fortran": "L2", "ada": "L2", "pascal": "L2",
        "rpg": "L3", "jcl": "L3", "natural": "L3", "rexx": "L3",
        "clist": "L3", "mumps": "L3", "clipper": "L3", "asm_ibm": "L3",
    }
