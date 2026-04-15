"""
Modulo: oraculo.audit.audit_chain
Proposito: Cadena de auditoria inmutable para perfil Banking.
Registro append-only con hash chain (cada entrada referencia la anterior).
"""
from __future__ import annotations
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    sequence: int
    timestamp: float
    event_type: str
    actor: str
    details: dict[str, Any]
    prev_hash: str
    entry_hash: str = ""

    def compute_hash(self) -> str:
        payload = f"{self.sequence}|{self.timestamp}|{self.event_type}|{self.actor}|{json.dumps(self.details, sort_keys=True)}|{self.prev_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "seq": self.sequence,
            "ts": self.timestamp,
            "type": self.event_type,
            "actor": self.actor,
            "details": self.details,
            "prev_hash": self.prev_hash,
            "hash": self.entry_hash,
        }

    @staticmethod
    def from_dict(data: dict) -> AuditEntry:
        return AuditEntry(
            sequence=data["seq"],
            timestamp=data["ts"],
            event_type=data["type"],
            actor=data["actor"],
            details=data.get("details", {}),
            prev_hash=data["prev_hash"],
            entry_hash=data["hash"],
        )


class AuditChain:
    """Cadena de auditoria append-only con integridad por hash chain."""

    GENESIS_HASH = "0" * 64

    def __init__(self, log_path: Path | None = None):
        self._entries: list[AuditEntry] = []
        self._log_path = log_path
        if self._log_path and self._log_path.exists():
            self._load()

    def record(self, event_type: str, actor: str, details: dict[str, Any] | None = None) -> AuditEntry:
        prev_hash = self._entries[-1].entry_hash if self._entries else self.GENESIS_HASH
        entry = AuditEntry(
            sequence=len(self._entries),
            timestamp=time.time(),
            event_type=event_type,
            actor=actor,
            details=details or {},
            prev_hash=prev_hash,
        )
        entry.entry_hash = entry.compute_hash()
        self._entries.append(entry)
        self._append_to_log(entry)
        logger.info("Audit[%d]: %s by %s", entry.sequence, event_type, actor)
        return entry

    def verify_chain(self) -> tuple[bool, list[str]]:
        """Verifica integridad de toda la cadena. Retorna (valid, errors)."""
        errors = []
        if not self._entries:
            return True, []

        if self._entries[0].prev_hash != self.GENESIS_HASH:
            errors.append(f"Entry 0: prev_hash should be genesis, got {self._entries[0].prev_hash}")

        for i, entry in enumerate(self._entries):
            expected_hash = entry.compute_hash()
            if entry.entry_hash != expected_hash:
                errors.append(f"Entry {i}: hash mismatch (expected {expected_hash[:16]}..., got {entry.entry_hash[:16]}...)")
            if i > 0 and entry.prev_hash != self._entries[i - 1].entry_hash:
                errors.append(f"Entry {i}: prev_hash doesn't match entry {i-1}")
            if entry.sequence != i:
                errors.append(f"Entry {i}: sequence mismatch (expected {i}, got {entry.sequence})")

        return len(errors) == 0, errors

    def get_entries(self, event_type: str | None = None, limit: int = 100) -> list[AuditEntry]:
        entries = self._entries
        if event_type:
            entries = [e for e in entries if e.event_type == event_type]
        return entries[-limit:]

    @property
    def length(self) -> int:
        return len(self._entries)

    @property
    def last_hash(self) -> str:
        return self._entries[-1].entry_hash if self._entries else self.GENESIS_HASH

    def _append_to_log(self, entry: AuditEntry) -> None:
        if not self._log_path:
            return
        with open(self._log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def _load(self) -> None:
        if not self._log_path or not self._log_path.exists():
            return
        try:
            for line in self._log_path.read_text(encoding="utf-8").strip().split("\n"):
                if line:
                    self._entries.append(AuditEntry.from_dict(json.loads(line)))
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Error cargando audit chain: %s", e)
