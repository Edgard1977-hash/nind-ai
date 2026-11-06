"""Named voices for Basic-mode narration.

The ids match the built-in voices accepted by OpenAI audio models on
OpenRouter (``openai/gpt-audio-mini``). Marin is the default: a natural
voice, not a forced male read.
"""

from __future__ import annotations

import os
from typing import Optional

VOICES: tuple[dict, ...] = (
    {"id": "marin", "label": "Marin", "gender": "female", "tone": "Natural"},
    {"id": "cedar", "label": "Cedar", "gender": "male", "tone": "Natural"},
    {"id": "alloy", "label": "Alloy", "gender": "neutral", "tone": "Neutral"},
    {"id": "nova", "label": "Nova", "gender": "female", "tone": "Bright"},
    {"id": "shimmer", "label": "Shimmer", "gender": "female", "tone": "Soft"},
    {"id": "coral", "label": "Coral", "gender": "female", "tone": "Warm"},
    {"id": "ash", "label": "Ash", "gender": "male", "tone": "Clear"},
    {"id": "echo", "label": "Echo", "gender": "male", "tone": "Calm"},
    {"id": "onyx", "label": "Onyx", "gender": "male", "tone": "Deep"},
)

DEFAULT_VOICE = "marin"
_IDS = {item["id"] for item in VOICES}


def list_voices() -> list[dict]:
    return [dict(item) for item in VOICES]


def resolve_voice(requested: Optional[str]) -> str:
    """Return a known voice id. Empty input uses ``TTS_VOICE`` or Marin."""
    raw = (requested or "").strip().lower()
    if raw in _IDS:
        return raw
    configured = os.getenv("TTS_VOICE", "").strip().lower()
    if configured in _IDS:
        return configured
    return DEFAULT_VOICE
