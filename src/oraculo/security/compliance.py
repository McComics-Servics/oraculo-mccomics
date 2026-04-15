"""
Modulo: oraculo.security.compliance
Proposito: Motor de compliance para perfiles Banking/Enterprise.
Verifica que la configuracion cumple con los requisitos de seguridad del perfil activo.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ComplianceCheck:
    name: str
    passed: bool
    severity: str  # critical, warning, info
    message: str


@dataclass
class ComplianceReport:
    profile: str
    checks: list[ComplianceCheck] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.checks if c.severity == "critical")

    @property
    def critical_failures(self) -> list[ComplianceCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "critical"]

    @property
    def warnings(self) -> list[ComplianceCheck]:
        return [c for c in self.checks if not c.passed and c.severity == "warning"]

    @property
    def total_checks(self) -> int:
        return len(self.checks)

    @property
    def passed_checks(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "passed": self.passed,
            "total": self.total_checks,
            "passed_count": self.passed_checks,
            "critical_failures": [{"name": c.name, "message": c.message} for c in self.critical_failures],
            "warnings": [{"name": c.name, "message": c.message} for c in self.warnings],
        }


BANKING_RULES = [
    ("air_gap_required", "El sistema debe operar sin conexion a Internet"),
    ("audit_chain_enabled", "La cadena de auditoria debe estar habilitada"),
    ("crypto_shred_ready", "Crypto-shred debe tener claves activas"),
    ("token_ttl_max_1h", "Los tokens deben expirar en maximo 1 hora"),
    ("no_external_providers", "No se permiten providers LLM remotos"),
    ("hmac_row_enabled", "HMAC por fila debe estar habilitado en el indice"),
    ("no_http_loopback", "HTTP loopback deshabilitado, solo IPC"),
]

ENTERPRISE_RULES = [
    ("auth_required", "Autenticacion por token obligatoria"),
    ("audit_chain_enabled", "La cadena de auditoria debe estar habilitada"),
    ("hmac_requests", "HMAC en requests HTTP obligatorio"),
]


def run_compliance(profile: str, context: dict[str, Any]) -> ComplianceReport:
    """Ejecuta todas las verificaciones de compliance para el perfil dado."""
    report = ComplianceReport(profile=profile)

    if profile == "banking":
        _check_banking(report, context)
    elif profile == "enterprise":
        _check_enterprise(report, context)
    else:
        report.checks.append(ComplianceCheck(
            name="basic_mode",
            passed=True,
            severity="info",
            message="Perfil basic: sin requisitos de compliance",
        ))

    return report


def _check_banking(report: ComplianceReport, ctx: dict[str, Any]) -> None:
    report.checks.append(ComplianceCheck(
        name="air_gap_required",
        passed=ctx.get("air_gap_verified", False),
        severity="critical",
        message="Air-gap verificado" if ctx.get("air_gap_verified") else "FALLO: Conexion externa detectada",
    ))
    report.checks.append(ComplianceCheck(
        name="audit_chain_enabled",
        passed=ctx.get("audit_chain_active", False),
        severity="critical",
        message="Audit chain activa" if ctx.get("audit_chain_active") else "FALLO: Audit chain no inicializada",
    ))
    report.checks.append(ComplianceCheck(
        name="crypto_shred_ready",
        passed=ctx.get("crypto_shred_keys", 0) > 0,
        severity="critical",
        message=f"{ctx.get('crypto_shred_keys', 0)} claves activas" if ctx.get("crypto_shred_keys", 0) > 0 else "FALLO: Sin claves crypto-shred",
    ))
    report.checks.append(ComplianceCheck(
        name="token_ttl_max_1h",
        passed=ctx.get("max_token_ttl", 86400) <= 3600,
        severity="critical",
        message="TTL tokens <= 1h" if ctx.get("max_token_ttl", 86400) <= 3600 else "FALLO: TTL > 1 hora",
    ))
    report.checks.append(ComplianceCheck(
        name="no_external_providers",
        passed=ctx.get("provider_type", "llama_cpp") in ("llama_cpp", "none"),
        severity="critical",
        message="Solo providers locales" if ctx.get("provider_type", "llama_cpp") in ("llama_cpp", "none") else "FALLO: Provider externo detectado",
    ))
    report.checks.append(ComplianceCheck(
        name="hmac_row_enabled",
        passed=ctx.get("hmac_row_enabled", False),
        severity="warning",
        message="HMAC por fila habilitado" if ctx.get("hmac_row_enabled") else "HMAC por fila no habilitado",
    ))
    report.checks.append(ComplianceCheck(
        name="no_http_loopback",
        passed=not ctx.get("http_server_running", False),
        severity="warning",
        message="HTTP deshabilitado" if not ctx.get("http_server_running") else "HTTP activo (solo IPC recomendado)",
    ))


def _check_enterprise(report: ComplianceReport, ctx: dict[str, Any]) -> None:
    report.checks.append(ComplianceCheck(
        name="auth_required",
        passed=ctx.get("auth_enabled", False),
        severity="critical",
        message="Auth habilitado" if ctx.get("auth_enabled") else "FALLO: Auth no habilitado",
    ))
    report.checks.append(ComplianceCheck(
        name="audit_chain_enabled",
        passed=ctx.get("audit_chain_active", False),
        severity="warning",
        message="Audit chain activa" if ctx.get("audit_chain_active") else "Audit chain no inicializada",
    ))
    report.checks.append(ComplianceCheck(
        name="hmac_requests",
        passed=ctx.get("hmac_enabled", False),
        severity="warning",
        message="HMAC habilitado" if ctx.get("hmac_enabled") else "HMAC no habilitado",
    ))
