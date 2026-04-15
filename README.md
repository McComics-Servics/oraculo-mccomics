<p align="center">
  <img src="https://img.shields.io/badge/version-4.0.0-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-brightgreen?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/license-BSL%201.1-orange?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/LLM-100%25%20local-purple?style=for-the-badge" alt="Local LLM">
  <img src="https://img.shields.io/badge/tests-382%20passing-success?style=for-the-badge" alt="Tests">
</p>

# El Oraculo McComics

### Tu codigo no deberia salir de tu maquina para que una IA lo entienda.

El Oraculo es un motor de inteligencia artificial **que corre completamente en tu computadora**. Indexa tu codebase, lo entiende y responde preguntas sobre el — sin enviar un solo byte a ningun servidor externo.

No es un wrapper de ChatGPT. No es un proxy a la nube. Es un LLM real corriendo en tu hardware, alimentado por un motor de busqueda hibrido que combina SQLite FTS5 + DuckDB con fusion de rankings y deduplicacion inteligente.

---

## Por que El Oraculo existe

Los desarrolladores que trabajan con codigo sensible — banca, gobierno, defensa, salud, finanzas — no pueden copiar su codigo en ChatGPT ni en Copilot. Y los que trabajan con sistemas legacy (COBOL, PL/I, RPG, JCL) directamente no tienen herramientas de IA que entiendan sus lenguajes.

El Oraculo resuelve ambos problemas: **IA real, local, que entiende desde Python hasta COBOL**.

---

## Que puede hacer

| Capacidad | Detalle |
|-----------|---------|
| **Busqueda inteligente** | No es grep. Entiende contexto, expande queries, fusiona resultados de multiples indices |
| **20+ lenguajes** | Python, Ruby, JavaScript, TypeScript, Java, Go, Rust, C/C++, COBOL, PL/I, RPG, JCL, Natural/Adabas y mas |
| **LLM local incluido** | Qwen 2.5 Coder 3B — se descarga automaticamente, corre con ~2 GB de RAM |
| **3 niveles de seguridad** | Basic (velocidad), Enterprise (balance), Banking (air-gap completo + crypto-shred + auditoria) |
| **Indexacion incremental** | Solo re-indexa lo que cambio. Detecta archivos modificados automaticamente |
| **API REST** | Puerto 9111, endpoints documentados. Integrable con cualquier editor o pipeline |
| **Interfaz grafica** | UI moderna con glassmorphism, 10 paneles funcionales, funciona en Windows, macOS y Linux |

---

## Arquitectura

```
          UI (pywebview)
              |
         API Local + IPC Bridge
              |
        Policy Engine ---- 3 perfiles YAML
              |
       Context Assembler ---- BM25 + RRF + SimHash
              |
       Cognitive Core ---- llama.cpp / Ollama / OpenAI-compatible
              |
       Index Engine ---- SQLite FTS5 + DuckDB
              |
       Polyglot Fabric ---- 20+ lenguajes + deteccion de encoding + escaneo de secretos
```

7 capas. Cada una desacoplada. Cada una testeada. Un integrador central (`OraculoApp`) las conecta en un solo flujo de arranque.

---

## Instalacion

```bash
git clone https://github.com/McComics-Servics/oraculo-mccomics.git
cd oraculo-mccomics
pip install -r requirements.txt
pip install -e .
```

El modelo LLM se descarga automaticamente la primera vez, o puedes forzarlo:

```python
from oraculo.cognitive.model_downloader import ModelDownloader
ModelDownloader().download("qwen2.5-coder:3b-instruct-q4_K_M")
```

---

## Uso

```bash
# Interfaz grafica completa
oraculo

# Solo servidor HTTP (puerto 9111)
oraculo --server

# Modo headless para scripting y CI/CD
oraculo --headless
```

---

## Perfiles de seguridad

| Perfil | Para quien | Que incluye |
|--------|-----------|-------------|
| **basic** | Desarrolladores individuales, startups | Velocidad maxima, sin overhead de seguridad |
| **enterprise** | Equipos, empresas medianas | Autenticacion por token, auditoria basica, balanceo seguridad/rendimiento |
| **banking** | Banca, gobierno, defensa, salud | Air-gap total, crypto-shred (destruccion criptografica), cadena de auditoria inmutable, verificacion de integridad por HMAC |

Cambiar de perfil es un solo comando. No hay que reconfigurar nada.

---

## Requisitos minimos

| Componente | Minimo |
|-----------|--------|
| Python | 3.11 o 3.12 |
| RAM libre | ~2 GB (para el modelo LLM) |
| Disco | ~2.5 GB (modelo + indices) |
| OS | Windows 10+, macOS 12+, Linux (glibc 2.31+) |

---

## Numeros reales

- **382 tests** pasando (367 unitarios + 15 de integracion)
- **139 archivos** de codigo fuente
- **15,246 lineas** de codigo
- **67 modulos** Python funcionales
- **0 dependencias** en servicios externos

---

## Licencia

**Business Source License 1.1** (BSL) — la misma licencia que usan MariaDB, CockroachDB y HashiCorp.

| Edicion | Precio | Incluye |
|---------|--------|---------|
| **Community** | Gratis | Uso libre para desarrollo, investigacion, educacion y uso interno |
| **Enterprise** | $29-99/mes | Uso comercial completo + soporte prioritario + actualizaciones |
| **Banking** | Desde $5,000 | Instalacion on-premise, configuracion air-gap, SLA 24/7, soporte dedicado |

El codigo se convierte automaticamente en **Apache License 2.0** el 14 de abril de 2030.

Puedes leer los terminos completos en [LICENSE](LICENSE).

---

## Quien esta detras

**McComics Servicios Generales** — Lima, Peru.

Hacemos herramientas que resuelven problemas reales para desarrolladores y fabricantes. Nuestro ecosistema incluye plugins de SketchUp para diseno de muebles, optimizadores de corte, y ahora inteligencia artificial local para codigo.

- **Web**: [www.grupomccomics.com](https://www.grupomccomics.com)
- **Email**: mccomicsservics@gmail.com
- **WhatsApp**: [+51 903 553 019](https://wa.me/51903553019)

---

<p align="center">
  <strong>Tu codigo es tuyo. Que tu IA tambien lo sea.</strong>
</p>
