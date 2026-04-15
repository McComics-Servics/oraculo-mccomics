"""
Modulo: oraculo.index.duckdb_store
Proposito: Almacen vectorial con DuckDB para embeddings y busqueda semantica.
Documento de LEY: PLAN_MAESTRO_v4.md (Capa 2) + CONTEXT_ASSEMBLY_POLICY.md
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any

import duckdb

logger = logging.getLogger(__name__)


class DuckDbStore:
    """Almacen DuckDB para vectores, metadatos y tabla de simbolos."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn: duckdb.DuckDBPyConnection | None = None

    def open(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = duckdb.connect(str(self._db_path))
        self._create_tables()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _create_tables(self) -> None:
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS file_metadata (
                file_path VARCHAR PRIMARY KEY,
                file_hash VARCHAR NOT NULL,
                language VARCHAR,
                parser_level VARCHAR,
                encoding VARCHAR,
                line_count INTEGER,
                size_bytes BIGINT,
                last_indexed TIMESTAMP DEFAULT current_timestamp,
                stale BOOLEAN DEFAULT false
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS symbols (
                symbol_id VARCHAR PRIMARY KEY,
                file_path VARCHAR NOT NULL,
                name VARCHAR NOT NULL,
                kind VARCHAR,
                start_line INTEGER,
                end_line INTEGER,
                signature VARCHAR,
                parent_symbol VARCHAR,
                FOREIGN KEY (file_path) REFERENCES file_metadata(file_path)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS call_edges (
                caller_id VARCHAR NOT NULL,
                callee_id VARCHAR NOT NULL,
                call_line INTEGER,
                dynamic_dispatch BOOLEAN DEFAULT false,
                PRIMARY KEY (caller_id, callee_id, call_line)
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                fragment_id VARCHAR PRIMARY KEY,
                file_path VARCHAR NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                embedding FLOAT[],
                model_name VARCHAR,
                trust_tier INTEGER DEFAULT 2,
                indexed_at TIMESTAMP DEFAULT current_timestamp
            )
        """)

    def upsert_file_metadata(self, file_path: str, file_hash: str, language: str,
                              parser_level: str, encoding: str,
                              line_count: int, size_bytes: int) -> None:
        self._conn.execute("""
            INSERT OR REPLACE INTO file_metadata
            (file_path, file_hash, language, parser_level, encoding, line_count, size_bytes, stale)
            VALUES (?, ?, ?, ?, ?, ?, ?, false)
        """, [file_path, file_hash, language, parser_level, encoding, line_count, size_bytes])

    def mark_stale(self, file_path: str) -> None:
        self._conn.execute("UPDATE file_metadata SET stale = true WHERE file_path = ?", [file_path])

    def get_file_hash(self, file_path: str) -> str | None:
        result = self._conn.execute(
            "SELECT file_hash FROM file_metadata WHERE file_path = ?", [file_path]
        ).fetchone()
        return result[0] if result else None

    def insert_symbol(self, symbol_id: str, file_path: str, name: str, kind: str,
                       start_line: int, end_line: int,
                       signature: str = "", parent: str | None = None) -> None:
        self._conn.execute("""
            INSERT OR REPLACE INTO symbols
            (symbol_id, file_path, name, kind, start_line, end_line, signature, parent_symbol)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [symbol_id, file_path, name, kind, start_line, end_line, signature, parent])

    def insert_call_edge(self, caller_id: str, callee_id: str,
                          call_line: int, dynamic: bool = False) -> None:
        self._conn.execute("""
            INSERT OR IGNORE INTO call_edges VALUES (?, ?, ?, ?)
        """, [caller_id, callee_id, call_line, dynamic])

    def insert_embedding(self, fragment_id: str, file_path: str,
                          start_line: int, end_line: int,
                          embedding: list[float], model_name: str,
                          trust_tier: int = 2) -> None:
        self._conn.execute("""
            INSERT OR REPLACE INTO embeddings
            (fragment_id, file_path, start_line, end_line, embedding, model_name, trust_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [fragment_id, file_path, start_line, end_line, embedding, model_name, trust_tier])

    def search_symbols(self, name_pattern: str, limit: int = 20) -> list[dict[str, Any]]:
        rows = self._conn.execute("""
            SELECT symbol_id, file_path, name, kind, start_line, end_line, signature
            FROM symbols WHERE name ILIKE ?
            LIMIT ?
        """, [f"%{name_pattern}%", limit]).fetchall()
        return [{"symbol_id": r[0], "file_path": r[1], "name": r[2], "kind": r[3],
                 "start_line": r[4], "end_line": r[5], "signature": r[6]} for r in rows]

    def get_callers(self, symbol_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT caller_id FROM call_edges WHERE callee_id = ?", [symbol_id]
        ).fetchall()
        return [r[0] for r in rows]

    def get_callees(self, symbol_id: str) -> list[str]:
        rows = self._conn.execute(
            "SELECT callee_id FROM call_edges WHERE caller_id = ?", [symbol_id]
        ).fetchall()
        return [r[0] for r in rows]

    def delete_by_file(self, file_path: str) -> None:
        self._conn.execute("DELETE FROM embeddings WHERE file_path = ?", [file_path])
        self._conn.execute("DELETE FROM symbols WHERE file_path = ?", [file_path])
        self._conn.execute("DELETE FROM file_metadata WHERE file_path = ?", [file_path])

    def count_files(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM file_metadata").fetchone()[0]

    def count_symbols(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]

    def count_embeddings(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

    def stale_files(self) -> list[str]:
        rows = self._conn.execute(
            "SELECT file_path FROM file_metadata WHERE stale = true"
        ).fetchall()
        return [r[0] for r in rows]
