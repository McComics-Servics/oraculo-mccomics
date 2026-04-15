📜 DOCUMENTO 1/6 — THREAT_MODEL_ORACULO_v4.md

Clasificación: LEY — Blueprint de Seguridad
Versión: 1.0
Propietario: McComics Servicios Generales
Fecha: 2026-04-14


1. Propósito
Este documento define qué protege el Oráculo, contra quién, y qué NO garantiza. Todo el código del sistema debe respetar estas afirmaciones. Las excepciones deben documentarse explícitamente como desviaciones conscientes.

2. Activos a proteger (en orden de criticidad)
#ActivoDescripciónCriticidadA1Código fuente indexadoArchivos del usuario: plugins, melamina, aplicaciones, algoritmos propietarios🔴 CríticoA2Índice vectorial y léxicoDuckDB + SQLite con representaciones del código🔴 CríticoA3Clave maestraClave de cifrado del índice🔴 CríticoA4Audit logRegistro de consultas (en Enterprise/Banking)🟠 AltoA5Glosario McComicsTérminos propietarios (RF, C45, etc.)🟠 AltoA6Configuración de dominiosMapeo carpeta → clave🟠 AltoA7Tokens de APICredenciales de acceso al daemon🟠 AltoA8Pesos RRF aprendidosAfinamiento por feedback🟡 MedioA9Golden testsSuite de regresión🟡 MedioA10Modelos LLM descargadosGGUF de Qwen, Phi, etc.🟢 Bajo

3. Actores amenaza (Threat Actors)
IDActorCapacidadesRelevante enT1Usuario curiosoVe la UI, puede acceder a archivos en disco con sus permisosBasic+T2Malware de usuarioEjecuta código con permisos del usuario, lee archivos sin permisos adminBasic+T3Malware con persistenciaInstalado en sistema, sobrevive reiniciosEnterprise+T4Compañero de trabajo con acceso físicoPuede tomar prestada la laptop desbloqueada durante minutosEnterprise+T5Atacante de red localMITM en la misma LAN, sniff de tráfico loopbackEnterprise+T6Supply chain attackerCompromete PyPI, GitHub releases, mirrors corporativosTodosT7Insider con credencialesEmpleado legítimo que excede su scope autorizadoBankingT8Atacante forense post-roboObtiene disco duro apagado después de robo físicoBankingT9Actor estatalNSA-level, 0-days, hardware compromise🚫 Fuera de alcanceT10Atacante con acceso root/admin persistenteControl total del sistema operativo🚫 Fuera de alcance

4. Aplicación de STRIDE por activo
STRIDE = Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege.
4.1 Matriz resumen
ActivoSTRIDEA1 Código fuente⚪🟢⚪🔴🟡⚪A2 Índice🟢🔴🟡🔴🟡⚪A3 Clave maestra🟢🔴⚪🔴🟢🔴A4 Audit log🟡🔴🔴🟡🟢⚪A5 Glosario⚪🟡⚪🟡⚪⚪A7 Tokens API🔴🟡🟡🔴🟢🔴
🔴 = amenaza crítica, 🟡 = moderada, 🟢 = baja, ⚪ = no aplica
4.2 Mitigaciones principales
A3 · Clave maestra — Information disclosure

Basic: Windows DPAPI / macOS Keychain / Linux libsecret
Enterprise: DPAPI + passphrase opcional en HKDF
Banking: Argon2id con passphrase obligatoria (iteraciones=3, memoria=64MB, paralelismo=4) + factor YubiKey/HSM opcional
Nunca derivar la clave del fingerprint de hardware (corrección de FALLO-A10 de v3)
Nunca escribir la clave en disco en claro
Nunca loggear la clave, ni siquiera en modo debug

A2 · Índice — Tampering

Basic: cifrado AES-256-GCM con nonce único por bloque
Enterprise: cifrado + checksum SHA-256 por tabla
Banking: cifrado + HMAC-SHA256 por fila con la clave maestra
Al leer: verificación obligatoria antes de servir resultados

A7 · Tokens API — Spoofing / Elevation

Basic: token estático almacenado en keyring (TTL 30 días)
Enterprise: tokens rotativos cada 24h firmados con HMAC
Banking: tokens cada 1h + HMAC del cuerpo de cada request + timestamp + nonce anti-replay

A4 · Audit log — Repudiation

Basic: log simple con rotación
Enterprise: log append-only + hash encadenado
Banking: hash encadenado + sello diario externo opcional (archivo .seal firmado con clave separada)


5. Amenazas específicas y defensas
TH-01 · Exfiltración por consulta sistemática
Descripción: Un malware con acceso al token API ejecuta 10.000 queries para reconstruir el código.
Defensa Basic: Rate limit 300 q/min.
Defensa Enterprise: Rate limit 60 q/min + audit log + detección básica.
Defensa Banking: Rate limit 30 q/min + z-score sobre distribución de queries + bloqueo automático al detectar anomalía + notificación en UI.
TH-02 · Prompt injection diferida vía archivos maliciosos
Descripción: Atacante coloca un .md con instrucciones disfrazadas. Al indexarse, el contenido fluye como contexto a una IA externa.
Defensa universal: Todo fragmento entregado lleva trust_tier y language. El sistema nunca presenta contenido como instrucción. La IA consumidora recibe el contexto envuelto en delimitadores explícitos (<<<FRAGMENT_START>>>...<<<FRAGMENT_END>>>).
Defensa Banking: Detector heurístico de patrones de prompt injection (ignore previous, system:, <|im_start|>, etc.) que marca el fragmento con suspicious=true.
TH-03 · Envenenamiento de embeddings
Descripción: Atacante inserta archivos diseñados para que ciertas queries devuelvan fragmentos específicos.
Defensa universal: Solo se indexan rutas explícitamente autorizadas en Index Manager. Cada cambio de scope se registra.
Defensa Banking: Firma HMAC por archivo indexado; cambios no autorizados disparan alerta.
TH-04 · Downgrade attack (Banking → Basic)
Descripción: Malware cambia el perfil a Basic para desactivar defensas.
Defensa: Bajar de perfil requiere passphrase + re-cifrado completo del índice. El audit log registra el intento aunque se cancele. En Banking, el downgrade puede requerir 2FA opcional (passphrase + archivo token).
TH-05 · Filtración por logs
Descripción: Logs contienen fragmentos de código; DLP corporativo los captura; auditores los ven.
Defensa Basic: Rotación + tamaño máximo.
Defensa Enterprise: Sanitización obligatoria — paths hasheados, contenido truncado a 40 chars, nombres de función opcional.
Defensa Banking: Modo paranoid — logs solo contienen IDs numéricos y timestamps. Cero contenido.
TH-06 · Supply chain attack en dependencias
Descripción: PyPI comprometido; duckdb==0.10.1 envía datos.
Defensa universal: requirements.txt con hashes SHA256 explícitos. pip install --require-hashes obligatorio.
Defensa Banking: Bundle offline firmado por McComics. Instalación air-gapped verificable.
TH-07 · Memory scraping
Descripción: Malware con debug privileges lee RAM del daemon y extrae fragmentos descifrados.
Defensa universal: Fragmentos descifrados se mantienen en memoria solo durante el ensamblaje de una query y se sobreescriben con ctypes.memset inmediatamente después.
Defensa Banking: Memoria para fragmentos se aloja en páginas bloqueadas (VirtualLock Windows, mlock Unix) para evitar swap a disco.
TH-08 · Side-channel por tamaño de respuesta
Descripción: Observador externo infiere contenido del código por el tamaño de las respuestas HTTP.
Defensa Enterprise: Padding aleatorio a múltiplos de 1KB.
Defensa Banking: Transporte IPC nativo (sin HTTP observable externamente) + padding obligatorio.
TH-09 · Acceso al índice tras robo físico
Descripción: Laptop robada apagada. Atacante obtiene disco.
Defensa Basic: El índice está cifrado con clave en DPAPI — indescifrable sin credenciales del usuario Windows.
Defensa Enterprise: Ídem + passphrase opcional requerida al arrancar.
Defensa Banking: Passphrase obligatoria + clave efímera por dominio (crypto-shredding posible con un clic remoto vía cable USB pre-configurado).
TH-10 · Falsificación de fragmentos en audit log
Descripción: Insider modifica el audit log para ocultar sus queries.
Defensa Enterprise: Hash encadenado — cualquier modificación rompe la cadena y es detectable.
Defensa Banking: Hash encadenado + exportación diaria firmada externamente + verificación automática al arranque.
TH-11 · CORS abuse (FALLO-A12 de v3 corregido)
Descripción: HTML malicioso abierto en WebView hace requests al daemon.
Defensa: Toda comunicación monitor↔daemon usa pywebview native API (js_api), no HTTP. El servidor HTTP escucha solo 127.0.0.1, requiere token + HMAC, y rechaza origen null.
TH-12 · Race conditions con múltiples clientes
Descripción: Dos procesos (CLI + UI) intentan escribir simultáneamente.
Defensa universal: DuckDB es single-writer por diseño. Toda escritura pasa por el daemon. Los clientes solo leen vía API. Solucion de FALLO-07 de v3.
TH-13 · DoS por query pesada
Descripción: Query con regex catastrófico o scope masivo satura el sistema.
Defensa universal: Timeout por query (Basic 5s, Enterprise 3s, Banking 2s). Circuit breaker después de 3 timeouts consecutivos.
TH-14 · Robo de modelo LLM con weights envenenados
Descripción: Atacante reemplaza qwen.gguf con un modelo entrenado para filtrar datos.
Defensa Enterprise: Hash SHA256 del modelo verificado al cargar.
Defensa Banking: Modelos deben estar en manifest firmado por McComics. Solo se cargan si el hash coincide exactamente.
TH-15 · Ataque por DNS local
Descripción: /etc/hosts modificado; el daemon contacta un dominio malicioso.
Defensa Basic: Ninguna (fuera de alcance).
Defensa Enterprise: Allowlist de dominios con IP pinning opcional.
Defensa Banking: Air-gap total — verificación activa con 10.255.255.255 al arranque (M10 de v4).

6. Garantías y NO-garantías explícitas
6.1 El Oráculo GARANTIZA

✅ Procedencia verificable de cada fragmento entregado
✅ Cifrado del índice en reposo (todos los perfiles)
✅ Aislamiento entre dominios (ningún query cruza límites sin autorización)
✅ Degradación elegante con reporte explícito
✅ Inmutabilidad del código núcleo ante cambios de perfil
✅ Compatibilidad con cualquier archivo de texto (vía lexical skeleton)
✅ Operación completamente local (sin cloud por defecto)
✅ Reproducibilidad de builds (hashes verificables)

6.2 El Oráculo NO GARANTIZA

❌ Protección contra atacantes con privilegios root/admin persistentes
❌ Protección contra actores estatales con 0-days
❌ Protección contra compromiso físico del hardware (rubber hose, cold boot)
❌ Protección contra el propio McComics si cooperase con un atacante (el usuario es la raíz de confianza)
❌ Protección contra el usuario mismo (quien borre archivos los pierde)
❌ Garantía de que una IA externa (Claude, GPT) usará el contexto correctamente
❌ Protección contra análisis de timing fino sobre tiempos de respuesta (mitigable pero no eliminable)


7. Principio de confianza: "Trust Tiers"
Todo fragmento entregado tiene un trust_tier de 1 a 3:
TierSignificadoCuándo se usa1 · CanonMatch exacto del símbolo objetivo + file_hash verificado + no staleCódigo específicamente solicitado2 · Alta confianzaMatch cercano (AST/semántico/léxico) + file_hash verificadoContexto relacionado útil3 · ContextualMetadata, documentación, matches débilesInformación ambiental
La IA consumidora recibe instrucciones explícitas en el payload: "Trata trust_tier 1 como verdad canónica. Trust_tier 2 como hipótesis verificable. Trust_tier 3 como contexto orientativo."

8. Modelo de decisión de seguridad
Antes de cualquier operación, el Policy Engine evalúa:
1. ¿Está el perfil activo cargado? → si no, abortar
2. ¿La operación está permitida en este perfil? → si no, rechazar con código 403
3. ¿El token es válido y no expirado? → si no, 401
4. ¿El rate limit permite esta operación? → si no, 429
5. ¿El scope autorizado incluye el recurso? → si no, 403
6. ¿Hay anomalía detectada? (Banking) → si sí, bloquear + alertar
7. Ejecutar operación
8. Registrar en audit log según política del perfil

9. Proceso de respuesta a incidentes
EventoAcción automáticaNotificación UIIntegridad del índice rotaCuarentena + marcar staleBanner rojo + botón reindexarHMAC inválido en fila (Banking)Excluir fila + loggearBanner amarilloAnomaly detection dispara (Banking)Bloquear token + forzar re-authModal bloqueantePassphrase incorrecta 3 vecesBackoff exponencial hasta 5 minModal con countdownSupply chain hash mismatchBloquear carga del móduloBanner rojo + instruccionesAir-gap violación detectada (Banking)Detener daemonModal crítico + auditMemory integrity check fallaDetener daemon + dump forenseModal crítico

10. Auditoría y compliance
Perfil Basic: No hay compromisos de compliance. Uso personal.
Perfil Enterprise: Preparado para SOC2 Type I con pequeños ajustes organizacionales. Audit log exportable.
Perfil Banking: Preparado para:

SOC2 Type II (con soporte del operador)
ISO 27001 (controles A.12, A.14 cubiertos)
PCI-DSS (no almacena PAN, pero respeta principios de least privilege y audit)
Normativa BCRP / SBS Perú (resiliencia operacional)
GDPR (derecho al olvido vía crypto-shredding)

El Compliance Report Generator (M11) exporta evidencia mensual firmada.

11. Revisión
Este documento se revisa:

Al liberar cada versión mayor del Oráculo
Cuando se detecta una amenaza real no contemplada
Anualmente de forma obligatoria

Cambios requieren aprobación explícita de McComics y se registran en THREAT_MODEL_CHANGELOG.md.

