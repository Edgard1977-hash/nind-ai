"""Text LLM via an OpenAI-compatible chat API (OpenRouter by default)."""

from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI

from ai.base import ProviderNotConfigured


class OpenAICompatibleTextProvider:
    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        name: str = "openrouter",
    ) -> None:
        self.name = name
        self.api_key = api_key if api_key is not None else os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = (
            base_url
            if base_url is not None
            else os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        )
        self.model = model or os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        self._client: Optional[AsyncOpenAI] = None

    def _require_client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise ProviderNotConfigured(
                "Text provider is not configured. Set OPENROUTER_API_KEY "
                "(and optionally OPENROUTER_MODEL / OPENROUTER_BASE_URL)."
            )
        if self._client is None:
            headers = {}
            referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
            title = os.getenv("OPENROUTER_APP_TITLE", "nind")
            if referer:
                headers["HTTP-Referer"] = referer
            if title:
                headers["X-Title"] = title
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                default_headers=headers or None,
            )
        return self._client

    async def complete(self, *, system: str, user: str, model: Optional[str] = None) -> str:
        client = self._require_client()
        response = await client.chat.completions.create(
            model=model or self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = response.choices[0].message.content
        return content or ""
