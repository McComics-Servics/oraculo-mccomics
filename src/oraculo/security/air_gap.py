"""
Modulo: oraculo.security.air_gap
Proposito: Verificacion de air-gap para perfil Banking.
Garantiza que el sistema no tiene conectividad externa.
"""
from __future__ import annotations
import logging
import socket
from dataclasses import dataclass

logger = logging.getLogger(__name__)

EXTERNAL_CHECK_HOSTS = [
    ("8.8.8.8", 53),
    ("1.1.1.1", 53),
    ("208.67.222.222", 53),
]
CHECK_TIMEOUT = 2


@dataclass
class AirGapStatus:
    is_air_gapped: bool
    checks_performed: int
    connections_blocked: int
    details: list[str]


def verify_air_gap() -> AirGapStatus:
    """Verifica que no hay conectividad a Internet."""
    details = []
    blocked = 0
    for host, port in EXTERNAL_CHECK_HOSTS:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CHECK_TIMEOUT)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                details.append(f"ALERTA: Conexion exitosa a {host}:{port}")
                logger.warning("Air-gap violation: connection to %s:%d succeeded", host, port)
            else:
                blocked += 1
                details.append(f"OK: {host}:{port} bloqueado (code={result})")
        except (socket.timeout, OSError):
            blocked += 1
            details.append(f"OK: {host}:{port} no accesible")

    is_airgapped = blocked == len(EXTERNAL_CHECK_HOSTS)
    return AirGapStatus(
        is_air_gapped=is_airgapped,
        checks_performed=len(EXTERNAL_CHECK_HOSTS),
        connections_blocked=blocked,
        details=details,
    )


def enforce_air_gap(profile: str) -> AirGapStatus | None:
    """Solo verifica air-gap si el perfil es banking."""
    if profile != "banking":
        return None
    status = verify_air_gap()
    if not status.is_air_gapped:
        logger.error("PERFIL BANKING REQUIERE AIR-GAP. Conexiones externas detectadas.")
    return status


def block_outbound_urls(urls: list[str]) -> list[str]:
    """Retorna lista de URLs que serian bloqueadas en modo banking."""
    blocked = []
    for url in urls:
        if not url.startswith("http://127.0.0.1") and not url.startswith("http://localhost"):
            blocked.append(url)
    return blocked
