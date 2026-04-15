📜 DOCUMENTO 3/6 — POLYGLOT_FABRIC_SPEC.md

Clasificación: LEY — Especificación del Núcleo Universal de Parsing
Versión: 1.0
Propietario: McComics Servicios Generales
Fecha: 2026-04-14


1. Propósito
Define cómo el Oráculo procesa cualquier archivo de texto del mundo, desde COBOL EBCDIC de 1975 hasta Rust 2026, garantizando que ningún archivo quede fuera del índice. Esta es la capa que diferencia al Oráculo de cualquier herramienta de retrieval comercial.

2. Principios fundamentales
#PrincipioSignificado1Cero exclusión por defectoSi el usuario autoriza una carpeta, todos sus archivos son indexables2Degradación elegante en cascadaSi L1 falla → L2 → L3 → L4. Nunca falla silenciosamente3Reportar siempre el nivel usadoCada fragmento indexado lleva parser_level en su metadata4Velocidad sobre completitud para L1tree-sitter es la primera opción siempre que esté disponible5DeterminismoEl mismo archivo procesado dos veces produce los mismos fragmentos6Tolerancia a archivos rotosUn archivo malformado no detiene la indexación del resto

3. Los 4 niveles de parsing
3.1 Tabla maestra
NivelTecnologíaLenguajes cubiertosVelocidadPrecisión sintácticaUso de RAML1tree-sitter (parsers compilados)~60 lenguajes modernos50-200 MB/s99%BajoL2ANTLR4 con gramáticas .g4Lenguajes legacy estructurados (COBOL, PL/I, Fortran, Ada, Pascal, Delphi, VHDL, Verilog, Solidity)10-30 MB/s92%MedioL3Pattern Library (regex + heurísticas)Lenguajes muy antiguos o nicho (RPG, Natural/ADABAS, JCL, CLIST, REXX, MUMPS, Clipper, FoxPro, Assembler IBM)30-80 MB/s75%BajoL4Lexical Skeleton (universal)Cualquier archivo de texto desconocido80-150 MB/s55%Mínimo
3.2 Selección automática del nivel
Pipeline de decisión (en orden):

1. Detectar extensión del archivo
2. Si extensión está en mapping L1 → intentar tree-sitter
3. Si tree-sitter falla o devuelve >5% nodos ERROR → intentar L2
4. Si extensión está en mapping L2 → intentar ANTLR
5. Si ANTLR falla → intentar L3
6. Si extensión está en mapping L3 → aplicar pattern library
7. Si nada matchea → aplicar L4 (lexical skeleton)
8. Registrar nivel usado en metadata del fragmento
Override del usuario: archivo db_storage/parser_overrides.yaml permite forzar nivel:
yaml"*.legacy_proprietary": L4
"src/banking/cobol_old/*.cob": L2
"vendor/*": SKIP

4. Mapeo extensión → lenguaje → nivel
4.1 Nivel L1 (tree-sitter)
yamlL1_extensions:
  python:    [.py, .pyi, .pyw]
  javascript: [.js, .mjs, .cjs, .jsx]
  typescript: [.ts, .tsx, .d.ts]
  ruby:      [.rb, .rbw, .rake, .gemspec, .ru]
  go:        [.go]
  rust:      [.rs]
  java:      [.java]
  c:         [.c, .h]
  cpp:       [.cpp, .cc, .cxx, .hpp, .hxx, .h++]
  csharp:    [.cs]
  php:       [.php, .phtml]
  kotlin:    [.kt, .kts]
  swift:     [.swift]
  scala:     [.scala, .sc]
  lua:       [.lua]
  bash:      [.sh, .bash, .zsh]
  sql:       [.sql]
  html:      [.html, .htm, .xhtml]
  css:       [.css, .scss, .sass, .less]
  yaml:      [.yaml, .yml]
  json:      [.json, .jsonc]
  markdown:  [.md, .markdown, .mdx]
  xml:       [.xml, .xsd, .xsl]
  toml:      [.toml]
  haskell:   [.hs, .lhs]
  ocaml:     [.ml, .mli]
  elixir:    [.ex, .exs]
  erlang:    [.erl, .hrl]
  clojure:   [.clj, .cljs, .cljc]
  r:         [.r, .R]
  julia:     [.jl]
  dart:      [.dart]
  zig:       [.zig]
  nim:       [.nim]
  perl:      [.pl, .pm]
  vim:       [.vim]
  dockerfile: [Dockerfile, .dockerfile]
  makefile:   [Makefile, .mk, .make]
4.2 Nivel L2 (ANTLR)
yamlL2_extensions:
  cobol:     [.cob, .cbl, .cobol, .cpy, .copy]
  pli:       [.pli, .pl1]
  fortran:   [.f, .for, .f77, .f90, .f95, .f03, .f08]
  ada:       [.ada, .adb, .ads]
  pascal:    [.pas, .pp]
  delphi:    [.dpr, .dpk]
  vhdl:      [.vhd, .vhdl]
  verilog:   [.v, .sv, .svh]
  solidity:  [.sol]
  modula2:   [.mod, .def]
  oberon:    [.ob, .ob2]
4.3 Nivel L3 (Pattern Library)
yamlL3_extensions:
  rpg:       [.rpg, .rpgle, .sqlrpgle]
  natural:   [.nat, .nsa, .nsg, .nsl, .nsm, .nsn, .nsp, .nss, .nst]
  jcl:       [.jcl, .job]
  clist:     [.clist, .cli]
  rexx:      [.rex, .rexx, .cmd]
  mumps:     [.m, .mumps]
  clipper:   [.prg, .ch, .ppo]
  foxpro:    [.prg, .scx, .sct, .vcx, .vct]
  asm_ibm:   [.s, .asm, .mac, .hlasm]
  basic_old: [.bas, .vb, .vbs, .frm]
  cobol_legacy: [.cobol_old, .ezt]   # cuando ANTLR falla
4.4 Nivel L4 (Lexical Skeleton)
Todo lo demás. Especialmente útil para:

Lenguajes propietarios sin gramática pública
Archivos de configuración exóticos
DSLs internos de empresas
Logs estructurados
Notaciones científicas
Formatos de banca core (Tandem TAL, Stratus PL/1G, etc.)


5. Detección de encoding (el problema EBCDIC)
5.1 Pipeline de detección
pythondef detect_encoding(filepath: Path) -> EncodingResult:
    # Leer primeros 4KB
    with open(filepath, 'rb') as f:
        sample = f.read(4096)
    
    # 1. BOM check (más confiable)
    if sample.startswith(b'\xef\xbb\xbf'):
        return EncodingResult('utf-8-sig', confidence=1.0)
    if sample.startswith(b'\xff\xfe'):
        return EncodingResult('utf-16-le', confidence=1.0)
    if sample.startswith(b'\xfe\xff'):
        return EncodingResult('utf-16-be', confidence=1.0)
    
    # 2. ASCII puro (rápido)
    if all(b < 128 for b in sample):
        return EncodingResult('ascii', confidence=1.0)
    
    # 3. UTF-8 válido
    try:
        sample.decode('utf-8')
        return EncodingResult('utf-8', confidence=0.95)
    except UnicodeDecodeError:
        pass
    
    # 4. EBCDIC heurística
    # En EBCDIC, los bytes 0x40-0xFE dominan (vs UTF-8 donde 0x20-0x7E)
    high_range_count = sum(1 for b in sample if 0x40 <= b <= 0xFE)
    low_ascii_count = sum(1 for b in sample if 0x20 <= b <= 0x7E)
    
    if high_range_count > low_ascii_count * 2:
        # Probable EBCDIC
        # Probar variantes en orden de probabilidad
        for codec in ['cp037', 'cp1047', 'cp1140', 'cp500']:
            try:
                decoded = sample.decode(codec)
                # Verificar que contiene caracteres legibles
                printable = sum(1 for c in decoded if c.isprintable() or c.isspace())
                if printable / len(decoded) > 0.85:
                    return EncodingResult(codec, confidence=0.80)
            except UnicodeDecodeError:
                continue
    
    # 5. chardet/charset-normalizer como backup
    import charset_normalizer
    result = charset_normalizer.detect(sample)
    if result['confidence'] > 0.7:
        return EncodingResult(result['encoding'], confidence=result['confidence'])
    
    # 6. Fallback final: latin-1 (nunca falla, nunca corrompe bytes)
    return EncodingResult('latin-1', confidence=0.30, is_fallback=True)
5.2 Override manual
db_storage/encoding_overrides.yaml:
yaml"src/legacy/banco_*/*.cob": cp1047
"src/cobol_caribe/*": cp1140
"src/iberica/*.cob": cp500
5.3 Reporting
Cada archivo indexado registra su encoding detectado. La pestaña Index Manager muestra una columna "Encoding" para que el usuario pueda detectar archivos con confidence < 0.5 y aplicar overrides manuales.

6. COBOL: el caso especial más importante
6.1 Formato fijo por columnas
Columnas:
1-6:    Número de secuencia (ignorable)
7:      Indicador (* = comentario, - = continuación, D = debug)
8-11:   Área A (DIVISION, SECTION, paragraph names)
12-72:  Área B (statements)
73-80:  Identificación (ignorable)
El parser COBOL del Oráculo debe respetar este formato fijo antes de pasar el contenido a ANTLR. Si lee texto como flujo libre, ANTLR fallará.
6.2 Pipeline COBOL
pythonclass CobolPreprocessor:
    def preprocess(self, raw_text: str) -> str:
        lines = raw_text.split('\n')
        cleaned = []
        for line in lines:
            # Padding a 80 columnas si la línea es más corta
            line = line.ljust(80)[:80]
            
            # Extraer indicador
            indicator = line[6:7]
            
            # Saltar comentarios
            if indicator in ('*', '/'):
                cleaned.append('')  # mantener numeración
                continue
            
            # Manejar continuación
            if indicator == '-':
                # Concatenar con línea previa removiendo espacios iniciales
                if cleaned:
                    cleaned[-1] = cleaned[-1].rstrip() + line[7:72].lstrip()
                continue
            
            # Línea normal: tomar áreas A + B
            code_part = line[6:72]
            cleaned.append(code_part)
        
        return '\n'.join(cleaned)
6.3 Resolución de copybooks
pythonclass CopybookResolver:
    def __init__(self, search_paths: list[Path]):
        self.search_paths = search_paths
        self.cache: dict[str, str] = {}
    
    def resolve(self, copy_name: str) -> Optional[str]:
        if copy_name in self.cache:
            return self.cache[copy_name]
        
        # Variantes comunes
        candidates = [
            f"{copy_name}.cpy",
            f"{copy_name}.copy",
            f"{copy_name}.cob",
            copy_name.upper() + ".cpy",
            copy_name.lower() + ".cpy",
        ]
        
        for path in self.search_paths:
            for candidate in candidates:
                full = path / candidate
                if full.exists():
                    content = read_with_encoding_detection(full)
                    self.cache[copy_name] = content
                    return content
        return None
Cuando una sección COBOL incluye COPY CUSTREC., el resolver inyecta el contenido del copybook como fragmento relacionado en el grafo de dependencias, no expande el texto en línea (eso saturaría el índice).
6.4 Niveles COBOL preservados
COBOL usa niveles jerárquicos en DATA DIVISION:
cobol01 CUSTOMER-RECORD.
   05 CUSTOMER-NAME PIC X(30).
   05 CUSTOMER-AGE PIC 99.
   05 CUSTOMER-ADDRESS.
      10 STREET PIC X(40).
      10 CITY PIC X(20).
El parser preserva esta jerarquía como atributo de cada fragmento:
json{
  "name": "STREET",
  "level": 10,
  "parent_path": "CUSTOMER-RECORD.CUSTOMER-ADDRESS",
  "pic": "X(40)",
  "fragment_type": "data_item"
}
Cuando una IA pregunta "qué campos tiene CUSTOMER-RECORD", el Context Assembler puede traer todos los fragmentos con parent_path empezando por "CUSTOMER-RECORD".

7. RPG/RPGLE: formato más extremo
7.1 Especificaciones RPG
RPG usa "specs" identificados por la columna 6:
H = Header
F = File
D = Definition
I = Input
C = Calculation
O = Output
P = Procedure
El parser L3 usa pattern library:
yamlrpg_patterns:
  procedure_start:
    regex: '^\s*P\s+(\w+)\s+B'
    captures: [name]
    type: procedure_definition
  
  procedure_end:
    regex: '^\s*P\s+(\w+)\s+E'
    captures: [name]
  
  file_def:
    regex: '^\s*F(\w+)\s+'
    captures: [filename]
    type: file_definition
  
  d_spec:
    regex: '^\s*D(\w+)\s+'
    captures: [name]
    type: data_definition
  
  free_format_block:
    regex: '/free.*?/end-free'
    flags: dotall
    type: free_block
    parse_as: c_like
Para el formato libre /free ... /end-free (RPGLE moderno), el parser usa heurísticas C-like.

8. JCL: descripción de jobs
JCL es declarativo, no procedural:
jcl//MYJOB    JOB (ACCT),'PROGRAMMER',CLASS=A,MSGCLASS=H
//STEP1    EXEC PGM=IEFBR14
//DD1      DD DSN=MY.DATASET,DISP=(NEW,CATLG,DELETE),
//            SPACE=(TRK,(10,5)),UNIT=SYSDA
Pattern library detecta:

Jobs (//NAME JOB)
Steps (//STEPNAME EXEC PGM=...)
DD statements
Procedimientos (//PROC)
Símbolos referenciados (&PARAM)

Cada job se indexa como una unidad lógica con sus steps como sub-fragmentos.

9. El Lexical Skeleton (L4)
9.1 Concepto
Para cualquier archivo de texto desconocido, extraer estructura sin entender la sintaxis.
9.2 Algoritmo
pythonclass LexicalSkeleton:
    def extract(self, text: str, filepath: Path) -> list[Fragment]:
        lines = text.split('\n')
        fragments = []
        
        # Paso 1: Detectar bloques por indentación
        blocks = self._dedent_chunking(lines)
        
        # Paso 2: Para cada bloque, extraer features
        for block in blocks:
            features = self._extract_features(block)
            
            # Paso 3: Inferir "tipo" probable
            inferred_type = self._infer_type(features)
            
            fragments.append(Fragment(
                content=block.text,
                start_line=block.start,
                end_line=block.end,
                language="unknown",
                parser_level="L4",
                inferred_type=inferred_type,
                features=features,
                file_path=str(filepath),
            ))
        
        return fragments
    
    def _dedent_chunking(self, lines: list[str]) -> list[Block]:
        """Divide en bloques cuando la indentación vuelve al nivel base."""
        blocks = []
        current = []
        current_start = 0
        base_indent = None
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                if current:
                    current.append(line)
                continue
            
            indent = len(line) - len(line.lstrip())
            
            # Inicio de archivo
            if base_indent is None:
                base_indent = indent
                current = [line]
                current_start = i
                continue
            
            # Vuelta al nivel base = nuevo bloque
            if indent <= base_indent and current:
                blocks.append(Block(
                    text='\n'.join(current),
                    start=current_start,
                    end=i - 1
                ))
                current = [line]
                current_start = i
            else:
                current.append(line)
        
        if current:
            blocks.append(Block(
                text='\n'.join(current),
                start=current_start,
                end=len(lines) - 1
            ))
        
        return blocks
    
    def _extract_features(self, block: Block) -> dict:
        text = block.text
        return {
            'line_count': block.end - block.start + 1,
            'char_count': len(text),
            'identifier_candidates': self._extract_identifiers(text),
            'comment_ratio': self._comment_ratio(text),
            'has_string_literals': self._has_strings(text),
            'has_numbers': bool(re.search(r'\b\d+\b', text)),
            'avg_line_length': sum(len(l) for l in text.split('\n')) / max(1, len(text.split('\n'))),
            'symbol_density': len(re.findall(r'[{}()[\];:=]', text)) / max(1, len(text)),
        }
    
    def _extract_identifiers(self, text: str) -> list[str]:
        # Tokens de 3+ caracteres alfanuméricos que no son keywords comunes
        common_keywords = {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'into'}
        candidates = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]{2,}\b', text)
        return [c for c in candidates if c.lower() not in common_keywords][:50]
    
    def _comment_ratio(self, text: str) -> float:
        # Heurística: líneas que empiezan con #, //, --, *, ;, %, ', "
        comment_starts = ('#', '//', '--', '*', ';', '%', "'", '"""', "'''")
        lines = text.split('\n')
        if not lines:
            return 0
        comments = sum(1 for l in lines if l.strip().startswith(comment_starts))
        return comments / len(lines)
    
    def _infer_type(self, features: dict) -> str:
        # Heurísticas simples para clasificar bloques
        if features['comment_ratio'] > 0.7:
            return "documentation_block"
        if features['symbol_density'] > 0.1:
            return "code_block"
        if features['has_string_literals'] and features['line_count'] > 5:
            return "data_block"
        return "text_block"
9.3 Embedding del fragmento L4
Aunque no entendemos la sintaxis, el embedding sí captura semántica:
pythondef build_embedding_text(fragment: Fragment) -> str:
    parts = [
        f"file: {fragment.file_path.name}",
        f"identifiers: {' '.join(fragment.features['identifier_candidates'])}",
        f"type: {fragment.inferred_type}",
        fragment.content[:1500],
    ]
    return '\n'.join(parts)
Los identificadores extraídos se expanden con la regla de snake_case/CamelCase (FALLO-17 de v3 ya resuelto).

10. Content-Defined Chunking (FastCDC)
10.1 Por qué es crítico
Cuando un usuario edita un archivo legacy de 5MB, los chunks de tamaño fijo se invalidan en cascada. FastCDC encuentra boundaries naturales basados en el contenido. Pequeñas ediciones afectan solo 1-2 chunks adyacentes.
10.2 Implementación
pythonclass FastCDC:
    """Content-defined chunking liviano."""
    
    MIN_SIZE = 256       # bytes
    AVG_SIZE = 2048      # bytes
    MAX_SIZE = 8192      # bytes
    MASK_S = 0x0003590703530000  # máscara estricta para chunks pequeños
    MASK_L = 0x0000d90003530000  # máscara relajada para chunks grandes
    
    def chunks(self, data: bytes) -> Iterator[tuple[int, int]]:
        n = len(data)
        offset = 0
        
        while offset < n:
            if n - offset <= self.MIN_SIZE:
                yield (offset, n)
                return
            
            end = self._find_cut(data, offset)
            yield (offset, end)
            offset = end
    
    def _find_cut(self, data: bytes, start: int) -> int:
        n = len(data)
        i = start + self.MIN_SIZE
        h = 0
        
        # Fase 1: máscara estricta hasta AVG_SIZE
        while i < min(start + self.AVG_SIZE, n):
            h = (h << 1) + GEAR_TABLE[data[i]]
            if (h & self.MASK_S) == 0:
                return i + 1
            i += 1
        
        # Fase 2: máscara relajada hasta MAX_SIZE
        while i < min(start + self.MAX_SIZE, n):
            h = (h << 1) + GEAR_TABLE[data[i]]
            if (h & self.MASK_L) == 0:
                return i + 1
            i += 1
        
        return min(start + self.MAX_SIZE, n)
GEAR_TABLE es una tabla pre-computada de 256 valores aleatorios fijos (determinista). Ver implementación de referencia FastCDC en literatura.
10.3 Cuándo se usa

L1, L2, L3: chunking semántico por funciones/secciones (no FastCDC)
L4: FastCDC obligatorio
Archivos >10MB: FastCDC obligatorio incluso si hay parser disponible


11. Resolución de includes/imports universal
11.1 Tabla de patrones por lenguaje
yamlinclude_patterns:
  cobol:
    - regex: 'COPY\s+([A-Z0-9-]+)'
      group: 1
      search_paths: [./copybooks/, ./cpy/, ./copy/]
  
  c_cpp:
    - regex: '#include\s+"([^"]+)"'
      group: 1
      search_paths: [./, ./include/, ./src/]
    - regex: '#include\s+<([^>]+)>'
      group: 1
      search_paths: [SYSTEM]
  
  python:
    - regex: 'from\s+(\S+)\s+import'
      group: 1
      resolver: python_module_resolver
    - regex: '^import\s+(\S+)'
      group: 1
      resolver: python_module_resolver
  
  ruby:
    - regex: 'require_relative\s+[''"]([^''"]+)'
      group: 1
      append_extension: .rb
      relative_to: file
    - regex: 'require\s+[''"]([^''"]+)'
      group: 1
      resolver: ruby_load_path_resolver
  
  java:
    - regex: 'import\s+([\w.]+);'
      group: 1
      resolver: java_classpath_resolver
  
  rpg:
    - regex: '/COPY\s+(\S+)'
      group: 1
      search_paths: [./qcpysrc/, ./QCPYSRC/]
  
  jcl:
    - regex: '//\s*INCLUDE\s+MEMBER=(\S+)'
      group: 1
11.2 Grafo de dependencias incremental
Cada include resuelto genera una arista en dependency_graph:
sqlCREATE TABLE dependency_graph (
    source_file TEXT NOT NULL,
    target_file TEXT NOT NULL,
    relationship TEXT NOT NULL,  -- 'include', 'import', 'copy', 'require'
    line_number INTEGER,
    confidence REAL DEFAULT 1.0,
    UNIQUE(source_file, target_file, line_number)
);
CREATE INDEX idx_dep_source ON dependency_graph(source_file);
CREATE INDEX idx_dep_target ON dependency_graph(target_file);
El Context Assembler usa este grafo para traer archivos relacionados al ensamblar contexto.

12. Detección de tampering pre-indexación
Cada archivo, antes de indexarse, pasa por:
pythondef pre_index_checks(filepath: Path) -> CheckResult:
    # 1. Verificar tamaño razonable
    size = filepath.stat().st_size
    if size > 100 * 1024 * 1024:  # 100MB
        return CheckResult.skip("file_too_large")
    
    # 2. Detectar binarios disfrazados de texto
    with open(filepath, 'rb') as f:
        sample = f.read(8192)
    null_count = sample.count(b'\x00')
    if null_count > len(sample) * 0.1:
        return CheckResult.skip("likely_binary")
    
    # 3. Detector de secretos (M18)
    secrets = scan_for_secrets(sample)
    if secrets:
        return CheckResult.partial(
            "contains_secrets",
            redactions=secrets
        )
    
    # 4. Detector de prompt injection (TH-02)
    if has_injection_patterns(sample):
        return CheckResult.proceed_with_warning(
            "suspicious_content"
        )
    
    return CheckResult.ok()

13. Pre-procesamiento de identificadores
Solución de FALLO-17 de v3, ahora formal:
pythondef expand_identifier(name: str) -> str:
    """
    snake_case → 'snake case'
    CamelCase → 'Camel Case'
    SCREAMING_CASE → 'screaming case'
    mixedCase_with_snake → 'mixed Case with snake'
    """
    # CamelCase → spaces
    s1 = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', name)
    s2 = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', ' ', s1)
    # snake_case → spaces
    s3 = s2.replace('_', ' ').replace('-', ' ')
    # Normalizar
    return ' '.join(s3.lower().split())

# Aplicación en glosario
def apply_glossary(text: str, glossary: dict) -> str:
    """Expande términos del glosario McComics."""
    words = text.split()
    expanded = []
    for w in words:
        upper = w.upper()
        if upper in glossary:
            expanded.append(f"{w} ({glossary[upper]})")
        else:
            expanded.append(w)
    return ' '.join(expanded)

14. Manejo de errores de parseo
14.1 tree-sitter ERROR nodes
pythondef has_parse_errors(node, threshold: float = 0.05) -> bool:
    total = 0
    errors = 0
    
    def walk(n):
        nonlocal total, errors
        total += 1
        if n.type == "ERROR" or n.is_missing:
            errors += 1
        for child in n.children:
            walk(child)
    
    walk(node)
    return total > 0 and (errors / total) > threshold
Si supera el threshold → degradar a L4 para ese archivo y registrar warning.
14.2 Logging de fallos de parseo
db_storage/parse_warnings.log

2026-04-14 10:22:31 | level_demoted | src/legacy/old.cob | L2→L3 | reason: antlr_grammar_mismatch
2026-04-14 10:22:33 | level_demoted | src/util.rb | L1→L4 | reason: 12% ERROR nodes (heredocs)
2026-04-14 10:22:35 | encoding_fallback | src/banco/data.cob | utf-8→cp1047 | confidence: 0.82
La pestaña Index Manager lee este log y muestra archivos problemáticos para revisión.

15. Plugin SDK para parsers de terceros
15.1 Interface
pythonfrom oraculo.plugins import ParserPlugin, Fragment

class MyLegacyParser(ParserPlugin):
    """Plugin para lenguaje propietario X."""
    
    language_name = "propietario_x"
    file_extensions = [".px", ".prx"]
    parser_level = "L3"  # equivalente
    
    def can_parse(self, filepath: Path, sample: bytes) -> bool:
        # Detección heurística adicional si la extensión no basta
        return b"PROPIETARIO X" in sample[:200]
    
    def parse(self, text: str, filepath: Path) -> list[Fragment]:
        fragments = []
        # ... lógica de parseo personalizada
        return fragments
    
    def metadata(self) -> dict:
        return {
            "version": "1.0",
            "author": "tu_nombre",
            "description": "Parser para Propietario X v3+",
        }
15.2 Registro de plugins
plugins/
├── enabled/
│   └── propietario_x.py
├── disabled/
└── manifest.json   ← lista de plugins firmados (para Banking)
En perfil Banking, solo se cargan plugins cuyo hash SHA256 está en manifest.json firmado.

16. Tests obligatorios del Polyglot Fabric
✓ Indexar archivo Python con tildes en comentarios
✓ Indexar archivo Ruby con heredocs (FALLO-12)
✓ Indexar COBOL en formato fijo con copybooks
✓ Indexar COBOL en EBCDIC cp1047
✓ Indexar RPG/RPGLE con specs F, D, C
✓ Indexar JCL con includes
✓ Indexar archivo desconocido vía L4
✓ Indexar archivo binario disfrazado (debe rechazarse)
✓ Indexar archivo con secretos (debe redactarse)
✓ Indexar archivo de 50MB (vía mmap)
✓ Indexar archivo con 12% ERROR nodes (degradar a L4)
✓ Indexar archivo con encoding desconocido (fallback latin-1)
✓ Verificar grafo de dependencias para imports cruzados
✓ Verificar idempotencia (re-indexar produce mismos hashes)
✓ Verificar plugin SDK con un parser de prueba

17. Métricas del Polyglot Fabric
MétricaObjetivoCobertura de archivos legibles del proyecto≥99%Tiempo promedio por archivo (L1)<50msTiempo promedio por archivo (L2)<200msTiempo promedio por archivo (L3)<80msTiempo promedio por archivo (L4)<30msFalsos negativos en detección de encoding<2%Pérdida de información en chunking L4<15%

18. Resumen ejecutivo
El Polyglot Fabric convierte al Oráculo en la única herramienta del mercado que indexa COBOL EBCDIC, RPG, Natural, MUMPS, Clipper y archivos completamente desconocidos con la misma confianza que Python o Rust. La cascada L1→L2→L3→L4 garantiza que ningún archivo queda fuera, y el sistema siempre reporta qué nivel se usó para que la IA consumidora calibre su confianza.

