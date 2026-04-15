"""
Modulo: oraculo.index.integrity_check
Proposito: Verificacion de integridad de las DBs (quick y full). M9 v4.
"""
from __future__ import annotations
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IntegrityReport:
    ok: bool = True
    checks_run: int = 0
    failures: list[str] = field(default_factory=list)

    def fail(self, msg: str) -> None:
        self.ok = False
        self.failures.append(msg)


def check_sqlite(db_path: Path, full: bool = False) -> IntegrityReport:
    report = IntegrityReport()
    if not db_path.exists():
        report.fail(f"DB no existe: {db_path}")
        return report
    try:
        conn = sqlite3.connect(str(db_path))
        if full:
            result = conn.execute("PRAGMA integrity_check").fetchone()
            report.checks_run += 1
            if result[0] != "ok":
                report.fail(f"integrity_check fallo: {result[0]}")
        else:
            result = conn.execute("PRAGMA quick_check").fetchone()
            report.checks_run += 1
            if result[0] != "ok":
                report.fail(f"quick_check fallo: {result[0]}")
        conn.close()
    except Exception as e:
        report.fail(f"Error al verificar {db_path}: {e}")
    return report


def check_duckdb(db_path: Path) -> IntegrityReport:
    report = IntegrityReport()
    if not db_path.exists():
        report.fail(f"DuckDB no existe: {db_path}")
        return report
    try:
        import duckdb
        conn = duckdb.connect(str(db_path), read_only=True)
        tables = conn.execute("SHOW TABLES").fetchall()
        report.checks_run += 1
        for (tbl,) in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
            report.checks_run += 1
        conn.close()
    except Exception as e:
        report.fail(f"Error al verificar {db_path}: {e}")
    return report
