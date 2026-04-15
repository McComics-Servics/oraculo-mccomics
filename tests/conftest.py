"""Fixtures compartidas para todos los tests."""
from __future__ import annotations
import shutil
from pathlib import Path

import pytest

PROFILES_SRC = Path(__file__).resolve().parents[0] / ".." / "profiles"


@pytest.fixture
def profiles_dir(tmp_path: Path) -> Path:
    """Copia los 3 perfiles YAML a un directorio temporal."""
    dest = tmp_path / "profiles"
    shutil.copytree(PROFILES_SRC.resolve(), dest)
    return dest
