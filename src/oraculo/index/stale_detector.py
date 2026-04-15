"""
Modulo: oraculo.index.stale_detector
Proposito: Detecta fragmentos stale (archivo modificado despues de indexacion).
"""
from __future__ import annotations
import logging
from pathlib import Path

from oraculo.index.sqlite_store import compute_file_hash

logger = logging.getLogger(__name__)


class StaleDetector:
    """Compara hash actual del archivo contra hash almacenado."""

    def __init__(self, get_stored_hash):
        self._get_stored_hash = get_stored_hash

    def is_stale(self, file_path: str) -> bool:
        p = Path(file_path)
        if not p.exists():
            return True
        stored = self._get_stored_hash(file_path)
        if stored is None:
            return True
        current = compute_file_hash(p)
        return current != stored

    def find_stale(self, file_paths: list[str]) -> list[str]:
        return [fp for fp in file_paths if self.is_stale(fp)]
