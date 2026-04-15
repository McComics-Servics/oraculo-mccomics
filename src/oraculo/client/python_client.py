"""
Modulo: oraculo.client.python_client
Proposito: Cliente Python para la API HTTP de El Oraculo.
"""
from __future__ import annotations
import json
import logging
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    fragments: list[dict[str, Any]]
    total: int
    query: str
    time_ms: float

    @staticmethod
    def from_dict(data: dict) -> QueryResult:
        return QueryResult(
            fragments=data.get("fragments", []),
            total=data.get("total_fragments", 0),
            query=data.get("query", ""),
            time_ms=data.get("assembly_time_ms", 0),
        )


class OraculoClient:
    """Cliente Python para la API HTTP local de El Oraculo."""

    def __init__(self, base_url: str = "http://127.0.0.1:9741",
                 token: str | None = None):
        self._base_url = base_url.rstrip("/")
        self._token = token

    def health(self) -> dict[str, Any]:
        return self._get("/api/v1/health")

    def status(self) -> dict[str, Any]:
        return self._get("/api/v1/status")

    def query(self, text: str, limit: int = 10) -> QueryResult:
        data = self._post("/api/v1/query", {"query": text, "limit": limit})
        return QueryResult.from_dict(data)

    def get_profile(self) -> dict[str, Any]:
        return self._get("/api/v1/profile")

    def switch_profile(self, name: str, passphrase: str | None = None) -> dict[str, Any]:
        body = {"profile": name}
        if passphrase:
            body["passphrase"] = passphrase
        return self._post("/api/v1/profile/switch", body)

    def index_files(self, paths: list[str], force: bool = False) -> dict[str, Any]:
        return self._post("/api/v1/index", {"paths": paths, "force": force})

    def _get(self, path: str) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self._base_url}{path}",
            method="GET",
            headers=self._headers(),
        )
        return self._execute(req)

    def _post(self, path: str, data: dict) -> dict[str, Any]:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}{path}",
            data=body,
            method="POST",
            headers={**self._headers(), "Content-Type": "application/json"},
        )
        return self._execute(req)

    def _headers(self) -> dict[str, str]:
        h = {}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    def _execute(self, req: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            logger.error("HTTP %d: %s", e.code, body)
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"error": f"http_{e.code}", "message": body}
        except urllib.error.URLError as e:
            return {"error": "connection_failed", "message": str(e.reason)}
