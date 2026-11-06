"""Provider-agnostic AI layer.

Text, image, speech-to-text, and text-to-speech are configured entirely from
environment variables and talk to public HTTP APIs. Basic voiceover uses
OpenRouter chat-audio (``openai/gpt-audio-mini``) when ``OPENROUTER_API_KEY``
is set. Video generation is a stub interface for a later provider (Kling,
Wan, Veo, or an aggregator).
"""

from ai.base import (
    ImageProvider,
    ProviderNotConfigured,
    SpeechToTextProvider,
    TextProvider,
    TextToSpeechProvider,
    VideoGenerationResult,
    VideoProvider,
)
from ai.factory import (
    clear_provider_overrides,
    get_image_provider,
    get_speech_provider,
    get_text_provider,
    get_tts_provider,
    get_video_provider,
    provider_status,
    set_provider_overrides,
)

__all__ = [
    "ImageProvider",
    "ProviderNotConfigured",
    "SpeechToTextProvider",
    "TextProvider",
    "TextToSpeechProvider",
    "VideoGenerationResult",
    "VideoProvider",
    "clear_provider_overrides",
    "get_image_provider",
    "get_speech_provider",
    "get_text_provider",
    "get_tts_provider",
    "get_video_provider",
    "provider_status",
    "set_provider_overrides",
]
