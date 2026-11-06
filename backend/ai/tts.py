"""Text-to-speech providers.

``OpenAICompatibleTTSProvider`` calls an OpenAI-compatible ``/audio/speech``
endpoint (tts-1 and similar). ``openai/gpt-audio-mini`` is not on that
endpoint. OpenRouter serves it as a streaming chat completion with
``modalities: ["text", "audio"]``, which ``OpenRouterChatAudioProvider``
implements.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Optional

import httpx
from openai import AsyncOpenAI

from ai.base import ProviderNotConfigured, SpeechSynthesis


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

    async def synthesize_detailed(self, text: str, *, voice: Optional[str] = None) -> SpeechSynthesis:
        chosen = voice or self.voice
        audio = await self.synthesize(text, voice=chosen)
        return SpeechSynthesis(audio=audio, transcript=text, audio_format="mp3", voice=chosen)


_READ_ALOUD = (
    "Speak the user's text verbatim as a calm documentary voiceover. "
    "Do not add, remove, translate, or paraphrase any words. "
    "Do not introduce yourself or describe the text."
)

_CLASSIC_SPEECH_MODELS = {"tts-1", "tts-1-hd", "gpt-4o-mini-tts"}
_AUDIO_FORMATS = {"wav", "mp3", "flac", "opus", "pcm16"}


def chat_audio_model() -> str:
    """Model id for OpenRouter chat-audio. Classic speech models are not valid here."""
    requested = os.getenv("TTS_MODEL", "").strip()
    if not requested or requested in _CLASSIC_SPEECH_MODELS or requested.startswith("tts-"):
        return "openai/gpt-audio-mini"
    return requested


def chat_audio_format() -> str:
    requested = os.getenv("TTS_AUDIO_FORMAT", "wav").strip().lower()
    if requested not in _AUDIO_FORMATS:
        return "wav"
    return requested


class AudioStreamAssembler:
    """Collect base64 audio and transcript slices from chat-completion SSE payloads."""

    def __init__(self) -> None:
        self.parts: list[bytes] = []
        self.pending = ""
        self.decoded = 0
        self.transcript = ""
        self.text_parts: list[str] = []
        self.snapshots: list[tuple[int, str]] = []

    def feed(self, payload: dict) -> Optional[str]:
        error = payload.get("error")
        if isinstance(error, dict):
            return error.get("message") or str(error)
        if isinstance(error, str) and error:
            return error
        choices = payload.get("choices") or []
        if not choices:
            return None
        choice = choices[0] or {}
        delta = choice.get("delta") or {}
        message = choice.get("message") or {}
        audio = delta.get("audio") or message.get("audio") or {}
        if not isinstance(audio, dict):
            audio = {}
        data = audio.get("data") or ""
        transcript = audio.get("transcript") or ""
        if data:
            self._add_b64(str(data))
        if transcript:
            self.transcript = _merge_transcript(self.transcript, str(transcript))
            self.snapshots.append((self.decoded, self.transcript))
        content = delta.get("content")
        if content is None:
            content = message.get("content")
        if isinstance(content, str) and content:
            self.text_parts.append(content)
        return None

    def finish(self) -> tuple[bytes, str, list[tuple[int, str]]]:
        self._flush_b64()
        transcript = self.transcript or "".join(self.text_parts)
        return b"".join(self.parts), transcript.strip(), list(self.snapshots)

    def _add_b64(self, data: str) -> None:
        self.pending += "".join(data.split())
        usable = len(self.pending) - (len(self.pending) % 4)
        if usable <= 0:
            return
        chunk = base64.b64decode(self.pending[:usable])
        self.parts.append(chunk)
        self.decoded += len(chunk)
        self.pending = self.pending[usable:]

    def _flush_b64(self) -> None:
        if not self.pending:
            return
        padded = self.pending + ("=" * ((4 - len(self.pending) % 4) % 4))
        chunk = base64.b64decode(padded)
        self.parts.append(chunk)
        self.decoded += len(chunk)
        self.pending = ""


class OpenRouterChatAudioProvider:
    """Speak text with an OpenRouter audio-output chat model."""

    name = "openrouter-chat-audio"

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        voice: Optional[str] = None,
        audio_format: Optional[str] = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else _first_env("OPENROUTER_API_KEY", "TTS_API_KEY")
        self.base_url = (base_url if base_url is not None else _openrouter_base_url()).rstrip("/")
        self.model = model or chat_audio_model()
        self.voice = voice or os.getenv("TTS_VOICE") or "marin"
        self.audio_format = audio_format or chat_audio_format()

    def _headers(self) -> dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        referer = os.getenv("OPENROUTER_HTTP_REFERER", "")
        title = os.getenv("OPENROUTER_APP_TITLE", "nind")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title
        return headers

    async def synthesize_detailed(self, text: str, *, voice: Optional[str] = None) -> SpeechSynthesis:
        spoken = " ".join((text or "").split())
        if not spoken:
            raise RuntimeError("TTS input is empty")
        if not self.api_key:
            raise ProviderNotConfigured(
                "TTS provider is not configured. Set OPENROUTER_API_KEY to use "
                "openai/gpt-audio-mini through OpenRouter chat audio, or set "
                "TTS_PROVIDER=speech with TTS_API_KEY for an /audio/speech endpoint."
            )
        chosen = (voice or self.voice or "marin").strip()
        url = f"{self.base_url}/chat/completions"
        body = {
            "model": self.model,
            "stream": True,
            "modalities": ["text", "audio"],
            "audio": {"voice": chosen, "format": self.audio_format},
            "max_tokens": 12000,
            "messages": [
                {"role": "system", "content": _READ_ALOUD},
                {"role": "user", "content": spoken},
            ],
        }
        try:
            audio, transcript, snapshots = await self._stream_speech(url, body)
        except RuntimeError as exc:
            message = str(exc).lower()
            if body.get("max_tokens") and "max_tokens" in message:
                retry = dict(body)
                retry.pop("max_tokens", None)
                audio, transcript, snapshots = await self._stream_speech(url, retry)
            else:
                raise
        if not audio:
            raise RuntimeError("OpenRouter speech response did not include audio bytes")
        return SpeechSynthesis(
            audio=audio,
            transcript=transcript or spoken,
            snapshots=snapshots,
            audio_format=self.audio_format,
            voice=chosen,
        )

    async def _stream_speech(self, url: str, body: dict) -> tuple[bytes, str, list]:
        assembler = AudioStreamAssembler()
        timeout = httpx.Timeout(180.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", url, headers=self._headers(), json=body) as response:
                if response.status_code >= 400:
                    detail = (await response.aread()).decode(errors="replace")[:800]
                    raise RuntimeError(
                        f"OpenRouter speech request failed ({response.status_code}): {detail}"
                    )
                async for line in response.aiter_lines():
                    payload = _sse_payload(line)
                    if payload is None:
                        continue
                    if payload is _DONE:
                        break
                    problem = assembler.feed(payload)
                    if problem:
                        raise RuntimeError(f"OpenRouter speech failed: {problem}")
        return assembler.finish()

    async def synthesize(self, text: str, *, voice: Optional[str] = None) -> bytes:
        result = await self.synthesize_detailed(text, voice=voice)
        return result.audio


_DONE = object()


def _sse_payload(line: str):
    text = (line or "").strip()
    if not text or text.startswith(":"):
        return None
    if text.startswith("data:"):
        data = text[5:].strip()
        if data == "[DONE]":
            return _DONE
        if not data:
            return None
        return json.loads(data)
    if text.startswith("{"):
        return json.loads(text)
    return None


def _merge_transcript(current: str, piece: str) -> str:
    if not piece:
        return current
    if not current or piece.startswith(current):
        return piece
    if current.endswith(piece):
        return current
    return current + piece


def _openrouter_base_url() -> str:
    explicit = os.getenv("TTS_BASE_URL", "").strip()
    if "openrouter.ai" in explicit:
        return explicit
    return os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")


def _first_env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "")
        if value:
            return value
    return ""
