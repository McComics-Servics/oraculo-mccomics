"""
Modulo: oraculo.cli.main
Proposito: CLI con subcomandos: query, index, profile, status, serve.
Conectado con OraculoApp para operaciones reales.
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

_app = None


def _get_app():
    """Inicializa OraculoApp headless una sola vez (lazy)."""
    global _app
    if _app is not None:
        return _app

    from oraculo.app import OraculoApp
    repo_root = Path(os.environ.get("ORACULO_REPO_ROOT", Path.cwd()))
    _app = OraculoApp(repo_root=repo_root, mode="headless")
    ctx = _app.start_headless()
    if "error" in ctx:
        logger.error("No se pudo inicializar: %s", ctx)
        return None
    return _app


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mccomics_brain",
        description="El Oraculo McComics — Motor de inteligencia de codigo local",
    )
    parser.add_argument("--profile", default=None, help="Perfil de seguridad (basic/enterprise/banking)")
    parser.add_argument("--data-dir", default=None, help="Directorio de datos")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")

    sub = parser.add_subparsers(dest="command", help="Comandos disponibles")

    q = sub.add_parser("query", help="Buscar en el indice")
    q.add_argument("text", help="Texto de busqueda en lenguaje natural")
    q.add_argument("--limit", "-n", type=int, default=10, help="Maximo de resultados")
    q.add_argument("--format", choices=["text", "json"], default="text", dest="out_format", help="Formato de salida")
    q.add_argument("--budget", type=int, default=4096, help="Presupuesto de tokens")
    q.add_argument("--domain", default=None, help="Dominio especifico (code/docs/email)")

    idx = sub.add_parser("index", help="Indexar archivos")
    idx.add_argument("paths", nargs="+", help="Archivos o directorios a indexar")
    idx.add_argument("--force", action="store_true", help="Forzar re-indexacion")

    p = sub.add_parser("profile", help="Gestionar perfil de seguridad")
    p.add_argument("action", choices=["show", "switch", "list"], help="Accion")
    p.add_argument("--name", help="Nombre del perfil para switch")

    sub.add_parser("health", help="Estado de salud del daemon")

    sub.add_parser("status", help="Ver estado del sistema")

    s = sub.add_parser("serve", help="Iniciar servidor HTTP")
    s.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    s.add_argument("--port", type=int, default=9741, help="Puerto (default: 9741)")

    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    if args.data_dir:
        os.environ["ORACULO_DATA_DIR"] = args.data_dir
    if args.profile:
        os.environ["ORACULO_PROFILE"] = args.profile

    if not args.command:
        parser.print_help()
        return 0

    handlers = {
        "query": _cmd_query,
        "index": _cmd_index,
        "profile": _cmd_profile,
        "health": _cmd_health,
        "status": _cmd_status,
        "serve": _cmd_serve,
    }
    handler = handlers.get(args.command)
    if handler:
        return handler(args)
    return 0


def _cmd_query(args) -> int:
    app = _get_app()
    if not app:
        print("Error: No se pudo inicializar El Oraculo.", file=sys.stderr)
        return 1

    ctx = app.context
    assembler = ctx.get("assembler")
    if not assembler:
        print("Error: Assembler no disponible.", file=sys.stderr)
        return 1

    t0 = time.monotonic()
    result = assembler.assemble(args.text, limit=args.limit)
    elapsed_ms = (time.monotonic() - t0) * 1000

    if args.out_format == "json":
        output = {
            "api_version": "1.0",
            "query": args.text,
            "fragments": [],
            "total": len(result.fragments) if hasattr(result, "fragments") else 0,
            "query_time_ms": round(elapsed_ms, 1),
        }
        for frag in (result.fragments if hasattr(result, "fragments") else []):
            output["fragments"].append({
                "file": getattr(frag, "file_path", "unknown"),
                "lines": [getattr(frag, "start_line", 0), getattr(frag, "end_line", 0)],
                "trust_tier": getattr(frag, "trust_tier", 2),
                "score": round(getattr(frag, "rrf_score", 0.0), 4),
                "stale": getattr(frag, "stale", False),
                "content": getattr(frag, "content", "")[:500],
            })
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"\n\U0001f50d Query: \"{args.text}\"\n")
        fragments = result.fragments if hasattr(result, "fragments") else []
        if not fragments:
            print("  Sin resultados.")
        for frag in fragments:
            tier = getattr(frag, "trust_tier", 2)
            tier_label = {1: "canon", 2: "alta", 3: "contextual"}.get(tier, "?")
            path = getattr(frag, "file_path", "?")
            start = getattr(frag, "start_line", 0)
            end = getattr(frag, "end_line", 0)
            score = getattr(frag, "rrf_score", 0.0)
            stale = " [STALE]" if getattr(frag, "stale", False) else ""
            print(f"\U0001f4c4 [trust:{tier}/{tier_label}] {path}:{start}-{end}  (score:{score:.4f}){stale}")
            content = getattr(frag, "content", "")
            if content:
                preview = content[:120].replace("\n", " ")
                print(f"   \u2192 {preview}")
            print()
        print(f"Fragmentos: {len(fragments)} | Tiempo: {elapsed_ms:.0f}ms")

    return 0


def _cmd_index(args) -> int:
    app = _get_app()
    if not app:
        print("Error: No se pudo inicializar El Oraculo.", file=sys.stderr)
        return 1

    ctx = app.context
    pipeline = ctx.get("index_pipeline")
    if not pipeline:
        print("Error: IndexPipeline no disponible.", file=sys.stderr)
        return 1

    all_files = []
    for p in args.paths:
        target = Path(p)
        if target.is_file():
            all_files.append(target)
        elif target.is_dir():
            all_files.extend(target.rglob("*"))
        else:
            print(f"Advertencia: {p} no existe, omitiendo.", file=sys.stderr)

    source_files = [f for f in all_files if f.is_file() and f.suffix in (
        ".py", ".rb", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h",
        ".cs", ".php", ".kt", ".swift", ".scala", ".lua", ".sh", ".bash",
        ".sql", ".html", ".css", ".yaml", ".yml", ".json", ".md", ".txt",
        ".cbl", ".cob", ".rpg", ".rpgle", ".jcl", ".pli", ".nat", ".f90",
        ".f77", ".ada", ".pas", ".prg",
    )]

    print(f"Indexando {len(source_files)} archivos...")
    t0 = time.monotonic()
    stats = pipeline.index_batch(source_files, force=args.force)
    elapsed = time.monotonic() - t0

    print(f"\n\u2705 Indexacion completada en {elapsed:.2f}s")
    print(f"   Archivos procesados: {stats.files_processed}")
    print(f"   Fragmentos creados:  {stats.fragments_created}")
    if stats.errors:
        print(f"   Errores:             {len(stats.errors)}")
    return 0


def _cmd_profile(args) -> int:
    app = _get_app()
    if not app:
        print("Error: No se pudo inicializar El Oraculo.", file=sys.stderr)
        return 1

    engine = app.context.get("policy_engine")
    if not engine:
        print("Error: PolicyEngine no disponible.", file=sys.stderr)
        return 1

    if args.action == "list":
        from oraculo.policy.loader import list_available_profiles
        profiles = list_available_profiles(engine.profiles_dir)
        active = engine.current_name
        for p in profiles:
            marker = " <-- activo" if p == active else ""
            print(f"  {p}{marker}")
    elif args.action == "show":
        profile = engine.current
        if profile:
            print(json.dumps(profile, indent=2, ensure_ascii=False, default=str))
        else:
            print("Sin perfil activo.")
    elif args.action == "switch":
        if not args.name:
            print("Error: --name requerido para switch", file=sys.stderr)
            return 1
        result = engine.activate(args.name)
        if result.success:
            print(f"\u2705 Perfil cambiado: {result.previous} \u2192 {result.current}")
        else:
            print(f"\u274c Error: {result.error_message}", file=sys.stderr)
            return 1
    return 0


def _cmd_health(args) -> int:
    app = _get_app()
    if not app:
        print("\u274c Daemon no disponible.", file=sys.stderr)
        return 1

    ctx = app.context
    fts = ctx.get("fts_store")
    duck = ctx.get("duck_store")
    cognitive = ctx.get("cognitive")

    fts_count = fts.count() if fts and hasattr(fts, "count") else 0
    duck_count = duck.file_count() if duck and hasattr(duck, "file_count") else 0
    llm_ok = cognitive.is_loaded if cognitive and hasattr(cognitive, "is_loaded") else False

    print(f"\u2705 Daemon activo | Perfil: {ctx.get('active_profile', '?')} | "
          f"Fragmentos FTS: {fts_count} | Archivos DuckDB: {duck_count} | "
          f"LLM: {'activo' if llm_ok else 'inactivo'}")
    return 0


def _cmd_status(args) -> int:
    app = _get_app()
    if not app:
        print("Error: No se pudo inicializar.", file=sys.stderr)
        return 1
    ctx = app.context
    status = {
        "version": ctx.get("version", "?"),
        "profile": ctx.get("active_profile", "?"),
        "provider": ctx.get("provider_type", "none"),
        "http_running": ctx.get("http_server_running", False),
        "server_url": ctx.get("server_url", None),
    }
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0


def _cmd_serve(args) -> int:
    from oraculo.app import OraculoApp
    os.environ["ORACULO_PORT"] = str(args.port)
    app = OraculoApp(mode="server")
    return app.start()


if __name__ == "__main__":
    sys.exit(run_cli())
