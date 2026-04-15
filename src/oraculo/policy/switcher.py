"""
Modulo: oraculo.policy.switcher
Proposito: Logica de alto nivel para switching entre perfiles (re-cifrado, rotacion de tokens).
Documento de LEY: POLICY_ENGINE_SPEC.md seccion 8 y 10
"""
from __future__ import annotations
import logging
from typing import Any

from oraculo.core.constants import PROFILE_RANK

logger = logging.getLogger(__name__)


def is_downgrade(current_name: str | None, target_name: str) -> bool:
    if current_name is None:
        return False
    return PROFILE_RANK.get(target_name, 0) < PROFILE_RANK.get(current_name, 0)


def requires_reencrypt(current: dict[str, Any] | None, target: dict[str, Any]) -> bool:
    """True si la estrategia cripto cambia y hay que re-cifrar el indice."""
    if current is None:
        return False
    return current.get("crypto") != target.get("crypto")


def requires_token_rotation(current: dict[str, Any] | None, target: dict[str, Any]) -> bool:
    if current is None:
        return False
    return current.get("auth") != target.get("auth")
