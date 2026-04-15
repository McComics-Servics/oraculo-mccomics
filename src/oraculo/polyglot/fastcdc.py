"""
Modulo: oraculo.polyglot.fastcdc
Proposito: Content-Defined Chunking para archivos sin parser. Mejora M4 de v4.0.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md
"""
from __future__ import annotations
from dataclasses import dataclass


GEAR_TABLE = [int.from_bytes(bytes([i, i ^ 0xAA, i ^ 0x55, i ^ 0xFF]), "big") for i in range(256)]

MIN_CHUNK = 256
MAX_CHUNK = 8192
AVG_CHUNK = 2048
MASK = (1 << 13) - 1


@dataclass(frozen=True)
class Chunk:
    offset: int
    length: int
    data: bytes


def fastcdc(data: bytes, min_size: int = MIN_CHUNK, avg_size: int = AVG_CHUNK,
            max_size: int = MAX_CHUNK) -> list[Chunk]:
    """Divide data en chunks con boundaries determinados por contenido."""
    chunks: list[Chunk] = []
    n = len(data)
    offset = 0
    mask = (1 << (avg_size.bit_length() - 1)) - 1

    while offset < n:
        remaining = n - offset
        if remaining <= min_size:
            chunks.append(Chunk(offset=offset, length=remaining, data=data[offset:offset + remaining]))
            break

        fp = 0
        i = offset + min_size
        limit = min(offset + max_size, n)

        while i < limit:
            fp = (fp >> 1) + GEAR_TABLE[data[i] & 0xFF]
            if (fp & mask) == 0:
                break
            i += 1

        length = i - offset
        if length < min_size:
            length = min(min_size, remaining)

        chunks.append(Chunk(offset=offset, length=length, data=data[offset:offset + length]))
        offset += length

    return chunks
