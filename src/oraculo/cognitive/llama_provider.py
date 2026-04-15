"""
Modulo: oraculo.cognitive.llama_provider
Proposito: Provider LLM usando llama-cpp-python (binding de llama.cpp). Provider por defecto.
"""
from __future__ import annotations
import logging
from pathlib import Path

from oraculo.cognitive.provider import LLMProvider, LLMRequest, LLMResponse, ProviderType

logger = logging.getLogger(__name__)


class LlamaCppProvider:
    """Provider basado en llama.cpp via llama-cpp-python. Carga modelo GGUF local."""

    def __init__(self, model_path: Path, n_ctx: int = 4096, n_gpu_layers: int = 0,
                 embedding: bool = True):
        self._model_path = model_path
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._embedding = embedding
        self._llm = None
        self._model_name_str = model_path.stem if model_path else "unknown"

    @property
    def name(self) -> str:
        return "llama_cpp"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LLAMA_CPP

    @property
    def is_available(self) -> bool:
        try:
            import llama_cpp
            return self._model_path.exists()
        except ImportError:
            return False

    @property
    def model_name(self) -> str:
        return self._model_name_str

    def load(self) -> None:
        """Carga el modelo en memoria. Llamar antes de generate()."""
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=str(self._model_path),
                n_ctx=self._n_ctx,
                n_gpu_layers=self._n_gpu_layers,
                embedding=self._embedding,
                verbose=False,
            )
            logger.info("Modelo cargado: %s (ctx=%d, gpu_layers=%d)",
                        self._model_name_str, self._n_ctx, self._n_gpu_layers)
        except Exception as e:
            logger.error("Error cargando modelo %s: %s", self._model_path, e)
            raise

    def unload(self) -> None:
        """Libera el modelo de memoria."""
        self._llm = None

    def generate(self, request: LLMRequest) -> LLMResponse:
        if self._llm is None:
            raise RuntimeError("Modelo no cargado. Llamar load() primero.")

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        result = self._llm.create_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stop=list(request.stop) if request.stop else None,
        )

        choice = result["choices"][0]
        usage = result.get("usage", {})

        return LLMResponse(
            text=choice["message"]["content"],
            tokens_used=usage.get("total_tokens", 0),
            model_name=self._model_name_str,
            provider="llama_cpp",
            finish_reason=choice.get("finish_reason", "stop"),
        )

    def generate_embedding(self, text: str) -> list[float] | None:
        if self._llm is None or not self._embedding:
            return None
        try:
            result = self._llm.embed(text)
            if isinstance(result, list) and len(result) > 0:
                return result[0] if isinstance(result[0], list) else result
            return None
        except Exception as e:
            logger.warning("Error generando embedding: %s", e)
            return None
