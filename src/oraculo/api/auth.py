"""
Modulo: oraculo.api.auth
Proposito: Autenticacion por token local. 3 niveles segun perfil de seguridad.
Documento de LEY: API_CONTRACT_SPEC.md seccion 5 (Auth)
"""
from __future__ import annotations
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

TOKEN_LENGTH = 32
DEFAULT_TTL_SECONDS = 3600 * 24  # 24 horas


@dataclass
class AuthToken:
    token: str
    created_at: float
    ttl_seconds: int
    profile: str

    @property
    def is_expired(self) -> bool:
        return time.time() - self.created_at > self.ttl_seconds


class LocalAuthManager:
    """Gestion de tokens locales para la API."""

    def __init__(self, profile: str = "basic"):
        self._profile = profile
        self._tokens: dict[str, AuthToken] = {}

    @property
    def auth_required(self) -> bool:
        """Basic no requiere auth. Enterprise y Banking si."""
        return self._profile in ("enterprise", "banking")

    def generate_token(self, ttl: int = DEFAULT_TTL_SECONDS) -> str:
        """Genera un token nuevo."""
        raw = secrets.token_hex(TOKEN_LENGTH)
        token = AuthToken(token=raw, created_at=time.time(), ttl_seconds=ttl, profile=self._profile)
        self._tokens[raw] = token
        logger.info("Token generado para perfil %s (TTL: %ds)", self._profile, ttl)
        return raw

    def validate_token(self, token: str) -> bool:
        """Valida un token. Retorna False si no existe, expirado, o auth no requerido y token vacio."""
        if not self.auth_required:
            return True
        if not token:
            return False
        stored = self._tokens.get(token)
        if not stored:
            return False
        if stored.is_expired:
            del self._tokens[token]
            return False
        return True

    def revoke_token(self, token: str) -> bool:
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False

    def revoke_all(self) -> int:
        count = len(self._tokens)
        self._tokens.clear()
        return count

    def cleanup_expired(self) -> int:
        expired = [t for t, info in self._tokens.items() if info.is_expired]
        for t in expired:
            del self._tokens[t]
        return len(expired)

    def set_profile(self, profile: str) -> None:
        self._profile = profile
        if profile == "banking":
            for token_info in self._tokens.values():
                token_info.ttl_seconds = min(token_info.ttl_seconds, 3600)
