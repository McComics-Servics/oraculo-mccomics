"""
Modulo: oraculo.index.debouncer
Proposito: Agrupa eventos de filesystem en ventanas de tiempo para evitar re-indexar multiples veces.
"""
from __future__ import annotations
import threading
import logging
from typing import Callable

logger = logging.getLogger(__name__)


class Debouncer:
    """Espera un intervalo sin nuevos eventos antes de ejecutar la accion."""

    def __init__(self, delay_seconds: float, action: Callable[[set[str]], None]):
        self._delay = delay_seconds
        self._action = action
        self._pending: set[str] = set()
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def trigger(self, file_path: str) -> None:
        with self._lock:
            self._pending.add(file_path)
            if self._timer:
                self._timer.cancel()
            self._timer = threading.Timer(self._delay, self._flush)
            self._timer.daemon = True
            self._timer.start()

    def _flush(self) -> None:
        with self._lock:
            paths = self._pending.copy()
            self._pending.clear()
            self._timer = None
        if paths:
            logger.info("Debouncer: procesando %d archivos", len(paths))
            try:
                self._action(paths)
            except Exception:
                logger.exception("Error en accion del debouncer")

    def cancel(self) -> None:
        with self._lock:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            self._pending.clear()
