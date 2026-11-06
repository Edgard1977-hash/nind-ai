"""Construct providers from the environment, with test overrides."""

from __future__ import annotations

import os
from typing import Any, Optional

from ai.base import ProviderNotConfigured
from ai.image import FallbackImageProvider, GeminiImageProvider, OpenRouterImageProvider
from ai.stt import OpenAICompatibleSTTProvider
from ai.text import OpenAICompatibleTextProvider
from ai.tts import OpenAICompatibleTTSProvider, OpenRouterChatAudioProvider
from ai.video import build_video_provider

_overrides: dict[str, Any] = {}


def set_provider_overrides(
    *,
    text: Any = None,
    image: Any = None,
    tts: Any = None,
    stt: Any = None,
    video: Any = None,
) -> None:
    if text is not None:
        _overrides["text"] = text
    if image is not None:
        _overrides["image"] = image
    if tts is not None:
        _overrides["tts"] = tts
    if stt is not None:
        _overrides["stt"] = stt
    if video is not None:
        _overrides["video"] = video


def clear_provider_overrides() -> None:
    _overrides.clear()


def get_text_provider() -> OpenAICompatibleTextProvider:
    return _overrides.get("text") or OpenAICompatibleTextProvider()


def get_image_provider() -> FallbackImageProvider:
    return _overrides.get("image") or FallbackImageProvider(
        GeminiImageProvider(),
        OpenRouterImageProvider(),
    )


_CLASSIC_SPEECH_MODELS = {"tts-1", "tts-1-hd", "gpt-4o-mini-tts"}


def _classic_speech_model(model: str) -> bool:
    cleaned = model.strip().lower()
    return cleaned in _CLASSIC_SPEECH_MODELS or cleaned.startswith("tts-")


def tts_backend_name() -> str:
    """Choose chat-audio on OpenRouter unless a classic speech endpoint is configured.

    ``OPENROUTER_API_KEY`` alone is enough. ``TTS_PROVIDER=speech`` keeps the
    OpenAI-compatible ``/audio/speech`` path. A classic ``TTS_MODEL`` such as
    ``tts-1`` is used only when a dedicated speech key is also set.
    """
    explicit = os.getenv("TTS_PROVIDER", "auto").strip().lower()
    if explicit in {"speech", "openai", "audio-speech"}:
        return "speech"
    if explicit in {"openrouter", "chat", "chat-audio"}:
        return "openrouter"
    speech_key = bool(os.getenv("TTS_API_KEY") or os.getenv("OPENAI_API_KEY"))
    openrouter_key = bool(os.getenv("OPENROUTER_API_KEY"))
    if openrouter_key and not (speech_key and _classic_speech_model(os.getenv("TTS_MODEL", ""))):
        return "openrouter"
    if speech_key:
        return "speech"
    return "openrouter"


def get_tts_provider():
    override = _overrides.get("tts")
    if override is not None:
        return override
    if tts_backend_name() == "speech":
        return OpenAICompatibleTTSProvider()
    return OpenRouterChatAudioProvider()


def get_speech_provider() -> OpenAICompatibleSTTProvider:
    return _overrides.get("stt") or OpenAICompatibleSTTProvider()


def get_video_provider():
    return _overrides.get("video") or build_video_provider()


def provider_status() -> dict:
    """Report which providers have credentials, without calling them."""
    video = get_video_provider()
    return {
        "text": bool(os.getenv("OPENROUTER_API_KEY")),
        "image_gemini": bool(os.getenv("GEMINI_API_KEY")),
        "image_openrouter_fallback": bool(os.getenv("OPENROUTER_API_KEY")),
        "tts": bool(
            os.getenv("OPENROUTER_API_KEY") or os.getenv("TTS_API_KEY") or os.getenv("OPENAI_API_KEY")
        ),
        "tts_backend": tts_backend_name(),
        "stt": bool(os.getenv("STT_API_KEY") or os.getenv("OPENAI_API_KEY")),
        "video": bool(getattr(video, "configured", False)),
        "video_provider": getattr(video, "name", "unconfigured"),
    }


def require_video_provider():
    provider = get_video_provider()
    if not getattr(provider, "configured", False):
        # Touch generate() only to reuse its message when the caller wants it.
        return provider
    return provider


__all__ = [
    "ProviderNotConfigured",
    "clear_provider_overrides",
    "get_image_provider",
    "get_speech_provider",
    "get_text_provider",
    "get_tts_provider",
    "tts_backend_name",
    "get_video_provider",
    "provider_status",
    "set_provider_overrides",
]
