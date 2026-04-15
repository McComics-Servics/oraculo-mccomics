"""
Modulo: oraculo.cognitive.ollama_provider
Proposito: Provider LLM usando Ollama (si esta instalado localmente).
"""
from __future__ import annotations
import json
import logging
import urllib.request
import urllib.error

from oraculo.cognitive.provider import LLMProvider, LLMRequest, LLMResponse, ProviderType

logger = logging.getLogger(__name__)

DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaProvider:
    """Provider que conecta con Ollama via HTTP API local."""

    def __init__(self, model: str = "qwen2.5-coder:3b",
                 base_url: str = DEFAULT_OLLAMA_URL):
        self._model = model
        self._base_url = base_url.rstrip("/")

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OLLAMA

    @property
    def is_available(self) -> bool:
        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except (urllib.error.URLError, OSError):
            return False

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, request: LLMRequest) -> LLMResponse:
        payload = {
            "model": self._model,
            "prompt": request.prompt,
            "system": request.system_prompt,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        }
        if request.stop:
            payload["options"]["stop"] = list(request.stop)

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        return LLMResponse(
            text=result.get("response", ""),
            tokens_used=result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
            model_name=self._model,
            provider="ollama",
            finish_reason="stop" if result.get("done") else "length",
        )

    def generate_embedding(self, text: str) -> list[float] | None:
        payload = {"model": self._model, "prompt": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/api/embeddings",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("embedding")
        except Exception as e:
            logger.warning("Ollama embedding error: %s", e)
            return None

    def list_local_models(self) -> list[str]:
        """Lista modelos disponibles en Ollama."""
        try:
            req = urllib.request.Request(f"{self._base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return [m["name"] for m in result.get("models", [])]
        except Exception:
            return []
