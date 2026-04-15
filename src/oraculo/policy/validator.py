"""
Modulo: oraculo.policy.validator
Proposito: Validar estructura, tipos y coherencia cruzada de perfiles.
Documento de LEY: POLICY_ENGINE_SPEC.md (seccion 7)
"""
from __future__ import annotations
from typing import Any

from oraculo.core.exceptions import ProfileValidationError

REQUIRED_TOP_KEYS = {
    "profile_name", "profile_version", "schema_version", "description",
    "crypto", "transport", "network", "auth", "logging", "audit",
    "rate_limit", "anomaly_detection", "integrity", "llm_local",
    "golden_tests", "backups", "telemetry", "ui", "slo",
}

ALLOWED_PROFILES = {"basic", "enterprise", "banking"}


def validate_profile(data: dict[str, Any]) -> None:
    """Valida estructura y coherencia cruzada. Lanza ProfileValidationError."""
    _check_keys(data)
    _check_types(data)
    _check_cross_rules(data)


def _check_keys(data: dict[str, Any]) -> None:
    missing = REQUIRED_TOP_KEYS - set(data.keys())
    if missing:
        raise ProfileValidationError(f"Faltan claves: {sorted(missing)}")
    name = data["profile_name"]
    if not (name in ALLOWED_PROFILES or name.startswith("custom_")):
        raise ProfileValidationError(f"profile_name invalido: {name}")


def _check_types(data: dict[str, Any]) -> None:
    if not isinstance(data["profile_version"], int) or data["profile_version"] < 1:
        raise ProfileValidationError("profile_version debe ser int >= 1")
    if data["schema_version"] != "1.0":
        raise ProfileValidationError("schema_version debe ser '1.0'")
    auth = data["auth"]
    if not isinstance(auth.get("token_ttl_seconds"), int) or auth["token_ttl_seconds"] <= 0:
        raise ProfileValidationError("auth.token_ttl_seconds invalido")


def _check_cross_rules(data: dict[str, Any]) -> None:
    """6 reglas de coherencia cruzada del POLICY_ENGINE_SPEC seccion 7."""
    anomaly = data["anomaly_detection"]["enabled"]
    audit_enabled = data["audit"]["enabled"]
    if anomaly and not audit_enabled:
        raise ProfileValidationError("anomaly_detection requiere audit.enabled=true")

    paranoid = data["logging"].get("paranoid_mode", False)
    if paranoid and not (data["logging"].get("sanitize_paths") and data["logging"].get("sanitize_content")):
        raise ProfileValidationError("paranoid_mode requiere sanitize_paths y sanitize_content")

    if data["network"].get("air_gap_verify") and data["network"].get("external_allowed"):
        raise ProfileValidationError("air_gap_verify=true requiere external_allowed=false")

    if data["crypto"].get("row_level_hmac") and data["integrity"].get("check_on_startup") != "full":
        raise ProfileValidationError("row_level_hmac requiere integrity.check_on_startup=full")

    rl = data["rate_limit"]
    if rl["queries_per_minute"] <= 0 or rl["queries_per_hour"] <= 0:
        raise ProfileValidationError("rate_limit debe ser positivo")

    if data["transport"].get("require_nonce") and not data["transport"].get("require_timestamp"):
        raise ProfileValidationError("require_nonce requiere require_timestamp")
