"""
Modulo: oraculo.api.ipc_bridge
Proposito: Bridge IPC para pywebview — expone metodos como js_api para la UI.
Documento de LEY: API_CONTRACT_SPEC.md seccion IPC
"""
from __future__ import annotations
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class IPCBridge:
    """
    Clase que se pasa como js_api a pywebview.
    Cada metodo publico es accesible desde JavaScript via pywebview.api.metodo().
    """

    def __init__(self, app_context: dict[str, Any]):
        self._ctx = app_context

    def health(self) -> str:
        import time
        return json.dumps({
            "status": "ok",
            "version": self._ctx.get("version", "4.0.0"),
            "profile": self._ctx.get("active_profile", "unknown"),
        })

    def query(self, query_text: str, limit: int = 10) -> str:
        assembler = self._ctx.get("assembler")
        if not assembler:
            return json.dumps({"error": "not_initialized"})
        result = assembler.assemble(query_text, limit=limit)
        return json.dumps(result.to_dict(), ensure_ascii=False)

    def get_profile(self) -> str:
        return json.dumps({
            "active": self._ctx.get("active_profile", "unknown"),
            "available": ["basic", "enterprise", "banking"],
        })

    def switch_profile(self, name: str, passphrase: str = "") -> str:
        engine = self._ctx.get("policy_engine")
        if not engine:
            return json.dumps({"error": "not_initialized"})
        try:
            result = engine.activate(name, passphrase=passphrase or None)
            self._ctx["active_profile"] = name
            return json.dumps({"success": result.success, "profile": name})
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_status(self) -> str:
        fts = self._ctx.get("fts_store")
        cognitive = self._ctx.get("cognitive")
        return json.dumps({
            "profile": self._ctx.get("active_profile", "unknown"),
            "indexed_files": fts.count() if fts else 0,
            "model_info": cognitive.model_info if cognitive else {},
        })

    def index_paths(self, paths_json: str) -> str:
        pipeline = self._ctx.get("index_pipeline")
        if not pipeline:
            return json.dumps({"error": "not_initialized"})
        from pathlib import Path
        paths = json.loads(paths_json)
        path_list = [Path(p) for p in paths]
        stats = pipeline.index_batch(path_list)
        return json.dumps({
            "processed": stats.files_processed,
            "fragments": stats.fragments_created,
        })

    def get_model_info(self) -> str:
        cognitive = self._ctx.get("cognitive")
        if cognitive:
            return json.dumps(cognitive.model_info)
        return json.dumps({"loaded": False})

    def download_model(self, model_id: str) -> str:
        try:
            from oraculo.cognitive.model_downloader import ModelDownloader
            downloader = self._ctx.get("downloader") or ModelDownloader()
            if downloader.is_downloaded(model_id):
                path = downloader.get_model_path(model_id)
                return json.dumps({"status": "already_downloaded", "path": str(path)})
            result = downloader.download(model_id)
            return json.dumps({
                "status": "completed" if result.success else "failed",
                "path": str(result.file_path) if result.file_path else None,
                "size_mb": result.size_mb,
                "error": result.error,
            })
        except Exception as e:
            return json.dumps({"error": str(e)})

    def list_models(self) -> str:
        try:
            from oraculo.cognitive.model_downloader import ModelDownloader
            downloader = self._ctx.get("downloader") or ModelDownloader()
            return json.dumps(downloader.list_available())
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_compliance(self) -> str:
        try:
            from oraculo.security.compliance import run_compliance
            profile = self._ctx.get("active_profile", "basic")
            ctx = {
                "air_gap_verified": self._ctx.get("air_gap_verified", False),
                "audit_chain_active": self._ctx.get("audit_chain_active", False),
                "crypto_shred_keys": self._ctx.get("crypto_shred_keys", 0),
                "max_token_ttl": self._ctx.get("max_token_ttl", 86400),
                "provider_type": self._ctx.get("provider_type", "llama_cpp"),
                "hmac_row_enabled": self._ctx.get("hmac_row_enabled", False),
                "http_server_running": self._ctx.get("http_server_running", False),
                "auth_enabled": self._ctx.get("auth_enabled", False),
                "hmac_enabled": self._ctx.get("hmac_enabled", False),
            }
            report = run_compliance(profile, ctx)
            return json.dumps(report.to_dict())
        except Exception as e:
            return json.dumps({"error": str(e)})

    def get_training_status(self) -> str:
        from oraculo.cognitive.model_downloader import get_data_dir, get_index_dir
        fts = self._ctx.get("fts_store")
        return json.dumps({
            "data_dir": str(get_data_dir()),
            "index_dir": str(get_index_dir()),
            "models_dir": str(get_data_dir() / "models"),
            "indexed_files": fts.count() if fts else 0,
            "auto_training": self._ctx.get("auto_training", False),
            "last_indexation": self._ctx.get("last_indexation", None),
        })

    def toggle_auto_training(self, enabled: bool) -> str:
        self._ctx["auto_training"] = enabled
        return json.dumps({"auto_training": enabled})

    def set_data_dir(self, path: str) -> str:
        self._ctx["custom_data_dir"] = path
        return json.dumps({"data_dir": path, "status": "updated"})

    def open_data_folder(self) -> str:
        import subprocess
        import platform
        from oraculo.cognitive.model_downloader import get_data_dir
        data_dir = str(get_data_dir())
        try:
            if platform.system() == "Windows":
                subprocess.Popen(["explorer", data_dir])
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", data_dir])
            else:
                subprocess.Popen(["xdg-open", data_dir])
            return json.dumps({"opened": data_dir})
        except Exception as e:
            return json.dumps({"error": str(e)})
