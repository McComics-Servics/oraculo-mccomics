"""
Modulo: oraculo.policy.loader
Proposito: Cargar archivos YAML de perfil desde disco.
Documento de LEY: POLICY_ENGINE_SPEC.md
"""
from __future__ import annotations
from pathlib import Path
from typing import Any

import yaml

from oraculo.core.exceptions import ProfileNotFoundError


def load_profile_yaml(profiles_dir: Path, name: str) -> dict[str, Any]:
    """Carga un YAML de perfil. No valida estructura (eso es del validator)."""
    path = profiles_dir / f"{name}.yaml"
    if not path.exists():
        raise ProfileNotFoundError(f"Perfil no encontrado: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ProfileNotFoundError(f"YAML invalido en {path}")
    return data


def list_available_profiles(profiles_dir: Path) -> list[str]:
    if not profiles_dir.exists():
        return []
    return sorted(p.stem for p in profiles_dir.glob("*.yaml"))


def merge_override(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Fusiona un override sobre un perfil base. Deep merge no-destructivo."""
    out = {k: v for k, v in base.items()}
    for key, value in override.items():
        if key in ("inherits_from", "profile_name"):
            continue
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = merge_override(out[key], value)
        else:
            out[key] = value
    return out
