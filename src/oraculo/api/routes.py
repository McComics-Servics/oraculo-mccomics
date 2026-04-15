"""
Modulo: oraculo.api.routes
Proposito: Definicion de rutas API — query, profile, index, health, status.
Documento de LEY: API_CONTRACT_SPEC.md
"""
from __future__ import annotations
import logging
import time
from typing import Any

from oraculo.api.server import Router

logger = logging.getLogger(__name__)


def register_routes(router: Router, app_context: dict[str, Any]) -> None:
    """Registra todas las rutas en el router usando el contexto de la aplicacion."""

    def health(data, handler):
        return {
            "status": "ok",
            "version": app_context.get("version", "4.0.0"),
            "profile": app_context.get("active_profile", "unknown"),
            "uptime_s": time.monotonic() - app_context.get("start_time", time.monotonic()),
        }

    def status(data, handler):
        fts = app_context.get("fts_store")
        duck = app_context.get("duck_store")
        cognitive = app_context.get("cognitive")
        return {
            "profile": app_context.get("active_profile", "unknown"),
            "indexed_files": fts.count() if fts else 0,
            "indexed_fragments": fts.count() if fts else 0,
            "model_info": cognitive.model_info if cognitive else {},
            "server_url": app_context.get("server_url", ""),
        }

    def query(data, handler):
        q = data.get("query") or data.get("q", "")
        limit = int(data.get("limit", 10))
        if not q:
            return {"error": "query_required", "message": "Parametro 'query' es requerido"}

        assembler = app_context.get("assembler")
        if not assembler:
            return {"error": "not_initialized", "message": "Assembler no inicializado"}

        result = assembler.assemble(q, limit=limit)
        return result.to_dict()

    def query_stream(data, handler):
        """Query con streaming SSE."""
        q = data.get("query") or data.get("q", "")
        if not q:
            return {"error": "query_required"}

        handler.send_response(200)
        handler.send_header("Content-Type", "text/event-stream")
        handler.send_header("Cache-Control", "no-cache")
        handler.send_header("Access-Control-Allow-Origin", "*")
        handler.end_headers()
        handler._response_sent = True

        handler.send_sse_event("start", {"query": q})

        assembler = app_context.get("assembler")
        if assembler:
            result = assembler.assemble(q)
            for i, frag in enumerate(result.fragments):
                handler.send_sse_event("fragment", {
                    "index": i,
                    "fragment_id": frag.fragment_id,
                    "file_path": frag.file_path,
                    "content": frag.content[:200],
                    "trust_tier": frag.trust_tier,
                    "score": frag.rrf_score,
                })

            handler.send_sse_event("complete", {
                "total": result.total_fragments,
                "time_ms": result.assembly_time_ms,
            })
        else:
            handler.send_sse_event("error", {"message": "assembler not initialized"})

        return None

    def profile_get(data, handler):
        engine = app_context.get("policy_engine")
        if not engine:
            return {"error": "not_initialized"}
        return {
            "active": app_context.get("active_profile", "unknown"),
            "available": ["basic", "enterprise", "banking"],
        }

    def profile_switch(data, handler):
        name = data.get("profile", "")
        passphrase = data.get("passphrase")
        engine = app_context.get("policy_engine")
        if not engine:
            return {"error": "not_initialized"}
        try:
            result = engine.activate(name, passphrase=passphrase)
            app_context["active_profile"] = name
            return {"success": result.success, "profile": name, "warnings": result.warnings}
        except Exception as e:
            return {"error": "switch_failed", "message": str(e)}

    def index_trigger(data, handler):
        paths = data.get("paths", [])
        pipeline = app_context.get("index_pipeline")
        if not pipeline:
            return {"error": "not_initialized"}
        from pathlib import Path
        path_list = [Path(p) for p in paths]
        stats = pipeline.index_batch(path_list, force=data.get("force", False))
        return {
            "processed": stats.files_processed,
            "skipped": stats.files_skipped,
            "errors": stats.files_errored,
            "fragments": stats.fragments_created,
        }

    router.add("GET", "/api/v1/health", health)
    router.add("GET", "/api/v1/status", status)
    router.add("POST", "/api/v1/query", query)
    router.add("POST", "/api/v1/query/stream", query_stream)
    router.add("GET", "/api/v1/profile", profile_get)
    router.add("POST", "/api/v1/profile/switch", profile_switch)
    router.add("POST", "/api/v1/index", index_trigger)
