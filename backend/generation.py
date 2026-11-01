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
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from ai.base import ProviderNotConfigured
from ai.factory import get_image_provider, get_text_provider, get_tts_provider, get_video_provider
from video_service import add_audio_to_video, concatenate_videos, create_image_video

logger = logging.getLogger(__name__)

BASIC_SYSTEM = (
    "You plan short vertical social videos made from still images. "
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


def _as_datetime(value) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    return None


def placeholder_image_bytes(prompt: str) -> bytes:
    """A vertical still used only when no image provider is configured."""
    import io

    from PIL import Image, ImageDraw, ImageFont

    width, height = 720, 1280
    image = Image.new("RGB", (width, height), (12, 12, 14))
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        body_font = title_font
    draw.rectangle((0, 0, width, 140), fill=(28, 28, 32))
    draw.text((36, 36), "Preview", fill=(255, 255, 255), font=title_font)
    draw.text((36, 86), "AI image provider is not configured", fill=(190, 190, 196), font=body_font)
    words = (prompt or "Untitled").split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if len(trial) > 32:
            if current:
                lines.append(current)
            current = word
        else:
            current = trial
    if current:
        lines.append(current)
    y = 200
    for line in lines[:14]:
        draw.text((36, y), line, fill=(255, 255, 255), font=body_font)
        y += 44
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


async def expire_stuck_project(db, project: dict) -> dict:
    """Mark a job failed when it has been processing longer than the timeout."""
    if not project or project.get("status") not in ("pending", "processing"):
        return project
    try:
        limit = int(os.getenv("GENERATION_TIMEOUT_MINUTES", "15"))
    except ValueError:
        limit = 15
    limit = max(1, limit)
    started = _as_datetime(project.get("updated_at")) or _as_datetime(project.get("created_at"))
    if started is None:
        return project
    age = datetime.now(timezone.utc) - started
    if age <= timedelta(minutes=limit):
        return project
    message = f"Generation timed out after {limit} minutes"
    await refund_generation_credits(db, project)
    await _mark(
        db,
        project["id"],
        status="failed",
        error=message,
        progress_message=message,
    )
    project["status"] = "failed"
    project["error"] = message
    project["progress_message"] = message
    return project


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
            status="failed",
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
            status="failed",
            error="Video provider returned no video URL",
            progress_message="Enhanced mode failed",
        )
        return
    await _mark(
        db,
        project_id,
        status="completed",
        progress=100,
        progress_message="Done",
        video_url=video_url,
        mode="enhanced",
        completed_at=datetime.now(timezone.utc).isoformat(),
    )


async def process_basic_generation(db, project: dict, work_dir: Path, uploads_dir: Path) -> None:
    """Image-base generation. Always finishes as completed or failed."""
    try:
        await _process_basic_body(db, project, work_dir, uploads_dir)
    except Exception as exc:
        logger.exception("Basic generation failed")
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project["id"],
            status="failed",
            error=str(exc),
            progress_message="Generation failed",
        )


async def _process_basic_body(db, project: dict, work_dir: Path, uploads_dir: Path) -> None:
    """Image-base generation: LLM scene plan, image provider, ffmpeg montage."""
    project_id = project["id"]
    prompt = project.get("prompt") or ""
    work_dir.mkdir(parents=True, exist_ok=True)
    uploads_dir.mkdir(parents=True, exist_ok=True)

    await _mark(db, project_id, status="processing", progress=8, progress_message="Writing the script...")

    text_available = True
    plan = None
    try:
        raw = await get_text_provider().complete(
            system=BASIC_SYSTEM,
            user=(
                f"User prompt: {prompt}\n"
                "Language should follow the prompt.\n"
                "Return JSON with title, narration, and 3 scenes. "
                "Each scene has text (one short on-screen caption, not the whole prompt), "
                "image_prompt (a visual description of a photograph; do not ask for words, "
                "letters, or captions inside the image), "
                "animation (zoom_in, zoom_out, pan_left, or pan_right), and duration (3 to 5)."
            ),
        )
        plan = _parse_json(raw)
    except ProviderNotConfigured:
        text_available = False
        logger.info("Text provider is not configured; using the prompt as the image description")
    except Exception as exc:
        raise RuntimeError(f"Script generation failed: {exc}") from exc

    if text_available:
        if not plan or not plan.get("scenes"):
            raise RuntimeError("The text model did not return a scene list.")
    elif not plan or not plan.get("scenes"):
        plan = _fallback_plan(prompt)

    scenes_out = []
    clip_paths: list[Path] = []
    image_provider = get_image_provider()
    scenes = list(plan.get("scenes") or [])[:6]
    used_placeholder = False
    await _mark(db, project_id, progress=25, progress_message="Creating images...")

    for index, scene in enumerate(scenes):
        image_prompt = (scene.get("image_prompt") or "").strip()
        caption = (scene.get("text") or "").strip() if text_available else ""
        if text_available and not image_prompt:
            image_prompt = "A cinematic vertical photograph with no written text"
        elif not image_prompt:
            image_prompt = (prompt or "A cinematic vertical photograph").strip()
        animation = scene.get("animation") or "zoom_in"
        if animation not in ("zoom_in", "zoom_out", "pan_left", "pan_right"):
            animation = "zoom_in"
        try:
            duration = float(scene.get("duration") or 4)
        except (TypeError, ValueError):
            duration = 4
        duration = min(8.0, max(2.0, duration))

        visual_prompt = image_prompt
        if text_available:
            visual_prompt = (
                "One photograph with no written words, letters, or captions in the frame. "
                + image_prompt
            )
        try:
            image_bytes = await image_provider.generate(visual_prompt, aspect_ratio="9:16")
        except ProviderNotConfigured:
            used_placeholder = True
            logger.info("AI image provider is not configured; using a labeled placeholder still")
            image_bytes = placeholder_image_bytes(image_prompt)
        except Exception as exc:
            raise RuntimeError(f"Image generation failed: {exc}") from exc

        image_name = f"{uuid.uuid4().hex}.png"
        image_path = uploads_dir / image_name
        image_path.write_bytes(image_bytes)
        image_url = f"/api/uploads/{image_name}"
        scenes_out.append(
            {
                "text": caption,
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
            caption=caption,
        )
        if clip:
            clip_paths.append(clip)
        progress = 25 + int(50 * (index + 1) / max(1, len(scenes)))
        await _mark(db, project_id, progress=progress, progress_message=f"Scene {index + 1}/{len(scenes)}")

    if not clip_paths:
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project_id,
            status="failed",
            error="ffmpeg did not produce a clip from the generated images",
            progress_message="Video assembly failed",
        )
        return

    await _mark(db, project_id, progress=80, progress_message="Assembling the video...")
    if len(clip_paths) == 1:
        final_video = clip_paths[0]
    else:
        final_video = await concatenate_videos(clip_paths, work_dir)

    audio_url = None
    narration = (plan.get("narration") or "").strip()
    if final_video and narration:
        try:
            audio_bytes = await get_tts_provider().synthesize(narration)
            audio_name = f"{uuid.uuid4().hex}.mp3"
            audio_path = uploads_dir / audio_name
            audio_path.write_bytes(audio_bytes)
            audio_url = f"/api/uploads/{audio_name}"
            mixed = await add_audio_to_video(final_video, audio_path, work_dir)
            if mixed:
                final_video = mixed
        except ProviderNotConfigured:
            logger.info("TTS is not configured; finishing Basic video without narration audio")
        except Exception as exc:
            logger.warning("TTS failed, continuing without audio: %s", exc)

    if not final_video or not Path(final_video).exists():
        await refund_generation_credits(db, project)
        await _mark(
            db,
            project_id,
            status="failed",
            error="Final video file is missing",
            progress_message="Video assembly failed",
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
        progress_message=(
            "Preview ready. AI image provider is not configured."
            if used_placeholder
            else "Done"
        ),
        mode="basic",
        title=plan.get("title") or prompt[:80],
        script=narration,
        scenes=scenes_out,
        audio_url=audio_url,
        video_url=f"/api/uploads/{final_name}",
        poster_url=scenes_out[0]["image_url"] if scenes_out else None,
        image_source="placeholder" if used_placeholder else "provider",
        notice=(
            "AI image provider is not configured. This video uses a labeled placeholder still."
            if used_placeholder
            else None
        ),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
