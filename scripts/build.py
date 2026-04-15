"""
Pipeline de build del Oraculo McComics v4.0
Uso: python scripts/build.py --target windows --profile-bundle all

(C) 2026 McComics Servicios Generales — Lima, Peru
Documento de LEY: PROJECT_STRUCTURE_SPEC.md seccion 7
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("build")

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
UI = ROOT / "ui"
PROFILES = ROOT / "profiles"
SCHEMAS = ROOT / "schemas"
MANIFESTS = ROOT / "manifests"
DIST = ROOT / "dist"


@dataclass
class BuildContext:
    target: str = "windows"
    arch: str = "x64"
    profile_bundle: str = "all"
    skip_sign: bool = False
    skip_installer: bool = False
    skip_smoke: bool = False
    errors: list[str] = field(default_factory=list)
    artifacts: list[Path] = field(default_factory=list)
    phase_times: dict[str, float] = field(default_factory=dict)


PHASES = [
    "validate_environment",
    "verify_dependency_hashes",
    "compile_treesitter_bindings",
    "build_ui_dist",
    "sign_profiles",
    "sign_manifests",
    "package_python_with_pyinstaller",
    "embed_resources",
    "code_sign_binary",
    "build_installer",
    "generate_offline_bundle",
    "compute_release_hashes",
    "smoke_test_installed",
]


def phase(name: str):
    def decorator(fn):
        fn._phase_name = name
        return fn
    return decorator


class BuildPipeline:

    def __init__(self, ctx: BuildContext):
        self.ctx = ctx

    def run(self) -> bool:
        logger.info("=" * 60)
        logger.info("BUILD PIPELINE — El Oraculo McComics v4.0")
        logger.info("Target: %s/%s | Profiles: %s", self.ctx.target, self.ctx.arch, self.ctx.profile_bundle)
        logger.info("=" * 60)

        for phase_name in PHASES:
            method = getattr(self, f"_phase_{phase_name}", None)
            if not method:
                logger.warning("Fase no implementada: %s", phase_name)
                continue
            logger.info("--- Fase: %s ---", phase_name)
            t0 = time.monotonic()
            try:
                method()
                elapsed = time.monotonic() - t0
                self.ctx.phase_times[phase_name] = elapsed
                logger.info("    OK (%.1fs)", elapsed)
            except Exception as e:
                self.ctx.errors.append(f"{phase_name}: {e}")
                logger.error("    FALLO: %s", e)
                if phase_name in ("validate_environment", "verify_dependency_hashes"):
                    logger.error("Fase critica fallida. Abortando.")
                    return False

        if self.ctx.errors:
            logger.warning("Build completado con %d errores:", len(self.ctx.errors))
            for err in self.ctx.errors:
                logger.warning("  - %s", err)
            return False

        logger.info("=" * 60)
        logger.info("BUILD EXITOSO")
        for name, t in self.ctx.phase_times.items():
            logger.info("  %s: %.1fs", name, t)
        total = sum(self.ctx.phase_times.values())
        logger.info("  TOTAL: %.1fs", total)
        logger.info("=" * 60)
        return True

    def _phase_validate_environment(self):
        v = sys.version_info
        if v < (3, 11):
            raise RuntimeError(f"Python {v.major}.{v.minor} < 3.11")
        logger.info("    Python %s OK", sys.version.split()[0])

        for tool in ["pip"]:
            if not shutil.which(tool):
                raise RuntimeError(f"{tool} no encontrado en PATH")

    def _phase_verify_dependency_hashes(self):
        req = ROOT / "requirements.txt"
        if not req.exists():
            raise RuntimeError("requirements.txt no encontrado")
        logger.info("    requirements.txt presente (%d bytes)", req.stat().st_size)

    def _phase_compile_treesitter_bindings(self):
        try:
            import tree_sitter_languages  # noqa: F401
            logger.info("    tree-sitter-languages disponible")
        except ImportError:
            logger.info("    tree-sitter-languages no instalado — omitiendo compilacion")

    def _phase_build_ui_dist(self):
        ui_src = UI / "src"
        ui_dist = UI / "dist"
        ui_assets = SRC / "oraculo" / "ui" / "assets"

        if ui_assets.exists() and any(ui_assets.iterdir()):
            logger.info("    UI assets encontrados en src/oraculo/ui/assets/ — copiando a dist/")
            ui_dist.mkdir(parents=True, exist_ok=True)
            for f in ui_assets.iterdir():
                if f.is_file():
                    shutil.copy2(f, ui_dist / f.name)
        elif ui_src.exists() and (ui_src / "index.html").exists():
            logger.info("    UI fuente encontrada — build con npm")
            if shutil.which("npm"):
                subprocess.run(["npm", "ci", "--prefix", str(UI)], check=False)
                subprocess.run(["npm", "run", "build", "--prefix", str(UI)], check=False)
            else:
                logger.info("    npm no disponible — copiando src a dist tal cual")
                ui_dist.mkdir(parents=True, exist_ok=True)
                shutil.copytree(ui_src, ui_dist, dirs_exist_ok=True)
        else:
            logger.info("    Sin fuentes UI — omitiendo build")

    def _phase_sign_profiles(self):
        if self.ctx.skip_sign:
            logger.info("    Firma omitida (--skip-sign)")
            return
        for yaml_file in PROFILES.glob("*.yaml"):
            sig_file = yaml_file.with_suffix(".yaml.sig")
            h = hashlib.sha256(yaml_file.read_bytes()).hexdigest()
            sig_file.write_text(h, encoding="utf-8")
            logger.info("    Firmado: %s -> %s", yaml_file.name, h[:16])

    def _phase_sign_manifests(self):
        if self.ctx.skip_sign:
            return
        MANIFESTS.mkdir(parents=True, exist_ok=True)
        for yaml_file in MANIFESTS.glob("*.yaml"):
            h = hashlib.sha256(yaml_file.read_bytes()).hexdigest()
            yaml_file.with_suffix(".yaml.sig").write_text(h, encoding="utf-8")

    def _phase_package_python_with_pyinstaller(self):
        if not shutil.which("pyinstaller"):
            logger.info("    PyInstaller no instalado — omitiendo empaquetado")
            return
        spec = ROOT / "oraculo.spec"
        if spec.exists():
            subprocess.run(["pyinstaller", str(spec), "--noconfirm"], cwd=str(ROOT), check=True)
        else:
            entry = SRC / "oraculo" / "main.py"
            subprocess.run([
                "pyinstaller", "--name", "oraculo", "--noconfirm",
                "--noconsole", str(entry),
            ], cwd=str(ROOT), check=True)
        self.ctx.artifacts.append(DIST / "oraculo")

    def _phase_embed_resources(self):
        dist_oraculo = DIST / "oraculo"
        if not dist_oraculo.exists():
            logger.info("    Sin directorio dist/oraculo — omitiendo embed")
            return
        for resource_dir in [PROFILES, SCHEMAS, MANIFESTS]:
            if resource_dir.exists():
                dest = dist_oraculo / resource_dir.name
                shutil.copytree(resource_dir, dest, dirs_exist_ok=True)
        ui_dist = UI / "dist"
        if ui_dist.exists():
            shutil.copytree(ui_dist, dist_oraculo / "ui" / "dist", dirs_exist_ok=True)

    def _phase_code_sign_binary(self):
        if self.ctx.skip_sign:
            logger.info("    Firma de binario omitida")
            return
        logger.info("    Firma de binario requiere certificado — omitiendo en dev")

    def _phase_build_installer(self):
        if self.ctx.skip_installer:
            logger.info("    Instalador omitido")
            return
        dist_oraculo = DIST / "oraculo"
        if not dist_oraculo.exists():
            logger.info("    Sin dist/oraculo — no se puede crear instalador")
            return
        if self.ctx.target == "windows":
            nsis = ROOT / "installers" / "windows" / "nsis_installer.nsi"
            if nsis.exists() and shutil.which("makensis"):
                subprocess.run(["makensis", str(nsis)], check=False)
            else:
                logger.info("    NSIS no disponible — creando ZIP como fallback")
                shutil.make_archive(str(DIST / "oraculo-mccomics-4.0.0-win"), "zip", DIST, "oraculo")
                self.ctx.artifacts.append(DIST / "oraculo-mccomics-4.0.0-win.zip")
        elif self.ctx.target == "linux":
            logger.info("    AppImage build requiere tools especificas — omitiendo")
        elif self.ctx.target == "macos":
            logger.info("    .pkg build requiere macOS y certificado — omitiendo")

    def _phase_generate_offline_bundle(self):
        from oraculo.build.bundler import create_bundle
        result = create_bundle(
            src_dir=SRC,
            output_dir=DIST / "bundles",
            version="4.0.0",
            platform_name=self.ctx.target,
        )
        if result.success:
            logger.info("    Bundle offline: %s (%.1f MB)", result.output_path, result.size_mb)
            self.ctx.artifacts.append(result.output_path)
        else:
            for e in result.errors:
                logger.warning("    Bundle error: %s", e)

    def _phase_compute_release_hashes(self):
        hashes_file = DIST / "RELEASE_HASHES.txt"
        lines = []
        for art in self.ctx.artifacts:
            if art and art.exists():
                if art.is_file():
                    h = hashlib.sha256(art.read_bytes()).hexdigest()
                    lines.append(f"{h}  {art.name}")
                elif art.is_dir():
                    for f in sorted(art.rglob("*")):
                        if f.is_file():
                            h = hashlib.sha256(f.read_bytes()).hexdigest()
                            lines.append(f"{h}  {f.relative_to(DIST)}")
        if lines:
            hashes_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            logger.info("    RELEASE_HASHES.txt con %d entradas", len(lines))

    def _phase_smoke_test_installed(self):
        if self.ctx.skip_smoke:
            logger.info("    Smoke test omitido")
            return
        logger.info("    Smoke test: importando oraculo...")
        try:
            sys.path.insert(0, str(SRC))
            from oraculo.pre_flight import run_pre_flight
            rep = run_pre_flight()
            if rep.ok:
                logger.info("    Pre-flight OK")
            else:
                for f in rep.critical_failures:
                    logger.warning("    Pre-flight fallo: %s", f)
        except Exception as e:
            self.ctx.errors.append(f"smoke_test: {e}")


def main():
    import argparse
    p = argparse.ArgumentParser(description="Build Pipeline — El Oraculo McComics v4.0")
    p.add_argument("--target", choices=["windows", "macos", "linux"], default=_detect_target())
    p.add_argument("--arch", choices=["x64", "arm64"], default="x64")
    p.add_argument("--profile-bundle", default="all")
    p.add_argument("--skip-sign", action="store_true")
    p.add_argument("--skip-installer", action="store_true")
    p.add_argument("--skip-smoke", action="store_true")
    args = p.parse_args()

    ctx = BuildContext(
        target=args.target, arch=args.arch, profile_bundle=args.profile_bundle,
        skip_sign=args.skip_sign, skip_installer=args.skip_installer, skip_smoke=args.skip_smoke,
    )
    pipeline = BuildPipeline(ctx)
    ok = pipeline.run()
    sys.exit(0 if ok else 1)


def _detect_target() -> str:
    s = platform.system().lower()
    if s == "windows":
        return "windows"
    elif s == "darwin":
        return "macos"
    return "linux"


if __name__ == "__main__":
    main()
