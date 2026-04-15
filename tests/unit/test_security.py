"""Tests para F9 — Seguridad Banking: air-gap, crypto-shred, audit chain, compliance."""
from __future__ import annotations
import json
import time
from pathlib import Path
import pytest

from oraculo.security.air_gap import (
    verify_air_gap, enforce_air_gap, block_outbound_urls, AirGapStatus,
)
from oraculo.crypto.crypto_shred import (
    CryptoShredManager, ShredKey, ShredResult,
)
from oraculo.audit.audit_chain import (
    AuditChain, AuditEntry,
)
from oraculo.security.compliance import (
    run_compliance, ComplianceReport, ComplianceCheck,
    BANKING_RULES, ENTERPRISE_RULES,
)


# ── Air Gap ─────────────────────────────────────────

class TestAirGap:
    def test_verify_returns_status(self):
        status = verify_air_gap()
        assert isinstance(status, AirGapStatus)
        assert status.checks_performed == 3

    def test_enforce_returns_none_for_non_banking(self):
        assert enforce_air_gap("basic") is None
        assert enforce_air_gap("enterprise") is None

    def test_enforce_returns_status_for_banking(self):
        status = enforce_air_gap("banking")
        assert isinstance(status, AirGapStatus)

    def test_block_outbound_urls(self):
        urls = [
            "http://127.0.0.1:9741/health",
            "http://localhost:8080/api",
            "https://example.com/api",
            "http://external.service:443/data",
        ]
        blocked = block_outbound_urls(urls)
        assert "https://example.com/api" in blocked
        assert "http://external.service:443/data" in blocked
        assert "http://127.0.0.1:9741/health" not in blocked
        assert "http://localhost:8080/api" not in blocked

    def test_block_empty_urls(self):
        assert block_outbound_urls([]) == []


# ── Crypto Shred ────────────────────────────────────

class TestCryptoShred:
    def test_generate_key(self):
        mgr = CryptoShredManager()
        key = mgr.generate_key("test_domain")
        assert isinstance(key, ShredKey)
        assert key.active is True
        assert key.domain == "test_domain"
        assert len(key.key_id) == 16

    def test_get_active_keys(self):
        mgr = CryptoShredManager()
        mgr.generate_key("dom1")
        mgr.generate_key("dom2")
        mgr.generate_key("dom1")
        assert len(mgr.get_active_keys()) == 3
        assert len(mgr.get_active_keys("dom1")) == 2

    def test_shred_domain(self):
        mgr = CryptoShredManager()
        mgr.generate_key("target")
        mgr.generate_key("keep")
        mgr.generate_key("target")
        result = mgr.shred_domain("target")
        assert isinstance(result, ShredResult)
        assert result.keys_destroyed == 2
        assert result.success is True
        assert len(mgr.get_active_keys("target")) == 0
        assert len(mgr.get_active_keys("keep")) == 1

    def test_shred_all(self):
        mgr = CryptoShredManager()
        mgr.generate_key("a")
        mgr.generate_key("b")
        result = mgr.shred_all()
        assert result.keys_destroyed == 2
        assert mgr.active_keys_count == 0

    def test_total_keys(self):
        mgr = CryptoShredManager()
        mgr.generate_key("d")
        mgr.generate_key("d")
        assert mgr.total_keys == 2

    def test_persistence(self, tmp_path):
        store = tmp_path / "keys.json"
        mgr1 = CryptoShredManager(key_store_path=store)
        mgr1.generate_key("persist_test")
        mgr1.generate_key("persist_test")
        assert store.exists()
        mgr2 = CryptoShredManager(key_store_path=store)
        assert mgr2.total_keys == 2
        assert len(mgr2.get_active_keys("persist_test")) == 2

    def test_shred_key_serialization(self):
        key = ShredKey(key_id="abc123", created_at=1000.0, domain="test", active=True)
        d = key.to_dict()
        restored = ShredKey.from_dict(d)
        assert restored.key_id == "abc123"
        assert restored.domain == "test"

    def test_shred_empty_domain(self):
        mgr = CryptoShredManager()
        result = mgr.shred_domain("nonexistent")
        assert result.keys_destroyed == 0
        assert result.success is True


# ── Audit Chain ─────────────────────────────────────

class TestAuditChain:
    def test_record_single(self):
        chain = AuditChain()
        entry = chain.record("login", "admin", {"ip": "127.0.0.1"})
        assert entry.sequence == 0
        assert entry.event_type == "login"
        assert entry.actor == "admin"
        assert len(entry.entry_hash) == 64

    def test_chain_integrity(self):
        chain = AuditChain()
        chain.record("event1", "user1")
        chain.record("event2", "user2")
        chain.record("event3", "user3")
        valid, errors = chain.verify_chain()
        assert valid is True
        assert errors == []

    def test_chain_links(self):
        chain = AuditChain()
        e0 = chain.record("first", "admin")
        e1 = chain.record("second", "admin")
        assert e1.prev_hash == e0.entry_hash

    def test_genesis_hash(self):
        chain = AuditChain()
        e0 = chain.record("genesis", "system")
        assert e0.prev_hash == AuditChain.GENESIS_HASH

    def test_length(self):
        chain = AuditChain()
        assert chain.length == 0
        chain.record("a", "x")
        chain.record("b", "y")
        assert chain.length == 2

    def test_last_hash(self):
        chain = AuditChain()
        assert chain.last_hash == AuditChain.GENESIS_HASH
        e = chain.record("test", "admin")
        assert chain.last_hash == e.entry_hash

    def test_get_entries_filtered(self):
        chain = AuditChain()
        chain.record("login", "user1")
        chain.record("query", "user2")
        chain.record("login", "user3")
        logins = chain.get_entries(event_type="login")
        assert len(logins) == 2

    def test_tampered_chain_detected(self):
        chain = AuditChain()
        chain.record("legit", "admin")
        chain.record("also_legit", "admin")
        chain._entries[0].entry_hash = "tampered_hash_value"
        valid, errors = chain.verify_chain()
        assert valid is False
        assert len(errors) >= 1

    def test_persistence(self, tmp_path):
        log_path = tmp_path / "audit.jsonl"
        chain1 = AuditChain(log_path=log_path)
        chain1.record("event1", "admin")
        chain1.record("event2", "admin")
        assert log_path.exists()
        chain2 = AuditChain(log_path=log_path)
        assert chain2.length == 2
        valid, errors = chain2.verify_chain()
        assert valid is True

    def test_entry_serialization(self):
        entry = AuditEntry(
            sequence=0, timestamp=1000.0, event_type="test",
            actor="admin", details={"key": "val"},
            prev_hash=AuditChain.GENESIS_HASH,
        )
        entry.entry_hash = entry.compute_hash()
        d = entry.to_dict()
        restored = AuditEntry.from_dict(d)
        assert restored.entry_hash == entry.entry_hash
        assert restored.compute_hash() == entry.entry_hash


# ── Compliance ──────────────────────────────────────

class TestCompliance:
    def test_basic_always_passes(self):
        report = run_compliance("basic", {})
        assert report.passed is True
        assert report.total_checks == 1

    def test_banking_full_compliance(self):
        ctx = {
            "air_gap_verified": True,
            "audit_chain_active": True,
            "crypto_shred_keys": 3,
            "max_token_ttl": 3600,
            "provider_type": "llama_cpp",
            "hmac_row_enabled": True,
            "http_server_running": False,
        }
        report = run_compliance("banking", ctx)
        assert report.passed is True
        assert len(report.critical_failures) == 0

    def test_banking_fails_without_air_gap(self):
        ctx = {
            "air_gap_verified": False,
            "audit_chain_active": True,
            "crypto_shred_keys": 1,
            "max_token_ttl": 3600,
            "provider_type": "llama_cpp",
        }
        report = run_compliance("banking", ctx)
        assert report.passed is False
        names = [c.name for c in report.critical_failures]
        assert "air_gap_required" in names

    def test_banking_fails_with_external_provider(self):
        ctx = {
            "air_gap_verified": True,
            "audit_chain_active": True,
            "crypto_shred_keys": 1,
            "max_token_ttl": 3600,
            "provider_type": "openai",
        }
        report = run_compliance("banking", ctx)
        assert report.passed is False
        names = [c.name for c in report.critical_failures]
        assert "no_external_providers" in names

    def test_banking_fails_with_long_ttl(self):
        ctx = {
            "air_gap_verified": True,
            "audit_chain_active": True,
            "crypto_shred_keys": 1,
            "max_token_ttl": 86400,
            "provider_type": "llama_cpp",
        }
        report = run_compliance("banking", ctx)
        assert report.passed is False

    def test_enterprise_compliance(self):
        ctx = {"auth_enabled": True, "audit_chain_active": True, "hmac_enabled": True}
        report = run_compliance("enterprise", ctx)
        assert report.passed is True

    def test_enterprise_fails_no_auth(self):
        ctx = {"auth_enabled": False}
        report = run_compliance("enterprise", ctx)
        assert report.passed is False

    def test_report_to_dict(self):
        report = run_compliance("basic", {})
        d = report.to_dict()
        assert d["profile"] == "basic"
        assert d["passed"] is True
        assert "total" in d

    def test_banking_rules_defined(self):
        assert len(BANKING_RULES) >= 5
        for name, desc in BANKING_RULES:
            assert len(name) > 0
            assert len(desc) > 0

    def test_enterprise_rules_defined(self):
        assert len(ENTERPRISE_RULES) >= 2
