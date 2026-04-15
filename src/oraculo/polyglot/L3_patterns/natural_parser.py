"""
Modulo: oraculo.polyglot.L3_patterns.natural_parser
Proposito: Parser Natural/Adabas L3 — extrae subprogramas, DEFINE DATA, PERFORM, CALLNAT.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.3 (Nivel L3)
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

_DEFINE_DATA_RE = re.compile(r"^\s*DEFINE\s+DATA\b", re.IGNORECASE)
_END_DEFINE_RE = re.compile(r"^\s*END-DEFINE\b", re.IGNORECASE)
_PERFORM_RE = re.compile(r"^\s*PERFORM\s+([\w-]+)", re.IGNORECASE)
_CALLNAT_RE = re.compile(r"^\s*CALLNAT\s+['\"]?([\w-]+)['\"]?", re.IGNORECASE)
_SUBROUTINE_RE = re.compile(r"^\s*DEFINE\s+SUBROUTINE\s+([\w-]+)", re.IGNORECASE)
_END_SUBROUTINE_RE = re.compile(r"^\s*END-SUBROUTINE\b", re.IGNORECASE)
_LOCAL_RE = re.compile(r"^\s*LOCAL\b", re.IGNORECASE)
_PARAMETER_RE = re.compile(r"^\s*PARAMETER\b", re.IGNORECASE)
_VAR_RE = re.compile(r"^\s*\d+\s+(#?[\w-]+)", re.IGNORECASE)


@dataclass
class NaturalSubroutine:
    name: str
    start_line: int
    end_line: int = 0


@dataclass
class NaturalParseResult:
    subroutines: list[NaturalSubroutine] = field(default_factory=list)
    local_variables: list[str] = field(default_factory=list)
    parameters: list[str] = field(default_factory=list)
    perform_targets: list[str] = field(default_factory=list)
    callnat_targets: list[str] = field(default_factory=list)
    has_define_data: bool = False
    line_count: int = 0


def parse_natural(content: str) -> NaturalParseResult:
    """Parsea codigo Natural/Adabas y extrae estructura."""
    lines = content.splitlines()
    result = NaturalParseResult(line_count=len(lines))
    in_define_data = False
    in_local = False
    in_parameter = False
    current_sr: NaturalSubroutine | None = None

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("*"):
            continue

        # DEFINE DATA block
        if _DEFINE_DATA_RE.match(stripped):
            in_define_data = True
            result.has_define_data = True
            continue

        if _END_DEFINE_RE.match(stripped):
            in_define_data = False
            in_local = False
            in_parameter = False
            continue

        if in_define_data:
            if _LOCAL_RE.match(stripped):
                in_local = True
                in_parameter = False
                continue
            if _PARAMETER_RE.match(stripped):
                in_parameter = True
                in_local = False
                continue
            m = _VAR_RE.match(stripped)
            if m:
                var_name = m.group(1)
                if in_local:
                    result.local_variables.append(var_name)
                elif in_parameter:
                    result.parameters.append(var_name)

        # Subroutines
        m = _SUBROUTINE_RE.match(stripped)
        if m:
            current_sr = NaturalSubroutine(name=m.group(1), start_line=i)
            result.subroutines.append(current_sr)
            continue

        if _END_SUBROUTINE_RE.match(stripped):
            if current_sr:
                current_sr.end_line = i
                current_sr = None
            continue

        # PERFORM
        m = _PERFORM_RE.match(stripped)
        if m:
            target = m.group(1)
            if target not in result.perform_targets:
                result.perform_targets.append(target)

        # CALLNAT
        m = _CALLNAT_RE.match(stripped)
        if m:
            target = m.group(1)
            if target not in result.callnat_targets:
                result.callnat_targets.append(target)

    return result
