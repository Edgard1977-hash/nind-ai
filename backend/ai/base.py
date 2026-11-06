"""Interfaces for the generation providers used by nind."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol


class ProviderNotConfigured(RuntimeError):
    """Raised when a generation mode needs a provider that has no credentials."""


class TextProvider(Protocol):
    name: str

    async def complete(self, *, system: str, user: str, model: Optional[str] = None) -> str:
        """Return the assistant text for a single-turn chat completion."""


class ImageProvider(Protocol):
    name: str

    async def generate(self, prompt: str, *, aspect_ratio: str = "9:16") -> bytes:
        """Return encoded image bytes (PNG or JPEG)."""


@dataclass
class SpeechSynthesis:
    """Spoken audio plus the timing hints needed for on-screen captions.

    ``snapshots`` are ``(decoded_byte_offset, transcript_so_far)`` pairs taken
    while a streaming audio model was speaking. Empty snapshots mean the
    caller should spread ``transcript`` evenly across the file.
    """

    audio: bytes
    transcript: str = ""
    snapshots: list = field(default_factory=list)
    audio_format: str = "wav"
    voice: str = ""


class TextToSpeechProvider(Protocol):
    name: str

    async def synthesize(self, text: str, *, voice: Optional[str] = None) -> bytes:
        """Return encoded audio bytes (WAV or MP3)."""


class SpeechToTextProvider(Protocol):
    name: str

    async def transcribe(self, audio_path: str, *, language: Optional[str] = None) -> str:
        """Transcribe an audio file and return plain text."""


@dataclass
class VideoGenerationResult:
    """Result of a video-generation provider call.

    ``video_url`` is a remote URL or an ``/api/uploads/...`` path once the
    bytes have been stored by the caller. ``provider_job_id`` is optional
    bookkeeping for async aggregators.
    """

    status: str
    video_url: Optional[str] = None
    provider_job_id: Optional[str] = None
    detail: Optional[str] = None
    raw: dict = field(default_factory=dict)


class VideoProvider(Protocol):
    """Video-generation providers (Kling, Wan, Veo, or an aggregator).

    This interface is intentionally not implemented yet. Enhanced mode calls
    it and surfaces ``ProviderNotConfigured`` until a later change wires a
    real backend.
    """

    name: str
    configured: bool

    async def generate(
        self,
        *,
        prompt: str,
        image_urls: Optional[list[str]] = None,
        duration_seconds: Optional[float] = None,
    ) -> VideoGenerationResult:
        """Start or complete a video generation job."""
