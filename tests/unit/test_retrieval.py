"""Tests unitarios de Retrieval (F4): BM25, RRF, SimHash, WeightLearner."""
from __future__ import annotations
from pathlib import Path

import pytest

from oraculo.retrieval.rrf_fusion import rrf_fuse, RankedItem
from oraculo.retrieval.simhash_dedup import simhash, hamming_distance, is_near_duplicate, dedup_fragments
from oraculo.retrieval.weight_learner import WeightLearner, DEFAULT_WEIGHTS
from oraculo.retrieval.vector_search import cosine_similarity


class TestRRFFusion:
    def test_single_source(self):
        results = rrf_fuse({"bm25": ["a", "b", "c"]})
        assert len(results) == 3
        assert results[0].fragment_id == "a"
        assert results[0].score > results[1].score

    def test_two_sources_boost(self):
        results = rrf_fuse({
            "bm25": ["a", "b", "c"],
            "vector": ["b", "a", "d"],
        })
        scores = {r.fragment_id: r.score for r in results}
        assert scores["b"] > scores["c"]
        assert scores["a"] > scores["d"]

    def test_weights(self):
        r1 = rrf_fuse({"bm25": ["a", "b"], "vector": ["b", "a"]}, weights={"bm25": 2.0, "vector": 1.0})
        assert r1[0].fragment_id == "a"

    def test_empty_rankings(self):
        results = rrf_fuse({})
        assert results == []

    def test_sources_tracked(self):
        results = rrf_fuse({"bm25": ["a"], "vector": ["a"]})
        assert "bm25" in results[0].sources
        assert "vector" in results[0].sources


class TestSimHash:
    def test_identical_texts(self):
        h1 = simhash("def calculate_total(items): return sum(items)")
        h2 = simhash("def calculate_total(items): return sum(items)")
        assert h1 == h2

    def test_similar_texts(self):
        h1 = simhash("def calculate_total items return sum items price tax discount")
        h2 = simhash("def calculate_total items return sum items price tax shipping")
        assert hamming_distance(h1, h2) < 30

    def test_different_texts(self):
        h1 = simhash("print hello world greeting")
        h2 = simhash("database query optimize index search")
        assert hamming_distance(h1, h2) > 5

    def test_near_duplicate_true(self):
        text = "function calculate total amount price tax discount items values result"
        assert is_near_duplicate(text, text, threshold=5)

    def test_near_duplicate_false(self):
        assert not is_near_duplicate(
            "network socket connection tcp",
            "database query optimize search index",
            threshold=3,
        )

    def test_dedup_removes_duplicates(self):
        frags = [
            ("a", "def calculate_total(items): return sum(items)"),
            ("b", "def calculate_total(items): return sum(items)"),
            ("c", "class DatabaseConnection: def connect(self): pass"),
        ]
        unique = dedup_fragments(frags)
        assert "a" in unique
        assert "b" not in unique
        assert "c" in unique

    def test_dedup_empty(self):
        assert dedup_fragments([]) == []


class TestWeightLearner:
    def test_initial_weights(self):
        wl = WeightLearner()
        assert wl.weights == DEFAULT_WEIGHTS
        assert wl.feedback_count == 0

    def test_positive_feedback(self):
        wl = WeightLearner()
        initial = wl.weights["bm25"]
        wl.record_feedback(["bm25"], positive=True)
        assert wl.weights["bm25"] > initial
        assert wl.feedback_count == 1

    def test_negative_feedback(self):
        wl = WeightLearner()
        initial = wl.weights["vector"]
        wl.record_feedback(["vector"], positive=False)
        assert wl.weights["vector"] < initial

    def test_persistence(self, tmp_path: Path):
        state_file = tmp_path / "weights.json"
        wl1 = WeightLearner(state_file=state_file)
        wl1.record_feedback(["bm25"], positive=True)
        wl2 = WeightLearner(state_file=state_file)
        assert wl2.weights["bm25"] == wl1.weights["bm25"]
        assert wl2.feedback_count == 1

    def test_weight_clamping(self):
        wl = WeightLearner()
        for _ in range(200):
            wl.record_feedback(["bm25"], positive=True)
        assert wl.weights["bm25"] <= 3.0
        for _ in range(400):
            wl.record_feedback(["bm25"], positive=False)
        assert wl.weights["bm25"] >= 0.1


class TestCosineSimilarity:
    def test_identical_vectors(self):
        v = [1.0, 2.0, 3.0]
        assert abs(cosine_similarity(v, v) - 1.0) < 1e-9

    def test_orthogonal_vectors(self):
        assert abs(cosine_similarity([1.0, 0.0], [0.0, 1.0])) < 1e-9

    def test_zero_vector(self):
        assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
