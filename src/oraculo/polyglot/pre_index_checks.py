"""
Modulo: oraculo.polyglot.pre_index_checks
Proposito: Verificaciones previas a indexar un archivo (tamaño, binario, encoding, secretos).
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path

from oraculo.polyglot.encoding_detect import detect_encoding
from oraculo.polyglot.secret_scanner import scan_for_secrets, SecretMatch

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
BINARY_CHECK_BYTES = 8192


@dataclass
class PreIndexResult:
    path: Path
    indexable: bool
    encoding: str = "utf-8"
    reason: str = ""
    secrets_found: list[SecretMatch] | None = None
    is_binary: bool = False
    is_oversized: bool = False


def check_file(path: Path) -> PreIndexResult:
    if not path.exists() or not path.is_file():
        return PreIndexResult(path=path, indexable=False, reason="no existe o no es archivo")

    size = path.stat().st_size
    if size > MAX_FILE_SIZE:
        return PreIndexResult(path=path, indexable=False, reason=f"tamaño {size} > {MAX_FILE_SIZE}",
                              is_oversized=True)
    if size == 0:
        return PreIndexResult(path=path, indexable=False, reason="archivo vacio")

    raw = path.read_bytes()[:BINARY_CHECK_BYTES]
    if b"\x00" in raw:
        return PreIndexResult(path=path, indexable=False, reason="archivo binario detectado",
                              is_binary=True)

    enc = detect_encoding(path)
    try:
        content = path.read_bytes().decode(enc)
    except (UnicodeDecodeError, LookupError) as e:
        return PreIndexResult(path=path, indexable=False, encoding=enc,
                              reason=f"error decodificando: {e}")

    secrets = scan_for_secrets(content)

    return PreIndexResult(
        path=path,
        indexable=True,
        encoding=enc,
        secrets_found=secrets if secrets else None,
    )
