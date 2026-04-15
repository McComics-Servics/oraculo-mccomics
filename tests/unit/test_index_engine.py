"""Tests unitarios del Index Engine (F3)."""
from __future__ import annotations
import time
from pathlib import Path

import pytest

from oraculo.index.sqlite_store import SqliteFtsStore, IndexedFragment, compute_file_hash, make_fragment_id
from oraculo.index.duckdb_store import DuckDbStore
from oraculo.index.domain_manager import DomainManager
from oraculo.index.incremental import IncrementalChecker
from oraculo.index.debouncer import Debouncer
from oraculo.index.stale_detector import StaleDetector
from oraculo.index.integrity_check import check_sqlite, check_duckdb
from oraculo.index.row_hmac import compute_row_hmac, verify_row_hmac
from oraculo.index.symbol_table import make_symbol_id, Symbol
from oraculo.index.call_graph import detect_dynamic_dispatch


class TestSqliteFtsStore:
    def test_open_and_count(self, tmp_path: Path):
        store = SqliteFtsStore(tmp_path / "test.db")
        store.open()
        assert store.count() == 0
        store.close()

    def test_insert_and_search(self, tmp_path: Path):
        store = SqliteFtsStore(tmp_path / "test.db")
        store.open()
        frag = IndexedFragment(
            fragment_id="abc123", file_path="foo.py", file_hash="h1",
            start_line=1, end_line=10, content="def calculate_total(items):\n    return sum(items)",
            language="python", parser_level="L1_treesitter", encoding="utf-8",
        )
        store.insert(frag)
        assert store.count() == 1
        results = store.search_bm25("calculate_total")
        assert len(results) >= 1
        assert results[0][0] == "abc123"
        store.close()

    def test_batch_insert(self, tmp_path: Path):
        store = SqliteFtsStore(tmp_path / "test.db")
        store.open()
        frags = [
            IndexedFragment(f"id_{i}", f"file_{i}.py", "h", 1, 10,
                            f"content number {i}", "python", "L1", "utf-8")
            for i in range(50)
        ]
        count = store.insert_batch(frags)
        assert count == 50
        assert store.count() == 50
        store.close()

    def test_delete_by_file(self, tmp_path: Path):
        store = SqliteFtsStore(tmp_path / "test.db")
        store.open()
        frag = IndexedFragment("x1", "delete_me.py", "h", 1, 5, "code here", "py", "L1", "utf-8")
        store.insert(frag)
        assert store.count() == 1
        store.delete_by_file("delete_me.py")
        assert store.count() == 0
        store.close()

    def test_files_indexed(self, tmp_path: Path):
        store = SqliteFtsStore(tmp_path / "test.db")
        store.open()
        store.insert(IndexedFragment("a", "one.py", "h", 1, 1, "x", "py", "L1", "utf-8"))
        store.insert(IndexedFragment("b", "two.py", "h", 1, 1, "y", "py", "L1", "utf-8"))
        assert sorted(store.files_indexed()) == ["one.py", "two.py"]
        store.close()


class TestDuckDbStore:
    def test_open_and_counts(self, tmp_path: Path):
        store = DuckDbStore(tmp_path / "test.duckdb")
        store.open()
        assert store.count_files() == 0
        assert store.count_symbols() == 0
        store.close()

    def test_upsert_file_metadata(self, tmp_path: Path):
        store = DuckDbStore(tmp_path / "test.duckdb")
        store.open()
        store.upsert_file_metadata("foo.py", "hash1", "python", "L1", "utf-8", 100, 2048)
        assert store.count_files() == 1
        assert store.get_file_hash("foo.py") == "hash1"
        store.close()

    def test_symbols_crud(self, tmp_path: Path):
        store = DuckDbStore(tmp_path / "test.duckdb")
        store.open()
        store.upsert_file_metadata("foo.py", "h", "python", "L1", "utf-8", 10, 100)
        store.insert_symbol("s1", "foo.py", "calculate_total", "function", 1, 5, "def calculate_total(items)")
        results = store.search_symbols("calculate")
        assert len(results) == 1
        assert results[0]["name"] == "calculate_total"
        store.close()

    def test_call_graph(self, tmp_path: Path):
        store = DuckDbStore(tmp_path / "test.duckdb")
        store.open()
        store.upsert_file_metadata("a.py", "h", "python", "L1", "utf-8", 10, 100)
        store.insert_symbol("s1", "a.py", "foo", "function", 1, 5)
        store.insert_symbol("s2", "a.py", "bar", "function", 6, 10)
        store.insert_call_edge("s1", "s2", 3)
        assert store.get_callees("s1") == ["s2"]
        assert store.get_callers("s2") == ["s1"]
        store.close()

    def test_stale_marking(self, tmp_path: Path):
        store = DuckDbStore(tmp_path / "test.duckdb")
        store.open()
        store.upsert_file_metadata("foo.py", "h", "python", "L1", "utf-8", 10, 100)
        store.mark_stale("foo.py")
        assert store.stale_files() == ["foo.py"]
        store.close()


class TestDomainManager:
    def test_create_and_list(self, tmp_path: Path):
        dm = DomainManager(tmp_path)
        dm.init()
        d = dm.create("code", ["/src"])
        assert d.name == "code"
        assert len(dm.list_domains()) == 1

    def test_get(self, tmp_path: Path):
        dm = DomainManager(tmp_path)
        dm.init()
        dm.create("docs", ["/docs"])
        assert dm.get("docs") is not None
        assert dm.get("no_existe") is None

    def test_remove(self, tmp_path: Path):
        dm = DomainManager(tmp_path)
        dm.init()
        dm.create("temp", ["/tmp"])
        assert dm.remove("temp")
        assert len(dm.list_domains()) == 0

    def test_persistence(self, tmp_path: Path):
        dm1 = DomainManager(tmp_path)
        dm1.init()
        dm1.create("code", ["/src"])
        dm2 = DomainManager(tmp_path)
        dm2.init()
        assert len(dm2.list_domains()) == 1


class TestIncrementalChecker:
    def test_new_file_needs_indexing(self, tmp_path: Path):
        f = tmp_path / "new.py"
        f.write_text("print('hello')")
        checker = IncrementalChecker(lambda _: None)
        assert checker.needs_indexing(f)

    def test_unchanged_file_skip(self, tmp_path: Path):
        f = tmp_path / "same.py"
        f.write_text("x = 1")
        h = compute_file_hash(f)
        checker = IncrementalChecker(lambda _: h)
        assert not checker.needs_indexing(f)


class TestDebouncer:
    def test_debounce_groups_events(self):
        results = []
        d = Debouncer(0.1, lambda paths: results.append(paths))
        d.trigger("a.py")
        d.trigger("b.py")
        d.trigger("a.py")
        time.sleep(0.3)
        assert len(results) == 1
        assert results[0] == {"a.py", "b.py"}
        d.cancel()


class TestStaleDetector:
    def test_missing_file_is_stale(self, tmp_path: Path):
        det = StaleDetector(lambda _: "some_hash")
        assert det.is_stale(str(tmp_path / "missing.py"))

    def test_changed_file_is_stale(self, tmp_path: Path):
        f = tmp_path / "changed.py"
        f.write_text("v1")
        det = StaleDetector(lambda _: "old_hash")
        assert det.is_stale(str(f))


class TestIntegrity:
    def test_sqlite_integrity(self, tmp_path: Path):
        store = SqliteFtsStore(tmp_path / "test.db")
        store.open()
        store.close()
        report = check_sqlite(tmp_path / "test.db")
        assert report.ok

    def test_duckdb_integrity(self, tmp_path: Path):
        store = DuckDbStore(tmp_path / "test.duckdb")
        store.open()
        store.close()
        report = check_duckdb(tmp_path / "test.duckdb")
        assert report.ok

    def test_missing_db(self, tmp_path: Path):
        report = check_sqlite(tmp_path / "nope.db")
        assert not report.ok


class TestRowHmac:
    def test_compute_and_verify(self):
        key = b"secret_key_mccomics"
        h = compute_row_hmac(key, "frag1", "file.py", "content_here")
        assert verify_row_hmac(key, h, "frag1", "file.py", "content_here")

    def test_tampered_fails(self):
        key = b"secret"
        h = compute_row_hmac(key, "a", "b")
        assert not verify_row_hmac(key, h, "a", "c")


class TestMiscIndex:
    def test_make_fragment_id(self):
        fid = make_fragment_id("foo.py", 1, 10)
        assert len(fid) == 16

    def test_make_symbol_id(self):
        sid = make_symbol_id("foo.py", "bar", 5)
        assert len(sid) == 16

    def test_dynamic_dispatch(self):
        assert detect_dynamic_dispatch("obj.send(:method_name)")
        assert not detect_dynamic_dispatch("x = 1 + 2")
