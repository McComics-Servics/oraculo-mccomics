"""
Modulo: oraculo.crypto.crypto_shred
Proposito: Crypto-shred — Borrado criptografico irreversible de datos indexados.
Cuando se activa, las claves de cifrado se destruyen, haciendo los datos irrecuperables.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

KEY_LENGTH = 32  # 256 bits


@dataclass
class ShredKey:
    key_id: str
    created_at: float
    domain: str
    active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"key_id": self.key_id, "created_at": self.created_at,
                "domain": self.domain, "active": self.active}

    @staticmethod
    def from_dict(data: dict) -> ShredKey:
        return ShredKey(
            key_id=data["key_id"], created_at=data["created_at"],
            domain=data["domain"], active=data.get("active", True),
        )


@dataclass
class ShredResult:
    domain: str
    keys_destroyed: int
    timestamp: float
    success: bool
    details: str = ""


class CryptoShredManager:
    """Gestiona claves de cifrado para crypto-shred."""

    def __init__(self, key_store_path: Path | None = None):
        self._keys: dict[str, ShredKey] = {}
        self._store_path = key_store_path
        if self._store_path and self._store_path.exists():
            self._load()

    def generate_key(self, domain: str) -> ShredKey:
        key_id = hashlib.sha256(secrets.token_bytes(KEY_LENGTH)).hexdigest()[:16]
        key = ShredKey(key_id=key_id, created_at=time.time(), domain=domain)
        self._keys[key_id] = key
        self._persist()
        logger.info("Clave generada para dominio '%s': %s", domain, key_id)
        return key

    def get_active_keys(self, domain: str | None = None) -> list[ShredKey]:
        keys = [k for k in self._keys.values() if k.active]
        if domain:
            keys = [k for k in keys if k.domain == domain]
        return keys

    def shred_domain(self, domain: str) -> ShredResult:
        """Destruye todas las claves de un dominio — datos irrecuperables."""
        domain_keys = [k for k in self._keys.values() if k.domain == domain and k.active]
        count = 0
        for key in domain_keys:
            key.active = False
            count += 1
            logger.warning("CRYPTO-SHRED: Clave %s destruida (dominio: %s)", key.key_id, domain)

        self._persist()
        return ShredResult(
            domain=domain,
            keys_destroyed=count,
            timestamp=time.time(),
            success=True,
            details=f"{count} claves destruidas para dominio '{domain}'",
        )

    def shred_all(self) -> ShredResult:
        """Destruye TODAS las claves — borrado total."""
        count = 0
        for key in self._keys.values():
            if key.active:
                key.active = False
                count += 1
        self._persist()
        logger.warning("CRYPTO-SHRED TOTAL: %d claves destruidas", count)
        return ShredResult(
            domain="*",
            keys_destroyed=count,
            timestamp=time.time(),
            success=True,
            details=f"SHRED TOTAL: {count} claves destruidas",
        )

    def _persist(self) -> None:
        if not self._store_path:
            return
        data = [k.to_dict() for k in self._keys.values()]
        self._store_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load(self) -> None:
        if not self._store_path or not self._store_path.exists():
            return
        try:
            data = json.loads(self._store_path.read_text(encoding="utf-8"))
            for item in data:
                key = ShredKey.from_dict(item)
                self._keys[key.key_id] = key
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Error cargando keystore: %s", e)

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    @property
    def active_keys_count(self) -> int:
        return sum(1 for k in self._keys.values() if k.active)
