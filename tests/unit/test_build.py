"""Tests para F10 — Build pipeline: doctor, bundler, installer."""
from __future__ import annotations
import json
from pathlib import Path
import pytest

from oraculo.build.doctor import (
    run_doctor, DoctorReport, DoctorCheck,
    REQUIRED_MODULES, OPTIONAL_MODULES,
)
from oraculo.build.bundler import (
    create_bundle, verify_bundle, BundleManifest, BundleResult,
)
from oraculo.build.installer import (
    InstallerConfig, detect_platform, generate_install_script,
    get_supported_platforms,
)


# ── Doctor ──────────────────────────────────────────

class TestDoctor:
    def test_run_doctor_basic(self):
        report = run_doctor()
        assert isinstance(report, DoctorReport)
        assert len(report.checks) > 0

    def test_python_version_check(self):
        report = run_doctor()
        py_check = next(c for c in report.checks if c.name == "python_version")
        assert py_check.passed is True

    def test_required_modules_present(self):
        report = run_doctor()
        for mod_name, _ in REQUIRED_MODULES:
            check = next(c for c in report.checks if c.name == mod_name)
            assert check.passed is True, f"{mod_name} deberia estar presente"

    def test_disk_space_check(self):
        report = run_doctor()
        disk = next(c for c in report.checks if c.name == "disk_space")
        assert disk.passed is True

    def test_system_info(self):
        report = run_doctor()
        assert "python" in report.system_info
        assert "platform" in report.system_info
        assert "os" in report.system_info

    def test_summary(self):
        report = run_doctor()
        s = report.summary()
        assert "passed" in s

    def test_to_dict(self):
        report = run_doctor()
        d = report.to_dict()
        assert "passed" in d
        assert "checks" in d
        assert "system_info" in d

    def test_data_dir_check(self, tmp_path):
        report = run_doctor(data_dir=tmp_path)
        data_check = next(c for c in report.checks if c.name == "data_dir")
        assert data_check.passed is True

    def test_missing_data_dir(self, tmp_path):
        report = run_doctor(data_dir=tmp_path / "nonexistent")
        data_check = next(c for c in report.checks if c.name == "data_dir")
        assert data_check.passed is False


# ── Bundler ─────────────────────────────────────────

class TestBundler:
    def _create_fake_project(self, tmp_path: Path) -> Path:
        src = tmp_path / "src" / "oraculo"
        src.mkdir(parents=True)
        (src / "__init__.py").write_text("", encoding="utf-8")
        (src / "main.py").write_text("print('hello')", encoding="utf-8")
        profiles = tmp_path / "profiles"
        profiles.mkdir()
        (profiles / "basic.yaml").write_text("name: basic", encoding="utf-8")
        return tmp_path / "src"

    def test_create_bundle(self, tmp_path):
        src = self._create_fake_project(tmp_path)
        output = tmp_path / "dist"
        result = create_bundle(src, output, version="4.0.0")
        assert result.success is True
        assert result.output_path is not None
        assert result.size_mb > 0

    def test_bundle_has_manifest(self, tmp_path):
        src = self._create_fake_project(tmp_path)
        output = tmp_path / "dist"
        result = create_bundle(src, output)
        manifest_path = result.output_path / "manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert data["version"] == "4.0.0"

    def test_bundle_has_src(self, tmp_path):
        src = self._create_fake_project(tmp_path)
        output = tmp_path / "dist"
        result = create_bundle(src, output)
        assert (result.output_path / "src").exists()

    def test_verify_valid_bundle(self, tmp_path):
        src = self._create_fake_project(tmp_path)
        output = tmp_path / "dist"
        result = create_bundle(src, output)
        valid, errors = verify_bundle(result.output_path)
        assert valid is True
        assert errors == []

    def test_verify_invalid_bundle(self, tmp_path):
        empty = tmp_path / "empty_bundle"
        empty.mkdir()
        valid, errors = verify_bundle(empty)
        assert valid is False
        assert len(errors) > 0

    def test_bundle_result_fields(self, tmp_path):
        src = self._create_fake_project(tmp_path)
        output = tmp_path / "dist"
        result = create_bundle(src, output)
        assert isinstance(result, BundleResult)
        assert result.manifest is not None
        assert isinstance(result.manifest, BundleManifest)

    def test_bundle_manifest_to_dict(self, tmp_path):
        src = self._create_fake_project(tmp_path)
        output = tmp_path / "dist"
        result = create_bundle(src, output)
        d = result.manifest.to_dict()
        assert d["version"] == "4.0.0"
        assert d["file_count"] > 0

    def test_bundle_nonexistent_src(self, tmp_path):
        output = tmp_path / "dist"
        result = create_bundle(tmp_path / "nope", output)
        assert len(result.errors) > 0


# ── Installer ───────────────────────────────────────

class TestInstaller:
    def test_detect_platform(self):
        p = detect_platform()
        assert p in ["windows", "macos", "linux"]

    def test_default_config(self):
        cfg = InstallerConfig()
        assert cfg.version == "4.0.0"
        assert cfg.python_min == "3.10"
        assert "Oraculo" in cfg.app_name

    def test_generate_windows_script(self):
        cfg = InstallerConfig()
        script = generate_install_script(cfg, target="windows")
        assert "@echo off" in script
        assert "pip install" in script
        assert cfg.version in script

    def test_generate_macos_script(self):
        cfg = InstallerConfig()
        script = generate_install_script(cfg, target="macos")
        assert "#!/bin/bash" in script
        assert "pip3 install" in script

    def test_generate_linux_script(self):
        cfg = InstallerConfig()
        script = generate_install_script(cfg, target="linux")
        assert "#!/bin/bash" in script
        assert "python3" in script

    def test_supported_platforms(self):
        platforms = get_supported_platforms()
        assert "windows" in platforms
        assert "macos" in platforms
        assert "linux" in platforms
        assert len(platforms) == 3

    def test_custom_config(self):
        cfg = InstallerConfig(version="5.0.0", python_min="3.12")
        script = generate_install_script(cfg, target="windows")
        assert "5.0.0" in script
        assert "3.12" in script
