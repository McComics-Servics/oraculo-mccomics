"""
Modulo: oraculo.polyglot.encoding_detect
Proposito: Detectar encoding de archivos. Pipeline de 7 pasos segun POLYGLOT_FABRIC_SPEC.md seccion 2.5
"""
from __future__ import annotations
import codecs
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_BOM_TABLE = [
    (codecs.BOM_UTF32_BE, "utf-32-be"),
    (codecs.BOM_UTF32_LE, "utf-32-le"),
    (codecs.BOM_UTF16_BE, "utf-16-be"),
    (codecs.BOM_UTF16_LE, "utf-16-le"),
    (codecs.BOM_UTF8, "utf-8-sig"),
]

EBCDIC_CODECS = ["cp037", "cp1047", "cp500", "cp1140"]


def detect_encoding(path: Path, sample_bytes: int = 4096) -> str:
    """Detecta encoding. Nunca errors='replace'. Devuelve codec name."""
    raw = path.read_bytes()[:sample_bytes]
    if not raw:
        return "utf-8"

    # 1. BOM
    for bom, codec in _BOM_TABLE:
        if raw.startswith(bom):
            return codec

    # 2. charset-normalizer (si disponible)
    try:
        from charset_normalizer import from_bytes
        result = from_bytes(raw).best()
        if result and result.encoding:
            return result.encoding
    except ImportError:
        pass

    # 3. Heuristica EBCDIC: bytes > 0x80 en rango 0x40-0xFE dominan
    high_bytes = sum(1 for b in raw if b > 0x80)
    ebcdic_range = sum(1 for b in raw if 0x40 <= b <= 0xFE)
    if len(raw) > 0 and high_bytes > len(raw) * 0.3 and ebcdic_range > high_bytes * 0.7:
        for codec in EBCDIC_CODECS:
            try:
                raw[:200].decode(codec)
                return codec
            except (UnicodeDecodeError, LookupError):
                continue

    # 4. UTF-8 attempt
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # 5. latin-1 (nunca falla)
    return "latin-1"


def read_file_normalized(path: Path) -> tuple[str, str]:
    """Lee archivo, detecta encoding, normaliza a UTF-8 NFC. Retorna (contenido, encoding_detectado)."""
    import unicodedata
    enc = detect_encoding(path)
    content = path.read_bytes().decode(enc)
    content = unicodedata.normalize("NFC", content)
    return content, enc
