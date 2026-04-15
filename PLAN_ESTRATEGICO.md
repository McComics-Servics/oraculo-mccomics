# PLAN ESTRATEGICO — El Oraculo McComics v4.0

**Clasificacion:** Documento operativo  
**Proposito:** Guiar la ejecucion completa del proyecto desde F1 hasta F10.  
**Ultima actualizacion:** 2026-04-14 (cierre final)

---

## Correcciones Estructurales (aprobadas 2026-04-14)

### Correccion A — IndexPipeline
**Problema:** F1-F3 crearon piezas sueltas (dispatcher, pre_check, encoding, skeleton, stores) sin un orquestador que las conecte.
**Solucion:** Crear `index/pipeline.py` en F4 como "pegamento" central: archivo -> pre_check -> encoding -> parse -> fragment -> store.

### Correccion B — Reorden F7 y F8
**Problema:** La UI (F7) depende del bridge pywebview js_api, pero la API (F8) se construiria despues. La UI no tendria backend.
**Solucion:** Invertir orden: F8 (API) se construye ANTES de F7 (UI). Asi la UI tiene backend real desde el inicio.

---

## Fases de Ejecucion

| Fase    | Descripcion                                                              | Complejidad | Criterio de Exito                                     |
| ------- | ------------------------------------------------------------------------ | ----------- | ----------------------------------------------------- |
| **F1**  | Estructura + esqueletos + Policy Engine + 3 perfiles + tests             | Alta        | pytest tests/unit/test_policy_engine.py pasa 100%     |
| **F2**  | Polyglot Fabric L1 (tree-sitter) + L4 (lexical skeleton)                 | Alta        | Indexa fixtures Python/Ruby/COBOL/unknown sin errores |
| **F3**  | Index Engine (DuckDB + SQLite FTS5) + cifrado + WAL + watcher            | Alta        | Indexa 1k archivos en <30s                            |
| **F4**  | Retrieval + RRF + SimHash + Assembler + **IndexPipeline**                | Alta        | Query top-10 con trust tiers correctos                |
| **F5**  | Cognitive Core (llama.cpp + Qwen 1.5b) + query expansion + reranker      | Media       | Re-ranking mejora precision >10% en golden tests      |
| **F6**  | Polyglot L2 (ANTLR COBOL/PL/I) + L3 (RPG/JCL/Natural) + copybooks        | Media-Alta  | Indexa fixtures legacy con metadata correcta          |
| **F7**  | ~~UI~~ **API local (IPC + HTTP + streaming SSE) + cliente Python + CLI** | Media       | Test e2e: install->query->profile_switch->audit       |
| **F8**  | ~~API~~ **UI completa 8 pestanas + 3 botones perfil + glassmorphism**    | Alta        | Switch de perfil en <2s desde UI                      |
| **F9**  | Seguridad Banking: air-gap + crypto-shred + audit chain + compliance     | Alta        | Test e2e Banking pasa todos los checks                |
| **F10** | Build pipeline + instaladores Win/Mac/Linux + offline bundle + doctor    | Media       | Smoke test en VM limpia pasa                          |

> **Nota:** F7 y F8 fueron intercambiadas respecto al plan original (Correccion B).

---

## Estado Actual

**PROYECTO COMPLETADO** — Todas las 10 fases ejecutadas exitosamente.

### Fases completadas
- **F1** — 18/18 tests. Policy Engine + core completo.
- **F2** — 24 tests adicionales. Polyglot Fabric L1+L4 completo.
- **F3** — 27 tests adicionales. Index Engine (DuckDB + SQLite FTS5) completo.
- **F4** — 50 tests adicionales. Retrieval RRF + SimHash + Assembler + IndexPipeline.
- **F5** — 35 tests adicionales. Cognitive Core multi-provider (llama.cpp/Ollama/OpenAI) + query expansion + reranker.
- **F6** — 39 tests adicionales. Polyglot L2 (COBOL, PL/I) + L3 (RPG, JCL, Natural) + copybook resolver + parser registry.
- **F7** — 61 tests adicionales. API HTTP local (server, routes, auth, IPC bridge) + CLI (5 subcomandos) + cliente Python.
- **F8** — 25 tests adicionales. UI pywebview glassmorphism (8 pestanas, 3 perfiles, theme manager).
- **F9** — 33 tests adicionales. Seguridad Banking (air-gap, crypto-shred, audit chain, compliance engine).
- **F10** — 24 tests adicionales. Build pipeline (doctor diagnostico, bundler offline, installer Win/Mac/Linux).
- **Total final:** 367 tests, ~6000 lineas src, ~65 archivos Python funcionales, 14 suites de tests.

### Mejoras Post-F10
- ModelDownloader con descarga real de GGUF desde Hugging Face
- UI expandida a 10 pestanas (+ Entrenamiento + Compliance)
- Disclaimers honestos en la UI sobre capacidades reales
- Licenciamiento AGPL-3.0 visible (Open Core model)
- Rutas de datos visibles y configurables (~/.oraculo/)

### Modelo de Licenciamiento (aprobado — actualizado a BSL)
- **Community Edition**: BSL 1.1, gratis para desarrollo/investigacion/uso interno, se vuelve Apache 2.0 en 2030
- **Enterprise Edition**: Licencia comercial, $29-99/mes, uso comercial completo
- **Banking Edition**: On-premise, $5000+, con soporte 24/7 e instalacion

### Modelo LLM por defecto
- **Recomendado:** Qwen 2.5 Coder 3B Q4_K_M (~2.1 GB RAM)
- Low-end: Qwen 2.5 Coder 1.5B (~1.2 GB RAM)
- High-end: Qwen 2.5 Coder 7B (~4.5 GB RAM)
- El usuario puede elegir cualquier modelo GGUF, Ollama, o API remota.

---

## Documentos de LEY (referencia)

Todos en `docs/`:

1. `PLAN_MAESTRO_v4.md` — Arquitectura y filosofia
2. `THREAT_MODEL_ORACULO_v4.md` — Modelo de amenazas
3. `POLICY_ENGINE_SPEC.md` — Perfiles de seguridad
4. `POLYGLOT_FABRIC_SPEC.md` — Parsing universal
5. `CONTEXT_ASSEMBLY_POLICY.md` — Ensamblado de contexto
6. `API_CONTRACT_SPEC.md` — Contrato API
7. `PROJECT_STRUCTURE_SPEC.md` — Estructura del proyecto
