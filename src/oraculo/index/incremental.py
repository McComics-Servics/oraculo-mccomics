"""
Modulo: oraculo.index.incremental
Proposito: Indexacion incremental — solo procesa archivos modificados o nuevos.
"""
from __future__ import annotations
import logging
from pathlib import Path

from oraculo.index.sqlite_store import compute_file_hash

logger = logging.getLogger(__name__)


class IncrementalChecker:
    """Determina que archivos necesitan re-indexacion comparando hashes."""

    def __init__(self, get_stored_hash):
        self._get_stored_hash = get_stored_hash

    def needs_indexing(self, path: Path) -> bool:
        current_hash = compute_file_hash(path)
        stored_hash = self._get_stored_hash(str(path))
        if stored_hash is None:
            return True
        return current_hash != stored_hash

    def filter_changed(self, paths: list[Path]) -> list[Path]:
        return [p for p in paths if self.needs_indexing(p)]
