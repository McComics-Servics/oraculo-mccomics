"""Verificaciones de arranque. Reporta degradado si falla algun check no critico."""
from __future__ import annotations
import logging
import sys
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PreFlightReport:
    ok: bool
    critical_failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)


def run_pre_flight() -> PreFlightReport:
    rep = PreFlightReport(ok=True)
    if sys.version_info < (3, 11):
        rep.ok = False
        rep.critical_failures.append(f"Python {sys.version_info[:2]} < 3.11 requerido")
    rep.info.append(f"Python {sys.version.split()[0]} OK")

    try:
        import yaml  # noqa: F401
        rep.info.append("PyYAML disponible")
    except ImportError:
        rep.ok = False
        rep.critical_failures.append("PyYAML no instalado")

    return rep
