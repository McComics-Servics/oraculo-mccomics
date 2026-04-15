"""
Modulo: oraculo.polyglot.resolvers.copybook_resolver
Proposito: Resolucion de COPY/INCLUDE en COBOL, PL/I, RPG. Busca copybooks en paths configurables.
Documento de LEY: POLYGLOT_FABRIC_SPEC.md seccion 2.6
"""
from __future__ import annotations
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

COBOL_COPYBOOK_EXTENSIONS = (".cpy", ".cbl", ".cob", ".copy", "")
PLI_INCLUDE_EXTENSIONS = (".pli", ".pl1", ".inc", "")
RPG_COPY_EXTENSIONS = (".rpgle", ".rpg", ".rpg4", "")


@dataclass
class ResolvedCopybook:
    name: str
    resolved_path: Path | None
    source_file: str
    source_line: int = 0
    language: str = "cobol"


@dataclass
class CopybookIndex:
    entries: dict[str, Path] = field(default_factory=dict)

    def add(self, name: str, path: Path) -> None:
        self.entries[name.upper()] = path

    def resolve(self, name: str) -> Path | None:
        return self.entries.get(name.upper())

    def count(self) -> int:
        return len(self.entries)


class CopybookResolver:
    """Resuelve referencias COPY/INCLUDE buscando en directorios configurados."""

    def __init__(self, search_paths: list[Path] | None = None):
        self._search_paths = search_paths or []
        self._index = CopybookIndex()
        self._built = False

    @property
    def index(self) -> CopybookIndex:
        return self._index

    def add_search_path(self, path: Path) -> None:
        if path not in self._search_paths:
            self._search_paths.append(path)
            self._built = False

    def build_index(self) -> int:
        """Escanea search_paths y construye indice de copybooks. Retorna cantidad encontrada."""
        self._index = CopybookIndex()
        all_exts = set(COBOL_COPYBOOK_EXTENSIONS + PLI_INCLUDE_EXTENSIONS + RPG_COPY_EXTENSIONS)

        for search_dir in self._search_paths:
            if not search_dir.is_dir():
                continue
            for f in search_dir.rglob("*"):
                if f.is_file() and (f.suffix.lower() in all_exts or f.suffix == ""):
                    self._index.add(f.stem, f)

        self._built = True
        logger.info("CopybookResolver: %d copybooks indexados en %d paths",
                     self._index.count(), len(self._search_paths))
        return self._index.count()

    def resolve(self, name: str, language: str = "cobol") -> Path | None:
        """Resuelve un nombre de copybook a su path. Busca primero en indice, luego en paths."""
        if not self._built:
            self.build_index()

        # 1. Buscar en indice
        found = self._index.resolve(name)
        if found:
            return found

        # 2. Buscar directamente en paths con extensiones
        exts = self._extensions_for_language(language)
        for search_dir in self._search_paths:
            for ext in exts:
                candidate = search_dir / f"{name}{ext}"
                if candidate.exists():
                    self._index.add(name, candidate)
                    return candidate

        return None

    def resolve_all(self, names: list[str], language: str = "cobol") -> list[ResolvedCopybook]:
        """Resuelve una lista de nombres de copybook."""
        results = []
        for name in names:
            path = self.resolve(name, language)
            results.append(ResolvedCopybook(name=name, resolved_path=path, source_file="", language=language))
        return results

    def _extensions_for_language(self, language: str) -> tuple[str, ...]:
        if language in ("cobol", "cob", "cbl"):
            return COBOL_COPYBOOK_EXTENSIONS
        if language in ("pli", "pl1"):
            return PLI_INCLUDE_EXTENSIONS
        if language in ("rpg", "rpgle"):
            return RPG_COPY_EXTENSIONS
        return ("",)
