"""
Modulo: oraculo.polyglot.L2_antlr.pli_parser
Proposito: Parser PL/I L2 — extrae procedimientos, declaraciones, CALL targets.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.3 (Nivel L2)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_PROC_RE = re.compile(r"^\s*([\w$#@]+)\s*:\s*(?:PROC|PROCEDURE)\b", re.IGNORECASE)
_PROC_END_RE = re.compile(r"^\s*END\s+([\w$#@]+)\s*;", re.IGNORECASE)
_DCL_RE = re.compile(r"^\s*(?:DCL|DECLARE)\s+([\w$#@]+)", re.IGNORECASE)
_CALL_RE = re.compile(r"\bCALL\s+([\w$#@]+)", re.IGNORECASE)
_INCLUDE_RE = re.compile(r"%INCLUDE\s+([\w$#@]+)", re.IGNORECASE)


@dataclass
class PliProcedure:
    name: str
    start_line: int
    end_line: int = 0


@dataclass
class PliVariable:
    name: str
    line: int


@dataclass
class PliParseResult:
    procedures: list[PliProcedure] = field(default_factory=list)
    variables: list[PliVariable] = field(default_factory=list)
    call_targets: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    line_count: int = 0


def parse_pli(content: str) -> PliParseResult:
    """Parsea codigo PL/I y extrae estructura."""
    lines = content.splitlines()
    result = PliParseResult(line_count=len(lines))
    proc_stack: list[PliProcedure] = []

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("/*"):
            continue

        # Procedure
        m = _PROC_RE.match(line)
        if m:
            proc = PliProcedure(name=m.group(1).upper(), start_line=i)
            proc_stack.append(proc)
            result.procedures.append(proc)

        # End Procedure
        m = _PROC_END_RE.match(line)
        if m and proc_stack:
            proc_stack[-1].end_line = i
            proc_stack.pop()

        # Declarations
        m = _DCL_RE.match(line)
        if m:
            result.variables.append(PliVariable(name=m.group(1), line=i))

        # CALL targets
        for m in _CALL_RE.finditer(line):
            target = m.group(1).upper()
            if target not in result.call_targets:
                result.call_targets.append(target)

        # %INCLUDE
        for m in _INCLUDE_RE.finditer(line):
            inc = m.group(1)
            if inc not in result.includes:
                result.includes.append(inc)

    for proc in proc_stack:
        if proc.end_line == 0:
            proc.end_line = len(lines)

    return result
