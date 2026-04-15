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

Si trabajas en un banco, una entidad de gobierno, una empresa de defensa o cualquier organizacion que opera bajo regulaciones de seguridad, ya sabes esto: **no puedes copiar tu codigo en ChatGPT, Copilot ni ningun servicio en la nube**. Hacerlo viola politicas internas, regulaciones de compliance y en muchos casos la ley.

¿Y que pasa con los equipos que mantienen sistemas legacy? COBOL, PL/I, RPG — lenguajes que mueven billones de dolares diarios en transacciones bancarias y que ningun asistente de IA del mercado entiende.

El Oraculo fue construido para resolver exactamente eso.

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

### 4. Hacer preguntas

Una vez indexado, puedes buscar y preguntar:

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

## Por que bancos y gobiernos deberian usarlo

1. **Cumplimiento normativo real.** No es un checkbox en un formulario. El perfil banking implementa air-gap verificado, destruccion criptografica y cadena de auditoria con hashes encadenados. Cosas que la mayoria de herramientas comerciales no ofrecen ni en su tier mas caro.

2. **El codigo nunca sale de la red interna.** No hay "confia en nosotros, no leemos tu codigo". Aqui no hay servidor al que enviar nada. El modelo corre en tu maquina. Punto.

3. **Soporte para sistemas legacy.** Los mainframes que procesan las transacciones del 90% de la banca mundial corren COBOL. Ningun otro asistente de IA los entiende. Este si.

4. **Auditabilidad total.** Cada consulta, cada indexacion, cada cambio de perfil queda registrado en una cadena inmutable. Si un auditor pregunta que paso el martes a las 3pm, hay un registro con hash criptografico que lo demuestra.

5. **Sin dependencia de terceros.** Si mañana OpenAI cambia sus terminos, si GitHub sube precios, si un proveedor de nube sufre un breach — El Oraculo sigue funcionando exactamente igual. Porque no depende de nadie.

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

Puedes usar El Oraculo libremente para desarrollo, investigacion, educacion y uso interno. Lo unico que no puedes hacer sin licencia comercial es montarlo como servicio y cobrar por el.

El 14 de abril de 2030 se convierte automaticamente en Apache License 2.0.

| Edicion | Precio | Que incluye |
|---------|--------|-------------|
| **Community** | Gratis | Todo el motor, sin limites de uso |
| **Enterprise** | $29-99/mes | Soporte prioritario, actualizaciones, uso comercial |
| **Banking** | Desde $5,000 | Instalacion on-premise, configuracion air-gap, SLA |

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
