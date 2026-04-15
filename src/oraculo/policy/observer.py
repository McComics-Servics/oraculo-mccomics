"""Observer para notificar cambios de perfil a subsistemas."""
from __future__ import annotations
import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class ProfileObserver(Protocol):
    def on_profile_change(self, previous: dict[str, Any] | None, current: dict[str, Any]) -> None:
        ...


class ObserverRegistry:
    """Registro de observers que reaccionan a cambios de perfil."""

    def __init__(self) -> None:
        self._observers: list[ProfileObserver] = []

    def register(self, obs: ProfileObserver) -> None:
        self._observers.append(obs)

    def notify_all(self, previous: dict[str, Any] | None, current: dict[str, Any]) -> None:
        for obs in list(self._observers):
            try:
                obs.on_profile_change(previous, current)
            except Exception:
                logger.exception("Error en observer %s", type(obs).__name__)
