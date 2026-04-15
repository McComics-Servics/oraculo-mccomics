# AVANCES — El Oraculo McComics v4.0

**Proposito:** Registro resumido de avances. Cualquier IA puede consultar este documento para continuar el proyecto.

---

## 2026-04-14 — Sesion 1: Estructura + F1

### Logros
- Estructura completa de carpetas creada segun PROJECT_STRUCTURE_SPEC.md
- Archivo original monolitico (4029 lineas) dividido en 7 documentos independientes en `docs/`
- Archivo original respaldado en `_BACKUP_ORIGINAL/`
- 3 perfiles YAML completos creados en `profiles/` (basic, enterprise, banking)
- Policy Engine implementado con:
  - `policy/loader.py` — Carga YAML, merging de overrides
  - `policy/validator.py` — Validacion de estructura + 6 reglas de coherencia cruzada
  - `policy/engine.py` — Motor principal con switching en caliente, history, subscribers
  - `policy/observer.py` — Protocolo observer para notificacion de subsistemas
  - `policy/switcher.py` — Logica de downgrade/upgrade, deteccion de re-cifrado
- Core completo:
  - `core/exceptions.py` — Catalogo de excepciones (10 tipos)
  - `core/constants.py` — Constantes globales, trust tiers, profile ranks
  - `core/config.py` — Carga de runtime config desde env vars
  - `core/logging_setup.py` — Logging con rotacion
  - `core/shutdown.py` — Graceful shutdown con signal handlers
  - `core/degraded_mode.py` — Estado degradado con persistencia
- `pre_flight.py` — Verificaciones de arranque
- `main.py` — Entry point del daemon (arranca, pre_flight, carga perfil)
- `pyproject.toml` + `requirements.txt` + `requirements-dev.txt`
- `tests/conftest.py` + `tests/unit/test_policy_engine.py` (18 tests)
- **18/18 tests pasando** — F1 COMPLETADA

### F2 — Polyglot Fabric (COMPLETADA)
- `polyglot/dispatcher.py` — Router central L1→L2→L3→L4 con mapeo de ~60 extensiones
- `polyglot/encoding_detect.py` — Pipeline de 7 pasos (BOM, charset-normalizer, EBCDIC, UTF-8, latin-1)
- `polyglot/lexical_skeleton.py` — Parser L4 agnostico: chunks por indentacion, extraccion de identificadores, ratio de comentarios, soporte COBOL area A
- `polyglot/fastcdc.py` — Content-Defined Chunking con Gear hash para archivos sin parser
- `polyglot/secret_scanner.py` — Detecta AWS keys, private keys, JWT, tokens de Slack/GitHub
- `polyglot/injection_detector.py` — Detecta patrones de prompt injection (Banking)
- `polyglot/pre_index_checks.py` — Verificaciones pre-indexacion (tamaño, binario, encoding, secretos)
- `polyglot/identifier_expansion.py` — Expansion de glosario McComics en queries
- `tests/unit/test_polyglot.py` (24 tests)
- **42/42 tests pasando (F1+F2)** — F2 COMPLETADA

### F3 — Index Engine (COMPLETADA)
- `index/sqlite_store.py` — Almacen BM25 con SQLite FTS5, WAL, batch insert, busqueda BM25 con snippets
- `index/duckdb_store.py` — Almacen vectorial DuckDB: file_metadata, symbols, call_edges, embeddings
- `index/domain_manager.py` — Gestion de dominios con cifrado independiente, persistencia JSON
- `index/incremental.py` — Indexacion incremental por hash SHA-256
- `index/debouncer.py` — Agrupacion de eventos con Timer thread
- `index/watcher.py` — Monitoreo filesystem con watchdog (60+ extensiones)
- `index/stale_detector.py` — Deteccion de fragmentos obsoletos
- `index/integrity_check.py` — Verificacion SQLite (quick/full) + DuckDB
- `index/row_hmac.py` — HMAC-SHA256 por fila (M9 Banking)
- `index/symbol_table.py` — Tabla de simbolos multi-lenguaje
- `index/call_graph.py` — Grafo de llamadas con deteccion de dispatch dinamico (M14)
- `tests/unit/test_index_engine.py` (27 tests)
- **69/69 tests pasando (F1+F2+F3)** — F3 COMPLETADA

### F4 — Retrieval + RRF + SimHash + Context Assembler + IndexPipeline (COMPLETADA)
- **Correcciones Estructurales (aprobadas)**:
  - Correccion A — IndexPipeline: Creado `index/pipeline.py` como orquestador central que conecta F1-F3
  - Correccion B — Reorden F7/F8: API (F7 nuevo) se construye antes de UI (F8 nuevo)
- `index/pipeline.py` — IndexPipeline orquestador: archivo -> pre_check -> encoding -> dispatch -> parse -> fragment -> store
- `retrieval/bm25.py` — Wrapper BM25 sobre SqliteFtsStore
- `retrieval/vector_search.py` — Busqueda vectorial por similitud coseno sobre DuckDB embeddings
- `retrieval/rrf_fusion.py` — Reciprocal Rank Fusion multi-fuente con pesos configurables
- `retrieval/simhash_dedup.py` — SimHash 64-bit para deduplicacion de fragmentos casi-identicos
- `retrieval/weight_learner.py` — Aprendizaje activo de pesos RRF con feedback binario (thumbs up/down)
- `assembler/trust_tier.py` — Asignacion de trust tiers (canon/high/contextual) segun procedencia
- `assembler/budget_allocator.py` — Distribucion jerarquica de token budget en 7 capas (L0-L6)
- `assembler/payload_builder.py` — Constructor de payload JSON con provenance completa
- `assembler/pipeline.py` — Pipeline completo: query -> BM25 -> fuse -> dedup -> budget -> payload
- `tests/unit/test_retrieval.py` (20 tests)
- `tests/unit/test_assembler.py` (17 tests)
- `tests/unit/test_pipeline.py` (13 tests)
- **119/119 tests pasando (F1+F2+F3+F4)** — F4 COMPLETADA

### F5 — Cognitive Core (COMPLETADA)
- **Arquitectura multi-provider** — El usuario elige su LLM:
  - `cognitive/provider.py` — Protocolo abstracto LLMProvider (interfaz comun)
  - `cognitive/llama_provider.py` — Provider llama.cpp (default, GGUF local)
  - `cognitive/ollama_provider.py` — Provider Ollama (HTTP API local)
  - `cognitive/openai_provider.py` — Provider API OpenAI-compatible (GPT, Claude, Groq, etc.)
- `cognitive/model_registry.py` — Registro de modelos recomendados con auto-deteccion de RAM:
  - Default: **Qwen 2.5 Coder 3B Q4_K_M** (~2.1 GB RAM)
  - Low-end: Qwen 2.5 Coder 1.5B (~1.2 GB RAM)
  - High-end: Qwen 2.5 Coder 7B (~4.5 GB RAM)
  - Alternativo: Phi-3.5 Mini 3.8B
- `cognitive/query_expander.py` — Expansion de queries via LLM (3 variantes complementarias)
- `cognitive/reranker.py` — Reranker LLM con scoring 0-10, combina score original + rerank
- `cognitive/core.py` — Orquestador CognitiveCore: init, generate, expand, rerank, embeddings
- `tests/unit/test_cognitive.py` (35 tests con MockProvider — no requiere modelo real)
- **154/154 tests pasando (F1+F2+F3+F4+F5)** — F5 COMPLETADA

### F6 — Polyglot L2 (ANTLR) + L3 (Patterns) + Copybooks (COMPLETADA)
- `polyglot/L2_antlr/cobol_parser.py` — Parser COBOL: divisiones, secciones, parrafos, PERFORM, CALL, COPY, variables PIC
- `polyglot/L2_antlr/pli_parser.py` — Parser PL/I: procedimientos, DCL, CALL, %INCLUDE
- `polyglot/L3_patterns/rpg_parser.py` — Parser RPG (fixed + free format): subrutinas, BEGSR/ENDSR, EXSR, DCL-PROC, /COPY
- `polyglot/L3_patterns/jcl_parser.py` — Parser JCL: JOB, EXEC steps, DD, PROCs, INCLUDE MEMBER
- `polyglot/L3_patterns/natural_parser.py` — Parser Natural/Adabas: DEFINE DATA, subrutinas, PERFORM, CALLNAT
- `polyglot/resolvers/copybook_resolver.py` — Resolucion de COPY/INCLUDE con indice, paths configurables, multi-lenguaje
- `polyglot/parser_registry.py` — Registro central: 25+ lenguajes mapeados a nivel L1/L2/L3, dispatch a parser concreto
- `tests/unit/test_legacy_parsers.py` (39 tests)
- **193/193 tests pasando (F1+F2+F3+F4+F5+F6)** — F6 COMPLETADA

### F7 — API Local + IPC Bridge + CLI + Cliente Python (COMPLETADA)
- `api/server.py` — Servidor HTTP stdlib con Router, OraculoHandler, SSE events, CORS, auth por token
- `api/routes.py` — 7 rutas registradas: health, status, query, query/stream (SSE), profile, profile/switch, index
- `api/auth.py` — LocalAuthManager con 3 niveles (basic=sin auth, enterprise/banking=token obligatorio), TTL, cleanup, banking reduce TTL a 1h max
- `api/ipc_bridge.py` — IPCBridge para pywebview js_api: health, query, get_profile, switch_profile, get_status, index_paths, get_model_info
- `cli/main.py` — CLI con argparse: subcomandos query, index, profile (show/switch/list), status, serve
- `client/python_client.py` — OraculoClient HTTP con health, status, query->QueryResult, get_profile, switch_profile, index_files
- Fix: directorio `routes/` vacio ocultaba `routes.py` — eliminado el directorio conflictivo
- `tests/unit/test_api.py` (44 tests: Router 6, Auth 10, IPCBridge 7, Routes 7, Server 7, QueryResult 2, Client 5)
- `tests/unit/test_cli.py` (17 tests: parser 2, query 3, index 3, profile 4, status 1, serve 2, misc 2)
- **254/254 tests pasando (F1+F2+F3+F4+F5+F6+F7)** — F7 COMPLETADA

### F8 — UI Completa con pywebview + Glassmorphism (COMPLETADA)
- `ui/window.py` — Lanzador pywebview con IPCBridge js_api, modo headless para testing, constantes de ventana
- `ui/theme_manager.py` — 3 temas por perfil (basic=cyan, enterprise=purple, banking=red), CSS vars generator
- `ui/assets/index.html` — UI completa single-file HTML/CSS/JS:
  - **8 pestanas:** Buscar, Indexar, Estado, Modelo, Simbolos, Config, Log, Acerca de
  - **3 botones perfil:** Basic, Enterprise, Banking con switch en caliente
  - **Glassmorphism:** backdrop-filter blur, glass borders, gradients, mesh background
  - **Marca McComics:** colores #2563EB/#38BDF8/#A855F7, branding completo
  - **Funcionalidad JS:** Query con resultados + feedback, indexacion con progreso, status refresh, model selector, toggle settings, log del sistema
  - **Integrada con pywebview.api:** Todos los metodos del IPCBridge accesibles desde JS
- `tests/unit/test_ui.py` (25 tests: Assets 13, Window 3, ThemeManager 9)
- **279/279 tests pasando (F1+F2+F3+F4+F5+F6+F7+F8)** — F8 COMPLETADA

### F9 — Seguridad Banking: air-gap + crypto-shred + audit chain + compliance (COMPLETADA)
- `security/air_gap.py` — Verificacion de air-gap (3 DNS checks), enforce_air_gap solo para banking, block_outbound_urls
- `crypto/crypto_shred.py` — CryptoShredManager con generacion/destruccion de claves, shred_domain, shred_all, persistencia JSON
- `audit/audit_chain.py` — AuditChain append-only con hash chain SHA-256, verify_chain detecta manipulacion, persistencia JSONL
- `security/compliance.py` — Motor de compliance: 7 reglas Banking (air-gap, audit, crypto-shred, TTL, provider, HMAC, HTTP), 3 reglas Enterprise
- `tests/unit/test_security.py` (33 tests: AirGap 5, CryptoShred 8, AuditChain 10, Compliance 10)
- **312/312 tests pasando (F1-F9)** — F9 COMPLETADA

### F10 — Build Pipeline + Instaladores + Doctor (COMPLETADA)
- `build/doctor.py` — Diagnostico del sistema: Python version, dependencias requeridas/opcionales/LLM, espacio disco, data dir, system info
- `build/bundler.py` — Empaquetado offline: create_bundle (copia src+profiles, genera manifest.json), verify_bundle
- `build/installer.py` — Generador de scripts de instalacion para Windows (.bat), macOS (.sh), Linux (.sh)
- `tests/unit/test_build.py` (24 tests: Doctor 9, Bundler 8, Installer 7)
- **336/336 tests pasando (F1-F10)** — F10 COMPLETADA

## PROYECTO COMPLETO — TODAS LAS 10 FASES TERMINADAS + MEJORAS POST-F10 + INTEGRACION FINAL

### Mejoras Post-F10 (Honestidad + UX + Descarga de Modelos)
- `cognitive/model_downloader.py` — Descargador de modelos GGUF con progreso (%, velocidad, ETA), verificacion, cancelacion, persistencia en ~/.oraculo/models/
- `api/ipc_bridge.py` — 7 nuevos metodos: download_model, list_models, get_compliance, get_training_status, toggle_auto_training, set_data_dir, open_data_folder
- `ui/assets/index.html` — REESCRITURA COMPLETA:
  - **10 pestanas** (antes 8): +Entrenamiento +Compliance
  - **Panel Entrenamiento**: auto-training toggle, ruta visible de datos (~/.oraculo/), estadisticas, re-entrenar, disclaimer honesto
  - **Panel Compliance**: 7 checks Banking en tiempo real (air-gap, audit, crypto-shred, TTL, providers, HMAC, HTTP), disclaimer de auditoria externa
  - **Panel Modelo**: Descarga con progreso + indicador honesto de capacidad ("Bueno para: X | No bueno para: Y")
  - **Licencia visible**: Community (BSL 1.1) | Enterprise | Banking
  - **Disclaimers honestos**: "NO entiende logica de negocio", "requiere auditoria externa"
- `tests/unit/test_model_downloader.py` (25 tests: Downloader 15, DataDirs 3, IPCBridge 7)
- `tests/unit/test_ui.py` — Actualizado para 10 pestanas + 7 tests nuevos
- **367/367 tests pasando** — Mejoras completadas

### Integracion Final (cierre del proyecto)
- `src/oraculo/app.py` — **Integrador principal OraculoApp**: conecta las 7 capas en un flujo de arranque unificado:
  - Config -> PreFlight -> PolicyEngine -> Stores (SQLite+DuckDB) -> IndexPipeline -> Assembler -> Cognitive -> AuditChain -> Server/UI
  - 3 modos: `ui` (pywebview), `server` (HTTP daemon), `headless` (testing/integracion)
  - Apagado limpio (graceful shutdown) con signal handlers
  - Auto-deteccion de modelo GGUF en ~/.oraculo/models/ con fallback a Ollama
  - Generacion automatica de auth token para perfiles enterprise/banking
- `src/oraculo/main.py` — Actualizado para usar OraculoApp como entry point
- `src/oraculo/__version__.py` — Version actualizada a `4.0.0` stable
- `LICENSE` — Migrado de AGPL-3.0 a **BSL 1.1** (Business Source License) — impide copia como servicio, se convierte en Apache 2.0 en 2030
- `tests/integration/test_e2e.py` — **15 tests de integracion end-to-end**:
  - Arranque headless completo
  - Switch de perfil (basic -> enterprise)
  - Indexacion de archivo individual y batch (5 archivos)
  - Query tras indexacion
  - Apertura y cierre de stores
  - Degradacion graceful del Cognitive Core
  - AuditChain activa para enterprise, ausente para basic
  - IPCBridge completo (health, profile, training, models, compliance)
  - Flujo completo end-to-end: arrancar -> indexar -> query -> switch
  - Servidor HTTP start/stop con request real GET /health
  - Compliance check via bridge para perfil banking
- **382/382 tests pasando** (367 unit + 15 integration) — 15 suites

### Resumen Final Actualizado
| Fase | Modulos | Tests | Descripcion |
|------|---------|-------|-------------|
| F1 | 11 | 18 | Policy Engine + Core |
| F2 | 8 | 24 | Polyglot Fabric L1+L4 |
| F3 | 11 | 27 | Index Engine (DuckDB + SQLite FTS5) |
| F4 | 10 | 50 | Retrieval RRF + Assembler + IndexPipeline |
| F5 | 7 | 35 | Cognitive Core multi-provider |
| F6 | 7 | 39 | Legacy Parsers (COBOL/PL-I/RPG/JCL/Natural) |
| F7 | 6 | 61 | API HTTP + IPC Bridge + CLI + Client |
| F8 | 3 | 25 | UI pywebview Glassmorphism |
| F9 | 4 | 33 | Seguridad Banking (air-gap/crypto-shred/audit/compliance) |
| F10 | 3 | 24 | Build Pipeline + Doctor + Installer |
| Post | 2 | 31 | Model Downloader + mejoras UI |
| **Integracion** | **1** | **15** | **OraculoApp + e2e tests** |
| **Total** | **~72** | **382** | **Proyecto 100% cerrado** |

### Archivos con Codigo Funcional
Total: ~67 archivos Python con codigo real  
Total tests: 382 (15 suites — 14 unit + 1 integration)  
Total lineas src estimadas: ~6500

### Estructura Final
```
oraculo-mccomics/
├── LICENSE                    (BSL 1.1)
├── PLAN_ESTRATEGICO.md
├── AVANCES.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── _BACKUP_ORIGINAL/          (TXT original)
├── docs/                       (7 documentos de LEY)
├── profiles/                   (3 YAML completos: basic, enterprise, banking)
├── src/oraculo/
│   ├── app.py                 (INTEGRADOR PRINCIPAL — OraculoApp)
│   ├── main.py                (Entry point)
│   ├── pre_flight.py          (Verificaciones de arranque)
│   ├── __version__.py         (4.0.0 stable)
│   ├── core/                  (config, constants, exceptions, logging, shutdown, degraded)
│   ├── policy/                (engine, loader, validator, observer, switcher)
│   ├── polyglot/              (dispatcher, encoding, skeleton, fastcdc, secrets, injection, L2_antlr/, L3_patterns/, resolvers/, parser_registry)
│   ├── index/                 (sqlite_store, duckdb_store, pipeline, incremental, watcher, debouncer, stale_detector, integrity, row_hmac, symbol_table, call_graph, domain_manager)
│   ├── retrieval/             (bm25, vector_search, rrf_fusion, simhash_dedup, weight_learner)
│   ├── assembler/             (pipeline, trust_tier, budget_allocator, payload_builder)
│   ├── cognitive/             (core, provider, llama_provider, ollama_provider, openai_provider, model_registry, query_expander, reranker, model_downloader)
│   ├── api/                   (server, routes, auth, ipc_bridge)
│   ├── cli/                   (main — 5 subcomandos)
│   ├── client/                (python_client — OraculoClient)
│   ├── ui/                    (window, theme_manager, assets/index.html)
│   ├── security/              (air_gap, compliance)
│   ├── crypto/                (crypto_shred)
│   ├── audit/                 (audit_chain)
│   └── build/                 (doctor, bundler, installer)
└── tests/
    ├── unit/                  (14 suites, 367 tests)
    └── integration/           (1 suite, 15 tests e2e)
```
