# El Oraculo McComics v4.0

**IA local universal para inteligencia de codigo con 3 niveles de seguridad.**

Busca, entiende y responde preguntas sobre cualquier codebase — sin enviar una sola linea a la nube.

## Caracteristicas

- **100% local** — Tu codigo nunca sale de tu maquina
- **Multi-lenguaje** — Python, Ruby, JavaScript, TypeScript, Java, Go, Rust, C/C++, COBOL, PL/I, RPG, JCL y mas
- **3 perfiles de seguridad** — Basic (velocidad), Enterprise (balance), Banking (air-gap + crypto-shred + audit chain)
- **LLM local incluido** — Qwen 2.5 Coder 3B (descarga automatica, ~2 GB RAM)
- **Busqueda hibrida** — SQLite FTS5 + DuckDB con fusion RRF y deduplicacion SimHash
- **API REST + IPC** — Integrable con cualquier editor o herramienta
- **UI glassmorphism** — Interfaz moderna con pywebview

## Requisitos

- Python 3.11 o 3.12
- ~2 GB RAM libres (para el modelo LLM)
- Windows 10+, macOS 12+, o Linux (glibc 2.31+)

## Instalacion

```bash
pip install -r requirements.txt
pip install -e .
```

## Uso

```bash
# Interfaz grafica
oraculo

# Servidor HTTP (puerto 9111)
oraculo --server

# Modo headless (para testing/scripting)
oraculo --headless
```

## Descarga del modelo LLM

```python
from oraculo.cognitive.model_downloader import ModelDownloader
dl = ModelDownloader()
dl.download("qwen2.5-coder:3b-instruct-q4_K_M")
```

## Arquitectura

```
UI (pywebview) -> API Local -> Policy Engine -> Context Assembler
     -> Cognitive Core (LLM) -> Index Engine (DuckDB+SQLite) -> Polyglot Fabric
```

7 capas conectadas por `OraculoApp`, el integrador central.

## Licencia

**Business Source License 1.1** (BSL)

- **Community Edition**: Gratis para desarrollo, investigacion, educacion y uso interno
- **Enterprise Edition**: $29-99/mes — uso comercial completo + soporte
- **Banking Edition**: Desde $5,000 — on-premise, air-gap, SLA 24/7

Se convierte en Apache License 2.0 el 2030-04-14.

Ver [LICENSE](LICENSE) para terminos completos.

## Contacto

- **Web**: [www.grupomccomics.com](https://www.grupomccomics.com)
- **Email**: mccomicsservics@gmail.com
- **WhatsApp**: +51 903 553 019

---

(C) 2026 McComics Servicios Generales — Lima, Peru.
