"""Tests de integracion end-to-end — El Oraculo McComics v4.0.
Verifica que las 7 capas se conectan correctamente via OraculoApp.
"""
from __future__ import annotations
import json
import os
import shutil
from pathlib import Path

import pytest

from oraculo.__version__ import __version__
from oraculo.app import OraculoApp

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def app_env(tmp_path):
    """Crea un entorno temporal copiando los perfiles reales del proyecto."""
    profiles_src = REPO_ROOT / "profiles"
    profiles_dst = tmp_path / "profiles"
    if profiles_src.exists():
        shutil.copytree(profiles_src, profiles_dst)
    else:
        profiles_dst.mkdir()

    db_dir = tmp_path / "db_storage"
    db_dir.mkdir()

    old_env = {}
    env_vars = {
        "ORACULO_DATA_DIR": str(db_dir),
        "ORACULO_PROFILE": "basic",
        "ORACULO_LOG_LEVEL": "warning",
        "ORACULO_NO_HTTP": "1",
        "ORACULO_DEGRADED_OK": "1",
    }
    for k, v in env_vars.items():
        old_env[k] = os.environ.get(k)
        os.environ[k] = v

    yield tmp_path

    for k, v in old_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


class TestOraculoAppIntegration:
    def test_headless_start_returns_context(self, app_env):
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        assert "error" not in ctx
        assert ctx["version"] == __version__
        assert ctx["active_profile"] == "basic"
        assert ctx["policy_engine"] is not None
        assert ctx["fts_store"] is not None
        assert ctx["duck_store"] is not None
        assert ctx["index_pipeline"] is not None
        assert ctx["assembler"] is not None
        app.shutdown()

    def test_policy_engine_switch(self, app_env):
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        engine = ctx["policy_engine"]
        assert engine.current_name == "basic"
        result = engine.activate("enterprise")
        assert result.success
        assert engine.current_name == "enterprise"
        app.shutdown()

    def test_index_pipeline_file(self, app_env):
        test_file = app_env / "sample.py"
        test_file.write_text("def hello():\n    return 'world'\n\ndef foo():\n    pass\n")

        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        pipeline = ctx["index_pipeline"]
        stats = pipeline.index_file(test_file)
        assert stats.files_processed == 1
        assert stats.fragments_created >= 1
        app.shutdown()

    def test_assembler_query_after_index(self, app_env):
        test_file = app_env / "calculator.py"
        test_file.write_text(
            "def add(a, b):\n    return a + b\n\n"
            "def subtract(a, b):\n    return a - b\n\n"
            "def multiply(a, b):\n    return a * b\n"
        )

        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        pipeline = ctx["index_pipeline"]
        pipeline.index_file(test_file)

        assembler = ctx["assembler"]
        payload = assembler.assemble("add function", limit=5)
        assert payload.total_fragments >= 0
        app.shutdown()

    def test_stores_open_and_close(self, app_env):
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        fts = ctx["fts_store"]
        duck = ctx["duck_store"]
        assert fts._conn is not None
        assert duck._conn is not None
        app.shutdown()
        assert fts._conn is None
        assert duck._conn is None

    def test_cognitive_degrades_gracefully(self, app_env):
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        cognitive = ctx["cognitive"]
        assert cognitive is not None
        app.shutdown()

    def test_downloader_in_context(self, app_env):
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        dl = ctx["downloader"]
        assert dl is not None
        available = dl.list_available()
        assert len(available) >= 3
        app.shutdown()

    def test_audit_chain_for_enterprise(self, app_env):
        os.environ["ORACULO_PROFILE"] = "enterprise"
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        assert ctx["audit_chain"] is not None
        app.shutdown()

    def test_audit_chain_absent_for_basic(self, app_env):
        os.environ["ORACULO_PROFILE"] = "basic"
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        assert ctx["audit_chain"] is None
        app.shutdown()

    def test_ipc_bridge_from_context(self, app_env):
        from oraculo.api.ipc_bridge import IPCBridge
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        bridge = IPCBridge(ctx)

        health = json.loads(bridge.health())
        assert health["status"] == "ok"
        assert health["version"] == __version__

        profile = json.loads(bridge.get_profile())
        assert profile["active"] == "basic"

        training = json.loads(bridge.get_training_status())
        assert "data_dir" in training

        models = json.loads(bridge.list_models())
        assert len(models) >= 3

        compliance = json.loads(bridge.get_compliance())
        assert compliance["profile"] == "basic"

        app.shutdown()

    def test_full_flow_index_query_switch(self, app_env):
        """Test e2e completo: arrancar -> indexar -> query -> switch perfil."""
        src_file = app_env / "services.py"
        src_file.write_text(
            "class UserService:\n"
            "    def get_user(self, user_id):\n"
            "        return {'id': user_id, 'name': 'McComics'}\n\n"
            "    def create_user(self, name, email):\n"
            "        return {'name': name, 'email': email}\n"
        )

        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()

        pipeline = ctx["index_pipeline"]
        stats = pipeline.index_file(src_file)
        assert stats.files_processed == 1

        assembler = ctx["assembler"]
        payload = assembler.assemble("UserService get_user", limit=5)
        assert payload is not None

        engine = ctx["policy_engine"]
        switch = engine.activate("enterprise")
        assert switch.success

        from oraculo.api.ipc_bridge import IPCBridge
        bridge = IPCBridge(ctx)
        status = json.loads(bridge.get_status())
        assert status["indexed_files"] >= 0

        app.shutdown()

    def test_index_batch_multiple_files(self, app_env):
        files = []
        for i in range(5):
            f = app_env / f"mod_{i}.py"
            f.write_text(f"def func_{i}():\n    return {i}\n")
            files.append(f)

        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()
        pipeline = ctx["index_pipeline"]
        stats = pipeline.index_batch(files)
        assert stats.files_processed == 5
        assert stats.fragments_created >= 5
        app.shutdown()

    def test_server_start_stop(self, app_env):
        os.environ["ORACULO_NO_HTTP"] = "0"
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()

        from oraculo.api.server import OraculoServer
        from oraculo.api.routes import register_routes
        server = OraculoServer(port=0)
        register_routes(server.router, ctx)
        server.start(background=True)
        assert server.is_running

        real_port = server._httpd.server_address[1]
        import urllib.request
        try:
            resp = urllib.request.urlopen(f"http://127.0.0.1:{real_port}/api/v1/health", timeout=3)
            data = json.loads(resp.read())
            assert data["status"] == "ok"
        finally:
            server.stop()
            app.shutdown()

    def test_profile_switch_updates_context(self, app_env):
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()

        from oraculo.api.ipc_bridge import IPCBridge
        bridge = IPCBridge(ctx)
        result = json.loads(bridge.switch_profile("enterprise"))
        assert result["success"] is True
        assert ctx["active_profile"] == "enterprise"
        app.shutdown()

    def test_compliance_check_via_bridge(self, app_env):
        os.environ["ORACULO_PROFILE"] = "banking"
        app = OraculoApp(repo_root=app_env, mode="headless")
        ctx = app.start_headless()

        from oraculo.api.ipc_bridge import IPCBridge
        bridge = IPCBridge(ctx)
        compliance = json.loads(bridge.get_compliance())
        assert compliance["profile"] == "banking"
        assert "critical_failures" in compliance or "passed" in compliance
        app.shutdown()
