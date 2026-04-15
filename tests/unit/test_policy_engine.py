"""Tests unitarios del Policy Engine. Bateria obligatoria segun POLICY_ENGINE_SPEC.md seccion 11."""
from __future__ import annotations
import json
from pathlib import Path

import pytest
import yaml

from oraculo.policy.engine import PolicyEngine, ProfileSwitchResult
from oraculo.policy.loader import load_profile_yaml, merge_override
from oraculo.policy.validator import validate_profile, ProfileValidationError


class TestLoaderBasic:
    def test_load_basic(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "basic")
        assert data["profile_name"] == "basic"
        assert data["schema_version"] == "1.0"

    def test_load_enterprise(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "enterprise")
        assert data["profile_name"] == "enterprise"

    def test_load_banking(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "banking")
        assert data["profile_name"] == "banking"

    def test_load_nonexistent_raises(self, profiles_dir: Path):
        from oraculo.core.exceptions import ProfileNotFoundError
        with pytest.raises(ProfileNotFoundError):
            load_profile_yaml(profiles_dir, "no_existe")


class TestValidator:
    def test_all_profiles_valid(self, profiles_dir: Path):
        for name in ("basic", "enterprise", "banking"):
            data = load_profile_yaml(profiles_dir, name)
            validate_profile(data)

    def test_missing_keys_rejected(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "basic")
        del data["crypto"]
        with pytest.raises(ProfileValidationError, match="Faltan claves"):
            validate_profile(data)

    def test_invalid_profile_name_rejected(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "basic")
        data["profile_name"] = "invalid_name"
        with pytest.raises(ProfileValidationError, match="profile_name invalido"):
            validate_profile(data)

    def test_cross_rule_anomaly_without_audit(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "enterprise")
        data["anomaly_detection"]["enabled"] = True
        data["audit"]["enabled"] = False
        with pytest.raises(ProfileValidationError, match="anomaly_detection requiere"):
            validate_profile(data)

    def test_cross_rule_airgap_with_external(self, profiles_dir: Path):
        data = load_profile_yaml(profiles_dir, "banking")
        data["network"]["air_gap_verify"] = True
        data["network"]["external_allowed"] = True
        with pytest.raises(ProfileValidationError, match="air_gap_verify"):
            validate_profile(data)


class TestMergeOverride:
    def test_deep_merge(self, profiles_dir: Path):
        base = load_profile_yaml(profiles_dir, "basic")
        override = {
            "profile_name": "custom_basic_strict",
            "inherits_from": "basic",
            "rate_limit": {"queries_per_minute": 100},
        }
        merged = merge_override(base, override)
        assert merged["rate_limit"]["queries_per_minute"] == 100
        assert merged["rate_limit"]["queries_per_hour"] == 10000
        assert merged["profile_name"] == "basic"


class TestPolicyEngine:
    def test_activate_basic(self, profiles_dir: Path, tmp_path: Path):
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "history.jsonl")
        r = engine.activate("basic")
        assert r.success
        assert engine.current_name == "basic"

    def test_activate_all_profiles(self, profiles_dir: Path, tmp_path: Path):
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "h.jsonl")
        for name in ("basic", "enterprise", "banking"):
            r = engine.activate(name)
            assert r.success, f"Fallo al activar {name}: {r.error_message}"
            assert engine.current_name == name

    def test_switch_basic_to_enterprise(self, profiles_dir: Path, tmp_path: Path):
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "h.jsonl")
        engine.activate("basic")
        r = engine.activate("enterprise")
        assert r.success
        assert r.previous == "basic"
        assert r.current == "enterprise"
        assert not r.is_downgrade

    def test_downgrade_banking_to_basic_requires_passphrase(self, profiles_dir: Path, tmp_path: Path):
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "h.jsonl")
        engine.activate("banking")
        r = engine.activate("basic")
        assert not r.success
        assert r.is_downgrade
        assert "passphrase" in r.error_message.lower()

    def test_history_jsonl_written(self, profiles_dir: Path, tmp_path: Path):
        hf = tmp_path / "history.jsonl"
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=hf)
        engine.activate("basic")
        engine.activate("enterprise")
        lines = hf.read_text().strip().split("\n")
        assert len(lines) == 2
        entry = json.loads(lines[1])
        assert entry["from"] == "basic"
        assert entry["to"] == "enterprise"

    def test_subscriber_notified(self, profiles_dir: Path, tmp_path: Path):
        calls = []
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "h.jsonl")
        engine.subscribe(lambda prev, cur: calls.append((prev, cur["profile_name"])))
        engine.activate("basic")
        assert len(calls) == 1
        assert calls[0] == (None, "basic")

    def test_nonexistent_profile_fails(self, profiles_dir: Path, tmp_path: Path):
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "h.jsonl")
        r = engine.activate("no_existe")
        assert not r.success
        assert r.error_code == "ORC_PROFILE_NOT_FOUND"

    def test_malformed_yaml_fails(self, profiles_dir: Path, tmp_path: Path):
        bad = profiles_dir / "broken.yaml"
        bad.write_text("esto no es yaml valido: [")
        engine = PolicyEngine(profiles_dir=profiles_dir, history_file=tmp_path / "h.jsonl")
        r = engine.activate("broken")
        assert not r.success
