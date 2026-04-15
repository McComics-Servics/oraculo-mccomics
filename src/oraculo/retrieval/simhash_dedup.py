"""
Modulo: oraculo.retrieval.simhash_dedup
Proposito: SimHash de 64 bits para deduplicar fragmentos casi-identicos.
Documento de LEY: CONTEXT_ASSEMBLY_POLICY.md seccion 3.4
"""
from __future__ import annotations
import hashlib
import re
import logging

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"\w+")


def simhash(text: str, hashbits: int = 64) -> int:
    """Calcula SimHash de 64 bits para un texto."""
    tokens = _TOKEN_RE.findall(text.lower())
    v = [0] * hashbits

    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        for i in range(hashbits):
            bitmask = 1 << i
            if h & bitmask:
                v[i] += 1
            else:
                v[i] -= 1

    fingerprint = 0
    for i in range(hashbits):
        if v[i] >= 0:
            fingerprint |= (1 << i)
    return fingerprint


def hamming_distance(a: int, b: int) -> int:
    """Distancia de Hamming entre dos hashes."""
    x = a ^ b
    count = 0
    while x:
        count += 1
        x &= x - 1
    return count


def is_near_duplicate(text_a: str, text_b: str, threshold: int = 3) -> bool:
    """Retorna True si dos textos son casi-duplicados (distancia Hamming <= threshold)."""
    return hamming_distance(simhash(text_a), simhash(text_b)) <= threshold


def dedup_fragments(fragments: list[tuple[str, str]], threshold: int = 3) -> list[str]:
    """
    Elimina casi-duplicados de una lista de (fragment_id, text).
    Retorna los fragment_id unicos.
    """
    kept: list[tuple[str, int]] = []
    result_ids: list[str] = []

    for frag_id, text in fragments:
        h = simhash(text)
        is_dup = False
        for _, existing_h in kept:
            if hamming_distance(h, existing_h) <= threshold:
                is_dup = True
                break
        if not is_dup:
            kept.append((frag_id, h))
            result_ids.append(frag_id)

    return result_ids
