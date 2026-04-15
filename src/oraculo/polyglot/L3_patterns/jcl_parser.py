"""
Modulo: oraculo.polyglot.L3_patterns.jcl_parser
Proposito: Parser JCL L3 — extrae JOB, EXEC, DD, PROCs, program calls.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.3 (Nivel L3)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_JOB_RE = re.compile(r"^//(\w+)\s+JOB\b", re.IGNORECASE)
_EXEC_RE = re.compile(r"^//(\w*)\s+EXEC\s+(?:PGM=|PROC=)?(\w+)", re.IGNORECASE)
_DD_RE = re.compile(r"^//(\w+)\s+DD\b", re.IGNORECASE)
_PROC_RE = re.compile(r"^//(\w+)\s+PROC\b", re.IGNORECASE)
_INCLUDE_RE = re.compile(r"^//\s+INCLUDE\s+MEMBER=(\w+)", re.IGNORECASE)
_COMMENT_RE = re.compile(r"^//\*")
_PEND_RE = re.compile(r"^//\s+PEND\b", re.IGNORECASE)


@dataclass
class JclStep:
    name: str
    program: str
    line: int
    is_proc: bool = False


@dataclass
class JclDd:
    name: str
    step: str
    line: int


@dataclass
class JclParseResult:
    job_name: str = ""
    steps: list[JclStep] = field(default_factory=list)
    dd_statements: list[JclDd] = field(default_factory=list)
    procs_defined: list[str] = field(default_factory=list)
    programs_called: list[str] = field(default_factory=list)
    includes: list[str] = field(default_factory=list)
    line_count: int = 0


def parse_jcl(content: str) -> JclParseResult:
    """Parsea JCL y extrae estructura de job/steps/DDs."""
    lines = content.splitlines()
    result = JclParseResult(line_count=len(lines))
    current_step = ""

    for i, line in enumerate(lines, 1):
        if _COMMENT_RE.match(line):
            continue

        # JOB
        m = _JOB_RE.match(line)
        if m and not result.job_name:
            result.job_name = m.group(1)
            continue

        # PROC definition
        m = _PROC_RE.match(line)
        if m:
            result.procs_defined.append(m.group(1))
            continue

        # EXEC step
        m = _EXEC_RE.match(line)
        if m:
            step_name = m.group(1) or f"STEP{len(result.steps) + 1}"
            program = m.group(2)
            is_proc = "PROC=" in line.upper()
            result.steps.append(JclStep(name=step_name, program=program, line=i, is_proc=is_proc))
            current_step = step_name
            if program not in result.programs_called:
                result.programs_called.append(program)
            continue

        # DD
        m = _DD_RE.match(line)
        if m:
            result.dd_statements.append(JclDd(name=m.group(1), step=current_step, line=i))
            continue

        # INCLUDE MEMBER
        m = _INCLUDE_RE.match(line)
        if m:
            inc = m.group(1)
            if inc not in result.includes:
                result.includes.append(inc)

    return result
