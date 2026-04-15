"""
Modulo: oraculo.polyglot.lexical_skeleton
Proposito: Parser L4 — analisis agnostico para CUALQUIER archivo de texto sin parser dedicado.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.3
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_COMMENT_MARKERS = {"#", "//", "--", ";", "!"}
_KEYWORD_BLACKLIST = frozenset({
    "the", "and", "for", "not", "with", "this", "that", "from",
    "def", "end", "class", "return", "import", "if", "else", "elif",
    "do", "while", "function", "var", "let", "const", "int", "void",
})
_IDENT_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]{2,})\b")
_COBOL_COLS = re.compile(r"^(.{6})(.)(.{4})(.{0,60})", re.MULTILINE)


@dataclass
class SkeletonFragment:
    start_line: int
    end_line: int
    text: str
    identifiers: list[str] = field(default_factory=list)
    comment_ratio: float = 0.0
    indent_level: int = 0
    is_cobol_area_a: bool = False


def extract_skeleton(content: str, is_cobol: bool = False) -> list[SkeletonFragment]:
    """Extrae fragmentos por indentacion y lineas en blanco."""
    lines = content.splitlines()
    if not lines:
        return []

    fragments: list[SkeletonFragment] = []
    current_lines: list[str] = []
    start = 0
    blank_count = 0

    for i, line in enumerate(lines):
        stripped = line.rstrip()
        if not stripped:
            blank_count += 1
            if blank_count >= 2 and current_lines:
                frag = _build_fragment(start, i - blank_count, current_lines, is_cobol)
                fragments.append(frag)
                current_lines = []
                blank_count = 0
                start = i + 1
            continue

        if blank_count > 0 and not current_lines:
            start = i
        blank_count = 0
        current_lines.append(stripped)

    if current_lines:
        frag = _build_fragment(start, start + len(current_lines) - 1, current_lines, is_cobol)
        fragments.append(frag)

    return fragments


def _build_fragment(start: int, end: int, lines: list[str], is_cobol: bool) -> SkeletonFragment:
    text = "\n".join(lines)
    idents = _extract_identifiers(text)
    comment_lines = sum(1 for l in lines if _is_comment_line(l))
    ratio = comment_lines / max(len(lines), 1)
    indent = _min_indent(lines)
    return SkeletonFragment(
        start_line=start + 1,
        end_line=end + 1,
        text=text,
        identifiers=idents,
        comment_ratio=ratio,
        indent_level=indent,
        is_cobol_area_a=is_cobol and any(_is_cobol_area_a(l) for l in lines),
    )


def _extract_identifiers(text: str) -> list[str]:
    found = _IDENT_RE.findall(text)
    return sorted(set(t for t in found if t.lower() not in _KEYWORD_BLACKLIST))


def _is_comment_line(line: str) -> bool:
    stripped = line.lstrip()
    return any(stripped.startswith(m) for m in _COMMENT_MARKERS)


def _min_indent(lines: list[str]) -> int:
    indents = []
    for l in lines:
        stripped = l.lstrip()
        if stripped:
            indents.append(len(l) - len(stripped))
    return min(indents) if indents else 0


def _is_cobol_area_a(line: str) -> bool:
    if len(line) < 12:
        return False
    return line[7:11].strip() != "" and line[7] != " "
