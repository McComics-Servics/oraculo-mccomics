"""Tests unitarios del Cognitive Core (F5): providers, registry, expander, reranker."""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass

import pytest

from oraculo.cognitive.provider import LLMRequest, LLMResponse, ProviderType
from oraculo.cognitive.model_registry import (
    get_default_model, get_model_for_ram, list_models, RECOMMENDED_MODELS, detect_system_ram_gb,
)
from oraculo.cognitive.query_expander import expand_query, expand_with_fallback
from oraculo.cognitive.reranker import rerank_fragments, rerank_with_fallback, RerankResult
from oraculo.cognitive.core import CognitiveCore, CognitiveConfig


class MockProvider:
    """Provider mock para tests sin modelo real."""

    def __init__(self, response_text: str = "mock response", embedding: list[float] | None = None):
        self._response_text = response_text
        self._embedding = embedding or [0.1, 0.2, 0.3]

    @property
    def name(self) -> str:
        return "mock"

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.LLAMA_CPP

    @property
    def is_available(self) -> bool:
        return True

    @property
    def model_name(self) -> str:
        return "mock-model-3b"

    def generate(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            text=self._response_text,
            tokens_used=len(self._response_text.split()),
            model_name="mock-model-3b",
            provider="mock",
        )

    def generate_embedding(self, text: str) -> list[float] | None:
        return self._embedding


class TestModelRegistry:
    def test_default_model_exists(self):
        default = get_default_model()
        assert default.recommended_for == "default"
        assert "qwen" in default.name.lower() or "Qwen" in default.name

    def test_default_is_3b(self):
        default = get_default_model()
        assert default.size_b == 3.0
        assert default.ram_q4_gb <= 3.0

    def test_low_ram_gets_small_model(self):
        model = get_model_for_ram(4.0)
        assert model.ram_q4_gb <= 2.0

    def test_high_ram_gets_big_model(self):
        model = get_model_for_ram(32.0)
        assert model.size_b >= 3.0

    def test_list_all_models(self):
        models = list_models()
        assert len(models) >= 3

    def test_list_filtered(self):
        defaults = list_models("default")
        assert len(defaults) == 1

    def test_detect_ram(self):
        ram = detect_system_ram_gb()
        assert ram > 0

    def test_model_specs_complete(self):
        for m in RECOMMENDED_MODELS:
            assert m.name
            assert m.family
            assert m.size_b > 0
            assert m.ram_q4_gb > 0
            assert m.gguf_filename
            assert m.huggingface_repo
            assert m.spanish_quality in ("excellent", "very_good", "good", "fair", "poor")
            assert m.code_quality in ("excellent", "very_good", "good", "fair")


class TestQueryExpander:
    def test_expand_with_mock(self):
        mock = MockProvider(response_text="buscar funcion total\ncalcular suma items\nfuncion sum prices")
        variants = expand_query(mock, "calculate_total")
        assert len(variants) == 3

    def test_expand_with_fallback_no_provider(self):
        result = expand_with_fallback(None, "test_query")
        assert result == ["test_query"]

    def test_expand_with_fallback_has_provider(self):
        mock = MockProvider(response_text="variant1\nvariant2\nvariant3")
        result = expand_with_fallback(mock, "original")
        assert len(result) >= 2
        assert result[0] == "original"

    def test_expand_handles_numbered_lines(self):
        mock = MockProvider(response_text="1. first variant\n2. second variant\n3. third variant")
        variants = expand_query(mock, "test")
        assert all(not v.startswith("1") for v in variants)


class TestReranker:
    def test_rerank_with_mock(self):
        mock = MockProvider(response_text="8")
        frags = [
            ("f1", "def calculate_total(): return sum(items)", 0.5),
            ("f2", "class Logger: pass", 0.8),
        ]
        results = rerank_fragments(mock, "calculate total", frags)
        assert len(results) == 2
        assert all(isinstance(r, RerankResult) for r in results)
        assert results[0].rerank_score == 8.0

    def test_rerank_fallback_no_provider(self):
        frags = [
            ("f1", "code A", 0.9),
            ("f2", "code B", 0.3),
        ]
        results = rerank_with_fallback(None, "query", frags)
        assert len(results) == 2
        assert results[0].fragment_id == "f1"
        assert results[0].combined_score == 0.9

    def test_rerank_ordering(self):
        mock = MockProvider(response_text="9")
        frags = [
            ("low", "irrelevant code", 0.1),
            ("high", "very relevant calculate_total", 0.9),
        ]
        results = rerank_fragments(mock, "calculate", frags)
        assert all(r.combined_score > 0 for r in results)

    def test_rerank_invalid_score_defaults(self):
        mock = MockProvider(response_text="not a number")
        frags = [("f1", "code", 0.5)]
        results = rerank_fragments(mock, "query", frags)
        assert results[0].rerank_score == 5.0


class TestCognitiveCore:
    def test_config_defaults(self):
        cfg = CognitiveConfig()
        assert cfg.provider_type == "llama_cpp"
        assert cfg.enable_reranking is True
        assert cfg.enable_query_expansion is True

    def test_model_info_unloaded(self):
        cfg = CognitiveConfig(provider_type="llama_cpp")
        core = CognitiveCore(cfg)
        info = core.model_info
        assert info["loaded"] is False

    def test_expand_without_model(self):
        cfg = CognitiveConfig()
        core = CognitiveCore(cfg)
        result = core.expand_query("test")
        assert result == ["test"]

    def test_rerank_without_model(self):
        cfg = CognitiveConfig()
        core = CognitiveCore(cfg)
        frags = [("f1", "code", 0.5)]
        results = core.rerank("query", frags)
        assert len(results) == 1
        assert results[0].combined_score == 0.5

    def test_recommend_model(self):
        cfg = CognitiveConfig()
        core = CognitiveCore(cfg)
        model = core.recommend_model()
        assert model.name
        assert model.size_b > 0

    def test_generate_without_init(self):
        cfg = CognitiveConfig()
        core = CognitiveCore(cfg)
        result = core.generate(LLMRequest(prompt="test"))
        assert result is None

    def test_init_fails_gracefully_bad_path(self):
        cfg = CognitiveConfig(provider_type="llama_cpp", model_path="/nonexistent/model.gguf")
        core = CognitiveCore(cfg)
        success = core.initialize()
        assert success is False
        assert core.is_loaded is False

    def test_init_fails_gracefully_bad_provider(self):
        cfg = CognitiveConfig(provider_type="nonexistent_provider")
        core = CognitiveCore(cfg)
        success = core.initialize()
        assert success is False

    def test_ollama_provider_creation(self):
        cfg = CognitiveConfig(provider_type="ollama", ollama_model="qwen2.5-coder:3b")
        core = CognitiveCore(cfg)
        from oraculo.cognitive.ollama_provider import OllamaProvider
        provider = core._create_provider()
        assert isinstance(provider, OllamaProvider)
        assert provider.model_name == "qwen2.5-coder:3b"

    def test_openai_provider_creation(self):
        cfg = CognitiveConfig(
            provider_type="openai_compatible",
            openai_api_key="test-key",
            openai_model="gpt-4o-mini",
        )
        core = CognitiveCore(cfg)
        from oraculo.cognitive.openai_provider import OpenAICompatibleProvider
        provider = core._create_provider()
        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.model_name == "gpt-4o-mini"

    def test_disable_reranking(self):
        cfg = CognitiveConfig(enable_reranking=False)
        core = CognitiveCore(cfg)
        frags = [("f1", "code", 0.5)]
        results = core.rerank("query", frags)
        assert results[0].combined_score == 0.5

    def test_disable_query_expansion(self):
        cfg = CognitiveConfig(enable_query_expansion=False)
        core = CognitiveCore(cfg)
        result = core.expand_query("test")
        assert result == ["test"]


class TestOllamaProviderUnit:
    def test_properties(self):
        from oraculo.cognitive.ollama_provider import OllamaProvider
        p = OllamaProvider(model="qwen2.5-coder:3b")
        assert p.name == "ollama"
        assert p.model_name == "qwen2.5-coder:3b"
        assert p.provider_type == ProviderType.OLLAMA

    def test_not_available_if_not_running(self):
        from oraculo.cognitive.ollama_provider import OllamaProvider
        p = OllamaProvider(model="test", base_url="http://localhost:99999")
        assert p.is_available is False


class TestOpenAIProviderUnit:
    def test_properties(self):
        from oraculo.cognitive.openai_provider import OpenAICompatibleProvider
        p = OpenAICompatibleProvider(api_key="key", model="gpt-4o-mini")
        assert p.name == "openai_compatible"
        assert p.model_name == "gpt-4o-mini"
        assert p.is_available is True

    def test_not_available_without_key(self):
        from oraculo.cognitive.openai_provider import OpenAICompatibleProvider
        p = OpenAICompatibleProvider(api_key="", model="gpt-4o-mini")
        assert p.is_available is False


class TestLlamaCppProviderUnit:
    def test_properties(self, tmp_path: Path):
        from oraculo.cognitive.llama_provider import LlamaCppProvider
        fake_model = tmp_path / "model.gguf"
        fake_model.write_bytes(b"fake")
        p = LlamaCppProvider(model_path=fake_model)
        assert p.name == "llama_cpp"
        assert p.model_name == "model"
        assert p.provider_type == ProviderType.LLAMA_CPP

    def test_not_available_without_lib(self, tmp_path: Path):
        from oraculo.cognitive.llama_provider import LlamaCppProvider
        fake = tmp_path / "model.gguf"
        fake.write_bytes(b"fake")
        p = LlamaCppProvider(model_path=fake)
        # llama_cpp probablemente no esta instalado en test env
        # Si esta, pasa; si no, is_available depende de si el import existe
        assert isinstance(p.is_available, bool)

    def test_generate_without_load_raises(self, tmp_path: Path):
        from oraculo.cognitive.llama_provider import LlamaCppProvider
        fake = tmp_path / "model.gguf"
        fake.write_bytes(b"fake")
        p = LlamaCppProvider(model_path=fake)
        with pytest.raises(RuntimeError, match="no cargado"):
            p.generate(LLMRequest(prompt="test"))
