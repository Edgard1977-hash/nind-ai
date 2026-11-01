"""Video-generation provider interface.

Enhanced mode ("Улучшенная") produces content from a generated video, sometimes
mixed with photos. Concrete adapters (Kling, Wan, Veo, or an aggregator such
as Fal or Replicate) belong in a follow-up change. Until ``VIDEO_PROVIDER``
names an implemented adapter, this module reports that the provider is not
configured.
"""

from __future__ import annotations

import os
from typing import Optional

from ai.base import ProviderNotConfigured, VideoGenerationResult


class UnconfiguredVideoProvider:
    """Placeholder used when no video backend has been selected."""

    configured = False

    def __init__(self, requested: str = "") -> None:
        self.requested = requested
        self.name = requested or "unconfigured"

    async def generate(
        self,
        *,
        prompt: str,
        image_urls: Optional[list[str]] = None,
        duration_seconds: Optional[float] = None,
    ) -> VideoGenerationResult:
        del prompt, image_urls, duration_seconds
        if self.requested:
            detail = (
                f"Enhanced mode is coming soon: video provider '{self.requested}' "
                "is not implemented yet. A later release will add Kling, Wan, or Veo "
                "through an aggregator. Set VIDEO_PROVIDER only after that adapter exists."
            )
        else:
            detail = (
                "Enhanced mode is coming soon: no video generation provider is configured. "
                "Basic mode (image generation plus ffmpeg montage) is available. "
                "Video providers (Kling, Wan, Veo) will be added in a later release."
            )
        raise ProviderNotConfigured(detail)


def build_video_provider() -> UnconfiguredVideoProvider:
    requested = os.getenv("VIDEO_PROVIDER", "").strip().lower()
    # Intentionally no concrete adapter yet. The call site still goes through
    # this factory so wiring a provider later does not change the API.
    return UnconfiguredVideoProvider(requested=requested)
