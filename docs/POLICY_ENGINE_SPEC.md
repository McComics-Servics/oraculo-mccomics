📜 DOCUMENTO 2/6 — POLICY_ENGINE_SPEC.md

Clasificación: LEY — Especificación de Políticas
Versión: 1.0


1. Propósito
Define el esquema formal de los 3 archivos YAML de perfil (basic.yaml, enterprise.yaml, banking.yaml) y cómo el Policy Engine los carga, valida y aplica en caliente.

2. Ubicación y carga
db_storage/
└── profiles/
    ├── basic.yaml          ← empaquetado con el binario
    ├── enterprise.yaml     ← empaquetado con el binario
    ├── banking.yaml        ← empaquetado con el binario
    ├── active.txt          ← contiene el nombre del perfil activo
    └── history.jsonl       ← historial append-only de cambios
Los 3 archivos base son read-only y vienen firmados con el binario. El usuario puede crear overrides en profiles/custom_*.yaml (solo en Basic y Enterprise; Banking no permite overrides).

3. Esquema formal (JSON Schema)
yamlprofile_name: string (enum: basic|enterprise|banking|custom_*)
profile_version: integer (>=1)
schema_version: "1.0"
description: string

# === CRIPTOGRAFÍA ===
crypto:
  master_key_source:
    type: enum (os_keyring | passphrase | keyring_plus_passphrase | hsm)
    kdf: enum (none | pbkdf2_sha256 | argon2id)
    kdf_params:
      iterations: integer (for pbkdf2)
      memory_kb: integer (for argon2)
      parallelism: integer (for argon2)
      salt_bytes: integer (default 16)
  cipher: enum (aes_256_gcm)
  row_level_hmac: boolean
  domain_separation: boolean
  key_rotation_days: integer (0 = disabled)
  secure_delete: enum (os_remove | overwrite_1pass | crypto_shred)

# === TRANSPORTE ===
transport:
  ipc_native: boolean           # named pipe / unix socket
  http_loopback: boolean        # 127.0.0.1 only
  http_port_range: [int, int]
  cors_allowed_origins: [string]
  require_hmac_body: boolean
  require_nonce: boolean
  require_timestamp: boolean
  timestamp_skew_seconds: integer

# === RED EXTERNA ===
network:
  external_allowed: boolean
  allowlist_domains: [string]
  ip_pinning: boolean
  air_gap_verify: boolean        # M10 de v4
  air_gap_test_ip: string        # default 10.255.255.255

# === AUTENTICACIÓN ===
auth:
  token_ttl_seconds: integer
  token_rotation: enum (manual | automatic)
  passphrase_required: boolean
  passphrase_max_attempts: integer
  passphrase_backoff_strategy: enum (linear | exponential)
  second_factor: enum (none | yubikey | hsm_pin | file_token)

# === LOGGING ===
logging:
  level: enum (debug | info | warning | error)
  max_file_size_mb: integer
  backup_count: integer
  sanitize_paths: boolean
  sanitize_content: boolean
  content_max_chars: integer
  paranoid_mode: boolean        # solo IDs numéricos

# === AUDIT LOG ===
audit:
  enabled: boolean
  append_only: boolean
  hash_chain: boolean
  daily_seal: boolean
  export_format: enum (none | csv | json | signed_csv)

# === RATE LIMITING ===
rate_limit:
  queries_per_minute: integer
  queries_per_hour: integer
  burst_size: integer
  circuit_breaker_timeouts: integer
  query_timeout_seconds: number

# === ANOMALY DETECTION ===
anomaly_detection:
  enabled: boolean
  zscore_threshold: number
  distinct_queries_window: integer
  distinct_queries_max: integer
  action_on_detection: enum (log | warn | block_token | shutdown)

# === INTEGRIDAD ===
integrity:
  check_on_startup: enum (none | quick | full)
  check_interval_hours: integer  # 0 = disabled
  memory_locked_pages: boolean

# === LLM LOCAL ===
llm_local:
  allowed: boolean
  require_signed_manifest: boolean
  allowed_models: [string]
  max_ram_mb: integer
  gpu_allowed: boolean

# === GOLDEN TESTS ===
golden_tests:
  run_on_startup: boolean
  run_interval_hours: integer
  regression_threshold_percent: integer
  block_on_regression: boolean

# === BACKUPS ===
backups:
  enabled: boolean
  encryption: enum (none | same_key | secondary_key | signed)
  interval_hours: integer
  retention_count: integer

# === TELEMETRÍA ===
telemetry:
  enabled: boolean
  anonymous: boolean
  endpoint: string or null

# === UI ===
ui:
  show_audit_tab: boolean
  show_compliance_export: boolean
  allow_profile_downgrade: boolean
  require_passphrase_for_downgrade: boolean

# === SLOs OBJETIVO ===
slo:
  query_p50_ms: integer
  query_p95_ms: integer
  query_p99_ms: integer
  startup_cold_seconds: number
  ram_steady_mb: integer
  indexing_files_per_second: integer

4. Perfil BÁSICO (basic.yaml)
yamlprofile_name: basic
profile_version: 1
schema_version: "1.0"
description: "Velocidad y simplicidad para desarrollo individual"

crypto:
  master_key_source:
    type: os_keyring
    kdf: none
  cipher: aes_256_gcm
  row_level_hmac: false
  domain_separation: true
  key_rotation_days: 0
  secure_delete: os_remove

transport:
  ipc_native: true
  http_loopback: true
  http_port_range: [8888, 8898]
  cors_allowed_origins: ["http://localhost"]
  require_hmac_body: false
  require_nonce: false
  require_timestamp: false
  timestamp_skew_seconds: 300

network:
  external_allowed: true
  allowlist_domains: ["huggingface.co", "github.com"]
  ip_pinning: false
  air_gap_verify: false

auth:
  token_ttl_seconds: 2592000       # 30 días
  token_rotation: manual
  passphrase_required: false
  passphrase_max_attempts: 10
  passphrase_backoff_strategy: linear
  second_factor: none

logging:
  level: info
  max_file_size_mb: 5
  backup_count: 3
  sanitize_paths: false
  sanitize_content: false
  content_max_chars: 200
  paranoid_mode: false

audit:
  enabled: true
  append_only: false
  hash_chain: false
  daily_seal: false
  export_format: csv

rate_limit:
  queries_per_minute: 300
  queries_per_hour: 10000
  burst_size: 20
  circuit_breaker_timeouts: 5
  query_timeout_seconds: 5.0

anomaly_detection:
  enabled: false
  zscore_threshold: 3.0
  distinct_queries_window: 600
  distinct_queries_max: 200
  action_on_detection: log

integrity:
  check_on_startup: quick
  check_interval_hours: 0
  memory_locked_pages: false

llm_local:
  allowed: true
  require_signed_manifest: false
  allowed_models: ["*"]
  max_ram_mb: 2048
  gpu_allowed: true

golden_tests:
  run_on_startup: false
  run_interval_hours: 0
  regression_threshold_percent: 20
  block_on_regression: false

backups:
  enabled: false
  encryption: none
  interval_hours: 0
  retention_count: 0

telemetry:
  enabled: false
  anonymous: true
  endpoint: null

ui:
  show_audit_tab: false
  show_compliance_export: false
  allow_profile_downgrade: true
  require_passphrase_for_downgrade: false

slo:
  query_p50_ms: 80
  query_p95_ms: 150
  query_p99_ms: 300
  startup_cold_seconds: 2.0
  ram_steady_mb: 500
  indexing_files_per_second: 60

5. Perfil EMPRESARIAL (enterprise.yaml)
yamlprofile_name: enterprise
profile_version: 1
schema_version: "1.0"
description: "Equilibrio profesional para equipos y PYMES"

crypto:
  master_key_source:
    type: keyring_plus_passphrase
    kdf: argon2id
    kdf_params:
      memory_kb: 32768           # 32 MB
      iterations: 2
      parallelism: 2
      salt_bytes: 16
  cipher: aes_256_gcm
  row_level_hmac: false
  domain_separation: true
  key_rotation_days: 90
  secure_delete: overwrite_1pass

transport:
  ipc_native: true
  http_loopback: true
  http_port_range: [8888, 8898]
  cors_allowed_origins: []       # solo IPC nativo para UI
  require_hmac_body: true
  require_nonce: false
  require_timestamp: true
  timestamp_skew_seconds: 60

network:
  external_allowed: true
  allowlist_domains: []          # usuario define explícitamente
  ip_pinning: false
  air_gap_verify: false

auth:
  token_ttl_seconds: 86400       # 24h
  token_rotation: automatic
  passphrase_required: false     # opcional
  passphrase_max_attempts: 5
  passphrase_backoff_strategy: exponential
  second_factor: none

logging:
  level: info
  max_file_size_mb: 10
  backup_count: 5
  sanitize_paths: true
  sanitize_content: true
  content_max_chars: 40
  paranoid_mode: false

audit:
  enabled: true
  append_only: true
  hash_chain: true
  daily_seal: false
  export_format: signed_csv

rate_limit:
  queries_per_minute: 60
  queries_per_hour: 2000
  burst_size: 10
  circuit_breaker_timeouts: 3
  query_timeout_seconds: 3.0

anomaly_detection:
  enabled: true
  zscore_threshold: 2.5
  distinct_queries_window: 600
  distinct_queries_max: 150
  action_on_detection: warn

integrity:
  check_on_startup: full
  check_interval_hours: 24
  memory_locked_pages: false

llm_local:
  allowed: true
  require_signed_manifest: true
  allowed_models:
    - "qwen2.5-0.5b-instruct-q5"
    - "qwen2.5-1.5b-instruct-q5"
    - "phi-3-mini-q4"
    - "gemma-2-2b-q5"
  max_ram_mb: 3072
  gpu_allowed: false

golden_tests:
  run_on_startup: true
  run_interval_hours: 12
  regression_threshold_percent: 10
  block_on_regression: false

backups:
  enabled: true
  encryption: secondary_key
  interval_hours: 24
  retention_count: 7

telemetry:
  enabled: false
  anonymous: true
  endpoint: null

ui:
  show_audit_tab: true
  show_compliance_export: true
  allow_profile_downgrade: true
  require_passphrase_for_downgrade: true

slo:
  query_p50_ms: 150
  query_p95_ms: 280
  query_p99_ms: 450
  startup_cold_seconds: 3.0
  ram_steady_mb: 750
  indexing_files_per_second: 50

6. Perfil BANCARIO (banking.yaml)
yamlprofile_name: banking
profile_version: 1
schema_version: "1.0"
description: "Paranoia verificable para entornos críticos"

crypto:
  master_key_source:
    type: keyring_plus_passphrase
    kdf: argon2id
    kdf_params:
      memory_kb: 65536           # 64 MB
      iterations: 3
      parallelism: 4
      salt_bytes: 32
  cipher: aes_256_gcm
  row_level_hmac: true
  domain_separation: true
  key_rotation_days: 30
  secure_delete: crypto_shred

transport:
  ipc_native: true
  http_loopback: false           # solo IPC nativo
  http_port_range: [0, 0]
  cors_allowed_origins: []
  require_hmac_body: true
  require_nonce: true
  require_timestamp: true
  timestamp_skew_seconds: 30

network:
  external_allowed: false
  allowlist_domains: []
  ip_pinning: true
  air_gap_verify: true
  air_gap_test_ip: "10.255.255.255"

auth:
  token_ttl_seconds: 3600        # 1h
  token_rotation: automatic
  passphrase_required: true
  passphrase_max_attempts: 3
  passphrase_backoff_strategy: exponential
  second_factor: file_token      # puede escalar a yubikey/hsm

logging:
  level: warning
  max_file_size_mb: 20
  backup_count: 10
  sanitize_paths: true
  sanitize_content: true
  content_max_chars: 0           # cero contenido
  paranoid_mode: true

audit:
  enabled: true
  append_only: true
  hash_chain: true
  daily_seal: true
  export_format: signed_csv

rate_limit:
  queries_per_minute: 30
  queries_per_hour: 1000
  burst_size: 5
  circuit_breaker_timeouts: 2
  query_timeout_seconds: 2.0

anomaly_detection:
  enabled: true
  zscore_threshold: 2.0
  distinct_queries_window: 300
  distinct_queries_max: 50
  action_on_detection: block_token

integrity:
  check_on_startup: full
  check_interval_hours: 6
  memory_locked_pages: true

llm_local:
  allowed: true
  require_signed_manifest: true
  allowed_models:
    - "qwen2.5-1.5b-instruct-q5-signed"
    - "phi-3-mini-q4-signed"
  max_ram_mb: 3072
  gpu_allowed: false

golden_tests:
  run_on_startup: true
  run_interval_hours: 6
  regression_threshold_percent: 5
  block_on_regression: true

backups:
  enabled: true
  encryption: signed
  interval_hours: 12
  retention_count: 14

telemetry:
  enabled: false                 # físicamente imposible
  anonymous: false
  endpoint: null

ui:
  show_audit_tab: true
  show_compliance_export: true
  allow_profile_downgrade: true
  require_passphrase_for_downgrade: true

slo:
  query_p50_ms: 280
  query_p95_ms: 500
  query_p99_ms: 800
  startup_cold_seconds: 5.0
  ram_steady_mb: 1100
  indexing_files_per_second: 40

7. Validación al cargar
Al iniciar el daemon o al cambiar de perfil, el Policy Engine ejecuta:
1. Leer YAML del perfil
2. Validar contra JSON Schema (estructura y tipos)
3. Validar rangos semánticos (ej: token_ttl > 0)
4. Validar coherencia cruzada:
   - Si anomaly_detection.enabled → audit.enabled debe ser true
   - Si paranoid_mode → sanitize_* deben ser true
   - Si air_gap_verify → external_allowed debe ser false
   - Si row_level_hmac → integrity.check_on_startup debe ser full
5. Verificar firma del perfil (Enterprise/Banking)
6. Aplicar en caliente (sin reiniciar)
7. Registrar cambio en profiles/history.jsonl
8. Notificar a todos los subsistemas vía observer pattern
Si alguna validación falla, el sistema permanece en el perfil anterior y reporta el error en la UI con razón específica.

8. Cambio de perfil en caliente
pythonclass PolicyEngine:
    def switch_profile(self, target: str, passphrase: str | None = None) -> Result:
        # 1. Cargar perfil destino
        new_profile = self.load_and_validate(target)
        
        # 2. Determinar si es upgrade o downgrade
        is_downgrade = self._is_downgrade(self.current, new_profile)
        
        # 3. Si downgrade: exigir passphrase + confirmación
        if is_downgrade and new_profile.ui.require_passphrase_for_downgrade:
            if not self._verify_passphrase(passphrase):
                return Result.fail("Passphrase inválida")
        
        # 4. Re-cifrar índice si cambia la estrategia criptográfica
        if self._crypto_changed(self.current, new_profile):
            self._reencrypt_index(new_profile)
        
        # 5. Rotar tokens si cambia política de auth
        if self._auth_changed(self.current, new_profile):
            self._rotate_all_tokens(new_profile)
        
        # 6. Notificar subsistemas
        for subscriber in self._subscribers:
            subscriber.on_profile_change(self.current, new_profile)
        
        # 7. Registrar en history
        self._append_history({
            "from": self.current.profile_name,
            "to": new_profile.profile_name,
            "timestamp": now_iso(),
            "is_downgrade": is_downgrade,
            "triggered_by": "ui|cli|api"
        })
        
        # 8. Activar
        self.current = new_profile
        return Result.ok()

9. Overrides (solo Basic y Enterprise)
El usuario puede crear profiles/custom_basic_strict.yaml con solo los campos que quiere sobrescribir:
yamlprofile_name: custom_basic_strict
inherits_from: basic
profile_version: 1
schema_version: "1.0"

# solo los overrides
rate_limit:
  queries_per_minute: 100
logging:
  sanitize_content: true
El Policy Engine fusiona con el perfil base. Banking no permite overrides — su configuración es inmutable para defender la certificación.

10. Tabla de compatibilidad entre perfiles
CaracterísticaBasic → EnterpriseEnterprise → BankingDowngradeRe-cifrado del índice✅ requerido✅ requerido✅ requeridoRotación de tokens✅✅✅Confirmación del usuario❌✅ passphrase✅ passphraseTiempo estimado~10s por GB~30s por GB~30s por GBReversible automáticamente——❌ no, requiere flujo formal

11. Tests del Policy Engine
Batería obligatoria que debe pasar antes de cualquier release:
✓ Cargar cada perfil base individualmente
✓ Switching Basic → Enterprise → Banking y vuelta
✓ Rechazar perfil con campos faltantes
✓ Rechazar perfil con firma inválida (Enterprise/Banking)
✓ Rechazar override de Banking
✓ Verificar validaciones cruzadas (6 reglas)
✓ Verificar rollback si switch falla a mitad
✓ Verificar notificación a todos los subscribers
✓ Verificar que history.jsonl crece correctamente
✓ Verificar comportamiento ante YAML malformado
✓ Verificar thread-safety del switch en caliente
✓ Benchmark de tiempo de switch (<2s objetivo)

12. Observaciones finales

Los perfiles son la única configuración de seguridad del sistema. No hay flags adicionales en código.
El código núcleo no sabe qué perfil está activo — solo consulta al Policy Engine.
Cualquier nueva funcionalidad debe declarar sus requisitos en el schema del perfil.
Auditoría externa debe poder leer los 3 YAML y entender las garantías del sistema sin leer código.


✅ Entrega 1/3 completada
Documentos entregados:

✅ THREAT_MODEL_ORACULO_v4.md — modelo de amenazas completo con 15 amenazas, matriz STRIDE, trust tiers y proceso de respuesta a incidentes
✅ POLICY_ENGINE_SPEC.md — esquema formal + los 3 perfiles YAML completos + validación + switching en caliente

Próxima entrega (2/3):
3. POLYGLOT_FABRIC_SPEC.md — los 4 niveles de parsing, lexical skeleton, copybooks, encoding detection, parsers por lenguaje
4. CONTEXT_ASSEMBLY_POLICY.md — RRF, budget jerárquico, SimHash dedup, glosario, trust tiers en payload
