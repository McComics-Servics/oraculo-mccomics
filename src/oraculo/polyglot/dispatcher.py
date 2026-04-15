"""
Modulo: oraculo.polyglot.dispatcher
Proposito: Router central que decide que parser usar para cada archivo (L1→L2→L3→L4 fallback).
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.2
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ParserLevel(Enum):
    L1_TREESITTER = "L1_treesitter"
    L2_ANTLR = "L2_antlr"
    L3_PATTERNS = "L3_patterns"
    L4_LEXICAL = "L4_lexical"


L1_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".rb", ".go", ".rs", ".java",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".kt", ".swift",
    ".scala", ".lua", ".sh", ".bash", ".sql", ".html", ".css",
    ".yaml", ".yml", ".json", ".md", ".toml",
}

L2_EXTENSIONS = {
    ".cob", ".cbl", ".cpy",  # COBOL
    ".pli", ".pl1",           # PL/I
    ".f", ".f77", ".f90", ".f95", ".for",  # Fortran
    ".ada", ".adb", ".ads",  # Ada
    ".pas", ".pp",            # Pascal
}

L3_EXTENSIONS = {
    ".rpg", ".rpgle", ".rpg4",  # RPG
    ".jcl", ".proc",            # JCL
    ".clist",                    # CLIST
    ".rexx", ".rex",            # REXX
    ".mps", ".m",               # MUMPS
    ".prg", ".ch",              # Clipper/FoxPro
    ".asm", ".s",               # Assembler
}


@dataclass
class DispatchResult:
    path: Path
    level: ParserLevel
    language: str


def dispatch(path: Path) -> DispatchResult:
    """Determina que parser usar para un archivo dado."""
    ext = path.suffix.lower()
    name = path.name.lower()

    if ext in L1_EXTENSIONS:
        lang = _ext_to_lang_l1(ext)
        return DispatchResult(path=path, level=ParserLevel.L1_TREESITTER, language=lang)

    if ext in L2_EXTENSIONS:
        lang = _ext_to_lang_l2(ext)
        return DispatchResult(path=path, level=ParserLevel.L2_ANTLR, language=lang)

    if ext in L3_EXTENSIONS:
        lang = _ext_to_lang_l3(ext)
        return DispatchResult(path=path, level=ParserLevel.L3_PATTERNS, language=lang)

    return DispatchResult(path=path, level=ParserLevel.L4_LEXICAL, language="unknown")


def _ext_to_lang_l1(ext: str) -> str:
    mapping = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript", ".rb": "ruby",
        ".go": "go", ".rs": "rust", ".java": "java",
        ".c": "c", ".h": "c", ".cpp": "cpp", ".hpp": "cpp",
        ".cs": "c_sharp", ".php": "php", ".kt": "kotlin",
        ".swift": "swift", ".scala": "scala", ".lua": "lua",
        ".sh": "bash", ".bash": "bash", ".sql": "sql",
        ".html": "html", ".css": "css",
        ".yaml": "yaml", ".yml": "yaml", ".json": "json",
        ".md": "markdown", ".toml": "toml",
    }
    return mapping.get(ext, "unknown")


def _ext_to_lang_l2(ext: str) -> str:
    if ext in (".cob", ".cbl", ".cpy"):
        return "cobol"
    if ext in (".pli", ".pl1"):
        return "pli"
    if ext in (".f", ".f77", ".f90", ".f95", ".for"):
        return "fortran"
    if ext in (".ada", ".adb", ".ads"):
        return "ada"
    if ext in (".pas", ".pp"):
        return "pascal"
    return "unknown"


def _ext_to_lang_l3(ext: str) -> str:
    if ext in (".rpg", ".rpgle", ".rpg4"):
        return "rpg"
    if ext in (".jcl", ".proc"):
        return "jcl"
    if ext == ".clist":
        return "clist"
    if ext in (".rexx", ".rex"):
        return "rexx"
    if ext in (".mps", ".m"):
        return "mumps"
    if ext in (".prg", ".ch"):
        return "clipper"
    if ext in (".asm", ".s"):
        return "asm_ibm"
    return "unknown"
