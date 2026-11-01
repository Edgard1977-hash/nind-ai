"""Speech-to-text via an OpenAI-compatible Whisper endpoint.

Works with OpenAI (``whisper-1``) and Groq (``whisper-large-v3`` on
``https://api.groq.com/openai/v1``). Select the host with ``STT_BASE_URL``.
"""

from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI

from ai.base import ProviderNotConfigured


class OpenAICompatibleSTTProvider:
    name = "openai-whisper"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else _first_env(
            "STT_API_KEY", "OPENAI_API_KEY"
        )
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("STT_BASE_URL", "https://api.openai.com/v1")
        )
        self.model = model or os.getenv("STT_MODEL", "whisper-1")
        self._client: Optional[AsyncOpenAI] = None

    def _require_client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ProviderNotConfigured(
                "STT provider is not configured. Set STT_API_KEY and STT_BASE_URL. "
                "Example: Groq (https://api.groq.com/openai/v1, model whisper-large-v3) "
                "or OpenAI (https://api.openai.com/v1, model whisper-1)."
            )
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        return self._client

    async def transcribe(self, audio_path: str, *, language: Optional[str] = None) -> str:
        client = self._require_client()
        with open(audio_path, "rb") as audio_file:
            kwargs = {"model": self.model, "file": audio_file}
            if language:
                kwargs["language"] = language
            result = await client.audio.transcriptions.create(**kwargs)
        return (getattr(result, "text", None) or "").strip()


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "")
        if value:
            return value
    return ""
