# PLAN ESTRATEGICO — El Oraculo McComics v4.0
## Plan de ejecucion por fases

> Ultima actualizacion: 2026-04-15
> Responsable: McComics Servicios Generales

---

## Resumen de fases

| Fase | Descripcion | Complejidad | Estado |
|------|-------------|-------------|--------|
| F1 | Estructura + Policy Engine + 3 perfiles | Alta | ✅ COMPLETA |
| F2 | Polyglot Fabric L1 (tree-sitter) + L4 (lexical skeleton) | Alta | ✅ COMPLETA |
| F3 | Index Engine (DuckDB + SQLite FTS5) + cifrado + watcher | Alta | ✅ COMPLETA |
| F4 | Retrieval (BM25 + HNSW + RRF) + Context Assembler | Alta | ✅ COMPLETA |
| F5 | Cognitive Core (llama.cpp + Ollama + OpenAI) | Media | ✅ COMPLETA |
| F6 | Polyglot Fabric L2 (ANTLR COBOL/PL/I) + L3 (RPG/JCL) | Media-Alta | ✅ COMPLETA |
| F7 | Interfaz completa (10 pestanas) + glassmorphism | Alta | ✅ COMPLETA (monolitico) |
| F8 | API local + HTTP + IPC + CLI funcional | Media | ✅ COMPLETA |
| F9 | Seguridad Banking: air-gap + crypto-shred + audit chain | Alta | ✅ COMPLETA |
| F10 | Build system + instaladores + doctor + offline bundle | Media | ✅ COMPLETA |

---

## Estado: TODAS LAS FASES COMPLETADAS (10/10)

### Resumen de cierre
- **F8 (CLI):** Los 6 subcomandos (query, index, profile, health, status, serve) conectados a OraculoApp.
- **F10 (Build):** `scripts/build.py` con pipeline de 13 fases, bundler offline, doctor, installer (NSIS/AppImage/pkg).
- **Siguiente paso:** Testing integral, pulido UI, distribucion.

---

## Dependencias del sistema

Archivo: `requirements.txt`
- pyyaml==6.0.1
- duckdb>=0.10.0
- watchdog>=4.0.0
- charset-normalizer>=3.3.0

Opcionales (en pyproject.toml):
- pywebview (UI)
- llama-cpp-python (LLM local)
- onnxruntime, tokenizers, numpy (embeddings)

---

## Documentos de LEY (en docs/)

1. PLAN_MAESTRO_v4.md
2. THREAT_MODEL_ORACULO_v4.md
3. POLICY_ENGINE_SPEC.md
4. POLYGLOT_FABRIC_SPEC.md
5. CONTEXT_ASSEMBLY_POLICY.md
6. API_CONTRACT_SPEC.md
7. PROJECT_STRUCTURE_SPEC.md
