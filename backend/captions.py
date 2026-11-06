"""Phrase captions and scene timings for the Basic Ken Burns pipeline.

Captions are short spoken phrases (about one to three words), not one
static line per scene. When the speech stream reports transcript slices
alongside audio bytes, those slices set the clock. A single late transcript
falls back to spreading the words evenly across the voiceover.
"""

from __future__ import annotations

import struct
from typing import Optional

ANIMATIONS = ("zoom_in", "zoom_out", "pan_left", "pan_right", "pan_up")


def wav_info(audio: bytes) -> Optional[dict]:
    """Return PCM layout for a standard WAV file, or None."""
    if len(audio) < 44 or audio[:4] != b"RIFF" or audio[8:12] != b"WAVE":
        return None
    offset = 12
    fmt = None
    data_offset = None
    data_size = None
    while offset + 8 <= len(audio):
        chunk_id = audio[offset : offset + 4]
        chunk_size = int.from_bytes(audio[offset + 4 : offset + 8], "little")
        start = offset + 8
        if chunk_id == b"fmt " and chunk_size >= 16:
            _audio_format, _channels, rate, _byte_rate, block_align, _bits = struct.unpack_from(
                "<HHIIHH", audio, start
            )
            fmt = (rate, block_align)
        elif chunk_id == b"data":
            data_offset = start
            data_size = chunk_size
            break
        offset = start + chunk_size + (chunk_size % 2)
    if not fmt or data_offset is None:
        return None
    rate, block_align = fmt
    if rate <= 0 or block_align <= 0:
        return None
    pcm_bytes = data_size if data_size is not None else max(0, len(audio) - data_offset)
    return {
        "data_offset": data_offset,
        "bytes_per_second": rate * block_align,
        "duration": pcm_bytes / (rate * block_align),
    }


def wav_duration(audio: bytes) -> Optional[float]:
    info = wav_info(audio)
    if not info or info["duration"] <= 0:
        return None
    return float(info["duration"])


def allocate_durations(weights: list[float], total: float, minimum: float = 1.5) -> list[float]:
    """Split ``total`` seconds across scenes, keeping each one at least ``minimum`` when possible."""
    count = len(weights)
    if count == 0:
        return []
    total = max(float(total), 0.1)
    if total < minimum * count:
        share = total / count
        return [share] * count
    clean = [max(float(weight), 0.01) for weight in weights]
    weight_sum = sum(clean)
    raw = [total * weight / weight_sum for weight in clean]
    for _ in range(6):
        deficit = 0.0
        free: list[int] = []
        for index, value in enumerate(raw):
            if value < minimum - 1e-6:
                deficit += minimum - value
                raw[index] = minimum
            else:
                free.append(index)
        if deficit <= 1e-6 or not free:
            break
        spare = [(index, raw[index] - minimum) for index in free]
        spare_sum = sum(amount for _, amount in spare)
        if spare_sum <= 1e-6:
            break
        for index, amount in spare:
            raw[index] -= deficit * (amount / spare_sum)
    raw[-1] += total - sum(raw)
    if raw[-1] < 0:
        scale = total / sum(raw)
        raw = [value * scale for value in raw]
    return raw


def _assign_spoken(scenes: list[dict], narration: str) -> None:
    words = narration.split()
    if not words:
        return
    base, extra = divmod(len(words), len(scenes))
    index = 0
    for scene_index, scene in enumerate(scenes):
        take = base + (1 if scene_index < extra else 0)
        spoken = " ".join(words[index : index + take])
        index += take
        scene["spoken"] = spoken
        scene["text"] = spoken


def normalize_plan(plan: Optional[dict], prompt: str) -> dict:
    """Make a scene plan safe to render and keep narration aligned with scenes."""
    prompt = " ".join((prompt or "").split())
    source = plan if isinstance(plan, dict) else {}
    scenes: list[dict] = []
    previous = None
    for index, scene in enumerate(list(source.get("scenes") or [])[:8]):
        if not isinstance(scene, dict):
            continue
        animation = scene.get("animation") or "zoom_in"
        if animation not in ANIMATIONS or animation == previous:
            animation = ANIMATIONS[index % len(ANIMATIONS)]
            if animation == previous:
                animation = ANIMATIONS[(index + 1) % len(ANIMATIONS)]
        previous = animation
        spoken = " ".join(str(scene.get("spoken") or scene.get("text") or "").split())
        image_prompt = str(scene.get("image_prompt") or prompt or "A cinematic vertical photograph").strip()
        try:
            duration = float(scene.get("duration") or 4)
        except (TypeError, ValueError):
            duration = 4.0
        scenes.append(
            {
                "spoken": spoken,
                "text": spoken,
                "image_prompt": image_prompt,
                "animation": animation,
                "duration": min(8.0, max(2.0, duration)),
            }
        )
    if not scenes:
        spoken = prompt or "A short film"
        scenes = [
            {
                "spoken": spoken,
                "text": spoken,
                "image_prompt": prompt or "A cinematic vertical photograph",
                "animation": "zoom_in",
                "duration": 4.0,
            }
        ]
    joined = " ".join(scene["spoken"] for scene in scenes if scene["spoken"])
    narration = " ".join(str(source.get("narration") or "").split())
    if joined and (not narration or len(joined) >= len(narration) * 0.8):
        narration = joined
    elif narration:
        _assign_spoken(scenes, narration)
    else:
        narration = joined or prompt
        if narration and not joined:
            _assign_spoken(scenes, narration)
    title = str(source.get("title") or narration or prompt or "Video").strip()[:80]
    return {"title": title, "narration": narration, "scenes": scenes}


def words_evenly(text: str, duration: float) -> list[dict]:
    tokens = [token for token in str(text or "").split() if token]
    duration = max(float(duration), 0.1)
    if not tokens:
        return []
    weights = [max(len(token), 1) for token in tokens]
    total = sum(weights)
    cursor = 0.0
    words = []
    for token, weight in zip(tokens, weights):
        span = duration * weight / total
        words.append({"text": token, "start": cursor, "end": cursor + span})
        cursor += span
    words[-1]["end"] = duration
    return words


def _byte_to_time(position: int, info: Optional[dict], duration: float) -> float:
    if not info:
        return 0.0
    sample = max(0, int(position) - int(info["data_offset"]))
    return min(float(duration), sample / float(info["bytes_per_second"]))


def _snapshots_are_timed(times: list[float], duration: float) -> bool:
    if len(times) < 4 or duration <= 0:
        return False
    span = times[-1] - times[0]
    return times[0] <= duration * 0.35 and span >= duration * 0.45


def words_from_snapshots(
    snapshots: list,
    audio: bytes,
    duration: float,
    transcript: str,
) -> list[dict]:
    info = wav_info(audio)
    cleaned = [(int(position), " ".join(str(text).split())) for position, text in snapshots if str(text).strip()]
    if not cleaned:
        return words_evenly(transcript, duration)
    times = [_byte_to_time(position, info, duration) for position, _text in cleaned]
    if not _snapshots_are_timed(times, duration):
        return words_evenly(transcript or cleaned[-1][1], duration)
    words: list[dict] = []
    previous_text = ""
    previous_time = 0.0
    for (_position, text), moment in zip(cleaned, times):
        if text.startswith(previous_text):
            fresh = text[len(previous_text) :]
        else:
            fresh = text
        tokens = fresh.split()
        if not tokens:
            previous_text = text
            previous_time = moment
            continue
        start = previous_time
        end = max(moment, start + 0.01)
        step = (end - start) / len(tokens)
        for index, token in enumerate(tokens):
            words.append({"text": token, "start": start + index * step, "end": start + (index + 1) * step})
        previous_text = text
        previous_time = moment
    if words and words[-1]["end"] < duration:
        words[-1]["end"] = duration
    return words


def phrase_cues(words: list[dict], *, max_words: int = 3, max_chars: int = 32) -> list[dict]:
    """Group word timings into the short on-screen phrases used in the reference."""
    phrases: list[dict] = []
    bucket: list[dict] = []

    def flush() -> None:
        if not bucket:
            return
        phrases.append(
            {
                "text": " ".join(item["text"] for item in bucket),
                "timestamp_start": float(bucket[0]["start"]),
                "timestamp_end": float(bucket[-1]["end"]),
            }
        )
        bucket.clear()

    for word in words:
        if not word.get("text"):
            continue
        tentative = " ".join(item["text"] for item in [*bucket, word])
        span = float(word["end"]) - (float(bucket[0]["start"]) if bucket else float(word["start"]))
        if bucket and (len(bucket) >= max_words or len(tentative) > max_chars or span > 1.45):
            flush()
        bucket.append(word)
    flush()
    for index, phrase in enumerate(phrases):
        if index + 1 < len(phrases):
            phrase["timestamp_end"] = max(phrase["timestamp_start"] + 0.05, phrases[index + 1]["timestamp_start"])
        else:
            phrase["timestamp_end"] = max(phrase["timestamp_end"], phrase["timestamp_start"] + 0.2)
    return phrases


def cues_for_narration(
    *,
    audio: bytes,
    snapshots: list,
    transcript: str,
    script: str,
    duration: float,
) -> list[dict]:
    spoken = " ".join((transcript or script or "").split())
    if duration <= 0 or not spoken:
        return []
    words = words_from_snapshots(snapshots or [], audio or b"", duration, spoken)
    return phrase_cues(words)
