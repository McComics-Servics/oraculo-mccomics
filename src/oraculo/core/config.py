"""Carga de configuracion de runtime (paths, env vars)."""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

from oraculo.core.constants import DEFAULT_DATA_DIR, DEFAULT_PROFILE


@dataclass(frozen=True)
class RuntimeConfig:
    data_dir: Path
    profiles_dir: Path
    initial_profile: str
    log_level: str
    http_port: int | None
    no_http: bool
    llm_model: str | None
    degraded_ok: bool


def load_runtime_config(repo_root: Path | None = None) -> RuntimeConfig:
    repo_root = repo_root or Path.cwd()
    data_dir = Path(os.environ.get("ORACULO_DATA_DIR", repo_root / DEFAULT_DATA_DIR))
    profiles_dir = repo_root / "profiles"
    return RuntimeConfig(
        data_dir=data_dir,
        profiles_dir=profiles_dir,
        initial_profile=os.environ.get("ORACULO_PROFILE", DEFAULT_PROFILE),
        log_level=os.environ.get("ORACULO_LOG_LEVEL", "info"),
        http_port=int(os.environ["ORACULO_PORT"]) if os.environ.get("ORACULO_PORT") else None,
        no_http=os.environ.get("ORACULO_NO_HTTP", "0") == "1",
        llm_model=os.environ.get("ORACULO_LLM_MODEL"),
        degraded_ok=os.environ.get("ORACULO_DEGRADED_OK", "0") == "1",
    )
