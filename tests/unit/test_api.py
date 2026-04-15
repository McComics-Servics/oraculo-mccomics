"""Tests para F7 — API HTTP, Auth, IPC Bridge, Cliente Python."""
from __future__ import annotations
import json
import time
import urllib.request
import urllib.error
import pytest

from oraculo.api.server import Router, OraculoServer
from oraculo.api.auth import LocalAuthManager, AuthToken, TOKEN_LENGTH
from oraculo.api.ipc_bridge import IPCBridge
from oraculo.api.routes import register_routes
from oraculo.client.python_client import OraculoClient, QueryResult


# ── Router ──────────────────────────────────────────

class TestRouter:
    def test_add_and_match(self):
        r = Router()
        handler = lambda d, h: {"ok": True}
        r.add("GET", "/test", handler)
        assert r.match("GET", "/test") is handler

    def test_match_returns_none_for_unknown(self):
        r = Router()
        assert r.match("GET", "/nope") is None

    def test_case_insensitive_method(self):
        r = Router()
        r.add("post", "/x", lambda d, h: None)
        assert r.match("POST", "/x") is not None

    def test_list_routes(self):
        r = Router()
        r.add("GET", "/a", lambda d, h: None)
        r.add("POST", "/b", lambda d, h: None)
        routes = r.list_routes()
        assert ("GET", "/a") in routes
        assert ("POST", "/b") in routes

    def test_decorator_get(self):
        r = Router()
        @r.get("/dec")
        def handler(d, h):
            return {"decorated": True}
        assert r.match("GET", "/dec") is handler

    def test_decorator_post(self):
        r = Router()
        @r.post("/dec")
        def handler(d, h):
            return {"posted": True}
        assert r.match("POST", "/dec") is handler


# ── Auth ────────────────────────────────────────────

class TestLocalAuthManager:
    def test_basic_no_auth_required(self):
        auth = LocalAuthManager(profile="basic")
        assert auth.auth_required is False
        assert auth.validate_token("") is True

    def test_enterprise_requires_auth(self):
        auth = LocalAuthManager(profile="enterprise")
        assert auth.auth_required is True
        assert auth.validate_token("") is False

    def test_generate_and_validate(self):
        auth = LocalAuthManager(profile="enterprise")
        token = auth.generate_token()
        assert len(token) == TOKEN_LENGTH * 2  # hex
        assert auth.validate_token(token) is True

    def test_invalid_token_rejected(self):
        auth = LocalAuthManager(profile="enterprise")
        assert auth.validate_token("fake_token_123") is False

    def test_revoke_token(self):
        auth = LocalAuthManager(profile="enterprise")
        token = auth.generate_token()
        assert auth.revoke_token(token) is True
        assert auth.validate_token(token) is False

    def test_revoke_all(self):
        auth = LocalAuthManager(profile="enterprise")
        auth.generate_token()
        auth.generate_token()
        count = auth.revoke_all()
        assert count == 2

    def test_expired_token_rejected(self):
        auth = LocalAuthManager(profile="enterprise")
        token = auth.generate_token(ttl=0)
        time.sleep(0.05)
        assert auth.validate_token(token) is False

    def test_cleanup_expired(self):
        auth = LocalAuthManager(profile="enterprise")
        auth.generate_token(ttl=0)
        auth.generate_token(ttl=86400)
        time.sleep(0.05)
        cleaned = auth.cleanup_expired()
        assert cleaned == 1

    def test_set_profile_banking_reduces_ttl(self):
        auth = LocalAuthManager(profile="enterprise")
        token = auth.generate_token(ttl=86400)
        auth.set_profile("banking")
        stored = auth._tokens[token]
        assert stored.ttl_seconds <= 3600

    def test_auth_token_is_expired_property(self):
        t = AuthToken(token="x", created_at=time.time() - 100, ttl_seconds=10, profile="basic")
        assert t.is_expired is True
        t2 = AuthToken(token="y", created_at=time.time(), ttl_seconds=3600, profile="basic")
        assert t2.is_expired is False


# ── IPC Bridge ──────────────────────────────────────

class TestIPCBridge:
    def _make_bridge(self, **overrides):
        ctx = {"version": "4.0.0", "active_profile": "enterprise"}
        ctx.update(overrides)
        return IPCBridge(ctx)

    def test_health(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.health())
        assert result["status"] == "ok"
        assert result["version"] == "4.0.0"

    def test_query_not_initialized(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.query("test"))
        assert result["error"] == "not_initialized"

    def test_get_profile(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.get_profile())
        assert result["active"] == "enterprise"
        assert "basic" in result["available"]

    def test_switch_profile_not_initialized(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.switch_profile("basic"))
        assert result["error"] == "not_initialized"

    def test_get_status_no_stores(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.get_status())
        assert result["profile"] == "enterprise"
        assert result["indexed_files"] == 0

    def test_index_paths_not_initialized(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.index_paths('["file.py"]'))
        assert result["error"] == "not_initialized"

    def test_get_model_info_no_cognitive(self):
        bridge = self._make_bridge()
        result = json.loads(bridge.get_model_info())
        assert result["loaded"] is False


# ── Routes Registration ─────────────────────────────

class TestRoutes:
    def test_register_routes_adds_all(self):
        router = Router()
        ctx = {"version": "4.0.0", "active_profile": "basic", "start_time": time.monotonic()}
        register_routes(router, ctx)
        routes = router.list_routes()
        assert len(routes) == 7
        assert ("GET", "/api/v1/health") in routes
        assert ("POST", "/api/v1/query") in routes
        assert ("POST", "/api/v1/query/stream") in routes

    def test_health_handler(self):
        router = Router()
        ctx = {"version": "4.0.0", "active_profile": "basic", "start_time": time.monotonic()}
        register_routes(router, ctx)
        handler = router.match("GET", "/api/v1/health")
        result = handler({}, None)
        assert result["status"] == "ok"
        assert result["version"] == "4.0.0"

    def test_status_handler_no_stores(self):
        router = Router()
        ctx = {"version": "4.0.0", "active_profile": "enterprise"}
        register_routes(router, ctx)
        handler = router.match("GET", "/api/v1/status")
        result = handler({}, None)
        assert result["profile"] == "enterprise"
        assert result["indexed_files"] == 0

    def test_query_handler_missing_query(self):
        router = Router()
        ctx = {"version": "4.0.0", "active_profile": "basic"}
        register_routes(router, ctx)
        handler = router.match("POST", "/api/v1/query")
        result = handler({}, None)
        assert result["error"] == "query_required"

    def test_query_handler_no_assembler(self):
        router = Router()
        ctx = {"version": "4.0.0", "active_profile": "basic"}
        register_routes(router, ctx)
        handler = router.match("POST", "/api/v1/query")
        result = handler({"query": "test"}, None)
        assert result["error"] == "not_initialized"

    def test_profile_get_no_engine(self):
        router = Router()
        ctx = {}
        register_routes(router, ctx)
        handler = router.match("GET", "/api/v1/profile")
        result = handler({}, None)
        assert result["error"] == "not_initialized"

    def test_index_no_pipeline(self):
        router = Router()
        ctx = {}
        register_routes(router, ctx)
        handler = router.match("POST", "/api/v1/index")
        result = handler({"paths": ["a.py"]}, None)
        assert result["error"] == "not_initialized"


# ── Server (integration light) ──────────────────────

class TestOraculoServer:
    def test_server_start_stop(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        server.router.add("GET", "/api/v1/health", lambda d, h: {"status": "ok"})
        server.start(background=True)
        assert server.is_running
        server.stop()
        time.sleep(0.1)
        assert not server.is_running

    def test_server_url_property(self):
        server = OraculoServer(host="127.0.0.1", port=9999)
        assert server.url == "http://127.0.0.1:9999"

    def test_server_http_health(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        ctx = {"version": "4.0.0", "active_profile": "test", "start_time": time.monotonic()}
        register_routes(server.router, ctx)
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            url = f"http://127.0.0.1:{port}/api/v1/health"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
        finally:
            server.stop()

    def test_server_404(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            url = f"http://127.0.0.1:{port}/nonexistent"
            req = urllib.request.Request(url)
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(req, timeout=5)
            assert exc_info.value.code == 404
        finally:
            server.stop()

    def test_server_auth_rejection(self):
        server = OraculoServer(host="127.0.0.1", port=0, auth_token="secret123")
        server.router.add("GET", "/api/v1/health", lambda d, h: {"status": "ok"})
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            url = f"http://127.0.0.1:{port}/api/v1/health"
            req = urllib.request.Request(url)
            with pytest.raises(urllib.error.HTTPError) as exc_info:
                urllib.request.urlopen(req, timeout=5)
            assert exc_info.value.code == 401
        finally:
            server.stop()

    def test_server_auth_accepted(self):
        server = OraculoServer(host="127.0.0.1", port=0, auth_token="secret123")
        server.router.add("GET", "/api/v1/health", lambda d, h: {"status": "ok"})
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            url = f"http://127.0.0.1:{port}/api/v1/health"
            req = urllib.request.Request(url, headers={"Authorization": "Bearer secret123"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
        finally:
            server.stop()

    def test_server_post_query(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        ctx = {"version": "4.0.0", "active_profile": "basic", "start_time": time.monotonic()}
        register_routes(server.router, ctx)
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            url = f"http://127.0.0.1:{port}/api/v1/query"
            body = json.dumps({"query": "test"}).encode("utf-8")
            req = urllib.request.Request(url, data=body, method="POST",
                                        headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            assert data["error"] == "not_initialized"
        finally:
            server.stop()


# ── QueryResult ─────────────────────────────────────

class TestQueryResult:
    def test_from_dict(self):
        data = {
            "fragments": [{"id": "f1"}],
            "total_fragments": 5,
            "query": "test query",
            "assembly_time_ms": 12.5,
        }
        qr = QueryResult.from_dict(data)
        assert qr.total == 5
        assert qr.query == "test query"
        assert qr.time_ms == 12.5
        assert len(qr.fragments) == 1

    def test_from_dict_defaults(self):
        qr = QueryResult.from_dict({})
        assert qr.total == 0
        assert qr.query == ""
        assert qr.fragments == []


# ── Client (con servidor real) ──────────────────────

class TestOraculoClient:
    def test_client_health(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        ctx = {"version": "4.0.0", "active_profile": "test", "start_time": time.monotonic()}
        register_routes(server.router, ctx)
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            client = OraculoClient(base_url=f"http://127.0.0.1:{port}")
            result = client.health()
            assert result["status"] == "ok"
        finally:
            server.stop()

    def test_client_status(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        ctx = {"version": "4.0.0", "active_profile": "test"}
        register_routes(server.router, ctx)
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            client = OraculoClient(base_url=f"http://127.0.0.1:{port}")
            result = client.status()
            assert result["profile"] == "test"
        finally:
            server.stop()

    def test_client_query(self):
        server = OraculoServer(host="127.0.0.1", port=0)
        ctx = {"version": "4.0.0", "active_profile": "test"}
        register_routes(server.router, ctx)
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            client = OraculoClient(base_url=f"http://127.0.0.1:{port}")
            qr = client.query("test search")
            assert isinstance(qr, QueryResult)
        finally:
            server.stop()

    def test_client_connection_failed(self):
        client = OraculoClient(base_url="http://127.0.0.1:1")
        result = client.health()
        assert result["error"] == "connection_failed"

    def test_client_with_token(self):
        server = OraculoServer(host="127.0.0.1", port=0, auth_token="tok123")
        server.router.add("GET", "/api/v1/health", lambda d, h: {"status": "ok"})
        server.start(background=True)
        try:
            port = server._httpd.server_address[1]
            client = OraculoClient(base_url=f"http://127.0.0.1:{port}", token="tok123")
            result = client.health()
            assert result["status"] == "ok"
        finally:
            server.stop()
