"""Tests para model_downloader y las mejoras de IPC Bridge."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from oraculo.cognitive.model_downloader import (
    ModelDownloader, KNOWN_MODELS, DownloadProgress, DownloadResult,
    get_data_dir, get_index_dir, get_config_path, DEFAULT_MODELS_DIR,
)
from oraculo.api.ipc_bridge import IPCBridge


# ── Model Downloader ────────────────────────────────

class TestModelDownloader:
    def test_known_models_exist(self):
        assert len(KNOWN_MODELS) >= 3
        assert "qwen2.5-coder:3b-instruct-q4_K_M" in KNOWN_MODELS

    def test_init_creates_dir(self, tmp_path):
        models_dir = tmp_path / "models"
        dl = ModelDownloader(models_dir=models_dir)
        assert models_dir.exists()

    def test_list_available(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        available = dl.list_available()
        assert len(available) >= 3
        for m in available:
            assert "model_id" in m
            assert "display_name" in m
            assert "downloaded" in m
            assert m["downloaded"] is False

    def test_list_downloaded_empty(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        assert dl.list_downloaded() == []

    def test_is_downloaded_false(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        assert dl.is_downloaded("qwen2.5-coder:3b-instruct-q4_K_M") is False

    def test_is_downloaded_true(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True)
        info = KNOWN_MODELS["qwen2.5-coder:3b-instruct-q4_K_M"]
        (models_dir / info["filename"]).write_text("fake model data")
        dl = ModelDownloader(models_dir=models_dir)
        assert dl.is_downloaded("qwen2.5-coder:3b-instruct-q4_K_M") is True

    def test_get_model_path_exists(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True)
        info = KNOWN_MODELS["qwen2.5-coder:1.5b-instruct-q4_K_M"]
        fake = models_dir / info["filename"]
        fake.write_text("data")
        dl = ModelDownloader(models_dir=models_dir)
        path = dl.get_model_path("qwen2.5-coder:1.5b-instruct-q4_K_M")
        assert path == fake

    def test_get_model_path_not_exists(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        assert dl.get_model_path("qwen2.5-coder:3b-instruct-q4_K_M") is None

    def test_unknown_model(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        assert dl.is_downloaded("nonexistent-model") is False
        assert dl.get_model_path("nonexistent-model") is None

    def test_download_unknown_model(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        result = dl.download("nonexistent")
        assert result.success is False
        assert "desconocido" in result.error.lower() or "unknown" in result.error.lower()

    def test_download_already_exists(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True)
        info = KNOWN_MODELS["qwen2.5-coder:3b-instruct-q4_K_M"]
        (models_dir / info["filename"]).write_text("fake")
        dl = ModelDownloader(models_dir=models_dir)
        result = dl.download("qwen2.5-coder:3b-instruct-q4_K_M")
        assert result.success is True
        assert "descargado" in result.error.lower() or "already" in result.error.lower()

    def test_delete_model(self, tmp_path):
        models_dir = tmp_path / "models"
        models_dir.mkdir(parents=True)
        info = KNOWN_MODELS["qwen2.5-coder:1.5b-instruct-q4_K_M"]
        (models_dir / info["filename"]).write_text("data")
        dl = ModelDownloader(models_dir=models_dir)
        assert dl.delete_model("qwen2.5-coder:1.5b-instruct-q4_K_M") is True
        assert not (models_dir / info["filename"]).exists()

    def test_delete_nonexistent_model(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        assert dl.delete_model("qwen2.5-coder:3b-instruct-q4_K_M") is False

    def test_cancel(self, tmp_path):
        dl = ModelDownloader(models_dir=tmp_path / "models")
        dl.cancel()
        assert dl._cancelled is True

    def test_download_progress_dataclass(self):
        p = DownloadProgress(
            model_id="test", filename="test.gguf",
            total_bytes=1000, downloaded_bytes=500,
            speed_mbps=1.5, eta_seconds=30, status="downloading",
        )
        assert p.percent == 50.0
        d = p.to_dict()
        assert d["percent"] == 50.0
        assert d["status"] == "downloading"


# ── Data Directories ────────────────────────────────

class TestDataDirs:
    def test_get_data_dir(self):
        d = get_data_dir()
        assert ".oraculo" in str(d)

    def test_get_index_dir(self):
        d = get_index_dir()
        assert "index" in str(d)

    def test_get_config_path(self):
        p = get_config_path()
        assert p.name == "config.json"


# ── IPC Bridge New Methods ──────────────────────────

class TestIPCBridgeNew:
    def _bridge(self, **overrides):
        ctx = {"version": "4.0.0", "active_profile": "basic"}
        ctx.update(overrides)
        return IPCBridge(ctx)

    def test_get_compliance_basic(self):
        bridge = self._bridge()
        result = json.loads(bridge.get_compliance())
        assert result["profile"] == "basic"
        assert result["passed"] is True

    def test_get_compliance_banking(self):
        bridge = self._bridge(active_profile="banking")
        result = json.loads(bridge.get_compliance())
        assert result["profile"] == "banking"
        assert result["passed"] is False  # no air-gap etc.

    def test_get_training_status(self):
        bridge = self._bridge()
        result = json.loads(bridge.get_training_status())
        assert "data_dir" in result
        assert "index_dir" in result
        assert "auto_training" in result

    def test_toggle_auto_training(self):
        bridge = self._bridge()
        result = json.loads(bridge.toggle_auto_training(True))
        assert result["auto_training"] is True
        result = json.loads(bridge.toggle_auto_training(False))
        assert result["auto_training"] is False

    def test_set_data_dir(self):
        bridge = self._bridge()
        result = json.loads(bridge.set_data_dir("/custom/path"))
        assert result["data_dir"] == "/custom/path"

    def test_list_models(self):
        bridge = self._bridge()
        result = json.loads(bridge.list_models())
        assert isinstance(result, list)
        assert len(result) >= 3

    def test_download_unknown_model(self):
        bridge = self._bridge()
        result = json.loads(bridge.download_model("nonexistent"))
        assert "error" in result or result.get("status") == "failed"
