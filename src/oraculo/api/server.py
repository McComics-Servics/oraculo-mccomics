"""
Modulo: oraculo.api.server
Proposito: Servidor HTTP local usando http.server stdlib. Sin dependencias externas.
Documento de LEY: API_CONTRACT_SPEC.md
"""
from __future__ import annotations
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9741


class OraculoHandler(BaseHTTPRequestHandler):
    """HTTP handler con routing a funciones registradas."""

    def log_message(self, format, *args):
        logger.debug(format, *args)

    def do_GET(self):
        parsed = urlparse(self.path)
        route = self.server.router.match("GET", parsed.path)
        if route:
            params = parse_qs(parsed.query)
            self._handle(route, params)
        else:
            self._send_json(404, {"error": "not_found", "path": parsed.path})

    def do_POST(self):
        parsed = urlparse(self.path)
        route = self.server.router.match("POST", parsed.path)
        if route:
            body = self._read_body()
            self._handle(route, body)
        else:
            self._send_json(404, {"error": "not_found", "path": parsed.path})

    def _handle(self, handler, data):
        try:
            token = self.headers.get("Authorization", "")
            if self.server.auth_token and token != f"Bearer {self.server.auth_token}":
                self._send_json(401, {"error": "unauthorized"})
                return
            result = handler(data, self)
            if result is not None and not getattr(self, '_response_sent', False):
                self._send_json(200, result)
        except Exception as e:
            logger.error("Error en handler: %s", e)
            self._send_json(500, {"error": "internal_error", "message": str(e)})

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            return {}

    def _send_json(self, code: int, data: Any) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_sse_event(self, event: str, data: Any) -> None:
        """Envia un evento SSE al cliente."""
        payload = f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(payload.encode("utf-8"))
        self.wfile.flush()


class Router:
    """Router simple: mapea (method, path) a handler functions."""

    def __init__(self):
        self._routes: dict[tuple[str, str], Any] = {}

    def get(self, path: str):
        def decorator(fn):
            self._routes[("GET", path)] = fn
            return fn
        return decorator

    def post(self, path: str):
        def decorator(fn):
            self._routes[("POST", path)] = fn
            return fn
        return decorator

    def add(self, method: str, path: str, handler) -> None:
        self._routes[(method.upper(), path)] = handler

    def match(self, method: str, path: str):
        return self._routes.get((method.upper(), path))

    def list_routes(self) -> list[tuple[str, str]]:
        return list(self._routes.keys())


class OraculoServer:
    """Servidor HTTP local para El Oraculo."""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 auth_token: str | None = None):
        self._host = host
        self._port = port
        self._auth_token = auth_token
        self.router = Router()
        self._httpd: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, background: bool = True) -> None:
        """Inicia el servidor. background=True lo corre en un thread."""
        self._httpd = HTTPServer((self._host, self._port), OraculoHandler)
        self._httpd.router = self.router
        self._httpd.auth_token = self._auth_token
        logger.info("Servidor iniciado en %s", self.url)
        if background:
            self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            self._thread.start()
        else:
            self._httpd.serve_forever()

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
            self._httpd = None
            self._thread = None
            logger.info("Servidor detenido.")
