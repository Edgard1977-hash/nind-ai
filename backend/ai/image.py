"""Image generation.

Primary path: Google Gemini image models ("Nano Banana"), currently
``gemini-2.5-flash-image``, via the public Gemini REST API.

Fallback: the same model through OpenRouter when ``GEMINI_API_KEY`` is unset
and ``OPENROUTER_API_KEY`` is present.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

import httpx

from ai.base import ProviderNotConfigured

DEFAULT_GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"
DEFAULT_OPENROUTER_IMAGE_MODEL = "google/gemini-2.5-flash-image"


def _decode_data_url(value: str) -> bytes:
    if value.startswith("data:"):
        _, _, payload = value.partition(",")
        return base64.b64decode(payload)
    return base64.b64decode(value)


class GeminiImageProvider:
    """Google AI Studio / Gemini API image generation."""

    name = "gemini"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY", "")
        self.model = model or os.getenv("GEMINI_IMAGE_MODEL", DEFAULT_GEMINI_IMAGE_MODEL)
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("GEMINI_API_BASE", "https://generativelanguage.googleapis.com/v1beta")
        ).rstrip("/")

    async def generate(self, prompt: str, *, aspect_ratio: str = "9:16") -> bytes:
        if not self.api_key:
            raise ProviderNotConfigured("GEMINI_API_KEY is not set")
        url = f"{self.base_url}/models/{self.model}:generateContent"
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"Generate a single image, aspect ratio {aspect_ratio}. "
                                f"{prompt}"
                            )
                        }
                    ],
                }
            ],
            "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]},
        }
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, params={"key": self.api_key}, json=body)
        if response.status_code >= 400:
            raise RuntimeError(
                f"Gemini image request failed ({response.status_code}): {response.text[:500]}"
            )
        payload = response.json()
        for candidate in payload.get("candidates") or []:
            for part in (candidate.get("content") or {}).get("parts") or []:
                inline = part.get("inlineData") or part.get("inline_data")
                if inline and inline.get("data"):
                    return base64.b64decode(inline["data"])
        raise RuntimeError("Gemini image response did not include image bytes")


class OpenRouterImageProvider:
    """OpenAI-compatible image generation through OpenRouter chat completions."""

    name = "openrouter-image"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY", "")
        self.model = model or os.getenv("OPENROUTER_IMAGE_MODEL", DEFAULT_OPENROUTER_IMAGE_MODEL)
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        ).rstrip("/")

    async def generate(self, prompt: str, *, aspect_ratio: str = "9:16") -> bytes:
        if not self.api_key:
            raise ProviderNotConfigured("OPENROUTER_API_KEY is not set")
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": (
                        f"Generate a single image, aspect ratio {aspect_ratio}. {prompt}"
                    ),
                }
            ],
            "modalities": ["image", "text"],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        title = os.getenv("OPENROUTER_APP_TITLE", "nind")
        if title:
            headers["X-Title"] = title
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(url, headers=headers, json=body)
        if response.status_code >= 400:
            raise RuntimeError(
                f"OpenRouter image request failed ({response.status_code}): {response.text[:500]}"
            )
        payload = response.json()
        message = ((payload.get("choices") or [{}])[0].get("message") or {})
        images = message.get("images") or []
        for image in images:
            if isinstance(image, str):
                return _decode_data_url(image)
            if isinstance(image, dict):
                url_value = (
                    image.get("image_url", {}).get("url")
                    if isinstance(image.get("image_url"), dict)
                    else image.get("url") or image.get("b64_json") or image.get("data")
                )
                if url_value:
                    return _decode_data_url(url_value)
        # Some gateways return inline data on content parts.
        content = message.get("content")
        if isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") in ("image_url", "image"):
                    image_url = part.get("image_url") or {}
                    url_value = image_url.get("url") if isinstance(image_url, dict) else None
                    if url_value:
                        return _decode_data_url(url_value)
        raise RuntimeError("OpenRouter image response did not include image bytes")


class FallbackImageProvider:
    """Try Gemini first, then OpenRouter."""

    def __init__(self, primary: GeminiImageProvider, fallback: OpenRouterImageProvider) -> None:
        self.primary = primary
        self.fallback = fallback
        self.name = "gemini"

    async def generate(self, prompt: str, *, aspect_ratio: str = "9:16") -> bytes:
        if self.primary.api_key:
            self.name = self.primary.name
            return await self.primary.generate(prompt, aspect_ratio=aspect_ratio)
        if self.fallback.api_key:
            self.name = self.fallback.name
            return await self.fallback.generate(prompt, aspect_ratio=aspect_ratio)
        raise ProviderNotConfigured(
            "Image provider is not configured. Set GEMINI_API_KEY "
            "(preferred, model gemini-2.5-flash-image) or OPENROUTER_API_KEY as a fallback."
        )
