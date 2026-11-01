"""Retry helpers for provider HTTP 429s."""

from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def is_rate_limit(exc: BaseException) -> bool:
    status = getattr(exc, "status_code", None)
    if status == 429:
        return True
    response = getattr(exc, "response", None)
    if getattr(response, "status_code", None) == 429:
        return True
    text = str(exc).lower()
    return "429" in text or "rate limit" in text or "resource_exhausted" in text


async def retry_rate_limits(
    operation: Callable[[], Awaitable[T]],
    *,
    label: str,
    delays: tuple[float, ...] = (1.0, 2.0, 4.0),
) -> T:
    """Run ``operation`` and back off when the provider returns 429.

    ``delays`` is the wait before each retry. The last failure becomes a
    clear RuntimeError so the generation job can store it and stop.
    """
    attempts = len(delays) + 1
    for index in range(attempts):
        try:
            return await operation()
        except Exception as exc:
            if not is_rate_limit(exc) or index == attempts - 1:
                if is_rate_limit(exc):
                    raise RuntimeError(
                        f"{label} rate limit (429). Try again in a moment."
                    ) from exc
                raise
            wait = delays[index]
            logger.warning("%s rate limited (429); retrying in %.1fs", label, wait)
            if wait:
                await asyncio.sleep(wait)
    raise RuntimeError(f"{label} rate limit (429). Try again in a moment.")
