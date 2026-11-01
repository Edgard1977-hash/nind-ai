"""Construct providers from the environment, with test overrides."""

from __future__ import annotations

import os
from typing import Any, Optional

from ai.base import ProviderNotConfigured
from ai.image import FallbackImageProvider, GeminiImageProvider, OpenRouterImageProvider
from ai.stt import OpenAICompatibleSTTProvider
from ai.text import OpenAICompatibleTextProvider, build_text_provider
from ai.tts import OpenAICompatibleTTSProvider
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
    return _overrides.get("text") or build_text_provider()


def get_image_provider() -> FallbackImageProvider:
    return _overrides.get("image") or FallbackImageProvider(
        GeminiImageProvider(),
        OpenRouterImageProvider(),
    )


def get_tts_provider() -> OpenAICompatibleTTSProvider:
    return _overrides.get("tts") or OpenAICompatibleTTSProvider()


def get_speech_provider() -> OpenAICompatibleSTTProvider:
    return _overrides.get("stt") or OpenAICompatibleSTTProvider()


def get_video_provider():
    return _overrides.get("video") or build_video_provider()


def provider_status() -> dict:
    """Report which providers have credentials, without calling them."""
    video = get_video_provider()
    return {
        "text": bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("GEMINI_API_KEY")),
        "image_gemini": bool(os.getenv("GEMINI_API_KEY")),
        "image_openrouter_fallback": bool(os.getenv("OPENROUTER_API_KEY")),
        "tts": bool(os.getenv("TTS_API_KEY") or os.getenv("OPENAI_API_KEY")),
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
    "get_video_provider",
    "provider_status",
    "set_provider_overrides",
]
