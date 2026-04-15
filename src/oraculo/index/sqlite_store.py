"""
Modulo: oraculo.index.sqlite_store
Proposito: Almacen BM25 con SQLite FTS5 para busqueda lexica exacta.
Documento de LEY: PLAN_MAESTRO_v4.md (Capa 2)
"""
from __future__ import annotations
import hashlib
import logging
import sqlite3
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexedFragment:
    fragment_id: str
    file_path: str
    file_hash: str
    start_line: int
    end_line: int
    content: str
    language: str
    parser_level: str
    encoding: str


class SqliteFtsStore:
    """Almacen SQLite FTS5. WAL activado. Thread-safe via serialized mode."""

    def __init__(self, db_path: Path):
        self._db_path = db_path
        self._conn: sqlite3.Connection | None = None

    def open(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._create_tables()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _create_tables(self) -> None:
        c = self._conn
        c.execute("""
            CREATE TABLE IF NOT EXISTS fragments (
                fragment_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                file_hash TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                content TEXT NOT NULL,
                language TEXT,
                parser_level TEXT,
                encoding TEXT,
                indexed_at TEXT DEFAULT (datetime('now'))
            )
        """)
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fragments_fts
            USING fts5(content, fragment_id UNINDEXED, content=fragments, content_rowid=rowid)
        """)
        c.execute("""
            CREATE TRIGGER IF NOT EXISTS fragments_ai AFTER INSERT ON fragments BEGIN
                INSERT INTO fragments_fts(rowid, content, fragment_id)
                VALUES (new.rowid, new.content, new.fragment_id);
            END
        """)
        c.execute("""
            CREATE TRIGGER IF NOT EXISTS fragments_ad AFTER DELETE ON fragments BEGIN
                INSERT INTO fragments_fts(fragments_fts, rowid, content, fragment_id)
                VALUES ('delete', old.rowid, old.content, old.fragment_id);
            END
        """)
        c.commit()

    def insert(self, frag: IndexedFragment) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO fragments VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))",
            (frag.fragment_id, frag.file_path, frag.file_hash,
             frag.start_line, frag.end_line, frag.content,
             frag.language, frag.parser_level, frag.encoding),
        )
        self._conn.commit()

    def insert_batch(self, frags: list[IndexedFragment]) -> int:
        rows = [(f.fragment_id, f.file_path, f.file_hash,
                 f.start_line, f.end_line, f.content,
                 f.language, f.parser_level, f.encoding) for f in frags]
        self._conn.executemany(
            "INSERT OR REPLACE INTO fragments VALUES (?,?,?,?,?,?,?,?,?,datetime('now'))", rows,
        )
        self._conn.commit()
        return len(rows)

    def search_bm25(self, query: str, limit: int = 20) -> list[tuple[str, float, str]]:
        """Busqueda BM25. Retorna [(fragment_id, rank, snippet)].
        Convierte queries de lenguaje natural a OR para FTS5."""
        fts_query = self._to_fts5_query(query)
        if not fts_query:
            return []
        try:
            cursor = self._conn.execute(
                """SELECT f.fragment_id, fts.rank, snippet(fragments_fts, 0, '<b>', '</b>', '...', 40)
                   FROM fragments_fts fts
                   JOIN fragments f ON f.rowid = fts.rowid
                   WHERE fragments_fts MATCH ?
                   ORDER BY fts.rank
                   LIMIT ?""",
                (fts_query, limit),
            )
            return cursor.fetchall()
        except Exception:
            return []

    @staticmethod
    def _to_fts5_query(query: str) -> str:
        """Convierte lenguaje natural a query FTS5 con OR."""
        stop = {"como", "que", "el", "la", "los", "las", "un", "una", "de", "del",
                "en", "y", "o", "a", "al", "por", "para", "con", "sin", "se", "su",
                "es", "no", "si", "mas", "the", "and", "or", "is", "in", "of", "to",
                "a", "an", "for", "with", "how", "what", "does", "do", "when", "this"}
        words = []
        for w in query.split():
            clean = "".join(c for c in w if c.isalnum() or c == "_")
            if clean and clean.lower() not in stop and len(clean) > 1:
                words.append(clean)
        return " OR ".join(words) if words else ""

    def delete_by_file(self, file_path: str) -> int:
        cur = self._conn.execute("DELETE FROM fragments WHERE file_path = ?", (file_path,))
        self._conn.commit()
        return cur.rowcount

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM fragments").fetchone()[0]

    def files_indexed(self) -> list[str]:
        rows = self._conn.execute("SELECT DISTINCT file_path FROM fragments").fetchall()
        return [r[0] for r in rows]

    def get_file_hash(self, file_path: str) -> str | None:
        row = self._conn.execute(
            "SELECT file_hash FROM fragments WHERE file_path = ? LIMIT 1", (file_path,)
        ).fetchone()
        return row[0] if row else None


def compute_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def make_fragment_id(file_path: str, start_line: int, end_line: int) -> str:
    raw = f"{file_path}:{start_line}-{end_line}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]
