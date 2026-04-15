"""
Modulo: oraculo.cli.main
Proposito: CLI con subcomandos: query, index, profile, status, serve.
"""
from __future__ import annotations
import argparse
import json
import sys
import logging

logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="oraculo",
        description="El Oraculo McComics — Motor de inteligencia de codigo local",
    )
    parser.add_argument("--profile", default="enterprise", help="Perfil de seguridad (basic/enterprise/banking)")
    parser.add_argument("--data-dir", default=None, help="Directorio de datos")
    parser.add_argument("--verbose", "-v", action="store_true", help="Modo verbose")

    sub = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # query
    q = sub.add_parser("query", help="Buscar en el indice")
    q.add_argument("text", help="Texto de busqueda")
    q.add_argument("--limit", "-n", type=int, default=10, help="Maximo de resultados")
    q.add_argument("--json", action="store_true", dest="as_json", help="Salida en JSON")

    # index
    idx = sub.add_parser("index", help="Indexar archivos")
    idx.add_argument("paths", nargs="+", help="Archivos o directorios a indexar")
    idx.add_argument("--force", action="store_true", help="Forzar re-indexacion")

    # profile
    p = sub.add_parser("profile", help="Gestionar perfil de seguridad")
    p.add_argument("action", choices=["show", "switch", "list"], help="Accion")
    p.add_argument("--name", help="Nombre del perfil para switch")

    # status
    sub.add_parser("status", help="Ver estado del sistema")

    # serve
    s = sub.add_parser("serve", help="Iniciar servidor HTTP")
    s.add_argument("--host", default="127.0.0.1", help="Host (default: 127.0.0.1)")
    s.add_argument("--port", type=int, default=9741, help="Puerto (default: 9741)")

    return parser


def run_cli(argv: list[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "query":
        return _cmd_query(args)
    if args.command == "index":
        return _cmd_index(args)
    if args.command == "profile":
        return _cmd_profile(args)
    if args.command == "status":
        return _cmd_status(args)
    if args.command == "serve":
        return _cmd_serve(args)

    return 0


def _cmd_query(args) -> int:
    print(json.dumps({
        "command": "query",
        "text": args.text,
        "limit": args.limit,
        "profile": args.profile,
        "note": "Requiere servidor corriendo o stores inicializados",
    }, indent=2, ensure_ascii=False))
    return 0


def _cmd_index(args) -> int:
    print(json.dumps({
        "command": "index",
        "paths": args.paths,
        "force": args.force,
        "profile": args.profile,
    }, indent=2, ensure_ascii=False))
    return 0


def _cmd_profile(args) -> int:
    if args.action == "list":
        profiles = ["basic", "enterprise", "banking"]
        for p in profiles:
            marker = " <-- activo" if p == args.profile else ""
            print(f"  {p}{marker}")
    elif args.action == "show":
        print(f"Perfil activo: {args.profile}")
    elif args.action == "switch":
        if not args.name:
            print("Error: --name requerido para switch")
            return 1
        print(f"Cambiando a perfil: {args.name}")
    return 0


def _cmd_status(args) -> int:
    print(json.dumps({
        "command": "status",
        "profile": args.profile,
        "data_dir": args.data_dir or "default",
    }, indent=2, ensure_ascii=False))
    return 0


def _cmd_serve(args) -> int:
    print(f"Iniciando servidor en http://{args.host}:{args.port}")
    print("(Requiere inicializacion completa de stores)")
    return 0


if __name__ == "__main__":
    sys.exit(run_cli())
