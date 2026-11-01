"""Gemini text fallback and rate-limit retries. Providers are not called for real."""

import asyncio

import pytest

from ai.factory import clear_provider_overrides, get_image_provider, get_text_provider, provider_status
from ai.image import OpenRouterImageProvider
from ai.retry import retry_rate_limits
from ai.text import GEMINI_OPENAI_BASE_URL, build_text_provider


@pytest.fixture(autouse=True)
def _clean_overrides():
    clear_provider_overrides()
    yield
    clear_provider_overrides()


def test_gemini_text_when_openrouter_is_empty(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.delenv("GEMINI_TEXT_MODEL", raising=False)
    provider = build_text_provider()
    assert provider.name == "gemini"
    assert provider.api_key == "gemini-test-key"
    assert provider.base_url == GEMINI_OPENAI_BASE_URL
    assert provider.model == "gemini-2.5-flash"
    assert provider_status()["text"] is True
    fallback = OpenRouterImageProvider()
    assert fallback.base_url.startswith("https://openrouter.ai")
    assert "generativelanguage" not in fallback.base_url
    image = get_image_provider()
    assert image.primary.api_key == "gemini-test-key"
    assert "openai" not in image.primary.base_url


def test_openrouter_text_is_preferred(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key")
    monkeypatch.setenv("GEMINI_API_KEY", "gemini-test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
    provider = get_text_provider()
    assert provider.name == "openrouter"
    assert provider.api_key == "or-key"
    assert provider.base_url.startswith("https://openrouter.ai")
    assert provider.model == "openai/gpt-4o-mini"


def test_text_status_is_false_without_either_key(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert provider_status()["text"] is False
    provider = build_text_provider()
    assert provider.name == "unconfigured"


def test_rate_limit_retries_then_succeeds():
    calls = {"n": 0}

    async def operation():
        calls["n"] += 1
        if calls["n"] < 3:
            limited = RuntimeError("429")
            limited.status_code = 429
            raise limited
        return "ok"

    result = asyncio.run(retry_rate_limits(operation, label="Gemini", delays=(0, 0, 0)))
    assert result == "ok"
    assert calls["n"] == 3


def test_rate_limit_gives_a_clear_error():
    async def operation():
        limited = RuntimeError("resource_exhausted")
        limited.status_code = 429
        raise limited

    with pytest.raises(RuntimeError, match="rate limit \\(429\\)"):
        asyncio.run(retry_rate_limits(operation, label="Gemini image", delays=(0,)))
