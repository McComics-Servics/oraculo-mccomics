"""
Modulo: oraculo.index.domain_manager
Proposito: Gestion de dominios (code, docs, emails, etc). Cada dominio tiene su clave de cifrado independiente.
Documento de LEY: POLICY_ENGINE_SPEC.md (multi-dominio M6) + CONTEXT_ASSEMBLY_POLICY.md
"""
from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Domain:
    name: str
    paths: list[str]
    db_dir: Path

    @property
    def duckdb_path(self) -> Path:
        return self.db_dir / "duckdb.db"

    @property
    def sqlite_fts_path(self) -> Path:
        return self.db_dir / "sqlite_fts.db"

    @property
    def meta_path(self) -> Path:
        return self.db_dir / "domain_meta.json"


class DomainManager:
    """Administra dominios persistentes. Cada dominio = directorio aislado con sus propias DBs."""

    def __init__(self, data_dir: Path):
        self._data_dir = data_dir
        self._domains_dir = data_dir / "domains"
        self._domains: dict[str, Domain] = {}

    def init(self) -> None:
        self._domains_dir.mkdir(parents=True, exist_ok=True)
        for d in self._domains_dir.iterdir():
            if d.is_dir() and (d / "domain_meta.json").exists():
                meta = json.loads((d / "domain_meta.json").read_text(encoding="utf-8"))
                self._domains[meta["name"]] = Domain(
                    name=meta["name"], paths=meta.get("paths", []), db_dir=d,
                )

    def create(self, name: str, paths: list[str]) -> Domain:
        if name in self._domains:
            raise ValueError(f"Dominio ya existe: {name}")
        db_dir = self._domains_dir / name
        db_dir.mkdir(parents=True, exist_ok=True)
        domain = Domain(name=name, paths=paths, db_dir=db_dir)
        meta = {"name": name, "paths": paths}
        domain.meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self._domains[name] = domain
        logger.info("Dominio creado: %s con %d rutas", name, len(paths))
        return domain

    def get(self, name: str) -> Domain | None:
        return self._domains.get(name)

    def list_domains(self) -> list[Domain]:
        return list(self._domains.values())

    def remove(self, name: str) -> bool:
        domain = self._domains.pop(name, None)
        if domain is None:
            return False
        import shutil
        shutil.rmtree(domain.db_dir, ignore_errors=True)
        logger.info("Dominio eliminado: %s", name)
        return True
