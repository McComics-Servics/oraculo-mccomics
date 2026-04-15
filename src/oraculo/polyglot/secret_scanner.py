"""
Modulo: oraculo.polyglot.secret_scanner
Proposito: Detectar secretos antes de indexar (M18). Excluye fragmentos con credenciales.
"""
from __future__ import annotations
import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_PATTERNS = [
    ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----")),
    ("GENERIC_SECRET", re.compile(r"""(?i)(?:password|secret|token|api_key|apikey)\s*[=:]\s*['"][^'"]{8,}['"]""")),
    ("GITHUB_TOKEN", re.compile(r"ghp_[A-Za-z0-9]{36}")),
    ("SLACK_TOKEN", re.compile(r"xox[bpors]-[A-Za-z0-9-]+")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("HEX_SECRET_32", re.compile(r"""(?i)(?:key|secret|pass)\s*[=:]\s*['"]?[0-9a-f]{32,}['"]?""")),
]


@dataclass
class SecretMatch:
    pattern_name: str
    line_number: int
    snippet: str


def scan_for_secrets(content: str) -> list[SecretMatch]:
    matches: list[SecretMatch] = []
    for i, line in enumerate(content.splitlines(), 1):
        for name, pattern in _PATTERNS:
            if pattern.search(line):
                safe_snippet = line[:80] + "..." if len(line) > 80 else line
                matches.append(SecretMatch(pattern_name=name, line_number=i, snippet=safe_snippet))
    return matches
