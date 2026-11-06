"""Basic and Enhanced generation pipelines.

Basic ("Базовая") builds a vertical video from still images (Gemini "Nano
Banana" or the OpenRouter fallback) animated with ffmpeg.

Enhanced ("Улучшенная") asks the video-generation provider. Until that
provider is implemented the call fails with a clear configuration error and
any reserved credits are returned.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ai.base import ProviderNotConfigured, SpeechSynthesis
from ai.factory import get_image_provider, get_text_provider, get_tts_provider, get_video_provider
from ai.voices import resolve_voice
from captions import allocate_durations, cues_for_narration, normalize_plan, wav_duration
from video_service import compose_basic_master, concatenate_videos, create_image_video, probe_duration

logger = logging.getLogger(__name__)

BASIC_WIDTH = 1080
BASIC_HEIGHT = 1920
BASIC_FPS = 30

BASIC_SYSTEM = (
    "You plan short vertical social videos made from photoreal still photographs. "
    "A voice reads the narration while each photo moves slowly (Ken Burns) and cuts hard to the next. "
    "Return ONLY valid JSON, no markdown."
)


def _parse_json(text: str) -> Optional[dict]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _fallback_plan(prompt: str) -> dict:
    return {
        "title": (prompt or "Video")[:80],
        "narration": prompt or "",
        "scenes": [
            {
                "image_prompt": prompt or "A cinematic vertical photograph",
                "animation": "zoom_in",
                "duration": 4,
            }
        ],
    }


async def _mark(db, project_id: str, **fields) -> None:
    fields["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.video_projects.update_one({"id": project_id}, {"$set": fields})


async def refund_generation_credits(db, project: dict) -> None:
    cost = int(project.get("credits_charged") or 0)
    user_id = project.get("user_id")
    if cost <= 0 or not user_id or project.get("credits_refunded"):
        return
    await db.users.update_one({"user_id": user_id}, {"$inc": {"credits": cost}})
    await db.video_projects.update_one(
        {"id": project["id"]},
        {"$set": {"credits_refunded": True}},
    )
    project["credits_refunded"] = True


async def process_enhanced_generation(db, project: dict, work_dir: Path, uploads_dir: Path) -> None:
    """Call the video provider. The current provider is a stub."""
    del work_dir, uploads_dir
    project_id = project["id"]
    await _mark(db, project_id, status="processing", progress=10, progress_message="Enhanced mode")
    provider = get_video_provider()
    try:
        result = await provider.generate(
            prompt=project.get("prompt") or "",
            image_urls=project.get("product_images") or None,
            duration_seconds=8,
        )
    except ProviderNotConfigured as exc:
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project_id,
            status="error",
            error=str(exc),
            progress_message="Enhanced mode is coming soon",
        )
        return
    video_url = getattr(result, "video_url", None)
    if not video_url:
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project_id,
            status="error",
            error="Video provider returned no video URL",
            progress_message="Enhanced mode failed",
        )
        return
    await _mark(
        db,
        project_id,
        status="completed",
        progress=100,
        progress_message="Готово!",
        video_url=video_url,
        mode="enhanced",
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


def _script_request(prompt: str) -> str:
    return (
        f"User prompt: {prompt}\n"
        "Write the narration in the same language as the user prompt.\n"
        "The narration is 45 to 70 spoken words, about 18 to 24 seconds at a natural pace.\n"
        "Return JSON with title, narration, and 6 to 8 scenes.\n"
        "Each scene has spoken (the exact words said during that photo), "
        "image_prompt (one photoreal vertical photograph, no text, no logos, no collage), "
        "and animation (zoom_in, zoom_out, pan_left, pan_right, or pan_up).\n"
        "Joining the spoken fields with single spaces must recreate the narration.\n"
        "Vary the animations and do not repeat the same animation twice in a row."
    )


async def _write_plan(prompt: str) -> dict:
    plan = None
    try:
        raw = await get_text_provider().complete(system=BASIC_SYSTEM, user=_script_request(prompt))
        plan = _parse_json(raw)
    except ProviderNotConfigured:
        logger.info("Text provider is not configured; using the prompt as the narration")
    except Exception as exc:
        logger.warning("Basic script generation failed, using fallback: %s", exc)
    if not plan or not plan.get("scenes"):
        plan = _fallback_plan(prompt)
    return normalize_plan(plan, prompt)


async def _speak(narration: str, voice: str) -> SpeechSynthesis:
    provider = get_tts_provider()
    detailed = getattr(provider, "synthesize_detailed", None)
    if detailed is not None:
        return await detailed(narration, voice=voice)
    audio = await provider.synthesize(narration, voice=voice)
    return SpeechSynthesis(audio=audio, transcript=narration, audio_format="mp3", voice=voice)


async def process_basic_generation(db, project: dict, work_dir: Path, uploads_dir: Path) -> None:
    """Script, full voiceover, photoreal stills, then a Ken Burns montage timed to the speech."""
    project_id = project["id"]
    prompt = project.get("prompt") or ""
    voice = resolve_voice(project.get("voice"))
    work_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    await _mark(db, project_id, status="processing", progress=8, progress_message="Пишем сценарий...")
    plan = await _write_plan(prompt)
    narration = (plan.get("narration") or "").strip()
    scenes = list(plan.get("scenes") or [])
    if not narration or not scenes:
        plan = normalize_plan(_fallback_plan(prompt), prompt)
        narration = plan["narration"]
        scenes = plan["scenes"]

    speech: Optional[SpeechSynthesis] = None
    if narration:
        await _mark(db, project_id, progress=18, progress_message="Записываем голос...")
        try:
            speech = await _speak(narration, voice)
        except ProviderNotConfigured:
            logger.info("TTS is not configured; finishing Basic video without narration audio")
        except Exception as exc:
            logger.error("Voiceover failed: %s", exc)
            await refund_generation_credits(db, project)
            await _mark(
                db,
                project_id,
                status="error",
                error=f"Voiceover failed: {exc}",
                progress_message="Не удалось записать голос",
            )
            return

    audio_url = None
    audio_path: Optional[Path] = None
    captions: list[dict] = []
    spoken_duration = 0.0
    if speech is not None and speech.audio:
        extension = speech.audio_format if speech.audio_format in {"wav", "mp3", "flac", "opus"} else "wav"
        audio_name = f"{uuid.uuid4().hex}.{extension}"
        audio_path = uploads_dir / audio_name
        audio_path.write_bytes(speech.audio)
        audio_url = f"/api/uploads/{audio_name}"
        spoken_duration = wav_duration(speech.audio) or 0.0
        if spoken_duration <= 0:
            spoken_duration = await probe_duration(audio_path)
        if spoken_duration <= 0:
            await refund_generation_credits(db, project)
            await _mark(
                db,
                project_id,
                status="error",
                error="Voiceover audio has no duration",
                progress_message="Не удалось записать голос",
            )
            return
        captions = cues_for_narration(
            audio=speech.audio,
            snapshots=speech.snapshots,
            transcript=speech.transcript,
            script=narration,
            duration=spoken_duration,
        )
        weights = [max(1, len((scene.get("spoken") or "").split())) for scene in scenes]
        durations = allocate_durations(weights, spoken_duration, minimum=1.5)
    else:
        durations = []
        for scene in scenes:
            try:
                duration = float(scene.get("duration") or 4)
            except (TypeError, ValueError):
                duration = 4.0
            durations.append(min(8.0, max(2.0, duration)))

    scenes_out = []
    clip_paths: list[Path] = []
    image_provider = get_image_provider()
    await _mark(db, project_id, progress=30, progress_message="Генерируем изображения...")

    for index, scene in enumerate(scenes):
        image_prompt = (scene.get("image_prompt") or prompt or "cinematic still").strip()
        visual_prompt = (
            "Photorealistic vertical photograph, natural light, sharp detail, "
            "no text, no watermark, no collage, no border. "
            f"{image_prompt}"
        )
        animation = scene.get("animation") or "zoom_in"
        duration = durations[index] if index < len(durations) else 4.0
        try:
            image_bytes = await image_provider.generate(visual_prompt, aspect_ratio="9:16")
        except ProviderNotConfigured as exc:
            await refund_generation_credits(db, project)
            await _mark(
                db,
                project_id,
                status="error",
                error=str(exc),
                progress_message="Image provider is not configured",
            )
            return
        except Exception as exc:
            logger.error("Image generation failed: %s", exc)
            await refund_generation_credits(db, project)
            await _mark(
                db,
                project_id,
                status="error",
                error=f"Image generation failed: {exc}",
                progress_message="Не удалось создать изображение",
            )
            return

        image_name = f"{uuid.uuid4().hex}.png"
        image_path = uploads_dir / image_name
        image_path.write_bytes(image_bytes)
        image_url = f"/api/uploads/{image_name}"
        spoken = scene.get("spoken") or scene.get("text") or ""
        scenes_out.append(
            {
                "text": spoken,
                "spoken": spoken,
                "image_prompt": image_prompt,
                "image_url": image_url,
                "animation": animation,
                "duration": duration,
            }
        )
        clip = await create_image_video(
            str(image_path),
            work_dir,
            duration=duration,
            animation=animation,
            width=BASIC_WIDTH,
            height=BASIC_HEIGHT,
            fps=BASIC_FPS,
        )
        if clip:
            clip_paths.append(clip)
        progress = 30 + int(45 * (index + 1) / max(1, len(scenes)))
        await _mark(db, project_id, progress=progress, progress_message=f"Сцена {index + 1}/{len(scenes)}")

    if not clip_paths:
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project_id,
            status="error",
            error="ffmpeg did not produce a clip from the generated images",
            progress_message="Сборка видео не удалась",
        )
        return

    await _mark(db, project_id, progress=82, progress_message="Собираем видео...")
    if len(clip_paths) == 1:
        final_video = clip_paths[0]
    else:
        final_video = await concatenate_videos(clip_paths, work_dir)

    if final_video and audio_path is not None:
        master = await compose_basic_master(
            Path(final_video),
            work_dir,
            voice_path=audio_path,
            captions=captions,
        )
        if not master:
            await refund_generation_credits(db, project)
            await _mark(
                db,
                project_id,
                status="error",
                error="ffmpeg could not mix the voiceover into the montage",
                progress_message="Сборка видео не удалась",
            )
            return
        final_video = master

    if not final_video or not Path(final_video).exists():
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project_id,
            status="error",
            error="Final video file is missing",
            progress_message="Сборка видео не удалась",
        )
        return

    final_name = f"video_{project_id}.mp4"
    final_path = uploads_dir / final_name
    Path(final_video).replace(final_path)
    await _mark(
        db,
        project_id,
        status="completed",
        progress=100,
        progress_message="Готово!",
        mode="basic",
        voice=voice,
        title=plan.get("title") or prompt[:80],
        script=narration,
        scenes=scenes_out,
        captions=captions,
        audio_url=audio_url,
        video_url=f"/api/uploads/{final_name}",
        poster_url=scenes_out[0]["image_url"] if scenes_out else None,
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
