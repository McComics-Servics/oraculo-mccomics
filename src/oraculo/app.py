"""
Modulo: oraculo.app
Proposito: Integrador principal que conecta las 7 capas del Oraculo McComics.
Flujo: Config -> PreFlight -> PolicyEngine -> Stores -> IndexPipeline -> Assembler -> Cognitive -> Server/UI

(C) 2026 McComics Servicios Generales — Lima, Peru
"""
from __future__ import annotations
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any

from oraculo.__version__ import __version__
from oraculo.core.config import load_runtime_config, RuntimeConfig
from oraculo.core.logging_setup import setup_logging
from oraculo.policy.engine import PolicyEngine
from oraculo.pre_flight import run_pre_flight
from oraculo.index.sqlite_store import SqliteFtsStore
from oraculo.index.duckdb_store import DuckDbStore
from oraculo.index.pipeline import IndexPipeline
from oraculo.assembler.pipeline import AssemblyPipeline
from oraculo.cognitive.core import CognitiveCore, CognitiveConfig
from oraculo.cognitive.model_downloader import ModelDownloader, get_data_dir
from oraculo.api.server import OraculoServer
from oraculo.api.routes import register_routes
from oraculo.audit.audit_chain import AuditChain

logger = logging.getLogger("oraculo.app")


class OraculoApp:
    """Aplicacion completa El Oraculo McComics v4.0.
    Integra las 7 capas arquitecturales en un unico punto de arranque.
    """

    def __init__(self, repo_root: Path | None = None, mode: str = "ui"):
        self._repo_root = repo_root or Path.cwd()
        self._mode = mode
        self._cfg: RuntimeConfig | None = None
        self._engine: PolicyEngine | None = None
        self._fts: SqliteFtsStore | None = None
        self._duck: DuckDbStore | None = None
        self._pipeline: IndexPipeline | None = None
        self._assembler: AssemblyPipeline | None = None
        self._cognitive: CognitiveCore | None = None
        self._server: OraculoServer | None = None
        self._audit: AuditChain | None = None
        self._downloader: ModelDownloader | None = None
        self._context: dict[str, Any] = {}
        self._running = False

    @property
    def context(self) -> dict[str, Any]:
        return self._context

    def start(self) -> int:
        """Arranca la aplicacion completa. Retorna 0 en exito."""
        try:
            self._cfg = load_runtime_config(self._repo_root)
            setup_logging(self._cfg.log_level, log_file=self._cfg.data_dir / "oraculo.log")
            logger.info("=" * 60)
            logger.info("El Oraculo McComics v%s — Iniciando", __version__)
            logger.info("=" * 60)

            if not self._pre_flight():
                return 2

            self._init_policy_engine()
            self._init_stores()
            self._init_index_pipeline()
            self._init_assembler()
            self._init_cognitive()
            self._init_audit()
            self._init_downloader()
            self._build_context()

            if self._mode == "server" and not self._cfg.no_http:
                self._init_server()

            self._running = True
            self._register_signals()

            if self._mode == "ui":
                self._launch_ui()
            elif self._mode == "server":
                self._run_server_loop()
            else:
                logger.info("Modo headless: contexto listo, retornando.")

            return 0

        except KeyboardInterrupt:
            logger.info("Interrupcion de usuario.")
            return 0
        except Exception as e:
            logger.exception("Error fatal: %s", e)
            return 1
        finally:
            self.shutdown()

    def start_headless(self) -> dict[str, Any]:
        """Arranca sin UI ni servidor — para testing e integracion.
        Retorna el contexto completo."""
        self._mode = "headless"
        self._cfg = load_runtime_config(self._repo_root)
        setup_logging(self._cfg.log_level)

        pre = run_pre_flight()
        if not pre.ok and not self._cfg.degraded_ok:
            return {"error": "pre_flight_failed", "failures": pre.critical_failures}

        self._init_policy_engine()
        self._init_stores()
        self._init_index_pipeline()
        self._init_assembler()
        self._init_cognitive()
        self._init_audit()
        self._init_downloader()
        self._build_context()
        self._running = True
        return self._context

    def shutdown(self) -> None:
        """Apagado limpio de todos los subsistemas."""
        if not self._running:
            return
        self._running = False
        logger.info("Apagando El Oraculo...")

        if self._server and self._server.is_running:
            self._server.stop()
        if self._cognitive and self._cognitive.is_loaded:
            self._cognitive.shutdown()
        if self._fts:
            self._fts.close()
        if self._duck:
            self._duck.close()

        logger.info("El Oraculo McComics apagado correctamente.")

    def _pre_flight(self) -> bool:
        rep = run_pre_flight()
        if not rep.ok and not self._cfg.degraded_ok:
            for msg in rep.critical_failures:
                logger.error("PRE-FLIGHT CRITICO: %s", msg)
            return False
        for msg in rep.info:
            logger.debug("PRE-FLIGHT: %s", msg)
        return True

    def _init_policy_engine(self) -> None:
        self._engine = PolicyEngine(
            profiles_dir=self._cfg.profiles_dir,
            history_file=self._cfg.data_dir / "profiles" / "history.jsonl",
        )
        result = self._engine.activate(self._cfg.initial_profile)
        if not result.success:
            logger.warning("Perfil %s no activado: %s — usando degraded",
                          self._cfg.initial_profile, result.error_message)
        else:
            logger.info("Perfil activo: %s", self._engine.current_name)

    def _init_stores(self) -> None:
        db_dir = self._cfg.data_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)

        self._fts = SqliteFtsStore(db_dir / "fts.sqlite3")
        self._fts.open()
        logger.info("FTS Store abierto: %s", db_dir / "fts.sqlite3")

        self._duck = DuckDbStore(db_dir / "vectors.duckdb")
        self._duck.open()
        logger.info("DuckDB Store abierto: %s", db_dir / "vectors.duckdb")

    def _init_index_pipeline(self) -> None:
        self._pipeline = IndexPipeline(self._fts, self._duck)
        logger.info("IndexPipeline inicializado.")

    def _init_assembler(self) -> None:
        profile = self._engine.current_name or "enterprise"
        budget = 4096
        if self._engine.current:
            budget = self._engine.current.get("context_assembly", {}).get("total_budget_tokens", 4096)

        self._assembler = AssemblyPipeline(
            fts_store=self._fts,
            duck_store=self._duck,
            profile=profile,
            total_budget=budget,
        )
        logger.info("AssemblyPipeline inicializado (budget=%d tokens).", budget)

    def _init_cognitive(self) -> None:
        model_path = self._cfg.llm_model
        if not model_path:
            dl = ModelDownloader()
            for mid in ["qwen2.5-coder:3b-instruct-q4_K_M",
                        "qwen2.5-coder:1.5b-instruct-q4_K_M",
                        "qwen2.5-coder:7b-instruct-q4_K_M"]:
                p = dl.get_model_path(mid)
                if p:
                    model_path = str(p)
                    break

        provider_type = "llama_cpp"
        if not model_path:
            provider_type = "ollama"
            logger.info("Sin modelo local GGUF — intentando Ollama como fallback.")

        config = CognitiveConfig(
            provider_type=provider_type,
            model_path=model_path,
        )
        self._cognitive = CognitiveCore(config)

        try:
            ok = self._cognitive.initialize()
            if ok:
                logger.info("Cognitive Core activo: %s", self._cognitive.model_info)
            else:
                logger.warning("Cognitive Core no pudo inicializarse — modo degradado (sin LLM).")
        except Exception as e:
            logger.warning("Cognitive Core error: %s — continuando sin LLM.", e)

    def _init_audit(self) -> None:
        profile = self._engine.current_name or "basic"
        if profile in ("enterprise", "banking"):
            audit_path = self._cfg.data_dir / "audit" / "chain.jsonl"
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            self._audit = AuditChain(audit_path)
            self._audit.record("system", "oraculo", {"event": "startup", "profile": profile})
            logger.info("AuditChain activada: %s", audit_path)
        else:
            logger.debug("AuditChain omitida (perfil basic).")

    def _init_downloader(self) -> None:
        self._downloader = ModelDownloader()

    def _build_context(self) -> None:
        self._context = {
            "version": __version__,
            "active_profile": self._engine.current_name or "basic",
            "start_time": time.monotonic(),
            "policy_engine": self._engine,
            "fts_store": self._fts,
            "duck_store": self._duck,
            "index_pipeline": self._pipeline,
            "assembler": self._assembler,
            "cognitive": self._cognitive,
            "audit_chain": self._audit,
            "downloader": self._downloader,
            "auto_training": False,
            "provider_type": self._cognitive._config.provider_type if self._cognitive else "none",
        }

    def _init_server(self) -> None:
        port = self._cfg.http_port or 9741
        profile = self._engine.current_name or "basic"
        auth_token = None
        if profile in ("enterprise", "banking"):
            import secrets
            auth_token = secrets.token_urlsafe(32)
            self._context["auth_token"] = auth_token
            logger.info("Token de autenticacion generado para perfil %s.", profile)

        self._server = OraculoServer(port=port, auth_token=auth_token)
        register_routes(self._server.router, self._context)
        self._server.start(background=True)
        self._context["server_url"] = self._server.url
        self._context["http_server_running"] = True
        logger.info("Servidor HTTP iniciado en %s", self._server.url)

    def _launch_ui(self) -> None:
        if not self._cfg.no_http:
            self._init_server()

        from oraculo.ui.window import launch_window
        logger.info("Lanzando UI pywebview...")
        launch_window(self._context, debug=False)

    def _run_server_loop(self) -> None:
        logger.info("Servidor corriendo. Ctrl+C para detener.")
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    def _register_signals(self) -> None:
        def _handler(sig, frame):
            logger.info("Senal %s recibida, apagando...", sig)
            self._running = False
        try:
            signal.signal(signal.SIGINT, _handler)
            signal.signal(signal.SIGTERM, _handler)
        except (ValueError, OSError):
            pass


def run_app(mode: str = "ui", repo_root: Path | None = None) -> int:
    """Punto de entrada principal recomendado."""
    app = OraculoApp(repo_root=repo_root, mode=mode)
    return app.start()


if __name__ == "__main__":
    mode = "ui"
    if "--server" in sys.argv:
        mode = "server"
    elif "--headless" in sys.argv:
        mode = "headless"
    sys.exit(run_app(mode=mode))
