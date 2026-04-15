"""Tests unitarios del Context Assembler (F4): TrustTier, BudgetAllocator, PayloadBuilder."""
from __future__ import annotations

import pytest

from oraculo.assembler.trust_tier import assign_tier, filter_by_min_tier, TRUST_CANON, TRUST_HIGH, TRUST_CONTEXTUAL
from oraculo.assembler.budget_allocator import BudgetAllocator
from oraculo.assembler.payload_builder import PayloadBuilder, FragmentPayload


class TestTrustTier:
    def test_canon_source(self):
        t = assign_tier("f1", "official_docs", "L1_treesitter")
        assert t.tier == TRUST_CANON

    def test_high_source(self):
        t = assign_tier("f2", "project_code", "L4_lexical")
        assert t.tier == TRUST_HIGH

    def test_high_parser(self):
        t = assign_tier("f3", "random_source", "L1_treesitter")
        assert t.tier == TRUST_HIGH

    def test_contextual_fallback(self):
        t = assign_tier("f4", "unknown_source", "L4_lexical")
        assert t.tier == TRUST_CONTEXTUAL

    def test_has_tests_boosts(self):
        t = assign_tier("f5", "unknown", "L4_lexical", has_tests=True)
        assert t.tier == TRUST_HIGH

    def test_filter_by_min_tier(self):
        assignments = [
            assign_tier("f1", "official_docs", "L1"),
            assign_tier("f2", "project_code", "L1"),
            assign_tier("f3", "unknown", "L4_lexical"),
        ]
        high_only = filter_by_min_tier(assignments, TRUST_HIGH)
        assert len(high_only) == 2


class TestBudgetAllocator:
    def test_default_allocations(self):
        ba = BudgetAllocator(total_budget=4096)
        assert ba.total_budget == 4096
        assert ba.total_remaining() > 0

    def test_consume(self):
        ba = BudgetAllocator(total_budget=1000, layer_weights={"L2_canon": 1.0})
        consumed = ba.consume("L2_canon", 500)
        assert consumed == 500
        assert ba.remaining("L2_canon") == 500

    def test_consume_exceeds(self):
        ba = BudgetAllocator(total_budget=100, layer_weights={"L2_canon": 1.0})
        consumed = ba.consume("L2_canon", 200)
        assert consumed == 100

    def test_consume_nonexistent_layer(self):
        ba = BudgetAllocator(total_budget=100, layer_weights={"L2_canon": 1.0})
        assert ba.consume("fake", 50) == 0

    def test_summary(self):
        ba = BudgetAllocator(total_budget=1000, layer_weights={"L2_canon": 0.5, "L3_high_confidence": 0.5})
        ba.consume("L2_canon", 100)
        s = ba.summary()
        assert s["L2_canon"]["used"] == 100
        assert s["L3_high_confidence"]["used"] == 0

    def test_multiple_layers(self):
        ba = BudgetAllocator(total_budget=4096)
        allocs = ba.allocations
        assert len(allocs) == 7


class TestPayloadBuilder:
    def test_build_empty(self):
        pb = PayloadBuilder(query="test", profile="basic")
        payload = pb.build()
        assert payload.query == "test"
        assert payload.profile == "basic"
        assert payload.total_fragments == 0

    def test_build_with_fragments(self):
        pb = PayloadBuilder(query="calculate", profile="enterprise")
        pb.add_fragment(FragmentPayload(
            fragment_id="f1", file_path="foo.py",
            start_line=1, end_line=10,
            content="def calculate(x): return x * 2",
            trust_tier=2, rrf_score=0.5,
            sources=["bm25"],
        ))
        payload = pb.build()
        assert payload.total_fragments == 1
        assert payload.fragments[0].fragment_id == "f1"

    def test_dedup_count(self):
        pb = PayloadBuilder(query="q", profile="basic")
        pb.set_dedup_removed(3)
        payload = pb.build()
        assert payload.dedup_removed == 3

    def test_to_dict(self):
        pb = PayloadBuilder(query="q", profile="basic")
        payload = pb.build()
        d = payload.to_dict()
        assert isinstance(d, dict)
        assert d["query"] == "q"
        assert "timestamp" in d

    def test_assembly_time(self):
        pb = PayloadBuilder(query="q", profile="basic")
        payload = pb.build()
        assert payload.assembly_time_ms >= 0
