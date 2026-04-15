"""Tests unitarios del IndexPipeline y AssemblyPipeline (F4) — integracion ligera."""
from __future__ import annotations
from pathlib import Path

import pytest

from oraculo.index.sqlite_store import SqliteFtsStore, IndexedFragment, make_fragment_id
from oraculo.index.duckdb_store import DuckDbStore
from oraculo.index.pipeline import IndexPipeline, PipelineStats
from oraculo.assembler.pipeline import AssemblyPipeline, estimate_tokens


@pytest.fixture
def stores(tmp_path: Path):
    fts = SqliteFtsStore(tmp_path / "test.db")
    fts.open()
    duck = DuckDbStore(tmp_path / "test.duckdb")
    duck.open()
    yield fts, duck
    fts.close()
    duck.close()


@pytest.fixture
def sample_file(tmp_path: Path) -> Path:
    f = tmp_path / "sample.py"
    f.write_text("def calculate_total(items):\n    return sum(items)\n\n\ndef get_price(item):\n    return item.price\n")
    return f


class TestIndexPipeline:
    def test_index_single_file(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        stats = pipeline.index_file(sample_file)
        assert stats.files_processed == 1
        assert stats.fragments_created >= 1
        assert stats.files_errored == 0
        assert fts.count() >= 1

    def test_skip_unchanged(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        pipeline.index_file(sample_file)
        stats2 = pipeline.index_file(sample_file)
        assert stats2.files_skipped == 1
        assert stats2.files_processed == 0

    def test_force_reindex(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        pipeline.index_file(sample_file)
        stats2 = pipeline.index_file(sample_file, force=True)
        assert stats2.files_processed == 1

    def test_non_indexable_file(self, stores, tmp_path):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        binary_file = tmp_path / "data.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")
        stats = pipeline.index_file(binary_file)
        assert stats.files_skipped == 1

    def test_batch_index(self, stores, tmp_path):
        fts, duck = stores
        files = []
        for i in range(5):
            f = tmp_path / f"file_{i}.py"
            f.write_text(f"def func_{i}():\n    return {i}\n")
            files.append(f)
        pipeline = IndexPipeline(fts, duck)
        stats = pipeline.index_batch(files)
        assert stats.files_processed == 5
        assert stats.fragments_created >= 5

    def test_missing_file_error(self, stores, tmp_path):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        stats = pipeline.index_file(tmp_path / "no_existe.py")
        assert stats.files_processed == 0
        assert (stats.files_skipped + stats.files_errored) >= 1

    def test_metadata_in_duckdb(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        pipeline.index_file(sample_file)
        assert duck.count_files() == 1
        h = duck.get_file_hash(str(sample_file))
        assert h is not None


class TestAssemblyPipeline:
    def test_assemble_empty_store(self, stores):
        fts, duck = stores
        ap = AssemblyPipeline(fts, duck, profile="basic")
        result = ap.assemble("calculate_total")
        assert result.total_fragments == 0
        assert result.query == "calculate_total"

    def test_assemble_with_data(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        pipeline.index_file(sample_file)
        ap = AssemblyPipeline(fts, duck, profile="enterprise")
        result = ap.assemble("calculate")
        assert result.total_fragments >= 1
        assert result.fragments[0].trust_tier in (1, 2, 3)
        assert result.fragments[0].rrf_score > 0
        assert result.assembly_time_ms >= 0

    def test_budget_respected(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        pipeline.index_file(sample_file)
        ap = AssemblyPipeline(fts, duck, profile="basic", total_budget=10)
        result = ap.assemble("calculate")
        assert result.total_fragments <= 10

    def test_payload_has_provenance(self, stores, sample_file):
        fts, duck = stores
        pipeline = IndexPipeline(fts, duck)
        pipeline.index_file(sample_file)
        ap = AssemblyPipeline(fts, duck, profile="enterprise")
        result = ap.assemble("calculate")
        if result.total_fragments > 0:
            frag = result.fragments[0]
            assert frag.file_path != "unknown"
            assert frag.language != "unknown"
            assert len(frag.sources) > 0


class TestEstimateTokens:
    def test_basic(self):
        assert estimate_tokens("hello world") >= 1

    def test_empty(self):
        assert estimate_tokens("") == 1
