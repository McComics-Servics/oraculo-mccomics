"""
Modulo: oraculo.cognitive.model_registry
Proposito: Registro de modelos recomendados, auto-deteccion de capacidad y seleccion inteligente.
"""
from __future__ import annotations
import logging
import shutil
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ModelSpec:
    name: str
    family: str
    size_b: float
    ram_q4_gb: float
    gguf_filename: str
    huggingface_repo: str
    languages_supported: int
    spanish_quality: str  # "excellent", "good", "poor"
    code_quality: str     # "excellent", "very_good", "good", "fair"
    recommended_for: str  # "low_end", "default", "high_end"
    notes: str = ""


RECOMMENDED_MODELS: list[ModelSpec] = [
    ModelSpec(
        name="Qwen 2.5 Coder 1.5B Q4_K_M",
        family="qwen2.5-coder",
        size_b=1.5,
        ram_q4_gb=1.2,
        gguf_filename="qwen2.5-coder-1.5b-instruct-q4_k_m.gguf",
        huggingface_repo="Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF",
        languages_supported=92,
        spanish_quality="good",
        code_quality="good",
        recommended_for="low_end",
        notes="Para laptops con 4-8 GB RAM. Funcional pero limitado en reranking.",
    ),
    ModelSpec(
        name="Qwen 2.5 Coder 3B Q4_K_M",
        family="qwen2.5-coder",
        size_b=3.0,
        ram_q4_gb=2.1,
        gguf_filename="qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        huggingface_repo="Qwen/Qwen2.5-Coder-3B-Instruct-GGUF",
        languages_supported=92,
        spanish_quality="very_good",
        code_quality="very_good",
        recommended_for="default",
        notes="RECOMENDADO. Mejor relacion calidad/recurso. Corre en 8 GB RAM sin problema.",
    ),
    ModelSpec(
        name="Qwen 2.5 Coder 7B Q4_K_M",
        family="qwen2.5-coder",
        size_b=7.0,
        ram_q4_gb=4.5,
        gguf_filename="qwen2.5-coder-7b-instruct-q4_k_m.gguf",
        huggingface_repo="Qwen/Qwen2.5-Coder-7B-Instruct-GGUF",
        languages_supported=92,
        spanish_quality="excellent",
        code_quality="excellent",
        recommended_for="high_end",
        notes="Calidad excelente. Requiere 16 GB+ RAM.",
    ),
    ModelSpec(
        name="Phi-3.5 Mini 3.8B Q4_K_M",
        family="phi-3.5",
        size_b=3.8,
        ram_q4_gb=2.5,
        gguf_filename="Phi-3.5-mini-instruct-Q4_K_M.gguf",
        huggingface_repo="bartowski/Phi-3.5-mini-instruct-GGUF",
        languages_supported=20,
        spanish_quality="fair",
        code_quality="good",
        recommended_for="alternative",
        notes="Buen razonamiento general. Mejor para texto que para codigo.",
    ),
]


def get_default_model() -> ModelSpec:
    """Retorna el modelo recomendado por defecto."""
    for m in RECOMMENDED_MODELS:
        if m.recommended_for == "default":
            return m
    return RECOMMENDED_MODELS[0]


def get_model_for_ram(available_ram_gb: float) -> ModelSpec:
    """Selecciona el mejor modelo que cabe en la RAM disponible."""
    candidates = [m for m in RECOMMENDED_MODELS if m.ram_q4_gb <= available_ram_gb * 0.5]
    if not candidates:
        return RECOMMENDED_MODELS[0]
    candidates.sort(key=lambda m: m.size_b, reverse=True)
    return candidates[0]


def list_models(filter_for: str | None = None) -> list[ModelSpec]:
    """Lista modelos, opcionalmente filtrados por recommended_for."""
    if filter_for:
        return [m for m in RECOMMENDED_MODELS if m.recommended_for == filter_for]
    return list(RECOMMENDED_MODELS)


def detect_system_ram_gb() -> float:
    """Detecta RAM del sistema. Retorna 8.0 como fallback seguro."""
    try:
        import psutil
        return psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass
    try:
        import os
        if hasattr(os, 'sysconf'):
            pages = os.sysconf('SC_PHYS_PAGES')
            page_size = os.sysconf('SC_PAGE_SIZE')
            return (pages * page_size) / (1024 ** 3)
    except (ValueError, OSError):
        pass
    return 8.0
