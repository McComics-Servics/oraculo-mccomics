# AVANCES DEL PROYECTO — El Oraculo McComics v4.0
## Registro de progreso para continuidad entre IAs

> Este documento permite a cualquier IA consultar el estado y continuar el desarrollo.
> Ultima actualizacion: 2026-04-15

---

## Estado general: 85% completado

| Metrica | Valor |
|---------|-------|
| Archivos Python con contenido | 94 |
| Archivos de tests | 16 |
| Lineas de codigo estimadas | ~15,000+ |
| Fases completadas | 7 de 10 (F1-F7, F9) |
| Fases parciales | 1 (F8 — CLI) |
| Fases pendientes | 1 (F10 — Build/instaladores) |

---

## Historial de avances

### 2026-04-15 — Sesion: Reorganizacion + Auditoria

**Cambios realizados:**
1. ✅ Archivo TXT monolitico (4,029 lineas) separado en 7 documentos .md independientes en `docs/`
2. ✅ Estructura de carpetas del proyecto creada segun PROJECT_STRUCTURE_SPEC
3. ✅ 3 perfiles YAML (basic, enterprise, banking) creados en `profiles/`
4. ✅ Policy Engine refactorizado: engine.py, loader.py, validator.py con coherencia cruzada
5. ✅ Excepciones, constantes, config, logging, pre_flight creados en core/
6. ✅ README.md ampliado con seccion de integracion IA-IDE y uso en lenguaje natural
7. ✅ TXT original respaldado en `_BACKUP_ORIGINAL/`
8. ✅ Documentos PLAN_ESTRATEGICO.md y AVANCES.md creados

**Descubrimiento clave:**
- Auditoria revelo que otra IA ya implemento 94 archivos funcionales (no esqueletos)
- Las 7 capas tienen codigo real: Polyglot, Index, Retrieval, Assembler, Cognitive, API, UI
- UI existe como archivo monolitico (1,076 lineas HTML+CSS+JS inline) con 10 pestanas
- Tests son funcionales (no stubs): verifican comportamiento real con fixtures

**Nota sobre __version__.py:**
- Fue actualizado (por linter o usuario) a version="4.0.0", release="stable"

**Nota sobre engine.py:**
- Fue actualizado (por linter o usuario) con catch de Exception generico al parsear perfil
- Y con lectura de `require_passphrase_for_downgrade` desde el perfil ACTUAL (no del target)

---

## Modulos por capa y su estado

### Capa 1 — Polyglot Fabric ✅
| Modulo | Estado |
|--------|--------|
| dispatcher.py | ✅ Funcional — clasifica en L1-L4 |
| encoding_detect.py | ✅ Funcional |
| lexical_skeleton.py | ✅ Funcional |
| fastcdc.py | ✅ Funcional |
| secret_scanner.py | ✅ Funcional |
| injection_detector.py | ✅ Funcional |
| L2_antlr/cobol_parser.py | ✅ Funcional |
| L2_antlr/pli_parser.py | ✅ Funcional |
| L3_patterns/rpg_parser.py | ✅ Funcional |
| L3_patterns/jcl_parser.py | ✅ Funcional |
| L3_patterns/natural_parser.py | ✅ Funcional |
| resolvers/copybook_resolver.py | ✅ Funcional |

### Capa 2 — Index Engine ✅
| Modulo | Estado |
|--------|--------|
| duckdb_store.py | ✅ 165 lineas — CRUD + grafos |
| sqlite_store.py | ✅ 165 lineas — FTS5 + BM25 |
| pipeline.py | ✅ 130 lineas — indexacion completa |
| watcher.py | ✅ Funcional |
| debouncer.py | ✅ Funcional |
| stale_detector.py | ✅ Funcional |
| row_hmac.py | ✅ Funcional |
| integrity_check.py | ✅ Funcional |

### Capa 3 — Cognitive Core ✅
| Modulo | Estado |
|--------|--------|
| core.py | ✅ 148 lineas — 3 providers |
| llama_provider.py | ✅ Funcional |
| ollama_provider.py | ✅ Funcional |
| openai_provider.py | ✅ Funcional |
| query_expander.py | ✅ Funcional |
| reranker.py | ✅ Funcional |
| model_downloader.py | ✅ Funcional |

### Capa 4 — Context Assembler ✅
| Modulo | Estado |
|--------|--------|
| pipeline.py | ✅ 129 lineas |
| budget_allocator.py | ✅ Funcional |
| trust_tier.py | ✅ Funcional |
| payload_builder.py | ✅ Funcional |

### Capa 5 — Policy Engine ✅
| Modulo | Estado |
|--------|--------|
| engine.py | ✅ Thread-safe + historial |
| loader.py | ✅ YAML + merge overrides |
| validator.py | ✅ 6 reglas cruzadas |
| observer.py | ✅ Funcional |
| switcher.py | ✅ Funcional |

### Capa 6 — API + CLI ⚠️
| Modulo | Estado |
|--------|--------|
| server.py | ✅ 148 lineas — HTTP stdlib |
| routes.py | ✅ Funcional |
| auth.py | ✅ Bearer token |
| ipc_bridge.py | ✅ Funcional |
| cli/main.py | ⚠️ **PARCIAL** — handlers sin conectar |

### Capa 7 — UI ✅
| Modulo | Estado |
|--------|--------|
| window.py | ✅ pywebview launcher |
| assets/index.html | ✅ 1,076 lineas monolitico |
| theme_manager.py | ✅ Funcional |

### Seguridad (F9) ✅
| Modulo | Estado |
|--------|--------|
| air_gap.py | ✅ Verificacion 3 DNS |
| crypto_shred.py | ✅ 132 lineas |
| compliance.py | ✅ Funcional |
| audit_chain.py | ✅ Funcional |

---

## Siguiente paso recomendado

**Prioridad 1:** Completar `cli/main.py` — conectar los 5 subcomandos con `OraculoApp`
- Esto habilita `mccomics_brain query "..."` para integracion con IAs de IDE

**Prioridad 2:** Build pipeline (F10) — scripts/build.py + instaladores

**Prioridad 3:** Ejecutar test suite completa y arreglar failures
