"""
Modulo: oraculo.polyglot.L2_antlr.cobol_parser
Proposito: Parser COBOL L2 — extrae divisiones, secciones, parrafos, PERFORM targets, variables WORKING-STORAGE.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.3 (Nivel L2)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# COBOL column layout: 1-6 sequence, 7 indicator, 8-11 area A, 12-72 area B
_DIVISION_RE = re.compile(r"(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION", re.IGNORECASE)
_SECTION_RE = re.compile(r"^\s{0,7}(\S[\w-]+)\s+SECTION\s*\.", re.IGNORECASE)
_PARAGRAPH_RE = re.compile(r"^\s*([\w-]{2,30})\s*\.\s*$", re.IGNORECASE)
_PERFORM_RE = re.compile(r"\bPERFORM\s+([\w-]+)", re.IGNORECASE)
_CALL_RE = re.compile(r"\bCALL\s+['\"]?([\w-]+)['\"]?", re.IGNORECASE)
_COPY_RE = re.compile(r"\bCOPY\s+([\w-]+)", re.IGNORECASE)
_PIC_RE = re.compile(r"\b(\d{2})\s+([\w-]+)\s+PIC\s+", re.IGNORECASE)
_PROGRAM_ID_RE = re.compile(r"\bPROGRAM-ID\.\s*([\w-]+)", re.IGNORECASE)


@dataclass
class CobolDivision:
    name: str
    start_line: int
    end_line: int = 0


@dataclass
class CobolSection:
    name: str
    division: str
    start_line: int
    end_line: int = 0


@dataclass
class CobolParagraph:
    name: str
    section: str
    start_line: int
    end_line: int = 0


@dataclass
class CobolVariable:
    name: str
    level: int
    line: int
    pic: str = ""


@dataclass
class CobolParseResult:
    program_id: str = ""
    divisions: list[CobolDivision] = field(default_factory=list)
    sections: list[CobolSection] = field(default_factory=list)
    paragraphs: list[CobolParagraph] = field(default_factory=list)
    variables: list[CobolVariable] = field(default_factory=list)
    perform_targets: list[str] = field(default_factory=list)
    call_targets: list[str] = field(default_factory=list)
    copy_statements: list[str] = field(default_factory=list)
    line_count: int = 0


def parse_cobol(content: str) -> CobolParseResult:
    """Parsea codigo COBOL y extrae estructura jerárquica."""
    lines = content.splitlines()
    result = CobolParseResult(line_count=len(lines))

    current_division = ""
    current_section = ""

    for i, raw_line in enumerate(lines, 1):
        line = _strip_cobol_columns(raw_line)
        if not line.strip() or _is_comment(raw_line):
            continue

        # Program ID
        m = _PROGRAM_ID_RE.search(line)
        if m and not result.program_id:
            result.program_id = m.group(1)

        # Division
        m = _DIVISION_RE.search(line)
        if m:
            if result.divisions:
                result.divisions[-1].end_line = i - 1
            div_name = m.group(1).upper()
            result.divisions.append(CobolDivision(name=div_name, start_line=i))
            current_division = div_name
            continue

        # Section
        m = _SECTION_RE.search(line)
        if m:
            if result.sections:
                result.sections[-1].end_line = i - 1
            sec_name = m.group(1).upper()
            result.sections.append(CobolSection(name=sec_name, division=current_division, start_line=i))
            current_section = sec_name
            continue

        # Paragraph (solo en PROCEDURE DIVISION)
        if current_division == "PROCEDURE":
            m = _PARAGRAPH_RE.match(line)
            if m:
                if result.paragraphs:
                    result.paragraphs[-1].end_line = i - 1
                para_name = m.group(1).upper()
                result.paragraphs.append(CobolParagraph(name=para_name, section=current_section, start_line=i))

        # PERFORM targets
        for m in _PERFORM_RE.finditer(line):
            target = m.group(1).upper()
            if target not in result.perform_targets:
                result.perform_targets.append(target)

        # CALL targets
        for m in _CALL_RE.finditer(line):
            target = m.group(1)
            if target not in result.call_targets:
                result.call_targets.append(target)

        # COPY statements
        for m in _COPY_RE.finditer(line):
            copybook = m.group(1)
            if copybook not in result.copy_statements:
                result.copy_statements.append(copybook)

        # Variables (DATA DIVISION)
        if current_division == "DATA":
            m = _PIC_RE.search(line)
            if m:
                level = int(m.group(1))
                var_name = m.group(2)
                result.variables.append(CobolVariable(name=var_name, level=level, line=i))

    # Close last entries
    if result.divisions:
        result.divisions[-1].end_line = len(lines)
    if result.sections:
        result.sections[-1].end_line = len(lines)
    if result.paragraphs:
        result.paragraphs[-1].end_line = len(lines)

    return result


def _strip_cobol_columns(line: str) -> str:
    """Remueve columnas 1-6 (sequence) y 7 (indicator) si la linea tiene formato fijo."""
    if len(line) >= 7 and line[6] in (' ', '-', '*', '/'):
        return line[7:]
    return line


def _is_comment(line: str) -> bool:
    """Detecta linea de comentario COBOL (asterisco en col 7)."""
    if len(line) >= 7 and line[6] == '*':
        return True
    stripped = line.lstrip()
    return stripped.startswith("*>")
