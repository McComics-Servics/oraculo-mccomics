📜 DOCUMENTO 4/6 — CONTEXT_ASSEMBLY_POLICY.md

Clasificación: LEY — Política de Ensamblado de Contexto
Versión: 1.0
Propietario: McComics Servicios Generales
Fecha: 2026-04-14


1. Propósito
Define cómo se construye el payload de respuesta ante una query, incluyendo asignación de presupuesto de tokens, fusión de métodos de retrieval, deduplicación, scoring de confianza y formato del JSON final entregado a la IA consumidora.

2. Principios
#PrincipioSignificado1Presupuesto férreoNunca exceder el budget configurado, incluso si hay resultados de alto score2Asignación jerárquicaCada capa tiene cuota máxima y mínima3Procedencia siempre visibleCada fragmento lleva su origen explícito4Anti-duplicación obligatoriaSimHash dedupe antes del ensamblaje5Frescura verificableStale fragments marcados o excluidos según política6DeterminismoMisma query + mismo índice = mismo resultado7Cero alucinación inducidaTrust tiers explícitos para que la IA receptora calibre

3. Pipeline completo de query
Usuario / IA externa → /v1/query
    ↓
1. Validación de auth + rate limit (Policy Engine)
    ↓
2. Cache lookup (Semantic Query Cache)
    ↓ (miss)
3. Query Expansion (LLM local opcional)
    ↓
4. Multi-method retrieval en paralelo:
    ├─ BM25 (SQLite FTS5)
    ├─ Vector HNSW (DuckDB)
    ├─ AST direct (call_graph + symbol table)
    ├─ AST similarity (APTED sobre top candidates)
    └─ Lexical exact (regex sobre identifier index)
    ↓
5. RRF Fusion (Reciprocal Rank Fusion)
    ↓
6. SimHash deduplication
    ↓
7. Re-ranking semántico (LLM local opcional)
    ↓
8. Hierarchical budget allocation
    ↓
9. Stale check + integrity verification (HMAC en Banking)
    ↓
10. Trust tier assignment
    ↓
11. JSON payload assembly
    ↓
12. Audit log entry (según perfil)
    ↓
13. Response → Cache update → Cliente

4. Asignación jerárquica del presupuesto
4.1 Capas y cuotas
yamlbudget_allocation:
  total_default: 8000  # tokens (configurable per-query)
  
  layers:
    L0_target_symbol:
      percent: 25
      min_percent: 15
      max_percent: 40
      trust_tier: 1
      content: "Función/símbolo objetivo + firma + docstring + 5 líneas contexto"
    
    L1_call_graph:
      percent: 20
      min_percent: 10
      max_percent: 30
      trust_tier: 1
      content: "Callers y callees directos (1 salto en grafo)"
    
    L2_ast_similar:
      percent: 20
      min_percent: 10
      max_percent: 25
      trust_tier: 2
      content: "Funciones con AST similar (APTED ≤0.85)"
    
    L3_semantic:
      percent: 15
      min_percent: 5
      max_percent: 25
      trust_tier: 2
      content: "Top-K vector con re-rank LLM local"
    
    L4_lexical:
      percent: 10
      min_percent: 5
      max_percent: 15
      trust_tier: 2
      content: "BM25 matches exactos de keywords"
    
    L5_metadata:
      percent: 5
      min_percent: 2
      max_percent: 10
      trust_tier: 3
      content: "Reglas McComics, README, glosario, dependencias"
    
    L6_buffer:
      percent: 5
      min_percent: 5
      max_percent: 5
      trust_tier: null
      content: "Reserva anti-desborde para padding y delimitadores"
4.2 Algoritmo de asignación
pythonclass BudgetAllocator:
    def allocate(
        self,
        total_budget: int,
        candidates_by_layer: dict[str, list[Fragment]],
        config: BudgetConfig
    ) -> AllocationResult:
        layers = config.layers
        allocated = {}
        used_tokens = 0
        
        # Fase 1: Asignar mínimos garantizados
        for layer_id, layer_cfg in layers.items():
            min_tokens = int(total_budget * layer_cfg.min_percent / 100)
            allocated[layer_id] = {
                'budget': min_tokens,
                'fragments': [],
                'used': 0
            }
            used_tokens += min_tokens
        
        # Fase 2: Distribuir el target percent
        remaining = total_budget - used_tokens
        for layer_id, layer_cfg in layers.items():
            target = int(total_budget * layer_cfg.percent / 100)
            extra = target - allocated[layer_id]['budget']
            if extra > 0 and remaining >= extra:
                allocated[layer_id]['budget'] += extra
                remaining -= extra
        
        # Fase 3: Llenar capas con candidatos
        for layer_id in layers:
            self._fill_layer(
                allocated[layer_id],
                candidates_by_layer.get(layer_id, [])
            )
        
        # Fase 4: Redistribuir sobrante a capas superiores (L0, L1)
        priority_order = ['L0_target_symbol', 'L1_call_graph', 'L2_ast_similar']
        for src_layer in allocated:
            unused = allocated[src_layer]['budget'] - allocated[src_layer]['used']
            if unused > 100:
                # Donar a capa prioritaria
                for dst_layer in priority_order:
                    if dst_layer == src_layer:
                        continue
                    # Verificar que no exceda max_percent
                    max_for_dst = int(total_budget * layers[dst_layer].max_percent / 100)
                    if allocated[dst_layer]['used'] < max_for_dst:
                        donatable = min(unused, max_for_dst - allocated[dst_layer]['used'])
                        # Intentar añadir más fragmentos
                        added = self._fill_layer(
                            allocated[dst_layer],
                            candidates_by_layer.get(dst_layer, []),
                            extra_budget=donatable
                        )
                        unused -= added
                        if unused <= 0:
                            break
        
        return AllocationResult(allocated)
    
    def _fill_layer(
        self,
        layer_state: dict,
        candidates: list[Fragment],
        extra_budget: int = 0
    ) -> int:
        """Añade fragmentos hasta agotar el presupuesto. Retorna tokens añadidos."""
        budget = layer_state['budget'] + extra_budget - layer_state['used']
        added_tokens = 0
        
        for frag in candidates:
            tokens = frag.estimated_tokens
            if frag.id in {f.id for f in layer_state['fragments']}:
                continue
            if tokens <= budget:
                layer_state['fragments'].append(frag)
                layer_state['used'] += tokens
                budget -= tokens
                added_tokens += tokens
            elif budget > 200:
                # Truncar fragmento si vale la pena
                truncated = self._truncate_fragment(frag, budget)
                if truncated:
                    layer_state['fragments'].append(truncated)
                    layer_state['used'] += truncated.estimated_tokens
                    added_tokens += truncated.estimated_tokens
                break
        
        return added_tokens
4.3 Caso especial: L0 desbordado
Si el símbolo objetivo es enorme (función de 500 líneas), L0 puede consumir más del 50%. Política:

Si tokens_L0 > total_budget * 0.5 → aplicar window centering:

Tomar 30 líneas antes y después del nombre del símbolo
Marcar fragmento como truncated=true
Reportar tamaño original en metadata


Si tras truncar sigue desbordando → reducir presupuestos de L4 y L5 al mínimo
Si aun así desborda → respuesta con error: oversized_target_symbol y sugerencia: aumentar budget o consultar por sub-símbolo


5. Reciprocal Rank Fusion (RRF)
5.1 Fórmula
RRF_score(doc) = Σ_{m ∈ methods} weight_m × 1 / (k + rank_m(doc))

donde:
- methods = [BM25, HNSW, AST_similar, CallGraph, LexicalExact]
- rank_m(doc) = posición (1-indexed) del doc en los resultados del método m
- k = 60 (constante estándar de la literatura)
- weight_m = peso del método (configurable, default 1.0 todos)
5.2 Ventajas

Sin entrenamiento: funciona out-of-the-box
Liviano: O(n) sobre los top-K de cada método
Robusto: tolera scores en escalas distintas
Sintonizable: pesos ajustables por feedback (M5 active learning)

5.3 Implementación
pythonclass RRFFusion:
    def __init__(self, k: int = 60, weights: dict[str, float] = None):
        self.k = k
        self.weights = weights or {
            'bm25': 1.0,
            'hnsw': 1.0,
            'ast_similar': 1.2,    # ligeramente más confiable
            'call_graph': 1.5,     # estructural = más confiable
            'lexical_exact': 1.3,
        }
    
    def fuse(
        self,
        results_by_method: dict[str, list[Fragment]],
        top_n: int = 50
    ) -> list[Fragment]:
        scores = {}  # frag_id → score acumulado
        
        for method, fragments in results_by_method.items():
            weight = self.weights.get(method, 1.0)
            for rank, frag in enumerate(fragments, start=1):
                score = weight * (1.0 / (self.k + rank))
                if frag.id in scores:
                    scores[frag.id]['score'] += score
                    scores[frag.id]['methods'].add(method)
                else:
                    scores[frag.id] = {
                        'fragment': frag,
                        'score': score,
                        'methods': {method}
                    }
        
        # Ordenar por score acumulado
        ranked = sorted(scores.values(), key=lambda x: -x['score'])
        
        # Bonus: fragmentos encontrados por múltiples métodos suben
        for entry in ranked:
            multi_method_bonus = (len(entry['methods']) - 1) * 0.05
            entry['score'] *= (1 + multi_method_bonus)
        
        # Re-ordenar tras el bonus
        ranked = sorted(ranked, key=lambda x: -x['score'])
        
        return [
            self._attach_rrf_metadata(entry)
            for entry in ranked[:top_n]
        ]
    
    def _attach_rrf_metadata(self, entry: dict) -> Fragment:
        frag = entry['fragment']
        frag.rrf_score = entry['score']
        frag.matched_methods = list(entry['methods'])
        return frag
5.4 Active learning sobre pesos (M5)
pythonclass WeightLearner:
    """Ajusta pesos RRF basado en feedback 👍/👎 del usuario."""
    
    LEARNING_RATE = 0.02
    MAX_WEIGHT_CHANGE = 0.20  # ±20% del baseline
    
    def update_weights(
        self,
        fusion: RRFFusion,
        feedback: list[FeedbackEvent]
    ):
        baseline = {
            'bm25': 1.0, 'hnsw': 1.0, 'ast_similar': 1.2,
            'call_graph': 1.5, 'lexical_exact': 1.3,
        }
        
        # Calcular delta por método basado en feedback
        deltas = {m: 0.0 for m in baseline}
        for event in feedback:
            for method in event.fragment.matched_methods:
                if event.is_upvote:
                    deltas[method] += self.LEARNING_RATE
                else:
                    deltas[method] -= self.LEARNING_RATE
        
        # Aplicar deltas con cap
        for method, delta in deltas.items():
            new_weight = fusion.weights[method] + delta
            min_w = baseline[method] * (1 - self.MAX_WEIGHT_CHANGE)
            max_w = baseline[method] * (1 + self.MAX_WEIGHT_CHANGE)
            fusion.weights[method] = max(min_w, min(max_w, new_weight))

6. Deduplicación SimHash
6.1 Cálculo del SimHash
pythonclass SimHash64:
    """SimHash de 64 bits sobre tokens del fragmento."""
    
    def hash(self, fragment: Fragment) -> int:
        tokens = self._tokenize(fragment.content)
        if not tokens:
            return 0
        
        # Vector de 64 dimensiones
        v = [0] * 64
        
        for token in tokens:
            h = self._stable_hash(token)
            for i in range(64):
                bit = (h >> i) & 1
                v[i] += 1 if bit else -1
        
        # Combinar bits
        result = 0
        for i in range(64):
            if v[i] > 0:
                result |= (1 << i)
        
        return result
    
    def _tokenize(self, text: str) -> list[str]:
        # Tokens significativos de 3+ chars
        return re.findall(r'\b\w{3,}\b', text.lower())
    
    def _stable_hash(self, token: str) -> int:
        import hashlib
        h = hashlib.md5(token.encode()).digest()
        return int.from_bytes(h[:8], 'big')

def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count('1')
6.2 Política de deduplicación
pythonclass SimHashDedup:
    DUPLICATE_THRESHOLD = 6  # bits diferentes
    
    def dedupe(self, fragments: list[Fragment]) -> list[Fragment]:
        kept = []
        seen_hashes = []
        
        for frag in fragments:
            is_dup = False
            for kept_idx, prev_hash in enumerate(seen_hashes):
                dist = hamming_distance(frag.simhash, prev_hash)
                if dist < self.DUPLICATE_THRESHOLD:
                    # Conservar el más reciente
                    if frag.last_modified > kept[kept_idx].last_modified:
                        kept[kept_idx] = frag
                        seen_hashes[kept_idx] = frag.simhash
                    is_dup = True
                    break
            
            if not is_dup:
                kept.append(frag)
                seen_hashes.append(frag.simhash)
        
        return kept
6.3 Cuándo aplica

Siempre después de RRF fusion
Antes de la asignación de presupuesto
Excepción: si el usuario explícitamente pide --show-duplicates para auditoría


7. Trust Tier assignment
7.1 Reglas
pythondef assign_trust_tier(fragment: Fragment) -> int:
    # Tier 1: Canon
    if fragment.parser_level == "L1" \
       and fragment.matched_methods >= {'call_graph'} \
       and not fragment.stale \
       and fragment.file_hash_verified:
        return 1
    
    if fragment.matched_methods == {'lexical_exact'} \
       and fragment.is_exact_symbol_match \
       and not fragment.stale:
        return 1
    
    # Tier 2: Alta confianza
    if fragment.parser_level in ("L1", "L2") \
       and not fragment.stale:
        return 2
    
    if len(fragment.matched_methods) >= 2 \
       and not fragment.stale:
        return 2
    
    # Tier 3: Contextual
    return 3
7.2 Filtrado por trust tier
El query puede especificar min_trust_tier:

min_trust_tier=1: solo canon (estricto)
min_trust_tier=2: canon + alta confianza (default)
min_trust_tier=3: todo (exploratorio)


8. Stale handling
8.1 Detección
Cada fragmento almacena file_hash_at_index (MD5 al momento de indexar). Antes de servir:
pythondef check_staleness(fragment: Fragment) -> bool:
    try:
        current_hash = compute_md5(fragment.file_path)
    except FileNotFoundError:
        fragment.stale_reason = "file_deleted"
        return True
    
    if current_hash != fragment.file_hash_at_index:
        fragment.current_hash = current_hash
        fragment.stale_reason = "content_changed"
        return True
    
    return False
8.2 Política según perfil
PerfilComportamiento ante staleBasicMarcar stale=true y servir igualEnterpriseMarcar stale=true y servir solo si query no es strictBankingExcluir completamente. Reportar excluded_stale count
8.3 Cuarentena masiva
Si stale_count / total_count > 0.10:
pythonif stale_ratio > 0.10:
    if profile == 'banking':
        return Response.error("INDEX_TOO_STALE", reindex_required=True)
    else:
        warning = f"⚠️ {stale_ratio*100:.0f}% del índice está obsoleto. Reindexar recomendado."
        response.warnings.append(warning)

9. Verificación de integridad por fila (Banking)
pythonclass RowIntegrityChecker:
    def __init__(self, master_key: bytes):
        self.master_key = master_key
    
    def verify(self, fragment: Fragment) -> bool:
        expected_hmac = fragment.row_hmac
        computed = self._compute_hmac(fragment)
        return hmac.compare_digest(expected_hmac, computed)
    
    def _compute_hmac(self, fragment: Fragment) -> bytes:
        canonical = self._canonicalize(fragment)
        return hmac.new(self.master_key, canonical, hashlib.sha256).digest()
    
    def _canonicalize(self, fragment: Fragment) -> bytes:
        # Serialización determinista
        parts = [
            fragment.id.encode(),
            fragment.file_path.encode(),
            str(fragment.start_line).encode(),
            str(fragment.end_line).encode(),
            fragment.content.encode(),
            fragment.file_hash_at_index.encode(),
        ]
        return b'\x00'.join(parts)
Si la verificación falla → fragmento marcado corrupted=true, excluido del response, registrado en audit log con severidad alta.

10. Re-ranking semántico con LLM local
10.1 Cuándo aplica

Basic: solo si LLM local está cargado y query tiene >5 candidates
Enterprise: por defecto activado
Banking: por defecto activado, con LLM signed

10.2 Prompt de re-ranking
pythonRERANK_PROMPT = """Tarea: ordena los siguientes fragmentos de código por relevancia para la pregunta del usuario.
Responde SOLO con los IDs en orden de mayor a menor relevancia, separados por coma.
No expliques. No agregues texto.

Pregunta: {query}

Fragmentos:
{fragments_listing}

Respuesta (solo IDs separados por coma):"""

def rerank_with_llm(
    query: str,
    candidates: list[Fragment],
    llm: LocalLLM,
    top_n: int = 20
) -> list[Fragment]:
    if len(candidates) <= 5 or not llm.available:
        return candidates
    
    # Construir listado compacto
    listing = []
    for frag in candidates[:top_n]:
        snippet = frag.content[:200].replace('\n', ' ')
        listing.append(f"[{frag.id}] {frag.name}: {snippet}")
    
    prompt = RERANK_PROMPT.format(
        query=query,
        fragments_listing='\n'.join(listing)
    )
    
    response = llm.generate(prompt, max_tokens=200, temperature=0.1)
    
    # Parsear orden
    order_ids = [s.strip() for s in response.split(',') if s.strip()]
    
    # Reordenar candidatos según el orden del LLM
    by_id = {f.id: f for f in candidates}
    reordered = []
    for fid in order_ids:
        if fid in by_id:
            reordered.append(by_id.pop(fid))
    # Anexar los no mencionados al final
    reordered.extend(by_id.values())
    
    return reordered
10.3 Fallback gracioso
Si el LLM falla, da timeout, o devuelve un formato no parseable → usar el orden original de RRF. Nunca bloquear la query por fallo del re-ranker.

11. Query expansion
11.1 Sin LLM (siempre disponible)
pythondef expand_query_basic(query: str, glossary: dict) -> str:
    expanded = query
    
    # 1. Expansión de glosario McComics
    for term, expansion in glossary.items():
        if term.lower() in query.lower():
            expanded += f" {expansion}"
    
    # 2. Expansión de identificadores (snake_case, CamelCase)
    tokens = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]+\b', query)
    for tok in tokens:
        expanded_tok = expand_identifier(tok)
        if expanded_tok != tok.lower():
            expanded += f" {expanded_tok}"
    
    return expanded
11.2 Con LLM (si está disponible)
pythonEXPAND_PROMPT = """Reformula y expande esta consulta de búsqueda de código añadiendo sinónimos, nombres alternativos y términos relacionados. Mantén el idioma original. Responde solo con la consulta expandida, sin explicaciones.

Consulta original: {query}

Consulta expandida:"""

def expand_query_with_llm(query: str, llm: LocalLLM) -> str:
    if not llm.available:
        return query
    response = llm.generate(
        EXPAND_PROMPT.format(query=query),
        max_tokens=80,
        temperature=0.2
    )
    return f"{query} {response.strip()}"

12. Semantic Query Cache (M1)
pythonclass SemanticQueryCache:
    """Cache LRU con invalidación por hash de scope."""
    
    def __init__(self, max_size: int = 200):
        self.cache: OrderedDict[str, CachedResponse] = OrderedDict()
        self.max_size = max_size
    
    def get(self, query: str, scope_hashes: list[str]) -> Optional[Response]:
        key = self._make_key(query, scope_hashes)
        if key in self.cache:
            self.cache.move_to_end(key)
            cached = self.cache[key]
            if self._is_still_valid(cached, scope_hashes):
                return cached.response
            else:
                del self.cache[key]
        return None
    
    def put(self, query: str, scope_hashes: list[str], response: Response):
        key = self._make_key(query, scope_hashes)
        self.cache[key] = CachedResponse(
            response=response,
            scope_hash=hashlib.sha256(''.join(sorted(scope_hashes)).encode()).hexdigest(),
            cached_at=time.time(),
        )
        self.cache.move_to_end(key)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def invalidate_by_file(self, file_path: str):
        """Elimina entradas que dependen de un archivo modificado."""
        to_remove = [
            k for k, v in self.cache.items()
            if file_path in v.response.referenced_files
        ]
        for k in to_remove:
            del self.cache[k]
    
    def _make_key(self, query: str, scope_hashes: list[str]) -> str:
        h = hashlib.sha256()
        h.update(query.encode())
        for sh in sorted(scope_hashes):
            h.update(sh.encode())
        return h.hexdigest()

13. Formato del JSON de respuesta
13.1 Schema completo
json{
  "api_version": "1.0",
  "query_id": "uuid-v4",
  "timestamp": "2026-04-14T15:22:31Z",
  "profile_active": "enterprise",
  
  "query": {
    "original": "como funciona el escalador",
    "expanded": "como funciona el escalador ESCALADOR_ULTRA_MCCOMICS scaling geometry",
    "scope": ["src/plugins/escalador/"],
    "min_trust_tier": 2,
    "max_results": 10
  },
  
  "budget": {
    "total_tokens": 8000,
    "chars_used": 6234,
    "estimated_tokens": {
      "cl100k_base": 1547,
      "gemini": "est:1680",
      "note": "Use chars_used for cross-model budgeting"
    },
    "allocation_used": {
      "L0_target_symbol": {"used": 1980, "budget": 2000},
      "L1_call_graph": {"used": 1580, "budget": 1600},
      "L2_ast_similar": {"used": 1490, "budget": 1600},
      "L3_semantic": {"used": 720, "budget": 1200},
      "L4_lexical": {"used": 380, "budget": 800},
      "L5_metadata": {"used": 84, "budget": 400},
      "L6_buffer": {"used": 0, "budget": 400}
    }
  },
  
  "fragments": [
    {
      "id": "frag_a3f2e1",
      "trust_tier": 1,
      "layer": "L0_target_symbol",
      "provenance": "ast_direct",
      "matched_methods": ["call_graph", "lexical_exact"],
      "rrf_score": 0.0421,
      "confidence": 0.94,
      
      "content": "def scale_handle(self, anchor, delta_mm):\n    ...",
      "language": "ruby",
      "parser_level": "L1",
      
      "file": "file:7b9a2c",
      "file_path_redacted": true,
      "name": "scale_handle",
      "start_line": 142,
      "end_line": 178,
      
      "file_hash_at_index": "sha256:abc123...",
      "file_hash_current": "sha256:abc123...",
      "file_hash_verified": true,
      "stale": false,
      "last_modified": "2026-04-12T10:22:00Z",
      
      "row_hmac_verified": true,
      "dynamic_dispatch_warning": false,
      "suspicious_content": false,
      "truncated": false
    }
  ],
  
  "graph": {
    "callers": ["update_geometry", "process_drag"],
    "callees": ["compute_anchor_offset", "apply_scale_to_face"],
    "include_paths": []
  },
  
  "warnings": [
    {
      "code": "STALE_DETECTED",
      "severity": "info",
      "message": "3 fragmentos relacionados están desactualizados (excluidos por perfil)"
    }
  ],
  
  "stats": {
    "total_candidates_before_dedup": 47,
    "duplicates_removed": 12,
    "stale_excluded": 3,
    "corrupted_excluded": 0,
    "retrieval_ms": 84,
    "fusion_ms": 12,
    "rerank_ms": 156,
    "assembly_ms": 22,
    "total_ms": 274
  },
  
  "instructions_for_consumer": "Trata trust_tier 1 como verdad canónica. Trust_tier 2 como hipótesis alta. Trust_tier 3 como contexto. Cita siempre el campo 'name' al referenciar código.",
  
  "audit": {
    "logged": true,
    "audit_id": "audit_xyz789"
  }
}
13.2 Reglas de redacción según perfil
CampoBasicEnterpriseBankingfile_pathCompletoHasheado (file:abc123)HasheadocontentCompletoCompletoCompleto (necesario para la query)name (símbolo)VisibleVisibleVisiblelast_modifiedISO completoISO completoSolo fecha (sin hora)audit_idNoSíSíinstructions_for_consumerSíSíSí + advertencia legal

14. Endpoint /v1/context (entrega para IA externa)
Variante simplificada que devuelve un bloque de texto listo para pegar en Claude/GPT/Gemini:
GET /v1/context?query=como+funciona+escalador&format=markdown
Respuesta:
markdown# Contexto del Oráculo McComics® v4.0

**Query:** como funciona el escalador
**Trust tier mínimo:** 2
**Generado:** 2026-04-14T15:22:31Z

> ⚠️ INSTRUCCIONES PARA LA IA: Los siguientes fragmentos provienen de un sistema de retrieval verificado. Cada fragmento lleva su nivel de confianza. Trata `[TIER 1]` como canon, `[TIER 2]` como contexto verificado, `[TIER 3]` como información ambiental.

## [TIER 1] · scale_handle (ruby) · escalador.rb:142-178

```ruby
def scale_handle(self, anchor, delta_mm):
    ...
```

**Llamada por:** update_geometry, process_drag  
**Llama a:** compute_anchor_offset, apply_scale_to_face  
**Verificado:** ✓ hash + ✓ HMAC + ✓ no stale

---

## [TIER 1] · update_geometry (ruby) · escalador.rb:80-120

```ruby
...
```
Este formato facilita el copy-paste en cualquier interfaz de chat IA.

15. Tests obligatorios del Context Assembler
✓ Allocation con todos los presupuestos llenos
✓ Allocation con L0 desbordado (window centering)
✓ Allocation con redistribución de sobrante
✓ RRF fusion con 5 métodos coincidiendo
✓ RRF fusion con bonus por multi-método
✓ SimHash dedup con 3 versiones de la misma función
✓ SimHash dedup conserva el más reciente
✓ Stale detection con archivo modificado
✓ Stale detection con archivo eliminado
✓ Cuarentena masiva (>10% stale en Banking)
✓ Trust tier assignment cubriendo los 3 niveles
✓ Re-ranking con LLM local mockado
✓ Re-ranking con fallback ante respuesta inválida del LLM
✓ Query expansion con glosario McComics
✓ Cache hit/miss con invalidación por archivo
✓ HMAC verification (Banking) con fila corrupta
✓ JSON output válido contra schema 1.0
✓ Determinismo: misma query 2 veces = mismo resultado
✓ Performance: P95 < SLO del perfil activo

16. Métricas del Context Assembler
MétricaObjetivoCache hit rate (uso normal)≥35%Tokens efectivos / tokens budget≥85%Trust tier 1 en top-5 resultados≥60%Fragmentos stale servidos (Basic/Enterprise)<5%Fragmentos stale servidos (Banking)0%Tiempo de fusion + dedup<50msTiempo de re-rank LLM<200msDeterminismo (test repetido)100%

17. Resumen ejecutivo
El Context Assembler es el cerebro táctico del Oráculo. Toma cinco fuentes de retrieval, las fusiona con RRF, las depura con SimHash, las asigna a un presupuesto jerárquico, las verifica criptográficamente (en Banking), y entrega un payload donde cada fragmento tiene procedencia, frescura y confianza explícitas. Esto resuelve los 3 problemas centrales:

Tokens: asignación férrea + dedup + truncado inteligente
Alucinaciones: trust tiers + procedencia + verificación de hash
Privacidad: redacción según perfil + HMAC en Banking + audit log inmutable


✅ Entrega 2/3 completada
Documentos entregados en esta entrega:
3. ✅ POLYGLOT_FABRIC_SPEC.md — Los 4 niveles de parsing, lexical skeleton, COBOL/RPG/JCL, encoding EBCDIC, FastCDC, plugin SDK
4. ✅ CONTEXT_ASSEMBLY_POLICY.md — Pipeline completo, RRF, SimHash, trust tiers, stale handling, HMAC, JSON schema, query cache
Próxima entrega (3/3) — final:
5. API_CONTRACT_SPEC.md — Endpoints completos, autenticación, IPC nativo vs HTTP, schemas request/response, códigos de error, streaming SSE
6. PROJECT_STRUCTURE_SPEC.md — Estructura de carpetas del repo, módulos Python, dependencias con hashes, build pipeline, instaladores
¿Continúo con la Entrega 3/3 final ahora?SI POR FAVOR7:18 p.m.ENTREGA 3/3 — Documentos Finales Pre-Construcción Oráculo v4.0

