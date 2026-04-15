"""Graceful shutdown del daemon."""
from __future__ import annotations
import logging
import signal
import threading

logger = logging.getLogger(__name__)

_shutdown_event = threading.Event()


def request_shutdown(signum: int | None = None, frame=None) -> None:
    logger.info("Shutdown solicitado (signal=%s)", signum)
    _shutdown_event.set()


def is_shutdown_requested() -> bool:
    return _shutdown_event.is_set()


def wait_for_shutdown(timeout: float | None = None) -> bool:
    return _shutdown_event.wait(timeout=timeout)


def install_signal_handlers() -> None:
    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
