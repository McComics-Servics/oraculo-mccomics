"""
Modulo: oraculo.policy.engine
Proposito: Motor de politicas. Singleton por daemon. Carga, valida y conmuta perfiles.
Documento de LEY: POLICY_ENGINE_SPEC.md
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from oraculo.core.constants import PROFILE_RANK
from oraculo.core.exceptions import (
    ProfileDowngradeError,
    ProfileError,
)
from oraculo.policy.loader import load_profile_yaml, merge_override
from oraculo.policy.validator import validate_profile

logger = logging.getLogger(__name__)

ProfileChangeCallback = Callable[[dict[str, Any] | None, dict[str, Any]], None]


@dataclass
class ProfileSwitchResult:
    success: bool
    previous: str | None
    current: str
    is_downgrade: bool = False
    error_code: str | None = None
    error_message: str | None = None


@dataclass
class PolicyEngine:
    profiles_dir: Path
    history_file: Path | None = None
    _current: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _subscribers: list[ProfileChangeCallback] = field(default_factory=list, init=False, repr=False)
    _lock: threading.RLock = field(default_factory=threading.RLock, init=False, repr=False)

    @property
    def current(self) -> dict[str, Any] | None:
        return self._current

    @property
    def current_name(self) -> str | None:
        return self._current["profile_name"] if self._current else None

    def subscribe(self, callback: ProfileChangeCallback) -> None:
        self._subscribers.append(callback)

    def load(self, name: str) -> dict[str, Any]:
        """Carga, valida y resuelve overrides. Devuelve perfil listo."""
        data = load_profile_yaml(self.profiles_dir, name)
        if "inherits_from" in data:
            base = load_profile_yaml(self.profiles_dir, data["inherits_from"])
            data = merge_override(base, data)
        validate_profile(data)
        return data

    def activate(self, name: str, passphrase: str | None = None) -> ProfileSwitchResult:
        """Cambio de perfil en caliente. Thread-safe."""
        with self._lock:
            try:
                target = self.load(name)
            except ProfileError as e:
                return ProfileSwitchResult(
                    success=False, previous=self.current_name, current=name,
                    error_code=getattr(e, "code", "ORC_PROFILE"),
                    error_message=str(e),
                )
            except Exception as e:
                return ProfileSwitchResult(
                    success=False, previous=self.current_name, current=name,
                    error_code="ORC_PROFILE_PARSE_ERROR",
                    error_message=f"Error al parsear perfil: {e}",
                )

            previous_name = self.current_name
            is_downgrade = self._is_downgrade(self._current, target)

            source_ui = self._current["ui"] if self._current else {}
            if is_downgrade and source_ui.get("require_passphrase_for_downgrade"):
                if not passphrase:
                    return ProfileSwitchResult(
                        success=False, previous=previous_name, current=name,
                        is_downgrade=True,
                        error_code="ORC_PROFILE_DOWNGRADE_DENIED",
                        error_message="passphrase requerida para downgrade",
                    )

            previous = self._current
            self._current = target
            self._notify(previous, target)
            self._append_history(previous_name, target["profile_name"], is_downgrade)
            logger.info("Perfil activado: %s (downgrade=%s)", name, is_downgrade)
            return ProfileSwitchResult(
                success=True, previous=previous_name, current=name, is_downgrade=is_downgrade,
            )

    def _is_downgrade(self, current: dict[str, Any] | None, target: dict[str, Any]) -> bool:
        if current is None:
            return False
        cr = PROFILE_RANK.get(current["profile_name"], 0)
        tr = PROFILE_RANK.get(target["profile_name"], 0)
        return tr < cr

    def _notify(self, previous: dict[str, Any] | None, current: dict[str, Any]) -> None:
        for cb in list(self._subscribers):
            try:
                cb(previous, current)
            except Exception:
                logger.exception("Error en subscriber de policy")

    def _append_history(self, frm: str | None, to: str, is_downgrade: bool) -> None:
        if not self.history_file:
            return
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "from": frm,
            "to": to,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "is_downgrade": is_downgrade,
        }
        with self.history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
