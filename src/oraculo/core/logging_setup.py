"""Configuracion centralizada de logging."""
from __future__ import annotations
import logging
import logging.handlers
from pathlib import Path


def setup_logging(level: str = "info", log_file: Path | None = None,
                  max_mb: int = 5, backup_count: int = 3) -> None:
    """Configura logging raiz. Idempotente."""
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    root.addHandler(console)

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_mb * 1024 * 1024, backupCount=backup_count, encoding="utf-8"
        )
        fh.setFormatter(fmt)
        root.addHandler(fh)
