"""
Modulo: oraculo.polyglot.L3_patterns.rpg_parser
Proposito: Parser RPG L3 — extrae subrutinas, indicadores, spec types (H/F/D/C/O/P).
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.3 (Nivel L3)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_SPEC_TYPE_RE = re.compile(r"^(\s{5})?([HFDCOP])", re.IGNORECASE)
_BEGSR_RE = re.compile(r"\bBEGSR\b", re.IGNORECASE)
_ENDSR_RE = re.compile(r"\bENDSR\b", re.IGNORECASE)
_EXSR_RE = re.compile(r"\bEXSR\s+([\w]+)", re.IGNORECASE)
_DCL_PROC_RE = re.compile(r"^\s*DCL-PROC\s+([\w]+)", re.IGNORECASE)
_DCL_S_RE = re.compile(r"^\s*DCL-S\s+([\w]+)", re.IGNORECASE)
_DCL_DS_RE = re.compile(r"^\s*DCL-DS\s+([\w]+)", re.IGNORECASE)
_CALL_RE = re.compile(r"\bCALL[P]?\s*\(?\s*'?([\w]+)'?\s*\)?", re.IGNORECASE)
_COPY_RE = re.compile(r"/COPY\s+([\w/]+)", re.IGNORECASE)


@dataclass
class RpgSubroutine:
    name: str
    start_line: int
    end_line: int = 0


@dataclass
class RpgProcedure:
    name: str
    start_line: int
    end_line: int = 0


@dataclass
class RpgParseResult:
    subroutines: list[RpgSubroutine] = field(default_factory=list)
    procedures: list[RpgProcedure] = field(default_factory=list)
    variables: list[str] = field(default_factory=list)
    data_structures: list[str] = field(default_factory=list)
    exsr_targets: list[str] = field(default_factory=list)
    call_targets: list[str] = field(default_factory=list)
    copy_members: list[str] = field(default_factory=list)
    spec_counts: dict[str, int] = field(default_factory=dict)
    line_count: int = 0
    is_free_format: bool = False


def parse_rpg(content: str) -> RpgParseResult:
    """Parsea codigo RPG (fixed y free format) y extrae estructura."""
    lines = content.splitlines()
    result = RpgParseResult(line_count=len(lines))

    if any("**FREE" in l.upper() for l in lines[:5]):
        result.is_free_format = True

    current_sr: RpgSubroutine | None = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped:
            continue

        # Spec type counting (fixed format)
        if not result.is_free_format and len(line) >= 6:
            spec = line[5:6].upper() if len(line) > 5 else ""
            if spec in "HFDCOP":
                result.spec_counts[spec] = result.spec_counts.get(spec, 0) + 1

        # BEGSR / ENDSR (subroutines)
        if _BEGSR_RE.search(line):
            sr_name = _extract_sr_name(line)
            current_sr = RpgSubroutine(name=sr_name, start_line=i)
            result.subroutines.append(current_sr)
        elif _ENDSR_RE.search(line):
            if current_sr:
                current_sr.end_line = i
                current_sr = None

        # DCL-PROC (free format procedures)
        m = _DCL_PROC_RE.match(stripped)
        if m:
            result.procedures.append(RpgProcedure(name=m.group(1), start_line=i))

        # DCL-S (variables)
        m = _DCL_S_RE.match(stripped)
        if m:
            result.variables.append(m.group(1))

        # DCL-DS (data structures)
        m = _DCL_DS_RE.match(stripped)
        if m:
            result.data_structures.append(m.group(1))

        # EXSR targets
        for m in _EXSR_RE.finditer(line):
            target = m.group(1)
            if target not in result.exsr_targets:
                result.exsr_targets.append(target)

        # CALL targets
        for m in _CALL_RE.finditer(line):
            target = m.group(1)
            if target not in result.call_targets:
                result.call_targets.append(target)

        # /COPY
        for m in _COPY_RE.finditer(line):
            member = m.group(1)
            if member not in result.copy_members:
                result.copy_members.append(member)

    return result


def _extract_sr_name(line: str) -> str:
    """Extrae nombre de subrutina de una linea BEGSR."""
    parts = line.upper().split("BEGSR")
    if len(parts) > 1:
        name = parts[1].strip().rstrip(";").strip()
        if name:
            return name
    before = parts[0].strip()
    tokens = before.split()
    return tokens[-1] if tokens else "UNKNOWN"
