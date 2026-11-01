"""Text LLM via an OpenAI-compatible chat API.

OpenRouter is used when ``OPENROUTER_API_KEY`` is set. Otherwise a
``GEMINI_API_KEY`` talks to Gemini's OpenAI-compatible endpoint. That
endpoint is for text only; image generation stays on the Gemini image API.
"""

from __future__ import annotations

import os
from typing import Optional

from openai import AsyncOpenAI

from ai.base import ProviderNotConfigured
from ai.retry import retry_rate_limits

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_TEXT_MODEL = "gemini-2.5-flash"


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
                "Text provider is not configured. Set OPENROUTER_API_KEY, "
                "or GEMINI_API_KEY to use Gemini text (GEMINI_TEXT_MODEL, default gemini-2.5-flash)."
            )
        if self._client is None:
            headers = {}
            if self.name == "openrouter":
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
        chosen = model or self.model
        label = "Gemini" if self.name == "gemini" else "Text provider"

        async def _once() -> str:
            response = await client.chat.completions.create(
                model=chosen,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return response.choices[0].message.content or ""

        return await retry_rate_limits(_once, label=label)


def build_text_provider() -> OpenAICompatibleTextProvider:
    """OpenRouter when its key is set, otherwise Gemini text, otherwise unconfigured."""
    if os.getenv("OPENROUTER_API_KEY", "").strip():
        return OpenAICompatibleTextProvider(name="openrouter")
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if gemini_key:
        return OpenAICompatibleTextProvider(
            api_key=gemini_key,
            base_url=os.getenv("GEMINI_OPENAI_BASE_URL", GEMINI_OPENAI_BASE_URL),
            model=os.getenv("GEMINI_TEXT_MODEL", DEFAULT_GEMINI_TEXT_MODEL),
            name="gemini",
        )
    return OpenAICompatibleTextProvider(api_key="", name="unconfigured")
