"""
Modulo: oraculo.cognitive.provider
Proposito: Protocolo abstracto para proveedores de LLM. Permite usar llama.cpp, Ollama, o API remota.
Documento de LEY: PLAN_MAESTRO_v4.md (Capa 5 — Cognitive Core)
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Protocol, AsyncIterator

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    LLAMA_CPP = "llama_cpp"
    OLLAMA = "ollama"
    OPENAI_COMPATIBLE = "openai_compatible"


@dataclass(frozen=True)
class LLMRequest:
    prompt: str
    system_prompt: str = ""
    max_tokens: int = 512
    temperature: float = 0.1
    stop: tuple[str, ...] = ()


@dataclass(frozen=True)
class LLMResponse:
    text: str
    tokens_used: int
    model_name: str
    provider: str
    finish_reason: str = "stop"


class LLMProvider(Protocol):
    """Protocolo que todo provider de LLM debe implementar."""

    @property
    def name(self) -> str: ...

    @property
    def provider_type(self) -> ProviderType: ...

    @property
    def is_available(self) -> bool: ...

    @property
    def model_name(self) -> str: ...

    def generate(self, request: LLMRequest) -> LLMResponse: ...

    def generate_embedding(self, text: str) -> list[float] | None: ...
