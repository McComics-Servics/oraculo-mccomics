"""
Modulo: oraculo.cognitive.openai_provider
Proposito: Provider LLM compatible con API OpenAI (GPT, Claude via proxy, Groq, Together, etc.).
"""
from __future__ import annotations
import json
import logging
import urllib.request
import urllib.error

from oraculo.cognitive.provider import LLMProvider, LLMRequest, LLMResponse, ProviderType

logger = logging.getLogger(__name__)


class OpenAICompatibleProvider:
    """Provider para cualquier API compatible con OpenAI (chat/completions)."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini",
                 base_url: str = "https://api.openai.com/v1",
                 embedding_model: str = "text-embedding-3-small"):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._embedding_model = embedding_model

    @property
    def name(self) -> str:
        return "openai_compatible"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.OPENAI_COMPATIBLE

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    @property
    def model_name(self) -> str:
        return self._model

    def generate(self, request: LLMRequest) -> LLMResponse:
        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": self._model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        if request.stop:
            payload["stop"] = list(request.stop)

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        choice = result["choices"][0]
        usage = result.get("usage", {})

        return LLMResponse(
            text=choice["message"]["content"],
            tokens_used=usage.get("total_tokens", 0),
            model_name=self._model,
            provider="openai_compatible",
            finish_reason=choice.get("finish_reason", "stop"),
        )

    def generate_embedding(self, text: str) -> list[float] | None:
        payload = {"model": self._embedding_model, "input": text}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/embeddings",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["data"][0]["embedding"]
        except Exception as e:
            logger.warning("OpenAI embedding error: %s", e)
            return None
