"""Text-to-speech via an OpenAI-compatible ``/audio/speech`` endpoint."""

from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI

from ai.base import ProviderNotConfigured


class OpenAICompatibleTTSProvider:
    name = "openai-tts"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else _first_env("TTS_API_KEY", "OPENAI_API_KEY")
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("TTS_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = model or os.getenv("TTS_MODEL", "tts-1")
        self.voice = voice or os.getenv("TTS_VOICE", "nova")
        self._client: Optional[AsyncOpenAI] = None

    def _require_client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ProviderNotConfigured(
                "TTS provider is not configured. Set TTS_API_KEY and TTS_BASE_URL "
                "(OpenAI-compatible). OPENAI_API_KEY is used when TTS_API_KEY is empty."
            )
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    async def synthesize(self, text: str, *, voice: Optional[str] = None) -> bytes:
        client = self._require_client()
        response = await client.audio.speech.create(
            model=self.model,
            voice=voice or self.voice,
            input=text,
        )
        return response.content


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "")
        if value:
            return value
    return ""
