📜 DOCUMENTO 6/6 — PROJECT_STRUCTURE_SPEC.md

Clasificación: LEY — Estructura del Proyecto
Versión: 1.0
Propietario: McComics Servicios Generales
Fecha: 2026-04-14


1. Propósito
Define la estructura física del repositorio, los módulos Python, las dependencias con hashes verificables, el pipeline de build, los instaladores multi-plataforma y las convenciones de código McComics aplicables.

2. Estructura raíz del repositorio
oraculo-mccomics/
├── README.md
├── LICENSE                          # Propietario McComics
├── pyproject.toml                   # config principal
├── requirements.txt                 # con hashes SHA256
├── requirements-dev.txt
├── requirements-build.txt
├── .python-version                  # 3.11.7 fijo
├── .gitignore
├── .gitattributes
├── CHANGELOG.md
├── SECURITY.md
│
├── src/
│   └── oraculo/                     # paquete principal
│       ├── __init__.py
│       ├── __version__.py
│       ├── main.py                  # entry point del daemon
│       ├── pre_flight.py            # checks de arranque
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py            # carga de config
│       │   ├── logging_setup.py
│       │   ├── shutdown.py          # graceful shutdown
│       │   ├── degraded_mode.py
│       │   ├── exceptions.py
│       │   └── constants.py
│       │
│       ├── policy/                  # Policy Engine
│       │   ├── __init__.py
│       │   ├── engine.py
│       │   ├── loader.py
│       │   ├── validator.py
│       │   ├── switcher.py
│       │   └── observer.py
│       │
│       ├── crypto/
│       │   ├── __init__.py
│       │   ├── master_key.py        # DPAPI/Keychain/libsecret
│       │   ├── kdf.py               # Argon2id
│       │   ├── aes_gcm.py
│       │   ├── hmac_chain.py
│       │   ├── crypto_shred.py
│       │   ├── secure_memory.py     # mlock/VirtualLock
│       │   └── fingerprint.py       # hardware factors
│       │
│       ├── transport/
│       │   ├── __init__.py
│       │   ├── ipc_pipe.py          # Windows named pipe
│       │   ├── ipc_socket.py        # Unix domain socket
│       │   ├── http_loopback.py     # FastAPI app
│       │   ├── frame_protocol.py    # ORCL frame
│       │   └── auth_middleware.py
│       │
│       ├── api/                     # endpoints
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── health.py
│       │   │   ├── query.py
│       │   │   ├── index.py
│       │   │   ├── profile.py
│       │   │   ├── audit.py
│       │   │   ├── llm.py
│       │   │   ├── glossary.py
│       │   │   ├── feedback.py
│       │   │   ├── golden.py
│       │   │   └── tokens.py
│       │   ├── schemas/             # pydantic models
│       │   ├── errors.py
│       │   └── rate_limit.py
│       │
│       ├── polyglot/                # Polyglot Fabric
│       │   ├── __init__.py
│       │   ├── dispatcher.py
│       │   ├── encoding_detect.py
│       │   ├── pre_index_checks.py
│       │   ├── secret_scanner.py
│       │   ├── injection_detector.py
│       │   ├── identifier_expansion.py
│       │   ├── fastcdc.py
│       │   ├── lexical_skeleton.py
│       │   │
│       │   ├── L1_treesitter/
│       │   │   ├── __init__.py
│       │   │   ├── builder.py       # compila bindings
│       │   │   ├── parser.py
│       │   │   └── languages.yaml
│       │   │
│       │   ├── L2_antlr/
│       │   │   ├── __init__.py
│       │   │   ├── runtime.py
│       │   │   ├── grammars/
│       │   │   │   ├── Cobol.g4
│       │   │   │   ├── Pli.g4
│       │   │   │   ├── Fortran.g4
│       │   │   │   ├── Ada.g4
│       │   │   │   └── Pascal.g4
│       │   │   ├── cobol_preproc.py
│       │   │   └── pli_preproc.py
│       │   │
│       │   ├── L3_patterns/
│       │   │   ├── __init__.py
│       │   │   ├── runner.py
│       │   │   └── patterns/
│       │   │       ├── rpg.yaml
│       │   │       ├── natural.yaml
│       │   │       ├── jcl.yaml
│       │   │       ├── clist.yaml
│       │   │       ├── rexx.yaml
│       │   │       ├── mumps.yaml
│       │   │       ├── clipper.yaml
│       │   │       ├── foxpro.yaml
│       │   │       └── asm_ibm.yaml
│       │   │
│       │   ├── resolvers/           # includes/imports
│       │   │   ├── __init__.py
│       │   │   ├── base.py
│       │   │   ├── cobol_copybook.py
│       │   │   ├── c_include.py
│       │   │   ├── python_module.py
│       │   │   ├── ruby_require.py
│       │   │   ├── java_classpath.py
│       │   │   └── rpg_copy.py
│       │   │
│       │   └── plugin_sdk/
│       │       ├── __init__.py
│       │       ├── interface.py
│       │       ├── loader.py
│       │       └── sandbox.py       # solo Banking
│       │
│       ├── index/                   # Index Engine
│       │   ├── __init__.py
│       │   ├── duckdb_store.py
│       │   ├── sqlite_store.py
│       │   ├── hnsw_index.py
│       │   ├── call_graph.py
│       │   ├── symbol_table.py
│       │   ├── domain_manager.py
│       │   ├── incremental.py
│       │   ├── debouncer.py
│       │   ├── watcher.py           # watchdog
│       │   ├── integrity_check.py
│       │   ├── row_hmac.py
│       │   └── stale_detector.py
│       │
│       ├── retrieval/
│       │   ├── __init__.py
│       │   ├── bm25.py
│       │   ├── vector_search.py
│       │   ├── ast_similar.py       # APTED
│       │   ├── lexical_exact.py
│       │   ├── call_graph_search.py
│       │   ├── rrf_fusion.py
│       │   ├── simhash_dedup.py
│       │   └── weight_learner.py
│       │
│       ├── assembler/               # Context Assembler
│       │   ├── __init__.py
│       │   ├── pipeline.py
│       │   ├── budget_allocator.py
│       │   ├── trust_tier.py
│       │   ├── window_centering.py
│       │   ├── payload_builder.py
│       │   ├── markdown_formatter.py
│       │   └── stream_emitter.py
│       │
│       ├── cognitive/               # LLM local
│       │   ├── __init__.py
│       │   ├── llm_loader.py
│       │   ├── llama_runner.py
│       │   ├── model_manifest.py
│       │   ├── query_expansion.py
│       │   ├── reranker.py
│       │   ├── summarizer.py
│       │   └── intent_classifier.py
│       │
│       ├── cache/
│       │   ├── __init__.py
│       │   ├── semantic_cache.py
│       │   └── embedding_cache.py
│       │
│       ├── audit/
│       │   ├── __init__.py
│       │   ├── append_only_log.py
│       │   ├── hash_chain.py
│       │   ├── daily_seal.py
│       │   ├── compliance_export.py
│       │   └── verifier.py
│       │
│       ├── security/
│       │   ├── __init__.py
│       │   ├── token_manager.py
│       │   ├── nonce_store.py
│       │   ├── anomaly_detector.py
│       │   ├── rate_limiter.py
│       │   ├── air_gap_verify.py
│       │   ├── circuit_breaker.py
│       │   └── log_sanitizer.py
│       │
│       ├── jobs/
│       │   ├── __init__.py
│       │   ├── job_runner.py
│       │   ├── scan_job.py
│       │   ├── reencrypt_job.py
│       │   ├── reembed_job.py
│       │   └── verify_job.py
│       │
│       ├── golden_tests/
│       │   ├── __init__.py
│       │   ├── runner.py
│       │   ├── capture.py
│       │   └── regression_check.py
│       │
│       ├── feedback/
│       │   ├── __init__.py
│       │   └── store.py
│       │
│       ├── client/                  # cliente Python oficial
│       │   ├── __init__.py
│       │   ├── client.py
│       │   ├── transport_auto.py
│       │   └── exceptions.py
│       │
│       └── cli/
│           ├── __init__.py
│           ├── mccomics_brain.py    # CLI principal
│           └── commands/
│               ├── query.py
│               ├── index.py
│               ├── profile.py
│               ├── audit.py
│               └── doctor.py
│
├── ui/                              # frontend pywebview
│   ├── package.json                 # solo para build
│   ├── tailwind.config.js
│   ├── vite.config.js
│   ├── src/
│   │   ├── index.html
│   │   ├── main.js
│   │   ├── styles/
│   │   │   ├── tailwind.css
│   │   │   ├── glassmorphism.css
│   │   │   └── mccomics_theme.css
│   │   ├── components/
│   │   │   ├── Tabs.js
│   │   │   ├── ProfileSwitcher.js
│   │   │   ├── QueryExplorer.js
│   │   │   ├── IndexManager.js
│   │   │   ├── SecurityCenter.js
│   │   │   ├── Cognitive.js
│   │   │   ├── AuditLog.js
│   │   │   ├── Dependencies.js
│   │   │   └── Dashboard.js
│   │   └── lib/
│   │       ├── api_client.js
│   │       └── ipc_native.js        # bridge a pywebview js_api
│   ├── public/
│   │   └── icons/
│   └── dist/                        # generado, incluido en el build
│
├── profiles/                        # YAMLs de perfil firmados
│   ├── basic.yaml
│   ├── basic.yaml.sig
│   ├── enterprise.yaml
│   ├── enterprise.yaml.sig
│   ├── banking.yaml
│   └── banking.yaml.sig
│
├── schemas/                         # JSON schemas
│   └── v1/
│       ├── query_request.json
│       ├── query_response.json
│       ├── health_response.json
│       └── ...
│
├── manifests/
│   ├── models.yaml                  # modelos LLM aprobados
│   ├── models.yaml.sig
│   ├── plugins.yaml                 # plugins firmados (Banking)
│   └── plugins.yaml.sig
│
├── tests/
│   ├── unit/
│   │   ├── test_policy_engine.py
│   │   ├── test_polyglot_dispatcher.py
│   │   ├── test_lexical_skeleton.py
│   │   ├── test_cobol_preproc.py
│   │   ├── test_encoding_detect.py
│   │   ├── test_fastcdc.py
│   │   ├── test_simhash_dedup.py
│   │   ├── test_rrf_fusion.py
│   │   ├── test_budget_allocator.py
│   │   ├── test_trust_tier.py
│   │   ├── test_crypto_master_key.py
│   │   ├── test_hmac_chain.py
│   │   ├── test_token_manager.py
│   │   ├── test_anomaly_detector.py
│   │   └── test_air_gap_verify.py
│   │
│   ├── integration/
│   │   ├── test_full_query_pipeline.py
│   │   ├── test_profile_switch.py
│   │   ├── test_index_then_query.py
│   │   ├── test_audit_chain.py
│   │   └── test_streaming_sse.py
│   │
│   ├── e2e/
│   │   ├── test_install_to_first_query.py
│   │   ├── test_basic_profile_lifecycle.py
│   │   ├── test_enterprise_profile_lifecycle.py
│   │   └── test_banking_profile_lifecycle.py
│   │
│   ├── fixtures/
│   │   ├── code_samples/
│   │   │   ├── python/
│   │   │   ├── ruby/
│   │   │   ├── cobol/               # incluye EBCDIC
│   │   │   ├── rpg/
│   │   │   ├── jcl/
│   │   │   └── unknown_lang/
│   │   └── golden/
│   │       └── golden_queries.yaml
│   │
│   └── conftest.py
│
├── scripts/
│   ├── build.py                     # pipeline de build
│   ├── sign_profiles.py             # firma YAMLs
│   ├── sign_manifests.py
│   ├── verify_install.py
│   ├── doctor.py                    # standalone doctor
│   ├── generate_root_token.py
│   └── benchmark.py
│
├── installers/
│   ├── windows/
│   │   ├── nsis_installer.nsi
│   │   ├── webview2_bootstrap.exe
│   │   └── icon.ico
│   ├── macos/
│   │   ├── pkg_build.sh
│   │   ├── notarize.sh
│   │   └── icon.icns
│   ├── linux/
│   │   ├── appimage_build.sh
│   │   ├── deb_build.sh
│   │   ├── rpm_build.sh
│   │   └── icon.png
│   └── offline_bundle/
│       └── build_bundle.py
│
├── docs/
│   ├── THREAT_MODEL_ORACULO_v4.md
│   ├── POLICY_ENGINE_SPEC.md
│   ├── POLYGLOT_FABRIC_SPEC.md
│   ├── CONTEXT_ASSEMBLY_POLICY.md
│   ├── API_CONTRACT_SPEC.md
│   ├── PROJECT_STRUCTURE_SPEC.md   # este documento
│   ├── ARCHITECTURE_OVERVIEW.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── COMPLIANCE_GUIDE.md
│   └── api/
│       └── openapi.yaml             # generado automáticamente
│
└── .github/
    └── workflows/
        ├── tests.yml
        ├── build_release.yml
        └── security_scan.yml

3. pyproject.toml
toml[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "oraculo-mccomics"
version = "4.0.0"
description = "IA local universal con 3 niveles de seguridad — McComics®"
authors = [{name = "McComics Servicios Generales", email = "mccomicsservics@gmail.com"}]
license = {text = "Proprietary"}
requires-python = ">=3.11,<3.13"
readme = "README.md"
keywords = ["ai", "local", "code-search", "rag", "cobol", "security"]

[project.scripts]
oraculo = "oraculo.main:main"
mccomics_brain = "oraculo.cli.mccomics_brain:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
oraculo = [
    "../profiles/*.yaml",
    "../profiles/*.sig",
    "../schemas/v1/*.json",
    "../manifests/*.yaml",
    "../manifests/*.sig",
    "polyglot/L2_antlr/grammars/*.g4",
    "polyglot/L3_patterns/patterns/*.yaml",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit",
    "integration",
    "e2e",
    "slow",
    "requires_llm",
]

[tool.ruff]
line-length = 100
target-version = "py311"

4. requirements.txt con hashes
# === NÚCLEO ===
fastapi==0.111.0 --hash=sha256:abc...
uvicorn[standard]==0.30.1 --hash=sha256:def...
pydantic==2.7.1 --hash=sha256:...
pyyaml==6.0.1 --hash=sha256:...
jsonschema==4.22.0 --hash=sha256:...

# === ALMACENAMIENTO ===
duckdb==0.10.1 --hash=sha256:...
# sqlite3 viene con Python

# === PARSING ===
tree-sitter==0.21.3 --hash=sha256:...
tree-sitter-languages==1.10.2 --hash=sha256:...
antlr4-python3-runtime==4.13.1 --hash=sha256:...

# === EMBEDDINGS ===
onnxruntime==1.17.3 --hash=sha256:...
tokenizers==0.19.1 --hash=sha256:...
numpy==1.26.4 --hash=sha256:...

# === LLM LOCAL ===
llama-cpp-python==0.2.77 --hash=sha256:...

# === ENCODING ===
charset-normalizer==3.3.2 --hash=sha256:...

# === CRIPTO ===
cryptography==42.0.7 --hash=sha256:...
argon2-cffi==23.1.0 --hash=sha256:...

# === KEYRING NATIVO ===
keyring==25.2.1 --hash=sha256:...
pywin32==306 --hash=sha256:... ; sys_platform == "win32"
secretstorage==3.3.3 --hash=sha256:... ; sys_platform == "linux"

# === UI ===
pywebview==5.1 --hash=sha256:...

# === FILESYSTEM ===
watchdog==4.0.1 --hash=sha256:...

# === CLI ===
typer==0.12.3 --hash=sha256:...
rich==13.7.1 --hash=sha256:...

# === LOGGING ===
structlog==24.1.0 --hash=sha256:...

# === MEMORY LOCKING ===
# usa ctypes / win32api del stdlib
Instalación obligatoria con verificación:
powershellpwsh -Command "pip install --require-hashes -r requirements.txt"

5. Estructura de db_storage/ en runtime
db_storage/                          # creado al primer arranque
├── build_meta.json                  # versión Python, hashes bindings
├── active_port.txt                  # puerto HTTP activo (chmod 600)
├── root_token.enc                   # token raíz cifrado
├── fingerprint.json                 # factores de hardware
│
├── domains/
│   ├── code/
│   │   ├── duckdb.db                # vector + estructura
│   │   ├── duckdb.db.wal
│   │   ├── sqlite_fts.db            # BM25
│   │   ├── sqlite_fts.db-wal
│   │   ├── domain_meta.json
│   │   └── encryption.key.enc
│   ├── docs/
│   └── ...
│
├── profiles/
│   ├── active.txt                   # nombre del perfil activo
│   ├── history.jsonl
│   └── custom_*.yaml                # overrides Basic/Enterprise
│
├── audit/
│   ├── audit.log.jsonl              # append-only
│   ├── chain_state.json             # último HMAC
│   ├── seals/
│   │   └── 2026-04-13.seal
│   └── exports/
│
├── cache/
│   ├── semantic_queries.lru
│   └── embeddings.lru
│
├── golden/
│   ├── golden_queries.yaml
│   └── baselines.json
│
├── feedback/
│   └── feedback.jsonl
│
├── llm_models/
│   ├── qwen2.5-1.5b-instruct-q5.gguf
│   ├── qwen2.5-1.5b-instruct-q5.gguf.sha256
│   └── active.txt
│
├── glossary.yaml
├── encoding_overrides.yaml
├── parser_overrides.yaml
├── parse_warnings.log               # rotado
├── oraculo.log                      # rotado
└── degraded_state.json              # si en modo degradado

6. Convenciones de código McComics
6.1 Estilo Python

Python 3.11+ (sin from __future__ import annotations necesario para tipos PEP 604)
ruff como linter único
Type hints obligatorios en funciones públicas
Docstrings en español para funciones de negocio, inglés para utilidades técnicas
Líneas máx 100 caracteres
Sin emojis en el código
Comentarios explican por qué, no qué

6.2 Nomenclatura

Módulos: snake_case.py
Clases: PascalCase
Funciones/variables: snake_case
Constantes: SCREAMING_SNAKE_CASE
Privado: prefijo _
Protegido: sin prefijo, documentado

6.3 Estructura de un módulo
python"""
Módulo: oraculo.policy.engine
Propósito: Carga y conmutación de perfiles de seguridad.
Documento de LEY: POLICY_ENGINE_SPEC.md
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

# Imports stdlib primero
# Imports terceros
# Imports propios

__all__ = ["PolicyEngine", "ProfileSwitchResult"]

logger = logging.getLogger(__name__)


@dataclass
class ProfileSwitchResult:
    """Resultado de un cambio de perfil."""
    success: bool
    previous: str | None
    current: str
    reencryption_eta_seconds: int = 0
    error_code: str | None = None


class PolicyEngine:
    """Motor de políticas de seguridad. Singleton por daemon."""
    
    def __init__(self, profiles_dir: Path):
        self._profiles_dir = profiles_dir
        self._current = None
        # ...
6.4 Manejo de errores

Excepciones específicas en oraculo.core.exceptions
Nunca except: pass
Siempre loguear con logger.exception() (incluye traceback)
Errores que llegan al API → traducidos a códigos del catálogo

6.5 Tests

Cada módulo oraculo/foo/bar.py tiene tests/unit/foo/test_bar.py
Cobertura objetivo: 80% líneas, 90% en módulos críticos (crypto, policy, audit)
Fixtures en tests/fixtures/
Tests deterministas (sin tiempo real, sin red)


7. Pipeline de build (scripts/build.py)
python"""
Pipeline de build del Oráculo McComics v4.0
Uso: python scripts/build.py --target windows --profile-bundle all
"""

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

TARGETS = ["windows", "macos", "linux"]
ARCHITECTURES = ["x64", "arm64"]
7.1 Fase por fase
FaseDetalle1. validate_environmentPython 3.11.7, herramientas de cada OS2. verify_dependency_hashespip install --require-hashes en venv limpio3. compile_treesitter_bindingstree_sitter_languages.build_library() con todas las gramáticas4. build_ui_distcd ui && npm ci && npm run build → ui/dist/5. sign_profilesFirma cada profiles/*.yaml con clave privada McComics6. sign_manifestsFirma manifests/models.yaml, manifests/plugins.yaml7. package_python_with_pyinstallerpyinstaller oraculo.spec --noconfirm8. embed_resourcesCopia profiles/, schemas/, manifests/, ui/dist/ al bundle9. code_sign_binaryAuthenticode (Windows) / codesign + notarize (macOS)10. build_installerNSIS / pkg / AppImage / deb / rpm11. generate_offline_bundleZip con instalador + modelos LLM + manifest firmado12. compute_release_hashesSHA256 de cada artefacto, RELEASE_HASHES.txt firmado13. smoke_test_installedVM limpia: instala, arranca, query simple, profile switch
7.2 Spec de PyInstaller
python# oraculo.spec
block_cipher = None

a = Analysis(
    ['src/oraculo/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('profiles', 'profiles'),
        ('schemas', 'schemas'),
        ('manifests', 'manifests'),
        ('ui/dist', 'ui/dist'),
        ('src/oraculo/polyglot/L2_antlr/grammars', 'oraculo/polyglot/L2_antlr/grammars'),
        ('src/oraculo/polyglot/L3_patterns/patterns', 'oraculo/polyglot/L3_patterns/patterns'),
    ],
    hiddenimports=[
        'oraculo.api.routes.health',
        'oraculo.api.routes.query',
        # ... todos los routes
        'tree_sitter_languages',
        'llama_cpp',
        'onnxruntime',
    ],
    hookspath=[],
    runtime_hooks=['scripts/runtime_hook.py'],
    excludes=['tkinter', 'matplotlib', 'pytest'],
    win_no_prefer_redirects=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='oraculo',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI mode
    icon='installers/windows/icon.ico',
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=False,
    name='oraculo',
)

8. Instaladores
8.1 Windows (NSIS)
installers/windows/nsis_installer.nsi (resumen):
nsis!define APP_NAME "Oraculo McComics"
!define APP_VERSION "4.0.0"
!define INSTALL_DIR "$LOCALAPPDATA\McComics\Oraculo"

Section "Oraculo (requerido)"
  SetOutPath "${INSTALL_DIR}"
  File /r "dist\oraculo\*"
  
  ; Verificar WebView2
  Call CheckWebView2
  
  ; Crear accesos directos
  CreateShortcut "$DESKTOP\Oraculo McComics.lnk" "${INSTALL_DIR}\oraculo.exe"
  CreateDirectory "$SMPROGRAMS\McComics"
  CreateShortcut "$SMPROGRAMS\McComics\Oraculo.lnk" "${INSTALL_DIR}\oraculo.exe"
  
  ; Mostrar selector de perfil inicial
  Exec "${INSTALL_DIR}\oraculo.exe --first-run"
SectionEnd

Function CheckWebView2
  ReadRegStr $0 HKLM "SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}" "pv"
  ${If} $0 == ""
    MessageBox MB_YESNO "WebView2 Runtime no encontrado. ¿Instalar ahora?" IDYES install_wv2
    Goto skip_wv2
    install_wv2:
      File "webview2_bootstrap.exe"
      ExecWait "$INSTDIR\webview2_bootstrap.exe /silent /install"
    skip_wv2:
  ${EndIf}
FunctionEnd
8.2 macOS (.pkg + notarización)
bash#!/bin/bash
# installers/macos/pkg_build.sh
pkgbuild \
  --root dist/oraculo.app \
  --identifier com.mccomics.oraculo \
  --version 4.0.0 \
  --install-location /Applications \
  --sign "Developer ID Installer: McComics" \
  Oraculo-4.0.0.pkg

xcrun notarytool submit Oraculo-4.0.0.pkg \
  --apple-id "$APPLE_ID" --team-id "$TEAM_ID" --wait
xcrun stapler staple Oraculo-4.0.0.pkg
8.3 Linux (AppImage + .deb + .rpm)
AppImage para máxima portabilidad. .deb y .rpm para integración con paquetes nativos.
8.4 Bundle offline (Banking)
python# installers/offline_bundle/build_bundle.py
"""
Genera oraculo-v4-offline-bundle-banking.zip:
- Instalador del OS objetivo
- requirements/*.whl pre-descargados
- modelos LLM aprobados (qwen 1.5b signed, phi-3-mini signed)
- profiles/*.yaml.sig
- manifests/*.yaml.sig
- README_OFFLINE_INSTALL.md
- VERIFY_HASHES.sh / .ps1
- public_key.pem para verificar firmas
"""

9. Plan de fases con criterios de éxito
FaseEntregableCriterio de éxitoF1Esqueleto del repo + Policy Engine + 3 perfiles + tests unitpytest tests/unit/test_policy_engine.py pasa 100%F2Polyglot L1 + L4 + encoding detect + pre-checksIndexa fixtures Python/Ruby/COBOL/unknown sin erroresF3Index Engine + crypto por dominio + WAL + watcher + debouncerIndexa proyecto real de 1k archivos en <30sF4Retrieval (BM25 + HNSW + AST + lexical + call_graph) + RRF + SimHash + Context AssemblerQuery devuelve top-10 con trust tiers correctosF5Cognitive Core (llama.cpp + Qwen 1.5b) + query expansion + rerankerRe-ranking mejora precisión >10% en golden testsF6Polyglot L2 (ANTLR COBOL/PL/I) + L3 (RPG/JCL/Natural) + copybook resolverIndexa fixtures legacy con metadata correctaF7UI completa 8 pestañas + 3 botones perfil + glassmorphismSwitch de perfil completo en <2s desde UIF8API completa (IPC + HTTP + streaming SSE) + cliente Python + CLITest e2e pasa: install → query → profile_switch → auditF9Seguridad Banking: air-gap verify + crypto-shred + audit chain + compliance exportTest e2e Banking pasa todos los checksF10Build pipeline + instaladores Win/Mac/Linux + offline bundle + doctorSmoke test en VM limpia pasa

10. CI/CD
10.1 GitHub Actions: tests.yml
yamlname: Tests
on: [push, pull_request]

jobs:
  test:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python: ["3.11"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - run: pip install --require-hashes -r requirements.txt
      - run: pip install --require-hashes -r requirements-dev.txt
      - run: pytest tests/unit -v --cov=oraculo
      - run: pytest tests/integration -v
10.2 Security scan
yaml- run: pip-audit --require-hashes -r requirements.txt
- run: bandit -r src/oraculo
- run: ruff check src/

11. Variables de entorno respetadas
VariablePropósitoORACULO_DATA_DIRSobrescribe ubicación de db_storage/ORACULO_PROFILEPerfil inicial (basic/enterprise/banking)ORACULO_LOG_LEVELdebug/info/warning/errorORACULO_PORTPuerto HTTP fijo (rango 1024-65535)ORACULO_NO_HTTPSi 1, deshabilita HTTP loopbackORACULO_LLM_MODELID de modelo LLM a cargarORACULO_DEGRADED_OKSi 1, arranca aunque pre_flight tenga fallos no-críticos

12. Reglas de inmutabilidad del repo

docs/*.md clasificados como LEY → solo modificables vía PR aprobado por McComics
profiles/*.yaml → modificables solo en su versión, nunca en perfil base
schemas/v1/*.json → inmutables; cambios van a /v2/
manifests/*.yaml.sig → regenerados automáticamente por build, nunca a mano


13. Tamaños objetivo
ComponenteTamañoBinario PyInstaller (sin modelos)~140 MBBundle Basic (con Qwen 0.5B)~520 MBBundle Enterprise (con Qwen 1.5B)~1.1 GBBundle Banking (con Qwen 1.5B + Phi-3-mini signed)~3.4 GBRAM en uso normal (Enterprise)~750 MBTamaño del índice (proyecto 5k archivos)~120 MB

14. Tests obligatorios de la estructura del proyecto
✓ pyproject.toml válido
✓ requirements.txt con hashes verificables
✓ Todos los módulos tienen __init__.py
✓ Todos los módulos críticos tienen tests
✓ Build pipeline ejecuta sin errores en CI
✓ PyInstaller spec produce binario funcional
✓ Instalador NSIS genera .exe instalable
✓ Instalador .pkg notarizado
✓ AppImage portable funciona en distros base
✓ Offline bundle se verifica con hashes
✓ Smoke test post-install pasa
✓ Doctor reporta estado correcto en VM limpia

15. Resumen ejecutivo
La estructura del proyecto está diseñada para ser navegable, auditable y construible por cualquier ingeniero senior sin contexto previo. Cada documento de LEY tiene su contraparte en código (policy/ ↔ POLICY_ENGINE_SPEC.md, etc.). El pipeline de build es completamente reproducible con hashes verificables. Los instaladores cubren los 3 sistemas operativos principales con experiencias nativas. El bundle offline para Banking permite deployment air-gapped real.

