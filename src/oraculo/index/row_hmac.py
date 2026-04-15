"""
Modulo: oraculo.index.row_hmac
Proposito: HMAC por fila para perfil Banking (M9). Integridad a nivel de registro.
"""
from __future__ import annotations
import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def compute_row_hmac(key: bytes, *fields: str) -> str:
    """HMAC-SHA256 de campos concatenados."""
    data = "|".join(str(f) for f in fields).encode("utf-8")
    return hmac.new(key, data, hashlib.sha256).hexdigest()


def verify_row_hmac(key: bytes, expected_hmac: str, *fields: str) -> bool:
    computed = compute_row_hmac(key, *fields)
    return hmac.compare_digest(computed, expected_hmac)
