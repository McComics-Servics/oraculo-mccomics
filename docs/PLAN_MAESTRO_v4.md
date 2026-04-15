PLAN MAESTRO DE INGENIERÍA v4.0
"El Oráculo McComics®" — IA Local Universal de Grado Mundial

Clasificación: Documento de LEY — Blueprint Post-Auditoría v2
Versión: 4.0 — Universal / Legacy / Multi-Perfil de Seguridad
Propietario: McComics Servicios Generales — Lima, Perú
Fecha: 2026-04-14


PARTE 0 — FILOSOFÍA DE DISEÑO (EL ESPÍRITU)
El Oráculo v4.0 se construye sobre cinco invariantes innegociables. Los 3 perfiles de seguridad modifican políticas, nunca el núcleo.
#InvarianteSignificado1Un solo motorBasic, Enterprise y Banking comparten el mismo binario. Solo cambian políticas cargadas desde profile.yaml.2Todo es local por defectoNada sale de la máquina a menos que el usuario lo autorice explícitamente por carpeta y por dominio.3Cualquier código, cualquier épocaDesde COBOL de 1975 hasta Rust de 2026. Si es texto, es indexable.4Degradación eleganteSi una capa falla, el sistema sigue sirviendo con funcionalidad reducida y lo reporta. Jamás miente.5Procedencia verificableCada fragmento entregado a una IA consumidora lleva su trust tier, su hash, su fuente y su frescura.

PARTE 1 — ARQUITECTURA EN 7 CAPAS
┌─────────────────────────────────────────────────────────────┐
│  CAPA 7 · INTERFAZ (pywebview + HTML/CSS/JS + WebView2)     │
│  8 pestañas, glassmorphism McComics, botones de perfil      │
├─────────────────────────────────────────────────────────────┤
│  CAPA 6 · API LOCAL (IPC nativo + HTTP loopback opcional)   │
│  /v1/query  /v1/health  /v1/index  /v1/feedback  /v1/audit  │
├─────────────────────────────────────────────────────────────┤
│  CAPA 5 · POLICY ENGINE (carga Basic/Enterprise/Banking)    │
│  Decide: cifrado, logs, red, auditoría, rate limits         │
├─────────────────────────────────────────────────────────────┤
│  CAPA 4 · CONTEXT ASSEMBLER (presupuesto jerárquico)        │
│  RRF fusion: BM25 + Vector + AST + Call Graph + SimHash     │
├─────────────────────────────────────────────────────────────┤
│  CAPA 3 · COGNITIVE CORE (LLM local pequeño opcional)       │
│  llama.cpp + Qwen 2.5 0.5B/1.5B o Phi-3 mini (~600MB)      │
│  Expansión de consulta, re-ranking, resúmenes locales       │
├─────────────────────────────────────────────────────────────┤
│  CAPA 2 · INDEX ENGINE (DuckDB+HNSW / SQLite-FTS5 / mmap)  │
│  Incremental, WAL, cifrado por dominio, crypto-shredding    │
├─────────────────────────────────────────────────────────────┤
│  CAPA 1 · POLYGLOT FABRIC (parsers federados universales)   │
│  tree-sitter · ANTLR · regex-patterns · lexical skeleton    │
└─────────────────────────────────────────────────────────────┘
Cada capa es reemplazable. Si tree-sitter falla para un lenguaje exótico, el Polyglot Fabric cae automáticamente al lexical skeleton sin perder servicio.

PARTE 2 — POLYGLOT FABRIC: EL CORAZÓN UNIVERSAL
2.1 El problema real de la banca y el código antiguo
Los bancos corren sistemas críticos en lenguajes que tree-sitter no soporta oficialmente: COBOL, RPG/RPGLE, PL/I, Natural/ADABAS, JCL, CLIST, REXX, Assembler IBM, Fortran 77, Ada, Clipper, FoxPro, MUMPS. Muchos archivos están en EBCDIC, con formato fijo por columnas (COBOL col 7–72), con copybooks incluidos por nombre, y a veces comprimidos en PDS members (.pds, .mbr).
2.2 Estrategia de cuatro niveles de fallback
NivelTécnicaCoberturaVelocidadPrecisiónL1 · tree-sitter nativoParser compiladoPython, JS, TS, Ruby, Go, Rust, Java, C, C++, C#, PHP, Kotlin, Swift, Scala, Lua, Bash, SQL, HTML, CSS, YAML, JSON, Markdown (~60 lenguajes)⚡⚡⚡99%L2 · ANTLR grammar loaderGramáticas .g4 cargadas dinámicamenteCOBOL, PL/I, Fortran, Ada, Verilog, VHDL, Solidity, Delphi⚡⚡92%L3 · Regex pattern libraryPatrones por lenguaje en patterns/*.yamlRPG, Natural, JCL, CLIST, REXX, MUMPS, Clipper, FoxPro, Assembler⚡⚡75%L4 · Lexical SkeletonAnálisis agnóstico por indentación + heurísticas léxicasCUALQUIER archivo de texto desconocido⚡⚡⚡55%
2.3 El Lexical Skeleton (innovación crítica)
Para cualquier archivo de texto sin parser dedicado, extraer sin comprender la sintaxis:
· Bloques por indentación (dedent-based chunking)
· Rangos de líneas con densidad de comentarios (ratio comentario/código)
· Identificadores candidatos (tokens ≥3 chars, alfanuméricos, no keywords comunes)
· Señales léxicas (mayúsculas → probablemente constantes, snake_case → funciones, etc.)
· Boundaries por líneas en blanco consecutivas
· Para COBOL: detección automática de columnas 1-6 (número), 7 (indicador), 8-11 (área A), 12-72 (área B)
Esto garantiza que ningún archivo queda fuera del índice, aunque sea un .prg de Clipper de 1992.
2.4 Copybooks, includes y resolución simbólica
Motor incremental de tabla de símbolos multi-lenguaje:
yamlsymbol_resolver:
  cobol: 
    include_pattern: 'COPY\s+([A-Z0-9-]+)'
    search_paths: ['./copybooks/', './cpy/']
  c_cpp: 
    include_pattern: '#include\s+[<"]([^>"]+)[>"]'
  ruby: 
    include_pattern: 'require(?:_relative)?\s+[''"]([^''"]+)'
  python: 
    include_pattern: '(?:from\s+(\S+)\s+)?import\s+(\S+)'
  java: 
    include_pattern: 'import\s+([\w.]+);'
El grafo de dependencias se vuelve universal y el Context Assembler puede traer copybooks relacionados cuando una IA pregunta sobre una función COBOL.
2.5 Detección automática de encoding
Pipeline de lectura de archivo:
1. Leer primeros 4KB
2. chardet/charset-normalizer → candidato
3. Verificar BOM (UTF-8, UTF-16 LE/BE)
4. Si bytes > 0x80 dominan el rango 0x40-0xFE → probable EBCDIC → codec 'cp037' o 'cp1047'
5. Si falla → latin-1 (nunca falla, nunca corrompe bytes)
6. Normalizar a UTF-8 NFC antes de indexar
7. Registrar encoding detectado en metadata
Nunca errors='replace'. Archivos que no pueden leerse se marcan unreadable=true y se reportan en /v1/health.

PARTE 3 — LOS TRES PERFILES DE SEGURIDAD
3.1 Filosofía: mismo motor, tres políticas
Los 3 botones en la interfaz cargan profiles/basic.yaml, profiles/enterprise.yaml o profiles/banking.yaml. El Policy Engine aplica la configuración en caliente sin reiniciar el daemon. Cambiar de perfil toma <2 segundos.
3.2 Tabla maestra comparativa
Dimensión🟢 BÁSICO🔵 EMPRESARIAL🔴 BANCARIOClave maestraDPAPI/Keychain/libsecretDPAPI + passphrase opcionalArgon2id passphrase obligatoria + soporte YubiKey/HSMTransporteHTTP 127.0.0.1 + token estáticoIPC nativo (named pipe / unix socket) + HMAC por requestIPC exclusivo + HMAC + nonce + timestamp (anti-replay)Red externaPermitida (opcional cloud embeddings)Solo dominios en allowlist explícitaAir-gap total: socket bloqueado a nivel kernelCifrado índiceAES-256-GCM con clave del keyringAES-256-GCM + clave por dominioAES-256-GCM + rotación cada 30 días + crypto-shreddingLogsRotación 5MB×3Sanitización DLP + paths hasheadosAppend-only + HMAC encadenado + sello diario externoAuditoríaLog básico localAudit log consultable desde UIAudit log inmutable + export firmado para complianceRate limit300 q/min60 q/min por token30 q/min + detección de anomalías + bloqueo automáticoTokens APITTL 30 díasTTL 24h rotativosTTL 1h + rotación forzada + revocación inmediataBackupsSin cifrar (veloz)Cifrados con clave secundariaCifrados + firmados + integridad verificableTelemetría opcionalAnonimizada hacia McComics (opt-in)Deshabilitada por defectoFísicamente imposible (no hay código de telemetría cargado)LLM localCualquier modelo, descarga automáticaModelos verificados con hash SHA256Solo modelos pre-aprobados del manifest firmadoGolden testsAl arranque manualAl arranque automáticoAl arranque + cada 6h + bloqueo si regresión >10%Integridad DBPRAGMA quick_checkPRAGMA integrity_check completointegrity_check + verificación HMAC por filaBorrado seguroos.remove()Sobrescritura 1 pasadaCrypto-shredding (destruye clave efímera por dominio)Query P95 objetivo~150ms~280ms~500msRAM steady state~500MB~750MB~1.1GBInstalación1 clic, 80MB1 clic + verificación hashes, 95MBPaquete offline firmado, 140MB
3.3 Ventajas y desventajas honestas
🟢 BÁSICO — "Velocidad y simplicidad"

✅ Ultra rápido. Arranca en 1.5s. Ideal para desarrollo individual.
✅ Instalación de un solo clic con descarga de modelos.
✅ Sin fricción — el desarrollador no siente el sistema.
❌ Si un malware obtiene acceso de usuario, puede leer la clave del keyring.
❌ No adecuado para código propietario de alto valor.
🎯 Para: desarrolladores individuales, proyectos open source, estudiantes.

🔵 EMPRESARIAL — "Equilibrio profesional"

✅ Protección real contra filtraciones accidentales y malware común.
✅ Audit log consultable para retrospectivas.
✅ HMAC previene que otros procesos inyecten queries falsas.
❌ Queries ~80ms más lentas por criptografía y logging.
❌ Requiere gestión ocasional de tokens rotativos.
🎯 Para: startups, PYMES técnicas, consultoras, equipos de 2–50 personas.

🔴 BANCARIO — "Paranoia verificable"

✅ Defensible ante auditorías SOC2, ISO 27001, PCI-DSS, normativa BCRP.
✅ Air-gap real. Imposible exfiltrar aunque haya malware activo.
✅ Evidencia criptográfica de cada consulta para forense.
✅ Compliance report generator exporta CSV firmado mensual.
❌ ~350ms extra por query (sigue siendo aceptable).
❌ Instalación requiere ceremonia: passphrase inicial, verificación offline de hashes.
❌ Requiere intervención humana para rotaciones críticas.
🎯 Para: bancos, gobierno, defensa, salud, legal, propiedad intelectual crítica.

3.4 Migración entre perfiles
Subir de nivel (Basic → Enterprise → Banking) es siempre seguro: solo endurece. Bajar de nivel requiere confirmación explícita con passphrase y re-cifrado del índice con las nuevas políticas. Esto previene ataques donde un malware baja el perfil para robar datos.

PARTE 4 — COGNITIVE CORE: IA LOCAL PEQUEÑA INTEGRADA
4.1 Por qué un LLM local junto al Oráculo
El Oráculo es un cerebro de memoria (retrieval). El LLM pequeño es un cerebro de lenguaje (generation). Juntos forman una IA local completa que no necesita cloud para tareas comunes.
4.2 Modelos soportados (todos GGUF vía llama.cpp)
ModeloTamañoRAMUso recomendadoQwen 2.5 0.5B Instruct380MB600MBExpansión de consulta, clasificaciónQwen 2.5 1.5B Instruct1.0GB1.4GBRe-ranking, resúmenes cortosPhi-3 mini 3.8B Q42.3GB3.0GBRespuestas completas localesGemma 2 2B Q51.6GB2.2GBBalance generalLlama 3.2 3B Q42.0GB2.8GBMulti-idioma robusto
Por defecto: Qwen 2.5 1.5B (mejor ratio calidad/RAM). El usuario puede cambiarlo desde la pestaña Cognitive.
4.3 Funciones del LLM local

Query expansion — "bug en escalador" → "error bug fallo defecto en ESCALADOR_ULTRA_MCCOMICS scaling geometry"
Re-ranking semántico — reordenar top 20 del retrieval fusionado a top 5 final
Resúmenes de fragmentos largos — comprime funciones de 200 líneas en 40 líneas preservando semántica clave
Clasificación de intención — ¿el usuario quiere código, documentación, o explicación?
Respuestas directas para consultas triviales — "¿qué hace X?" se responde localmente sin enviar a cloud

4.4 Modo híbrido Oráculo + LLM externo
El Oráculo sirve contexto enriquecido a Claude/GPT/Gemini via el endpoint /v1/context. El usuario copia un bloque JSON y lo pega en su chat preferido, o usa la integración directa (solo perfiles Basic/Enterprise).

PARTE 5 — CONTEXT ASSEMBLER: ASIGNACIÓN JERÁRQUICA DE TOKENS
5.1 Política de presupuesto por capas
Presupuesto total configurable (por defecto 8000 tokens). Se asigna siempre en estas proporciones, nunca se desborda ninguna capa:
Capa% BudgetContenidoTrust tierL0 · Núcleo exacto25%Función/símbolo objetivo + firma + docstring1 (canon)L1 · Grafo de llamadas20%Callers y callees directos (1 salto)1 (canon)L2 · Match sintáctico AST20%Funciones con AST similar (APTED ≤0.85)2 (alta)L3 · Match semántico vectorial15%Top-K del HNSW con re-rank del LLM local2 (alta)L4 · Match léxico BM2510%Coincidencias exactas de palabras clave2 (alta)L5 · Metadata del proyecto5%Reglas McComics activas, README, glosario3 (contextual)L6 · Reserva anti-desborde5%Buffer para truncación segura—
Si una capa no llena su cuota → se redistribuye a las capas superiores. Si L0 sola ya consume >50% → se recorta con ventana deslizante centrada en el símbolo.
5.2 Fusión Reciprocal Rank Fusion (RRF)
final_score(doc) = Σ [ 1 / (k + rank_i(doc)) ]  para cada método i
k = 60 (estándar)
métodos = [BM25, HNSW, AST-APTED, CallGraph, SimHash-dedup]
RRF es liviano, sin entrenamiento y sorprendentemente preciso — supera a esquemas ponderados manualmente en la mayoría de benchmarks.
5.3 Deduplicación SimHash de 64 bits
Cada fragmento indexado lleva su SimHash. Al ensamblar, si dos fragmentos tienen hamming_distance < 6 → conservar solo el más reciente (por file_hash y mtime). Esto elimina los duplicados de versiones (_v2, _backup, _old) sin necesidad de heurísticas por nombre.
5.4 Glosario McComics integrado
db_storage/glossary.yaml cargado al inicio. Términos se expanden antes del embedding:
yamlRF: refuerzo
C45: corte 45 grados
FR: frente
FD: fondo
CJN: cajon
MEL: melamina
DESP: despiece
El usuario puede editar el glosario desde la pestaña Cognitive.
5.5 Procedencia verificable en cada respuesta
json{
  "api_version": "1.0",
  "query_id": "uuid",
  "chars_used": 1842,
  "estimated_tokens": {"cl100k_base": 287, "gemini": "est:310"},
  "fragments": [
    {
      "content": "...",
      "provenance": "ast_direct|call_graph|semantic|bm25|stale",
      "confidence": 0.94,
      "trust_tier": 1,
      "file": "file:a3f2e1",
      "file_hash_current": "sha256:...",
      "file_hash_at_index": "sha256:...",
      "stale": false,
      "last_modified": "2026-04-12T10:22:00Z",
      "language": "cobol",
      "parser_level": "L2_antlr",
      "dynamic_dispatch_warning": false
    }
  ],
  "excluded_stale": 3,
  "warnings": []
}

PARTE 6 — INTERFAZ GRÁFICA: 8 PESTAÑAS
Stack: pywebview + HTML/CSS/JS embebido + Tailwind-lite compilado estáticamente. Sin servidor de desarrollo. Sin npm en runtime. Todo precompilado en ui/dist/.
6.1 Estructura de pestañas
#PestañaContenido principal1📊 DashboardEstado del daemon, perfil activo, archivos indexados, últimas queries, RAM/CPU, salud del índice2🔍 Query ExplorerInput de consulta, resultados en vivo, inspector de fragmentos, prueba de presupuestos3📁 Index ManagerCarpetas autorizadas, dominios (code/docs/email/wiki), pausar/reanudar, reindexar, estadísticas por lenguaje4🛡️ Security CenterLos 3 botones grandes Básico/Empresarial/Bancario + estado detallado + historial de cambios de perfil5🧠 CognitiveSelector de LLM local, descarga de modelos, glosario editable, golden tests, feedback histórico6📜 Audit LogVisible solo en Enterprise/Banking, filtros, exportación firmada7⚙️ DependenciesDoctor (diagnóstico), auto-instalador, estado WebView2, tree-sitter bindings, ONNX runtime8ℹ️ Acerca deVersión, licencia, contacto McComics, links legales, botón de soporte
6.2 Criterios de UI McComics

Marco azul #2563EB, cyan #38BDF8, púrpura #A855F7
Glassmorphism en paneles flotantes
Animaciones solo con transform y opacity (60fps garantizados)
Sin backdrop-filter en el frame principal (compatible con WebView2 degradado)
Atajos de teclado: Ctrl+1..8 para pestañas, Ctrl+K para query rápida, Ctrl+Shift+P para cambio de perfil
Modo oscuro por defecto, modo claro opcional
Tamaño mínimo de ventana 1024×700

6.3 Los 3 botones de perfil (sección crítica)
Panel superior de la pestaña Security Center con 3 tarjetas grandes una al lado de otra:
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   🟢 BÁSICO  │  │ 🔵 EMPRESAR │  │ 🔴 BANCARIO │
│             │  │             │  │             │
│ [Ventajas]  │  │ [Ventajas]  │  │ [Ventajas]  │
│ [Limites]   │  │ [Limites]   │  │ [Limites]   │
│             │  │             │  │             │
│ [ACTIVAR]   │  │ [ACTIVO ✓]  │  │ [ACTIVAR]   │
└─────────────┘  └─────────────┘  └─────────────┘
Al hacer clic: modal de confirmación con lista de cambios + passphrase si es un downgrade. Transición en <2s sin reiniciar.

PARTE 7 — COMPILACIÓN Y DISTRIBUCIÓN
7.1 Estrategia dual
MétodoPropósitoVentajaDesventajaPyInstaller --onedirDistribución principalCompatible con todo, fácil debugTamaño ~140MBNuitkaBuilds de alta performance2-3× más rápido en arranque, binario realCompilación lenta, ocasionales issues con libs nativas
Por defecto se distribuye PyInstaller. Nuitka se ofrece como "edición optimizada" opcional.
7.2 Pipeline de build (build.py automático)
Fase 1: Descarga pre-compiled wheels para la plataforma target
Fase 2: Compila tree-sitter bindings contra el Python embebido
Fase 3: Empaqueta UI estática (ui/dist/) como recurso
Fase 4: Incluye modelos LLM en `models/` (opcional, configurable)
Fase 5: Firma binaria (Authenticode Windows, codesign macOS)
Fase 6: Genera instalador:
  · NSIS (.exe) para Windows
  · DMG + .pkg para macOS (notarizado)
  · AppImage + .deb + .rpm para Linux
Fase 7: Genera manifest de hashes SHA256 firmado
Fase 8: Genera paquete offline (.zip) con todas las deps pre-descargadas
7.3 Instalador con perfiles desde el primer clic
Durante la instalación el usuario elige el perfil antes de ejecutar por primera vez. El instalador:

Descarga solo los componentes necesarios (modo Basic no descarga YubiKey libs)
Verifica WebView2 Runtime
Compila tree-sitter bindings contra el Python del sistema (o usa los embebidos)
Crea accesos directos
Registra el daemon como servicio (opcional en Banking)

7.4 Modo offline para bancos
Paquete oraculo-v4-offline-bundle.zip (~550MB) contiene:

Binario principal
Todas las dependencias pre-compiladas
3 modelos LLM pre-descargados
Manifest firmado
Hashes verificables

Un auditor bancario puede verificar el hash del zip contra uno publicado externamente antes de instalarlo en red air-gapped.

PARTE 8 — DEPENDENCIAS Y DOCTOR
8.1 Pestaña Dependencies con "Doctor" automático
Al abrir la pestaña ejecuta un diagnóstico completo en <3 segundos:
✓ Python 3.11.7 (compatible)
✓ WebView2 Runtime 131.0.2903 (OK)
✓ SQLite con FTS5 habilitado
✓ DuckDB 0.10.1 con extensión vector
✓ tree-sitter bindings compilados para Python 3.11
✓ ONNX Runtime CPU 1.17 (GPU deshabilitado intencional)
✓ llama.cpp binario con soporte AVX2
✗ Modelo Qwen 2.5 1.5B NO descargado → [Descargar 1.0GB]
⚠ Hardware fingerprint: 2/3 factores estables (warning en VMs)
✓ Permisos de escritura en db_storage/
✓ Puerto 8888 disponible
Cada fila tiene su botón de auto-reparación si aplica.
8.2 Instalador de dependencias paso a paso
Para usuarios no técnicos, un asistente guía:

Verificación inicial
Descarga de componentes faltantes (con progreso)
Compilación de bindings (barra de progreso honesta)
Prueba de humo con 5 archivos dummy
Listo para usar

Todos los comandos que el sistema muestra al usuario están en PowerShell 7 format por preferencia McComics:
powershellpwsh -Command "& { Invoke-WebRequest -Uri 'https://...' -OutFile 'deps.zip' }"

PARTE 9 — MEJORAS CRÍTICAS v4.0 (NUEVAS SOBRE v3.0)
M1 · Semantic Query Cache con invalidación por hash
Cache LRU de 200 queries resueltas. Key = hash(query + sorted_file_hashes_del_scope). Hit = respuesta en ~5ms. Miss = pipeline completo. Se invalida automáticamente cuando cambian los archivos del scope.
M2 · Incremental re-embedding inteligente
Cuando cambias el modelo de embeddings, no re-embebas todo. El sistema:

Re-embebe solo el top-20% más consultado (cacheado en query_stats)
Sirve lo demás con embeddings viejos marcándolos trust_tier: 2
Re-embebe el resto en background durante idle
Al finalizar, promueve a trust_tier: 1

Esto convierte una operación de horas en minutos visibles.
M3 · Content-Defined Chunking (FastCDC) para archivos sin parser
Para archivos L4 (lexical skeleton), usar FastCDC en lugar de chunks de tamaño fijo. Pequeñas ediciones no invalidan todos los chunks posteriores — solo los afectados. Reduce re-indexación incremental en 85%.
M4 · Zero-copy mmap para archivos grandes
Archivos >10MB (típicos en Fortran científico y COBOL batch) se acceden vía mmap.mmap() sin cargar a RAM. El sistema maneja proyectos de 4GB+ con menos de 1GB de RAM.
M5 · Active learning con feedback binario
Cada respuesta tiene botones 👍/👎 en la UI. El feedback ajusta pesos RRF por proyecto:
rrf_weight[method] *= (1 + learning_rate * (upvotes - downvotes) / total)
Sin entrenar modelos. Sin requerir dataset etiquetado. Matemática pura sobre ranks.
M6 · Multi-dominio con cifrado independiente
El usuario define "dominios" en Index Manager:

code/ → clave_A
docs/ → clave_B
emails/ → clave_C
wiki_empresa/ → clave_D

Cada dominio se puede borrar, rotar clave o exportar de forma independiente. Crypto-shredding por dominio.
M7 · Hot reload de parsers y patrones
patterns/*.yaml se recarga en caliente. Agregar soporte a un nuevo lenguaje legacy es crear un .yaml y reiniciar nada.
M8 · Anomaly detection sobre queries (Banking)
Modelo estadístico simple (z-score sobre frecuencia y distribución de queries) detecta:

Escaneo sistemático (queries muy distintas en poco tiempo)
Enumeración (queries similares con incremento numérico)
Exfiltración lenta (baja frecuencia pero amplio scope)

Al detectar → bloquea el token y notifica por UI.
M9 · Integridad por fila (Banking)
Cada fila del índice lleva HMAC-SHA256 firmado con la clave maestra. Al servir resultados, se verifica HMAC. Si no cuadra → fila marcada corrupta, excluida, y reportada. Defensa contra tampering offline del archivo DuckDB.
M10 · Air-gap real verificado
En perfil Banking, el daemon intenta conectarse al inicio a 10.255.255.255 (dirección no ruteable). Si la conexión es rechazada inmediatamente → confirmación de que el socket está bloqueado correctamente. Si responde algo → alerta crítica "AIR-GAP COMPROMETIDO".
M11 · Compliance Report Generator (Banking)
Exporta CSV firmado mensual con:

Total queries ejecutadas
Usuarios (tokens) activos
Perfiles usados
Eventos de seguridad
Checksum de integridad del índice
Hash HMAC encadenado del audit log

Formato listo para adjuntar a reportes SOC2/ISO 27001.
M12 · Dry-run mode
/v1/query?dry_run=true retorna qué habría devuelto sin leer el contenido real de los fragmentos. Útil para probar políticas y auditar scope.
M13 · Streaming de respuestas
/v1/query/stream emite fragmentos via Server-Sent Events conforme se ensamblan. La UI muestra resultados mientras siguen llegando. Percepción de velocidad ~3× superior.
M14 · Grafo de llamadas tolerante a dispatch dinámico
Funciones con send, method_missing, define_method, reflection o punteros a función se marcan dynamic_dispatch=true. El payload incluye esta bandera para que la IA consumidora sepa que el grafo puede tener falsos negativos en ese nodo.
M15 · Golden tests editables por usuario
En la pestaña Cognitive el usuario puede capturar una query actual como golden test con un clic. Crecer la suite de regresión se vuelve orgánico.
M16 · Pre-flight en modo degradado
Si un check no-crítico falla, el sistema arranca con funcionalidad reducida explícitamente marcada en /v1/health. El usuario ve un banner en la UI "FUNCIONANDO EN MODO DEGRADADO: [razón]". Nunca un crash opaco.
M17 · Plugin-SDK para extender parsers
Archivo plugins/mi_lenguaje.py con interface simple:
pythonclass MiParserPlugin:
    language_name = "clipper"
    file_extensions = [".prg", ".ch"]
    def parse(self, source: bytes) -> list[Fragment]: ...
Cargado al arranque. Permite a usuarios avanzados agregar lenguajes sin modificar el núcleo.
M18 · Detección de secretos antes de indexar
Regex scanner (tipo detect-secrets ligero) corre antes de cada indexación. Si encuentra API keys, passwords hardcodeadas, private keys → ese fragmento específico se excluye del índice y se reporta al usuario. Protege contra que el Oráculo "recuerde" credenciales por accidente.

PARTE 10 — SLOs Y MÉTRICAS DE ÉXITO
MétricaBasicEnterpriseBankingQuery P50<80ms<150ms<280msQuery P95<150ms<280ms<500msQuery P99<300ms<450ms<800msArranque en frío<2s<3s<5sIndexación≥60 arch/s≥50 arch/s≥40 arch/sRAM steady<500MB<750MB<1.1GBPrecisión top-5≥85%≥85%≥85%Uptime objetivo99%99.5%99.9%Regresión máxima aceptable15%10%5%
Los SLOs se verifican automáticamente al arranque con golden tests. Falla en régimen = banner en UI.

PARTE 11 — PLAN DE EJECUCIÓN POR FASES
FaseCorrecciónComplejidadEntregableF1Estructura completa de carpetas + esqueletos de todos los módulos + Policy Engine con los 3 perfilesAltaDaemon arranca con 3 perfiles conmutablesF2Polyglot Fabric niveles L1 (tree-sitter) + L4 (lexical skeleton)AltaCualquier archivo indexableF3Index Engine (DuckDB + SQLite FTS5) + cifrado por dominio + WALAltaIndexación persistente con los 3 perfilesF4Context Assembler con RRF + presupuesto jerárquico + SimHash dedupAltaRespuestas con procedencia verificableF5Cognitive Core (llama.cpp + Qwen 2.5 1.5B) + query expansion + re-rankingMediaLLM local operativoF6Polyglot Fabric niveles L2 (ANTLR COBOL/PL/I) + L3 (regex RPG/JCL/Natural)Media-AltaSoporte real a banca legacyF7Interfaz completa con 8 pestañas + 3 botones de perfil + glassmorphism McComicsAltaExperiencia de usuario finalF8API local con IPC nativo + HTTP opcional + streaming SSEMediaIntegración con IAs externasF9Seguridad Banking completa: air-gap verify + crypto-shredding + audit chain + compliance exportAltaPerfil Banking certificableF10Build system + instaladores multi-plataforma + doctor de dependencias + offline bundleMediaDistribución profesional
Entregable total: 10 fases. Al no pedir confirmación entre fases, ejecución continua hasta F10.

PARTE 12 — FALLOS POTENCIALES NUEVOS DETECTADOS EN v4.0
#FalloMitigaciónv4-01ANTLR runtime en Python es lento (~5× más que tree-sitter)Cache agresivo de AST serializado en disco + solo parsear archivos modificadosv4-02llama.cpp requiere CPU con AVX2 (faltante en CPUs anteriores a 2013)Fallback a build sin AVX2 detectado automáticamente (~3× más lento)v4-03EBCDIC tiene 15+ variantes (cp037, cp1047, cp500, cp1140…)Auto-detección estadística por frecuencia de caracteres; permitir override manual por archivov4-04COBOL con niveles (01, 05, 10, 15) pierde jerarquía al chunkear por líneasParser COBOL ANTLR preserva niveles como atributo del fragmentov4-05Un dominio cifrado con clave perdida se vuelve irrecuperableUI advierte al crear dominio: "escribe la passphrase de recuperación en papel ahora"v4-06HMAC por fila en Banking multiplica tamaño del índice 1.3×Aceptable trade-off; documentado en perfil Bankingv4-07FastCDC puede generar chunks muy pequeños para algunos archivosMin chunk size 256 bytes, max 8KB; si no hay boundary → forzar splitv4-08Plugin-SDK permite ejecutar código arbitrario de tercerosEn perfil Banking, plugins requieren hash en manifest firmado para cargarv4-09El glosario McComics podría colisionar con términos estándar (ej: "FR" = "French")Glosario es por proyecto, no global; se activa solo si el archivo está en el scope del proyectov4-10Active learning puede ser envenenado con feedback maliciosoLímite: cambios de peso acotados a ±20% del baseline; reset manual disponible

PARTE 13 — RECOMENDACIÓN ÓPTIMA
v4.0 es la versión que debes construir. Los cambios frente a v3.0 son estructurales pero no explosivos en complejidad:

El Polyglot Fabric de 4 niveles cubre COBOL, RPG, Natural, Fortran y literalmente cualquier archivo de texto sin sacrificar velocidad para lenguajes modernos.
Los 3 botones de perfil resuelven el dilema entre "fácil de usar" y "certificable" con un solo motor — el espíritu del proyecto intacto.
La integración de un LLM local de 1.5B parámetros convierte al Oráculo en una IA local completa sin romper el budget de RAM.
Las 18 mejoras M1-M18 atacan los puntos débiles que solo se ven en producción.

El sistema resultante:

Ultra preciso — 4 métodos fusionados con RRF + LLM re-ranker + golden tests continuos
Ultra rápido — cache semántico, mmap, FastCDC, incremental re-embedding
Ultra seguro — 3 perfiles, crypto-shredding, air-gap verificable, audit chain
Universal — desde COBOL de 1975 a Rust de 2026
Distribuible — instalador profesional multi-plataforma + bundle offline
Extensible — Plugin-SDK para nuevos lenguajes

Próximo paso recomendado
Antes de tocar código, crear estos 3 documentos de LEY que v4.0 requiere:

THREAT_MODEL_ORACULO_v4.md — modelo de amenazas explícito para cada perfil
POLYGLOT_FABRIC_SPEC.md — especificación formal de los 4 niveles de parsing y el formato del lexical skeleton
POLICY_ENGINE_SPEC.md — esquema YAML de los 3 perfiles con todas sus keys y valores permitidos

Con estos 3 documentos aprobados, la Fase 1 puede ejecutarse sin ambigüedad.

