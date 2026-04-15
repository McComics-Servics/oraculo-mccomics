"""
Modulo: oraculo.index.pipeline
Proposito: Orquestador central de indexacion. Conecta: archivo -> pre_check -> encoding -> dispatch -> parse -> fragment -> store.
Correccion A del PLAN_ESTRATEGICO.md — el "pegamento" que faltaba entre F1-F3.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path

from oraculo.index.sqlite_store import SqliteFtsStore, IndexedFragment, compute_file_hash, make_fragment_id
from oraculo.index.duckdb_store import DuckDbStore
from oraculo.index.incremental import IncrementalChecker
from oraculo.polyglot.pre_index_checks import check_file, PreIndexResult
from oraculo.polyglot.encoding_detect import read_file_normalized
from oraculo.polyglot.dispatcher import dispatch, ParserLevel
from oraculo.polyglot.lexical_skeleton import extract_skeleton
from oraculo.polyglot.fastcdc import fastcdc

logger = logging.getLogger(__name__)


@dataclass
class PipelineStats:
    files_processed: int = 0
    files_skipped: int = 0
    files_errored: int = 0
    fragments_created: int = 0
    secrets_detected: int = 0
    errors: list[str] = field(default_factory=list)


class IndexPipeline:
    """Pipeline completo: archivo -> pre_check -> encoding -> dispatch -> parse -> fragment -> store."""

    def __init__(self, fts_store: SqliteFtsStore, duck_store: DuckDbStore):
        self._fts = fts_store
        self._duck = duck_store
        self._checker = IncrementalChecker(lambda p: self._fts.get_file_hash(p))

    def index_file(self, path: Path, force: bool = False) -> PipelineStats:
        stats = PipelineStats()
        try:
            self._process_one(path, stats, force)
        except Exception as e:
            stats.files_errored += 1
            stats.errors.append(f"{path}: {e}")
            logger.error("Pipeline error indexando %s: %s", path, e)
        return stats

    def index_batch(self, paths: list[Path], force: bool = False) -> PipelineStats:
        stats = PipelineStats()
        for path in paths:
            try:
                self._process_one(path, stats, force)
            except Exception as e:
                stats.files_errored += 1
                stats.errors.append(f"{path}: {e}")
                logger.error("Pipeline error indexando %s: %s", path, e)
        return stats

    def _process_one(self, path: Path, stats: PipelineStats, force: bool) -> None:
        if not force and not self._checker.needs_indexing(path):
            stats.files_skipped += 1
            return

        pre = check_file(path)
        if not pre.indexable:
            stats.files_skipped += 1
            logger.debug("Archivo no indexable: %s — %s", path, pre.reason)
            return

        if pre.secrets_found:
            stats.secrets_detected += len(pre.secrets_found)
            logger.warning("Secretos detectados en %s: %d", path, len(pre.secrets_found))

        content, encoding = read_file_normalized(path)
        file_hash = compute_file_hash(path)
        disp = dispatch(path)

        self._fts.delete_by_file(str(path))

        fragments = self._parse_to_fragments(path, content, disp.level, disp.language, encoding)

        fts_frags = []
        for start, end, text in fragments:
            fid = make_fragment_id(str(path), start, end)
            fts_frags.append(IndexedFragment(
                fragment_id=fid,
                file_path=str(path),
                file_hash=file_hash,
                start_line=start,
                end_line=end,
                content=text,
                language=disp.language,
                parser_level=disp.level.value,
                encoding=encoding,
            ))

        if fts_frags:
            self._fts.insert_batch(fts_frags)
            stats.fragments_created += len(fts_frags)

        lines = content.splitlines()
        self._duck.upsert_file_metadata(
            str(path), file_hash, disp.language, disp.level.value,
            encoding, len(lines), path.stat().st_size,
        )

        stats.files_processed += 1

    def _parse_to_fragments(self, path: Path, content: str,
                            level: ParserLevel, language: str,
                            encoding: str) -> list[tuple[int, int, str]]:
        if level in (ParserLevel.L1_TREESITTER, ParserLevel.L4_LEXICAL):
            is_cobol = language == "cobol"
            skeleton_frags = extract_skeleton(content, is_cobol=is_cobol)
            if skeleton_frags:
                return [(f.start_line, f.end_line, f.text) for f in skeleton_frags]

        raw = content.encode("utf-8")
        chunks = fastcdc(raw)
        result = []
        line_offset = 1
        for ch in chunks:
            text = ch.data.decode("utf-8", errors="replace")
            n_lines = text.count("\n") + 1
            result.append((line_offset, line_offset + n_lines - 1, text))
            line_offset += n_lines
        return result
