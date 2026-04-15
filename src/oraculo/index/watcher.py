"""
Modulo: oraculo.index.watcher
Proposito: Monitoreo de filesystem con watchdog. Dispara re-indexacion incremental.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {
    ".py", ".rb", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java",
    ".c", ".h", ".cpp", ".hpp", ".cs", ".php", ".kt", ".swift",
    ".scala", ".lua", ".sh", ".sql", ".html", ".css",
    ".yaml", ".yml", ".json", ".md", ".toml", ".txt",
    ".cob", ".cbl", ".cpy", ".pli", ".f", ".f90",
    ".rpg", ".rpgle", ".jcl", ".rexx", ".prg", ".asm",
    ".ada", ".pas", ".xml", ".ini", ".cfg", ".conf",
}


class IndexEventHandler(FileSystemEventHandler):
    def __init__(self, on_change: Callable[[str], None]):
        self._on_change = on_change

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_trigger(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_trigger(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._maybe_trigger(event.src_path)

    def _maybe_trigger(self, path: str) -> None:
        p = Path(path)
        if p.suffix.lower() in TEXT_EXTENSIONS:
            self._on_change(path)


class FileWatcher:
    """Observa carpetas autorizadas y notifica cambios al debouncer."""

    def __init__(self, on_change: Callable[[str], None]):
        self._observer = Observer()
        self._handler = IndexEventHandler(on_change)
        self._watching: list[str] = []

    def watch(self, directory: str | Path, recursive: bool = True) -> None:
        path = str(directory)
        self._observer.schedule(self._handler, path, recursive=recursive)
        self._watching.append(path)
        logger.info("Watching: %s (recursive=%s)", path, recursive)

    def start(self) -> None:
        self._observer.start()
        logger.info("FileWatcher activo con %d directorios", len(self._watching))

    def stop(self) -> None:
        self._observer.stop()
        self._observer.join(timeout=5)
        logger.info("FileWatcher detenido")
