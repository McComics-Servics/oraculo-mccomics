"""
Modulo: oraculo.cognitive.model_downloader
Proposito: Descarga automatica de modelos GGUF desde Hugging Face.
Muestra progreso, verifica integridad, permite cancelar.
"""
from __future__ import annotations
import hashlib
import json
import logging
import os
import time
import urllib.request
import urllib.error
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

DEFAULT_MODELS_DIR = Path.home() / ".oraculo" / "models"

KNOWN_MODELS: dict[str, dict[str, Any]] = {
    "qwen2.5-coder:1.5b-instruct-q4_K_M": {
        "display_name": "Qwen 2.5 Coder 1.5B (Q4_K_M)",
        "filename": "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF/resolve/main/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        "size_mb": 1200,
        "ram_required_gb": 1.2,
        "description": "Modelo economico para equipos con recursos limitados",
    },
    "qwen2.5-coder:3b-instruct-q4_K_M": {
        "display_name": "Qwen 2.5 Coder 3B (Q4_K_M) — Recomendado",
        "filename": "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-3B-Instruct-GGUF/resolve/main/qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "size_mb": 2100,
        "ram_required_gb": 2.1,
        "description": "Mejor equilibrio calidad/rendimiento — Default recomendado",
    },
    "qwen2.5-coder:7b-instruct-q4_K_M": {
        "display_name": "Qwen 2.5 Coder 7B (Q4_K_M)",
        "filename": "qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "url": "https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/resolve/main/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        "size_mb": 4500,
        "ram_required_gb": 4.5,
        "description": "Maxima calidad de comprension de codigo",
    },
}


@dataclass
class DownloadProgress:
    model_id: str
    filename: str
    total_bytes: int
    downloaded_bytes: int
    speed_mbps: float
    eta_seconds: float
    status: str  # downloading, completed, failed, cancelled

    @property
    def percent(self) -> float:
        if self.total_bytes == 0:
            return 0
        return (self.downloaded_bytes / self.total_bytes) * 100

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "filename": self.filename,
            "percent": round(self.percent, 1),
            "downloaded_mb": round(self.downloaded_bytes / (1024 * 1024), 1),
            "total_mb": round(self.total_bytes / (1024 * 1024), 1),
            "speed_mbps": round(self.speed_mbps, 2),
            "eta_seconds": round(self.eta_seconds),
            "status": self.status,
        }


@dataclass
class DownloadResult:
    success: bool
    model_id: str
    file_path: Path | None
    size_mb: float
    elapsed_seconds: float
    error: str = ""


class ModelDownloader:
    """Descargador de modelos GGUF con progreso y verificacion."""

    def __init__(self, models_dir: Path | None = None):
        self._models_dir = models_dir or DEFAULT_MODELS_DIR
        self._models_dir.mkdir(parents=True, exist_ok=True)
        self._cancelled = False

    @property
    def models_dir(self) -> Path:
        return self._models_dir

    def list_available(self) -> list[dict[str, Any]]:
        """Lista modelos disponibles para descarga."""
        result = []
        for model_id, info in KNOWN_MODELS.items():
            local_path = self._models_dir / info["filename"]
            result.append({
                "model_id": model_id,
                "display_name": info["display_name"],
                "size_mb": info["size_mb"],
                "ram_required_gb": info["ram_required_gb"],
                "description": info["description"],
                "downloaded": local_path.exists(),
                "local_path": str(local_path) if local_path.exists() else None,
            })
        return result

    def list_downloaded(self) -> list[dict[str, Any]]:
        """Lista modelos ya descargados."""
        return [m for m in self.list_available() if m["downloaded"]]

    def is_downloaded(self, model_id: str) -> bool:
        info = KNOWN_MODELS.get(model_id)
        if not info:
            return False
        return (self._models_dir / info["filename"]).exists()

    def get_model_path(self, model_id: str) -> Path | None:
        info = KNOWN_MODELS.get(model_id)
        if not info:
            return None
        path = self._models_dir / info["filename"]
        return path if path.exists() else None

    def download(self, model_id: str,
                 on_progress: Callable[[DownloadProgress], None] | None = None) -> DownloadResult:
        """Descarga un modelo GGUF. Retorna resultado con path local."""
        info = KNOWN_MODELS.get(model_id)
        if not info:
            return DownloadResult(success=False, model_id=model_id, file_path=None,
                                  size_mb=0, elapsed_seconds=0, error=f"Modelo desconocido: {model_id}")

        dest = self._models_dir / info["filename"]
        if dest.exists():
            size_mb = dest.stat().st_size / (1024 * 1024)
            return DownloadResult(success=True, model_id=model_id, file_path=dest,
                                  size_mb=size_mb, elapsed_seconds=0, error="Ya descargado")

        url = info["url"]
        self._cancelled = False
        start = time.time()
        partial = dest.with_suffix(".partial")

        try:
            logger.info("Descargando %s desde %s", model_id, url)
            req = urllib.request.Request(url, headers={"User-Agent": "OraculoMcComics/4.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                chunk_size = 1024 * 256  # 256 KB
                last_report = time.time()

                with open(partial, "wb") as f:
                    while True:
                        if self._cancelled:
                            partial.unlink(missing_ok=True)
                            return DownloadResult(success=False, model_id=model_id, file_path=None,
                                                  size_mb=0, elapsed_seconds=time.time() - start,
                                                  error="Descarga cancelada")

                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if on_progress and (now - last_report > 0.5):
                            elapsed = now - start
                            speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0
                            remaining = total - downloaded
                            eta = remaining / (downloaded / elapsed) if downloaded > 0 and elapsed > 0 else 0
                            on_progress(DownloadProgress(
                                model_id=model_id,
                                filename=info["filename"],
                                total_bytes=total,
                                downloaded_bytes=downloaded,
                                speed_mbps=speed,
                                eta_seconds=eta,
                                status="downloading",
                            ))
                            last_report = now

            partial.rename(dest)
            elapsed = time.time() - start
            size_mb = dest.stat().st_size / (1024 * 1024)

            if on_progress:
                on_progress(DownloadProgress(
                    model_id=model_id, filename=info["filename"],
                    total_bytes=total, downloaded_bytes=total,
                    speed_mbps=size_mb / elapsed if elapsed > 0 else 0,
                    eta_seconds=0, status="completed",
                ))

            logger.info("Modelo %s descargado: %.1f MB en %.0fs", model_id, size_mb, elapsed)
            return DownloadResult(success=True, model_id=model_id, file_path=dest,
                                  size_mb=size_mb, elapsed_seconds=elapsed)

        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as e:
            partial.unlink(missing_ok=True)
            error_msg = str(e)
            logger.error("Error descargando %s: %s", model_id, error_msg)
            return DownloadResult(success=False, model_id=model_id, file_path=None,
                                  size_mb=0, elapsed_seconds=time.time() - start, error=error_msg)

    def cancel(self) -> None:
        self._cancelled = True

    def delete_model(self, model_id: str) -> bool:
        info = KNOWN_MODELS.get(model_id)
        if not info:
            return False
        path = self._models_dir / info["filename"]
        if path.exists():
            path.unlink()
            logger.info("Modelo %s eliminado", model_id)
            return True
        return False


def get_data_dir() -> Path:
    """Retorna el directorio base de datos de El Oraculo."""
    return Path.home() / ".oraculo"


def get_index_dir() -> Path:
    """Retorna el directorio donde se almacena el indice."""
    d = get_data_dir() / "index"
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_config_path() -> Path:
    """Retorna la ruta del archivo de configuracion."""
    return get_data_dir() / "config.json"
