📜 DOCUMENTO 5/6 — API_CONTRACT_SPEC.md

Clasificación: LEY — Contrato de API
Versión: 1.0
Propietario: McComics Servicios Generales
Fecha: 2026-04-14


1. Propósito
Define el contrato exacto entre el daemon Oráculo y todos sus clientes (UI pywebview, CLI mccomics_brain, IAs externas vía HTTP, integraciones futuras). Cualquier cambio en este contrato requiere bump de api_version y plan de migración.

2. Modelos de transporte
2.1 Tabla por perfil
PerfilIPC nativoHTTP loopbackWebSocketBasic✅ default✅ opcional✅ opcionalEnterprise✅ default✅ con HMAC obligatorio❌Banking✅ exclusivo❌ deshabilitado❌
2.2 IPC nativo (preferido siempre)
OSMecanismoPathWindowsNamed pipe\\.\pipe\oraculo_mccomics_<user_sid>LinuxUnix domain socket$XDG_RUNTIME_DIR/oraculo_mccomics.sockmacOSUnix domain socket~/Library/Caches/oraculo_mccomics.sock
Permisos: 0600 (solo el usuario propietario).
2.3 HTTP loopback (opcional Basic/Enterprise)

Bind exclusivo a 127.0.0.1 (nunca 0.0.0.0)
Puerto en rango 8888-8898, primer libre
Puerto activo escrito en db_storage/active_port.txt (chmod 0600)
TLS no requerido (loopback) pero opcional con certificado auto-firmado almacenado en keyring

2.4 Protocolo de mensajes (IPC)
Frame format binario simple:
┌──────────┬──────────┬─────────────┬──────────┐
│ Magic    │ Version  │ Payload Len │ Payload  │
│ 4 bytes  │ 1 byte   │ 4 bytes BE  │ N bytes  │
│ "ORCL"   │ 0x01     │             │ JSON UTF8│
└──────────┴──────────┴─────────────┴──────────┘
Magic byte ORCL evita confusiones con otros protocolos. Version permite evolución sin romper.

3. Autenticación
3.1 Tokens
python@dataclass
class Token:
    token_id: str           # uuid v4
    secret: bytes           # 32 bytes random
    created_at: datetime
    expires_at: datetime
    profile: str            # basic|enterprise|banking
    scopes: list[str]       # ['query', 'index', 'admin']
    issued_to: str          # 'ui'|'cli'|'external_<name>'
3.2 Header de autenticación
Basic:
X-Oraculo-Token: <token_id>:<secret_b64>
Enterprise:
X-Oraculo-Token: <token_id>:<secret_b64>
X-Oraculo-Timestamp: 1744636951
X-Oraculo-HMAC: <hmac_sha256(timestamp + body, secret)>
Banking:
X-Oraculo-Token: <token_id>:<secret_b64>
X-Oraculo-Timestamp: 1744636951
X-Oraculo-Nonce: <random_16_bytes_b64>
X-Oraculo-HMAC: <hmac_sha256(timestamp + nonce + body, secret)>
El servidor mantiene un set de nonces vistos en los últimos 60s para rechazar replay.
3.3 Generación inicial del primer token
Al primer arranque del daemon:

Genera token raíz con scope admin
Lo escribe encriptado en db_storage/root_token.enc (cifrado con clave maestra)
La UI lo lee al iniciar y lo desbloquea con la clave del keyring
La CLI usa el mismo mecanismo


4. Endpoints completos
4.1 Salud y diagnóstico
GET /v1/health
Estado del daemon. No requiere autenticación. Útil para monitoreo externo.
Response 200:
json{
  "api_version": "1.0",
  "daemon_version": "4.0.0",
  "status": "healthy",
  "profile_active": "enterprise",
  "uptime_seconds": 18432,
  "timestamp": "2026-04-14T15:22:31Z",
  
  "checks": {
    "sqlite": "ok",
    "duckdb": "ok",
    "vector_index": "ok",
    "llm_local": "ok",
    "audit_log_chain": "ok",
    "memory_lock": "ok",
    "air_gap": "verified"
  },
  
  "stats": {
    "indexed_files": 4827,
    "indexed_fragments": 38291,
    "stale_count": 12,
    "stale_percent": 0.31,
    "domains_active": 3,
    "queries_last_hour": 47,
    "ram_mb": 712,
    "cpu_percent_avg": 8.2
  },
  
  "warnings": [],
  "degraded_mode": false
}
Códigos posibles:

200 healthy
503 unhealthy (con campo failures)

GET /v1/diagnostics (requiere admin)
Diagnóstico extenso para la pestaña Dependencies.
Response 200:
json{
  "python_version": "3.11.7",
  "platform": "Windows-11-10.0.22631-SP0",
  "webview2": {"present": true, "version": "131.0.2903"},
  "tree_sitter": {"compiled": true, "python_version_match": true},
  "duckdb_version": "0.10.1",
  "duckdb_extensions": ["vector"],
  "sqlite": {"version": "3.45.0", "fts5": true},
  "onnx_runtime": {"version": "1.17", "providers": ["CPUExecutionProvider"]},
  "llama_cpp": {"version": "0.2.50", "avx2": true, "models_available": ["qwen-1.5b", "phi-3-mini"]},
  "encoding_libs": ["chardet", "charset_normalizer"],
  "antlr_runtime": "4.13",
  "fingerprint_factors": {"cpu_id": true, "volume_uuid": true, "hostname": true}
}

4.2 Consultas (núcleo)
POST /v1/query
La operación principal del Oráculo. Devuelve fragmentos relevantes ensamblados.
Request:
json{
  "query": "como funciona el escalador",
  "scope": ["src/plugins/escalador/"],
  "domains": ["code"],
  "max_results": 10,
  "min_trust_tier": 2,
  "budget_tokens": 8000,
  "format": "json",
  "options": {
    "use_llm_rerank": true,
    "use_query_expansion": true,
    "include_call_graph": true,
    "include_metadata": true,
    "strict": false,
    "show_duplicates": false,
    "language_filter": null,
    "parser_level_min": "L4"
  }
}
Campos opcionales (todos tienen default sensato).
Response 200: Ver schema completo en CONTEXT_ASSEMBLY_POLICY.md sección 13.
Códigos de error específicos:
CódigoSignificadoAcción cliente400Query mal formadaCorregir401Token inválidoRe-autenticar403Scope fuera de autorizaciónPedir permiso al usuario413Query demasiado larga (>2KB)Acortar429Rate limitEsperar y reintentar503Daemon en modo degradadoReintentar más tarde507INDEX_TOO_STALE (Banking)Reindexar
POST /v1/query/stream
Variante streaming via Server-Sent Events. Devuelve fragmentos conforme se ensamblan.
Request: Igual que /v1/query.
Response (text/event-stream):
event: meta
data: {"query_id":"uuid","profile":"enterprise","total_budget":8000}

event: fragment
data: {"id":"frag_a3f2","trust_tier":1,"layer":"L0","content":"..."}

event: fragment
data: {"id":"frag_b7e1","trust_tier":1,"layer":"L1","content":"..."}

event: stats
data: {"used_tokens":3421,"remaining":4579}

event: warning
data: {"code":"STALE_DETECTED","count":2}

event: complete
data: {"total_ms":274,"fragment_count":8}
GET /v1/context
Variante simplificada para pegar en chats externos. Devuelve markdown listo para copiar.
Query params:

query (requerido)
scope (CSV)
format (markdown|plain|json)
min_trust_tier (1|2|3)

Response 200:

Content-Type: text/markdown; charset=utf-8
Body: ver formato en CONTEXT_ASSEMBLY_POLICY.md sección 14


4.3 Indexación
POST /v1/index/scan
Inicia escaneo de carpetas autorizadas.
Request:
json{
  "domain": "code",
  "paths": ["./src/", "./plugins/"],
  "incremental": true,
  "force_reindex": false
}
Response 202 (async):
json{
  "job_id": "scan_xyz789",
  "status": "queued",
  "eta_seconds": 84
}
GET /v1/index/jobs/{job_id}
Estado de un job.
Response 200:
json{
  "job_id": "scan_xyz789",
  "status": "running",
  "progress_percent": 47,
  "files_processed": 2284,
  "files_total": 4827,
  "files_per_second": 52,
  "fragments_added": 18203,
  "fragments_updated": 421,
  "errors": [],
  "warnings": [
    {"file": "file:abc", "code": "ENCODING_FALLBACK", "details": "cp1047"}
  ]
}
POST /v1/index/jobs/{job_id}/cancel
Cancela un job en curso.
GET /v1/index/domains
Lista los dominios configurados.
Response 200:
json{
  "domains": [
    {
      "name": "code",
      "paths": ["./src/", "./plugins/"],
      "files_indexed": 4827,
      "fragments": 38291,
      "size_mb": 142,
      "encryption_key_id": "key_a3f",
      "last_scan": "2026-04-14T08:00:00Z"
    }
  ]
}
POST /v1/index/domains (admin)
Crea un nuevo dominio.
Request:
json{
  "name": "docs_internal",
  "paths": ["./internal_docs/"],
  "encryption": "separate_key",
  "passphrase_hint": "Documentación confidencial"
}
DELETE /v1/index/domains/{name} (admin)
Elimina dominio. En Banking, ejecuta crypto-shredding.
Request:
json{
  "confirm": true,
  "passphrase": "..."
}
POST /v1/index/reindex (admin)
Reindexación completa de un dominio.

4.4 Perfil de seguridad
GET /v1/profile
Perfil activo y resumen.
Response 200:
json{
  "profile_active": "enterprise",
  "profile_version": 1,
  "switched_at": "2026-04-10T14:22:00Z",
  "switched_by": "ui",
  "available_profiles": ["basic", "enterprise", "banking"],
  "downgrade_allowed": true,
  "downgrade_requires_passphrase": true
}
POST /v1/profile/switch (admin)
Cambia perfil en caliente.
Request:
json{
  "target": "banking",
  "passphrase": "...",
  "confirm": true
}
Response 200:
json{
  "previous": "enterprise",
  "current": "banking",
  "reencryption_required": true,
  "reencryption_eta_seconds": 42,
  "tokens_rotated": 3
}
GET /v1/profile/history
Historial de cambios de perfil.

4.5 Auditoría
GET /v1/audit/log (Enterprise/Banking, admin)
Query params:

from ISO datetime
to ISO datetime
limit (default 100, max 1000)
event_type (query|index|profile_change|auth_failure|anomaly)

Response 200:
json{
  "events": [
    {
      "audit_id": "audit_xyz",
      "timestamp": "2026-04-14T15:22:31Z",
      "event_type": "query",
      "actor": "token_abc",
      "details": {"query_hash": "sha256:...", "results_count": 8},
      "hmac_chain_prev": "sha256:...",
      "hmac_chain_current": "sha256:..."
    }
  ],
  "chain_verified": true,
  "total_count": 1842
}
GET /v1/audit/export (Enterprise/Banking)
Exporta CSV firmado para compliance.
Query params:

from, to
format (csv|signed_csv|json)

Response 200:

Content-Type: application/octet-stream
Content-Disposition: attachment; filename="audit_2026-04.csv.sig"

POST /v1/audit/verify (admin)
Verifica integridad de la cadena hash.

4.6 LLM local
GET /v1/llm/models
Modelos disponibles y descargados.
Response 200:
json{
  "available": [
    {
      "id": "qwen2.5-1.5b-instruct-q5",
      "name": "Qwen 2.5 1.5B Instruct Q5",
      "size_mb": 1024,
      "ram_mb": 1400,
      "downloaded": true,
      "loaded": true,
      "signed": true
    }
  ],
  "active_model": "qwen2.5-1.5b-instruct-q5"
}
POST /v1/llm/download (admin)
Descarga modelo. Async (devuelve job_id).
POST /v1/llm/switch (admin)
Cambia modelo activo.
POST /v1/llm/generate (opcional, no usado por el núcleo)
Generación directa con el LLM local. Útil para integraciones.

4.7 Glosario y configuración
GET /v1/glossary
POST /v1/glossary (admin)
json{
  "terms": {
    "RF": "refuerzo",
    "C45": "corte 45 grados",
    "FR": "frente"
  }
}
GET /v1/config
Lee configuración no sensible.
POST /v1/config (admin)
Modifica configuración no sensible (rate limits dentro del rango del perfil, etc.).

4.8 Feedback y aprendizaje
POST /v1/feedback
Registra feedback 👍/👎 sobre un fragmento.
Request:
json{
  "query_id": "uuid",
  "fragment_id": "frag_a3f2",
  "rating": "up",
  "comment": "preciso"
}
GET /v1/feedback/stats
Estadísticas para la pestaña Cognitive.

4.9 Golden tests
GET /v1/golden
Lista golden tests configurados.
POST /v1/golden
Captura una query actual como golden test.
POST /v1/golden/run
Ejecuta toda la suite. Retorna métricas de regresión.

4.10 Tokens
GET /v1/tokens (admin)
Lista tokens activos.
POST /v1/tokens (admin)
Genera nuevo token.
json{
  "scopes": ["query"],
  "ttl_seconds": 86400,
  "issued_to": "external_vscode_extension"
}
DELETE /v1/tokens/{token_id} (admin)
Revoca token inmediatamente.

4.11 Shutdown
POST /v1/shutdown (admin)
Apagado graceful del daemon.
json{
  "force": false,
  "timeout_seconds": 10
}

5. Schemas request/response (resumen JSON Schema)
json{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://oraculo.mccomics.com/schemas/v1/query_request.json",
  "type": "object",
  "required": ["query"],
  "properties": {
    "query": {"type": "string", "minLength": 1, "maxLength": 2000},
    "scope": {"type": "array", "items": {"type": "string"}},
    "domains": {"type": "array", "items": {"type": "string"}},
    "max_results": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
    "min_trust_tier": {"type": "integer", "enum": [1, 2, 3], "default": 2},
    "budget_tokens": {"type": "integer", "minimum": 500, "maximum": 32000, "default": 8000},
    "format": {"type": "string", "enum": ["json", "markdown", "plain"], "default": "json"},
    "options": {
      "type": "object",
      "properties": {
        "use_llm_rerank": {"type": "boolean", "default": true},
        "use_query_expansion": {"type": "boolean", "default": true},
        "include_call_graph": {"type": "boolean", "default": true},
        "include_metadata": {"type": "boolean", "default": true},
        "strict": {"type": "boolean", "default": false},
        "show_duplicates": {"type": "boolean", "default": false},
        "language_filter": {"type": ["string", "null"]},
        "parser_level_min": {"type": "string", "enum": ["L1", "L2", "L3", "L4"], "default": "L4"}
      }
    }
  }
}
Schemas completos en schemas/v1/*.json del repo, validados con jsonschema en cada request.

6. Versionado de API
Todos los endpoints viven bajo /v1/. Cuando se rompa compatibilidad → /v2/. Los daemons soportan ambas versiones simultáneamente durante un período de gracia mínimo de 6 meses.
Header opcional para negociación:
Accept: application/vnd.oraculo.v1+json
Si el servidor no soporta la versión solicitada → 406 Not Acceptable con campo supported_versions.

7. Códigos de error estandarizados
json{
  "error": {
    "code": "INDEX_TOO_STALE",
    "message_es": "El índice tiene 12% de entradas obsoletas. Reindexar requerido.",
    "message_en": "Index has 12% stale entries. Reindex required.",
    "details": {
      "stale_count": 487,
      "total_count": 38291,
      "stale_percent": 12.7
    },
    "request_id": "req_abc123",
    "documentation_url": "https://docs.oraculo.mccomics.com/errors/INDEX_TOO_STALE"
  }
}
7.1 Catálogo
CódigoHTTPSignificadoINVALID_QUERY400Query mal formadaMISSING_REQUIRED_FIELD400Campo obligatorio ausenteAUTH_TOKEN_INVALID401Token inválido o expiradoAUTH_HMAC_MISMATCH401HMAC del cuerpo no coincideAUTH_TIMESTAMP_SKEW401Timestamp fuera de ventanaAUTH_NONCE_REPLAY401Nonce ya usado (Banking)SCOPE_DENIED403Path fuera del scope autorizadoPROFILE_OPERATION_FORBIDDEN403Operación no permitida en este perfilRESOURCE_NOT_FOUND404Job, dominio o token no existePAYLOAD_TOO_LARGE413Request supera límiteRATE_LIMITED429Cuota excedidaDAEMON_DEGRADED503Funcionalidad reducida temporalDAEMON_SHUTTING_DOWN503Apagado en cursoINDEX_TOO_STALE507Más del 10% obsoleto (Banking)INDEX_CORRUPTED507Verificación de integridad fallóANOMALY_DETECTED423Token bloqueado por anomaly detectionAIR_GAP_VIOLATION451Conexión externa detectada (Banking)

8. Rate limiting (HTTP headers)
Toda respuesta incluye:
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 47
X-RateLimit-Reset: 1744636960
X-RateLimit-Profile: enterprise
En 429:
Retry-After: 12

9. CORS (solo HTTP loopback, Basic/Enterprise)
Configuración fija (no editable por usuario):
pythonCORSMiddleware(
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["X-Oraculo-Token", "X-Oraculo-Timestamp", "X-Oraculo-HMAC", "X-Oraculo-Nonce", "Content-Type"],
    allow_credentials=False,
    max_age=600,
)
Nunca se permite origin null (corrige FALLO-A12 de v3).

10. Cliente Python oficial
Distribuido como módulo del propio Oráculo, usable desde scripts del usuario:
pythonfrom oraculo.client import OraculoClient

client = OraculoClient.from_keyring()  # auto-descubre IPC y token

result = client.query(
    "como funciona el escalador",
    scope=["src/plugins/escalador/"],
    min_trust_tier=2,
)

for fragment in result.fragments:
    print(f"[T{fragment.trust_tier}] {fragment.name}: {fragment.content[:80]}")
API del cliente:
pythonclass OraculoClient:
    @classmethod
    def from_keyring(cls) -> 'OraculoClient': ...
    @classmethod
    def from_token(cls, token: str, transport: str = "auto") -> 'OraculoClient': ...
    
    def query(self, q: str, **kwargs) -> QueryResult: ...
    def query_stream(self, q: str, **kwargs) -> Iterator[Fragment]: ...
    def context(self, q: str, format: str = "markdown") -> str: ...
    def health(self) -> HealthStatus: ...
    def feedback(self, query_id: str, fragment_id: str, rating: str): ...

11. Tests obligatorios del API
✓ Health endpoint sin auth
✓ Query con auth válida → 200
✓ Query sin auth → 401
✓ Query con HMAC inválido (Enterprise) → 401
✓ Query con nonce repetido (Banking) → 401
✓ Query con timestamp skewed → 401
✓ Query fuera de scope → 403
✓ Query excediendo rate limit → 429 con Retry-After
✓ Streaming SSE entrega eventos en orden
✓ Index scan async devuelve job_id válido
✓ Profile switch downgrade sin passphrase → 403
✓ Profile switch downgrade con passphrase → 200 + reencryption
✓ Audit log retorna eventos con cadena HMAC válida
✓ Tokens admin solo accesibles con scope admin
✓ Shutdown graceful no corrompe DB
✓ CORS rechaza origin null
✓ IPC nativo funciona en Win/Linux/Mac
✓ Cliente Python descubre transporte automáticamente
✓ JSON Schema validation rechaza requests malformados
✓ Versionado: header v2 inexistente → 406

12. Resumen ejecutivo
El contrato de API es el único punto de entrada al Oráculo. Ningún cliente lee directamente la base de datos. Esta separación garantiza que el Policy Engine intercepte cada operación, que el audit log capture toda actividad relevante, y que los cambios internos del sistema no rompan integraciones externas. El versionado explícito /v1/, /v2/ y los headers de negociación permiten evolución sin fricción.

