"""
Modulo: oraculo.cognitive.core
Proposito: Orquestador del Cognitive Core — selecciona provider, gestiona modelo, coordina expansion y reranking.
Documento de LEY: PLAN_MAESTRO_v4.md (Capa 5)
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oraculo.cognitive.provider import LLMProvider, LLMRequest, LLMResponse, ProviderType
from oraculo.cognitive.model_registry import get_default_model, get_model_for_ram, detect_system_ram_gb, ModelSpec
from oraculo.cognitive.query_expander import expand_with_fallback
from oraculo.cognitive.reranker import rerank_with_fallback, RerankResult

logger = logging.getLogger(__name__)


@dataclass
class CognitiveConfig:
    provider_type: str = "llama_cpp"
    model_path: str | None = None
    ollama_model: str = "qwen2.5-coder:3b"
    ollama_url: str = "http://localhost:11434"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    enable_reranking: bool = True
    enable_query_expansion: bool = True


class CognitiveCore:
    """Orquestador central del LLM: seleccion de provider, expansion de queries, reranking."""

    def __init__(self, config: CognitiveConfig):
        self._config = config
        self._provider: LLMProvider | None = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def provider(self) -> LLMProvider | None:
        return self._provider

    @property
    def model_info(self) -> dict[str, Any]:
        if self._provider:
            return {
                "name": self._provider.model_name,
                "provider": self._provider.name,
                "available": self._provider.is_available,
                "loaded": self._loaded,
            }
        return {"name": "none", "provider": "none", "available": False, "loaded": False}

    def initialize(self) -> bool:
        """Inicializa el provider segun la configuracion. Retorna True si exitoso."""
        try:
            self._provider = self._create_provider()
            if hasattr(self._provider, "load"):
                self._provider.load()
            self._loaded = True
            logger.info("Cognitive Core inicializado: %s (%s)",
                        self._provider.model_name, self._provider.name)
            return True
        except Exception as e:
            logger.error("Error inicializando Cognitive Core: %s", e)
            self._loaded = False
            return False

    def shutdown(self) -> None:
        """Libera el modelo de memoria."""
        if self._provider and hasattr(self._provider, "unload"):
            self._provider.unload()
        self._loaded = False
        logger.info("Cognitive Core detenido.")

    def generate(self, request: LLMRequest) -> LLMResponse | None:
        """Genera texto con el LLM actual."""
        if not self._provider or not self._loaded:
            logger.warning("Cognitive Core no inicializado")
            return None
        try:
            return self._provider.generate(request)
        except Exception as e:
            logger.error("Error en generate: %s", e)
            return None

    def expand_query(self, query: str) -> list[str]:
        """Expansion de query con fallback si LLM no disponible."""
        if not self._config.enable_query_expansion:
            return [query]
        return expand_with_fallback(self._provider if self._loaded else None, query)

    def rerank(self, query: str, fragments: list[tuple[str, str, float]]) -> list[RerankResult]:
        """Reranking de fragmentos con fallback si LLM no disponible."""
        if not self._config.enable_reranking:
            return rerank_with_fallback(None, query, fragments)
        return rerank_with_fallback(self._provider if self._loaded else None, query, fragments)

    def generate_embedding(self, text: str) -> list[float] | None:
        """Genera embedding vectorial del texto."""
        if not self._provider or not self._loaded:
            return None
        return self._provider.generate_embedding(text)

    def recommend_model(self) -> ModelSpec:
        """Recomienda el mejor modelo para el hardware actual."""
        ram = detect_system_ram_gb()
        return get_model_for_ram(ram)

    def _create_provider(self) -> LLMProvider:
        """Crea el provider apropiado segun config."""
        pt = self._config.provider_type

        if pt == "llama_cpp":
            from oraculo.cognitive.llama_provider import LlamaCppProvider
            model_path = Path(self._config.model_path) if self._config.model_path else None
            if not model_path or not model_path.exists():
                raise FileNotFoundError(f"Modelo GGUF no encontrado: {model_path}")
            return LlamaCppProvider(
                model_path=model_path,
                n_ctx=self._config.n_ctx,
                n_gpu_layers=self._config.n_gpu_layers,
            )

        if pt == "ollama":
            from oraculo.cognitive.ollama_provider import OllamaProvider
            return OllamaProvider(
                model=self._config.ollama_model,
                base_url=self._config.ollama_url,
            )

        if pt == "openai_compatible":
            from oraculo.cognitive.openai_provider import OpenAICompatibleProvider
            return OpenAICompatibleProvider(
                api_key=self._config.openai_api_key,
                model=self._config.openai_model,
                base_url=self._config.openai_base_url,
            )

        raise ValueError(f"Provider desconocido: {pt}")
