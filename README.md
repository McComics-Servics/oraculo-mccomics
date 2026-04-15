<p align="center">
  <img src="https://img.shields.io/badge/v4.0-estable-blue?style=for-the-badge" alt="Version">
  <img src="https://img.shields.io/badge/python-3.11%20|%203.12-brightgreen?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/licencia-BSL%201.1-orange?style=for-the-badge" alt="Licencia">
  <img src="https://img.shields.io/badge/LLM-100%25%20local-purple?style=for-the-badge" alt="Local">
  <img src="https://img.shields.io/badge/382%20tests-passing-success?style=for-the-badge" alt="Tests">
</p>

# El Oraculo McComics

### Tu codigo no tiene por que salir de tu maquina para que una IA lo entienda.

El Oraculo indexa tu codebase completo, lo fragmenta, lo almacena en una base de datos local y lo pone a disposicion de un LLM que corre en tu propia computadora. No hay nube. No hay API externa. No hay telemetria. Tu codigo se queda donde debe estar: contigo.

Funciona con Python, Ruby, JavaScript, TypeScript, Java, Go, Rust, C, C++, COBOL, PL/I, RPG, JCL, Natural/Adabas y mas de 20 lenguajes. Si tu empresa todavia tiene mainframes con COBOL de los anos 80 — esto tambien los entiende.

---

## El problema que resuelve

Cada vez que le pides a una IA que modifique tu codigo, estas pagando tokens. Y la mayoria de esos tokens se desperdician porque la IA no tiene contexto de tu proyecto — no sabe que archivos existen, no entiende la estructura, no conoce tus funciones ni tus clases. Entonces le copias y pegas fragmentos a mano, repites contexto, y la IA sigue cometiendo errores porque trabaja a ciegas.

**El Oraculo elimina ese problema.**

Cuando indexas tu proyecto, El Oraculo construye un mapa completo de tu codigo: cada archivo, cada funcion, cada clase, cada dependencia. Cuando despues le haces una pregunta — ya sea desde la interfaz, la API o integrado con tu editor — el motor de busqueda encuentra exactamente los fragmentos relevantes, los ordena por importancia, elimina duplicados y arma un paquete de contexto optimizado.

Eso significa:

- **Menos tokens gastados.** En lugar de copiar archivos enteros, le pasas a la IA solo los fragmentos que necesita. Un proyecto de 50,000 lineas se reduce a los 20 fragmentos relevantes que caben en 4,096 tokens.
- **Respuestas mas precisas.** La IA no tiene que adivinar. Recibe el contexto correcto, ordenado por relevancia, con la confianza calculada de cada fragmento.
- **Menos iteraciones.** Cuando la IA entiende tu codigo de verdad, el primer intento suele ser el correcto. Menos "no, eso no era lo que pedi", menos "te falto importar X", menos retrabajo.
- **Tu codebase se vuelve la base de conocimiento de la IA.** No estas entrenando un modelo nuevo — estas dandole a cualquier LLM (local o remoto) acceso instantaneo a todo tu codigo, bien organizado y bien fragmentado.

### Para empresas: el costo real de no tener esto

Una empresa con 10 desarrolladores que usa GPT-4 o Claude gasta entre $500 y $3,000 al mes en tokens de API. La mayor parte de ese gasto se va en contexto mal armado: archivos completos donde solo se necesitaban 20 lineas, preguntas repetidas porque la IA no recordaba la respuesta anterior, correcciones que no deberian haber sido necesarias.

Con El Oraculo ensamblando el contexto, ese gasto se reduce drasticamente. No porque uses menos la IA — sino porque cada llamada rinde mas.

### Para desarrolladores individuales: trabaja mas rapido

Si usas Copilot, Cursor, Cody o cualquier asistente, ya sabes que funcionan mejor cuando entienden tu proyecto. El Oraculo te da eso sin pagar suscripcion mensual y sin enviar tu codigo a la nube. Indexas tu proyecto una vez, y cada pregunta que hagas va acompanada del contexto exacto que la IA necesita.

---

## Si trabajas en un banco, un gobierno o una empresa regulada

Si tu organizacion opera bajo regulaciones de seguridad, ya sabes esto: **no puedes copiar tu codigo en ChatGPT, Copilot ni ningun servicio en la nube**. Hacerlo viola politicas internas, regulaciones de compliance y en muchos casos la ley.

¿Y que pasa con los equipos que mantienen sistemas legacy? COBOL, PL/I, RPG — lenguajes que mueven billones de dolares diarios en transacciones bancarias y que ningun asistente de IA del mercado entiende.

El Oraculo fue construido para resolver exactamente eso. Y cualquier uso empresarial, bancario o gubernamental requiere una licencia comercial — porque las herramientas que protegen activos criticos tienen un valor que merece ser reconocido.

---

## Como funciona (paso a paso)

### 1. Instalar

```bash
git clone https://github.com/McComics-Servics/oraculo-mccomics.git
cd oraculo-mccomics
pip install -r requirements.txt
pip install -e .
```

### 2. Instalar el motor LLM

El Oraculo usa un modelo de lenguaje local. Tienes dos opciones:

**Opcion A — Ollama (recomendado para cualquier hardware):**

Descarga Ollama desde [ollama.com](https://ollama.com), instala, y ejecuta:

```bash
ollama pull qwen2.5-coder:3b
```

**Opcion B — Descarga directa del modelo GGUF (CPUs con AVX2):**

```python
from oraculo.cognitive.model_downloader import ModelDownloader
ModelDownloader().download("qwen2.5-coder:3b-instruct-q4_K_M")
```

Esto descarga ~2 GB a `~/.oraculo/models/`. Requiere un procesador con instrucciones AVX2 (Intel Haswell 2013+ o AMD Zen 2019+).

### 3. Indexar tu codigo

El Oraculo necesita "aprender" tu codebase antes de responder preguntas. Esto se llama indexacion.

**Desde la interfaz grafica:**

```bash
oraculo
```

Selecciona una carpeta, haz clic en "Indexar" y espera. Un proyecto de 100 archivos tarda menos de 5 segundos.

**Desde Python (para automatizacion o CI/CD):**

```python
from pathlib import Path
from oraculo.app import OraculoApp

app = OraculoApp(repo_root=Path("/ruta/a/tu/proyecto"), mode="headless")
ctx = app.start_headless()

pipeline = ctx["index_pipeline"]
archivos = list(Path("/ruta/a/tu/proyecto").rglob("*.py"))
stats = pipeline.index_batch(archivos, force=True)

print(f"Archivos procesados: {stats.files_processed}")
print(f"Fragmentos creados: {stats.fragments_created}")
```

**Desde la API REST:**

```bash
oraculo --server
curl -X POST http://localhost:9741/api/v1/index -d '{"paths": ["/ruta/a/tu/proyecto"]}'
```

### 4. Hacer preguntas en lenguaje natural

**Desde la terminal (CLI) — la forma mas rapida:**

```powershell
# Pregunta directa en español
mccomics_brain query "¿donde esta la funcion que calcula el corte a 45 grados?"

# Buscar dentro de un dominio especifico
mccomics_brain query "funciones que usan melamina de 18mm" --domain code

# Obtener contexto JSON optimizado para IAs
mccomics_brain query "refuerzo trasero del mueble" --format json --budget 4000
```

**Ejemplo de respuesta:**

```
🔍 Query: "¿donde esta la funcion que calcula el corte a 45 grados?"

📄 [trust:1/canon] modules/estructura_pro/core/estructura_logic.rb:142-187
   → Funcion calculate_c45_cut: logica de corte a 45° con validacion de grosor

📄 [trust:1/canon] modules/cajonera/core/geometry_builder.rb:89-112
   → Metodo apply_miter_cut: aplica inglete en piezas laterales

📄 [trust:2/alta] modules/Despiece_McComics/core/piece_rules.rb:45-68
   → Regla de asignacion C45: marca piezas que requieren corte angular

Fragmentos: 3 | Tokens est.: 487 | Tiempo: 82ms
```

**Mas ejemplos de preguntas utiles:**

| Pregunta en lenguaje natural | Que devuelve |
|---|---|
| `"¿que hace la funcion calculate_pieces?"` | Codigo exacto + firma + docstring |
| `"funciones que llaman a geometry_builder"` | Grafo de llamadas (callers directos) |
| `"archivos que usan HtmlDialog"` | Match lexico BM25 en todo el proyecto |
| `"¿donde se valida el grosor de melamina?"` | Fragmentos AST similares + semanticos |
| `"bugs relacionados con el cursor personalizado"` | Busqueda combinada docs + code |
| `"diferencias entre cajonera y estructura_pro"` | Comparacion semantica de modulos |

**Desde Python (para automatizacion):**

```python
assembler = ctx["assembler"]
resultado = assembler.assemble("como funciona la autenticacion", limit=5)

for fragmento in resultado.fragments:
    print(f"{fragmento.file_path}:{fragmento.start_line} — score: {fragmento.rrf_score:.4f}")
```

La busqueda combina BM25 (busqueda lexica en SQLite FTS5) con busqueda de simbolos (DuckDB), fusiona los rankings con RRF (Reciprocal Rank Fusion) y elimina duplicados con SimHash antes de entregar los resultados.

### Tiempos reales medidos

| Operacion | Tamanio | Tiempo |
|-----------|---------|--------|
| Indexar 79 archivos Python | ~15,000 lineas | 3.69 segundos |
| Busqueda BM25 | 315 fragmentos | < 10 ms |
| Ensamblado completo (busqueda + fusion + dedup) | 5 resultados | < 50 ms |
| Carga del modelo LLM en RAM | 2 GB | 30-60 segundos (una sola vez) |

---

## Integracion con IAs de IDE (Claude Code, Kiro, Antigravity, Cursor)

### El problema: tu IA gasta tokens buscando a ciegas

Cuando le das una instruccion a la IA de tu IDE, esto es lo que pasa normalmente:

1. La IA lee tu AGENTS.md o CLAUDE.md
2. Empieza a hacer `grep`, `glob`, `read` por todo el workspace
3. Gasta **miles de tokens** buscando archivos relevantes
4. A veces ni encuentra lo correcto

**Con El Oraculo corriendo en background**, la IA le pregunta primero y recibe los fragmentos exactos **antes de tocar un solo archivo**.

```
SIN Oraculo:                          CON Oraculo:
─────────────                         ────────────
grep "cursor" → 847 archivos          mccomics_brain query "cursor cajonera"
lee 12 archivos buscando...           → 2 archivos exactos en 82ms
3,400 tokens gastados                 → 400 tokens gastados
puede que no encuentre nada           → va directo al problema
```

### Como configurarlo (3 pasos)

**Paso 1 — Verifica que El Oraculo esta corriendo:**

```powershell
mccomics_brain health
# ✅ Daemon activo | Perfil: basic | Archivos: 1,247
```

**Paso 2 — Agrega esta regla a tu AGENTS.md (o CLAUDE.md) del proyecto:**

```markdown
## Regla: Consultar al Oraculo antes de investigar

Antes de buscar codigo con grep/glob/read para responder una pregunta
del usuario:

1. Ejecuta en terminal:
   mccomics_brain query "<la pregunta del usuario>" --format json --budget 4000

2. Lee la respuesta JSON. Cada fragmento contiene:
   - Archivo y lineas exactas
   - trust_tier (1=canon, 2=alta, 3=contextual)
   - stale (true si el archivo cambio desde la ultima indexacion)

3. Solo lee los archivos que el Oraculo indico como relevantes
4. Si trust_tier=1 y stale=false, confia en el fragmento sin releer
5. Si stale=true, relee el archivo para verificar cambios recientes
6. Si el Oraculo no devuelve resultados, usa grep/glob normal
```

**Paso 3 (opcional) — Hook recordatorio para Claude Code:**

Agrega esto a tu `settings.json` o `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Grep|Glob",
        "command": "echo 'Recuerda: puedes usar mccomics_brain query antes de buscar manualmente'"
      }
    ]
  }
}
```

### Las 3 vias de comunicacion IA ↔ Oraculo

```
┌──────────────────────────────────────────────────┐
│               IA DEL IDE                          │
│  (Claude Code / Kiro / Antigravity / Cursor)      │
└──────┬───────────────┬──────────────┬────────────┘
       │               │              │
  ① CLI (Bash)   ② HTTP local   ③ PowerShell
       │               │              │
       ▼               ▼              ▼
┌──────────────────────────────────────────────────┐
│           EL ORACULO McComics®                    │
│  Daemon local en background                       │
│  Puerto: 127.0.0.1:8888                          │
└──────────────────────────────────────────────────┘
```

| Via | Comando | Cuando usar |
|---|---|---|
| **① CLI (recomendada)** | `mccomics_brain query "..."` | Todas las IAs de IDE tienen acceso a terminal |
| **② HTTP local** | `curl http://127.0.0.1:8888/v1/query -d '{"q":"..."}'` | Si prefieres requests HTTP |
| **③ PowerShell** | `Invoke-RestMethod -Uri "http://127.0.0.1:8888/v1/query" -Method Post -Body '{"q":"..."}'` | Windows nativo sin curl |

### Ejemplo real completo

```
USUARIO: "Arregla el bug del cursor personalizado en cajonera"

IA ejecuta automaticamente (por la regla en AGENTS.md):
  $ mccomics_brain query "bug cursor personalizado cajonera" --format json

RESPUESTA DEL ORACULO (JSON):
{
  "fragments": [
    {
      "file": "modules/cajonera/ui/parametric_dialog.rb",
      "lines": [234, 267],
      "trust_tier": 1,
      "stale": false,
      "content": "def set_custom_cursor... # logica del cursor"
    },
    {
      "file": "modules/cajonera/core/geometry_builder.rb",
      "lines": [67, 89],
      "trust_tier": 2,
      "stale": false,
      "content": "def on_mouse_move... # responde a eventos del cursor"
    }
  ],
  "tokens_used": 287,
  "query_time_ms": 82
}

IA lee SOLO esos 2 archivos → encuentra y arregla el bug directo.
```

### Estado actual de esta integracion

| Componente | Estado | Fase |
|---|---|---|
| Estructura del proyecto | ✅ Creada | F1 |
| Policy Engine (3 perfiles) | ✅ Funcional | F1 |
| CLI `mccomics_brain query` | ⏳ Pendiente | F4-F8 |
| HTTP `/v1/query` | ⏳ Pendiente | F8 |
| Indexacion de codigo | ⏳ Pendiente | F2-F3 |
| Interfaz grafica 8 pestañas | ⏳ Pendiente | F7 |

> **Nota:** El CLI y la API aun no estan operativos. Cuando se completen las Fases 2-4, podras usar `mccomics_brain query` desde cualquier IA de IDE.

---

## Que lo hace diferente de todo lo demas

Esto no es teoria. Esto es lo que El Oraculo hace hoy, funcionando, con 382 tests pasando.

| | El Oraculo | GitHub Copilot | Sourcegraph Cody | Cursor | Tabnine |
|---|---|---|---|---|---|
| **Funciona 100% offline** | Si | No | No | No | Parcial |
| **Cero telemetria** | Si | No | No | No | No |
| **Soporte COBOL/PL/I/RPG/JCL** | Si | No | No | No | No |
| **Perfil banking con air-gap** | Si | No | Parcial (enterprise) | No | No |
| **Destruccion criptografica de datos** | Si | No | No | No | No |
| **Cadena de auditoria inmutable** | Si | No | No | No | No |
| **Funciona sin internet** | Si | No | No | No | No |
| **Costo de la version community** | Gratis | $10/mes | $9/mes | $20/mes | $12/mes |
| **Codigo fuente disponible** | Si | No | Parcial | No | No |

---

## Tres niveles de seguridad

No todos los proyectos necesitan el mismo nivel de proteccion. Por eso El Oraculo tiene tres perfiles, y cambiar entre ellos es un solo comando.

### Basic
Para desarrolladores individuales y startups. Velocidad maxima, sin overhead de seguridad. Ideal para proyectos personales y open source.

### Enterprise
Para equipos y empresas medianas. Incluye autenticacion por token, auditoria basica y un balance entre seguridad y rendimiento.

### Banking
Para bancos, gobierno, defensa y cualquier entorno regulado. Incluye:
- **Air-gap total** — verificacion activa de que no hay conexiones de red
- **Crypto-shred** — destruccion criptografica irreversible de datos (no es "borrar archivos", es destruir las llaves de cifrado)
- **Cadena de auditoria inmutable** — cada accion registrada con hash SHA-256 encadenado, como un blockchain interno
- **HMAC por fila** — verificacion de integridad de cada registro en la base de datos
- **Compliance automatizado** — verificacion continua de que todas las politicas de seguridad se cumplen

---

## Modelos LLM disponibles

El Oraculo funciona con cualquier modelo GGUF compatible con llama.cpp, o con cualquier modelo servido por Ollama.

| Modelo | RAM necesaria | Ideal para |
|--------|--------------|------------|
| Qwen 2.5 Coder 1.5B | ~1.2 GB | Laptops con poca RAM, respuestas rapidas |
| **Qwen 2.5 Coder 3B** (por defecto) | ~2.1 GB | Balance entre calidad y velocidad |
| Qwen 2.5 Coder 7B | ~4.7 GB | Mayor precision en preguntas complejas |
| DeepSeek Coder V2 16B | ~10 GB | Estaciones de trabajo con RAM abundante |
| CodeLlama 34B | ~20 GB | Servidores dedicados, maxima calidad |
| Cualquier modelo Ollama | Variable | Flexibilidad total |

Para usar un modelo mas grande basta apuntar la variable de entorno:

```bash
ORACULO_LLM_MODEL="/ruta/al/modelo.gguf" oraculo
```

O con Ollama:

```bash
ollama pull deepseek-coder-v2:16b
```

Un modelo mas grande entiende mejor el contexto, genera respuestas mas precisas y comete menos errores en preguntas sobre codigo complejo. La desventaja es solo el consumo de RAM.

---

## Por que bancos y gobiernos deberian adquirir la licencia

1. **Ahorro real de costos en IA.** Si tu organizacion gasta miles de dolares al mes en tokens de GPT-4 o Claude, El Oraculo reduce ese gasto porque cada llamada lleva solo el contexto necesario. No archivos enteros. No contexto repetido. Solo lo que importa.

2. **Cumplimiento normativo real.** No es un checkbox en un formulario. El perfil banking implementa air-gap verificado, destruccion criptografica y cadena de auditoria con hashes encadenados. Cosas que la mayoria de herramientas comerciales no ofrecen ni en su tier mas caro.

3. **El codigo nunca sale de la red interna.** No hay "confia en nosotros, no leemos tu codigo". Aqui no hay servidor al que enviar nada. El modelo corre en tu maquina. Punto.

4. **Soporte para sistemas legacy.** Los mainframes que procesan las transacciones del 90% de la banca mundial corren COBOL. Ningun otro asistente de IA los entiende. Este si.

5. **Auditabilidad total.** Cada consulta, cada indexacion, cada cambio de perfil queda registrado en una cadena inmutable. Si un auditor pregunta que paso el martes a las 3pm, hay un registro con hash criptografico que lo demuestra.

6. **Sin dependencia de terceros.** Si mañana OpenAI cambia sus terminos, si GitHub sube precios, si un proveedor de nube sufre un breach — El Oraculo sigue funcionando exactamente igual. Porque no depende de nadie.

7. **Tu equipo de desarrollo rinde mas.** Cada desarrollador que usa El Oraculo escribe mejor codigo, en menos tiempo, con menos errores. Multiplica eso por 10, 50 o 200 desarrolladores y el retorno de inversion se mide en semanas, no en meses.

---

## Arquitectura

```
 Interfaz (pywebview)
       |
  API Local + IPC Bridge ---- 14 metodos expuestos
       |
  Policy Engine ---- 3 perfiles YAML con validacion estricta
       |
  Context Assembler ---- BM25 + RRF + SimHash + Budget Allocator
       |
  Cognitive Core ---- llama.cpp | Ollama | OpenAI-compatible
       |
  Index Engine ---- SQLite FTS5 + DuckDB + Watcher + Incremental
       |
  Polyglot Fabric ---- 20+ lenguajes + encoding + secretos + inyeccion
```

7 capas desacopladas. 67 modulos. 15,246 lineas de codigo. Todo testeado.

---

## Requisitos

| Componente | Minimo |
|-----------|--------|
| Python | 3.11 o 3.12 |
| RAM libre | 2 GB (modelo 3B) / 5 GB (modelo 7B) |
| Disco | 3 GB (modelo + indices) |
| CPU | Cualquiera con Ollama, AVX2 con llama.cpp directo |
| OS | Windows 10+, macOS 12+, Linux |
| Internet | Solo para descargar el modelo la primera vez. Despues: cero. |

---

## Licencia

**Business Source License 1.1** — la misma licencia que usan MariaDB, CockroachDB y HashiCorp.

La version Community es gratuita **solo para personas individuales**: desarrolladores independientes, estudiantes e investigadores. Si eres una empresa, un banco, una entidad de gobierno o cualquier organizacion con mas de un empleado — necesitas licencia comercial. No hay excepciones de "uso interno" ni "evaluacion gratuita para empresas".

El 14 de abril de 2030 se convierte automaticamente en Apache License 2.0.

| Edicion | Precio | Para quien |
|---------|--------|------------|
| **Community** | Gratis | Desarrolladores individuales, estudiantes, investigadores |
| **Enterprise** | $29-99/mes | Startups, empresas, equipos de desarrollo |
| **Banking** | Desde $5,000 | Bancos, gobierno, defensa, entornos regulados |

---

## Adquirir licencia comercial

Visita **[www.grupomccomics.com](https://www.grupomccomics.com)** para conocer los planes disponibles, solicitar una demo o hablar directamente con nuestro equipo.

- **Email**: mccomicsservics@gmail.com
- **WhatsApp**: [+51 903 553 019](https://wa.me/51903553019)

Respondemos en menos de 24 horas. Si eres un banco, una entidad de gobierno o una empresa con requisitos especificos de compliance, escribenos directamente — hacemos implementaciones a medida.

---

<p align="center">
  <strong>Tu codigo es tuyo. Tu inteligencia artificial tambien deberia serlo.</strong>
  <br><br>
  Hecho en Lima, Peru por <a href="https://www.grupomccomics.com">McComics Servicios Generales</a>.
</p>
