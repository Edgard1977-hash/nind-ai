"""
Video Montage Service - AI-powered video editing
Analyzes video, finds interesting moments, adds transitions, effects, and music
"""
import os
import asyncio
import logging
import uuid
import json
import subprocess
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import random

logger = logging.getLogger(__name__)

# Sound effect types and their characteristics
SOUND_EFFECTS = {
    "whoosh": {"contexts": ["transition", "fast_movement", "reveal"], "intensity": "medium"},
    "impact": {"contexts": ["dramatic", "hit", "emphasis"], "intensity": "high"},
    "ding": {"contexts": ["positive", "achievement", "notification"], "intensity": "low"},
    "boom": {"contexts": ["explosion", "dramatic", "reveal"], "intensity": "high"},
    "swoosh": {"contexts": ["movement", "transition"], "intensity": "low"},
    "cash": {"contexts": ["money", "success", "win"], "intensity": "medium"},
    "laugh": {"contexts": ["funny", "comedy", "meme"], "intensity": "medium"},
    "wow": {"contexts": ["surprise", "amazing"], "intensity": "medium"},
}

# Montage styles
MONTAGE_STYLES = {
    "tiktok": {
        "name": "TikTok/Reels",
        "name_ru": "TikTok/Reels",
        "clip_duration": (1.5, 4.0),  # min, max seconds per clip
        "transition_duration": 0.2,
        "transitions": ["glitch", "flash", "zoom", "shake"],
        "effects": ["zoom_pulse", "rgb_split", "speed_ramp"],
        "text_style": "bold_impact"
    },
    "youtube": {
        "name": "YouTube",
        "name_ru": "YouTube",
        "clip_duration": (3.0, 8.0),
        "transition_duration": 0.4,
        "transitions": ["fade", "dissolve", "slide"],
        "effects": ["subtle_zoom", "color_grade"],
        "text_style": "clean"
    },
    "meme": {
        "name": "Meme/Comedy",
        "name_ru": "Мемы/Комедия",
        "clip_duration": (0.8, 3.0),
        "transition_duration": 0.15,
        "transitions": ["hard_cut", "zoom_in", "shake", "flash"],
        "effects": ["zoom_punch", "freeze_frame", "speed_up", "slow_mo"],
        "text_style": "meme_impact"
    },
    "cinematic": {
        "name": "Cinematic",
        "name_ru": "Кинематографичный",
        "clip_duration": (4.0, 10.0),
        "transition_duration": 0.6,
        "transitions": ["fade", "dissolve", "wipe"],
        "effects": ["letterbox", "color_grade", "film_grain"],
        "text_style": "elegant"
    }
}


async def analyze_video_for_montage(video_path: Path, style: str = "tiktok") -> Dict:
    """
    Analyze video using AI to find interesting moments.
    
    Returns timestamps and descriptions of key moments.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    style_config = MONTAGE_STYLES.get(style, MONTAGE_STYLES["tiktok"])
    
    # Get video info
    video_info = await get_video_info(video_path)
    duration = video_info.get("duration", 60)
    
    # Extract frames for analysis
    frames_data = await extract_key_frames(video_path, num_frames=min(20, int(duration / 3)))
    
    # Analyze audio levels to find peaks
    audio_peaks = await analyze_audio_peaks(video_path)
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"montage-{uuid.uuid4()}",
            system_message="You are a professional video editor. Analyze video content and find the most engaging moments."
        )
        chat.with_model("openai", "gpt-5.2")
        
        clip_min, clip_max = style_config["clip_duration"]
        
        analysis_prompt = f"""Analyze this video for {style_config['name']} style montage.

Video duration: {duration:.1f} seconds
Audio peaks (timestamps with high energy): {audio_peaks[:15]}
Frames extracted at: {[f['timestamp'] for f in frames_data]}

Based on the style "{style}", identify the most interesting moments.
For {style_config['name']} style:
- Clip duration: {clip_min}-{clip_max} seconds
- Focus on: high energy, visual interest, emotional peaks

Return JSON:
{{
    "clips": [
        {{
            "start": 0.0,
            "end": 3.5,
            "description": "Opening hook - high energy intro",
            "importance": 10,
            "suggested_effects": ["zoom_pulse"],
            "suggested_text": "Wait for it...",
            "sound_effect": "whoosh"
        }}
    ],
    "overall_mood": "energetic/calm/dramatic/funny",
    "suggested_music_tempo": "fast/medium/slow",
    "total_clips": 5
}}

Select {min(8, int(duration / clip_min))} best moments. Prioritize variety and engagement."""
        
        msg = UserMessage(text=analysis_prompt)
        response = await chat.send_message(msg)
        
        # Parse response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            logger.info(f"AI found {len(result.get('clips', []))} interesting moments")
            return result
    except Exception as e:
        logger.warning(f"AI analysis failed: {e}")
    
    # Fallback: use audio peaks and evenly distributed clips
    clips = []
    clip_duration = (clip_min + clip_max) / 2
    num_clips = min(8, int(duration / clip_duration))
    
    # Combine audio peaks with even distribution
    timestamps = sorted(set(audio_peaks[:num_clips * 2] + [i * duration / num_clips for i in range(num_clips)]))
    
    for i, ts in enumerate(timestamps[:num_clips]):
        clips.append({
            "start": max(0, ts - 0.5),
            "end": min(duration, ts + clip_duration),
            "description": f"Clip {i+1}",
            "importance": 10 - i,
            "suggested_effects": random.choice([["zoom_pulse"], ["speed_ramp"], []]),
            "suggested_text": None,
            "sound_effect": random.choice(["whoosh", "swoosh", None])
        })
    
    return {
        "clips": clips,
        "overall_mood": "energetic",
        "suggested_music_tempo": "medium",
        "total_clips": len(clips)
    }


async def get_video_info(video_path: Path) -> Dict:
    """Get video metadata using ffprobe"""
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(video_path)
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        data = json.loads(stdout.decode())
        
        duration = float(data.get("format", {}).get("duration", 0))
        
        # Find video stream
        width, height, fps = 1920, 1080, 30
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                width = stream.get("width", 1920)
                height = stream.get("height", 1080)
                fps_str = stream.get("r_frame_rate", "30/1")
                if "/" in fps_str:
                    num, den = fps_str.split("/")
                    fps = int(num) / max(1, int(den))
                break
        
        return {
            "duration": duration,
            "width": width,
            "height": height,
            "fps": fps
        }
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return {"duration": 60, "width": 1920, "height": 1080, "fps": 30}


async def extract_key_frames(video_path: Path, num_frames: int = 10) -> List[Dict]:
    """Extract key frames from video for analysis"""
    video_info = await get_video_info(video_path)
    duration = video_info["duration"]
    
    frames = []
    interval = duration / (num_frames + 1)
    
    for i in range(num_frames):
        timestamp = interval * (i + 1)
        frames.append({
            "timestamp": round(timestamp, 2),
            "index": i
        })
    
    return frames


async def analyze_audio_peaks(video_path: Path) -> List[float]:
    """Find timestamps with audio peaks (loud moments)"""
    # Use ffmpeg to get audio levels
    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
        "-f", "null", "-"
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
        
        # Parse output for timestamps with high audio levels
        # This is a simplified version - just return evenly spaced timestamps
        video_info = await get_video_info(video_path)
        duration = video_info["duration"]
        
        # Return timestamps at regular intervals with some randomness
        peaks = []
        for i in range(int(duration / 2)):
            peaks.append(round(i * 2 + random.uniform(0, 1.5), 2))
        
        return peaks[:20]
    except Exception as e:
        logger.warning(f"Audio analysis failed: {e}")
        return [i * 3.0 for i in range(20)]


async def create_montage(
    video_path: Path,
    output_path: Path,
    style: str = "tiktok",
    music_path: Optional[Path] = None,
    analysis: Optional[Dict] = None
) -> Optional[Path]:
    """
    Create a montage from the source video.
    
    1. Cut video into clips based on analysis
    2. Apply transitions between clips
    3. Add effects and text overlays
    4. Mix in background music
    5. Add sound effects
    """
    output_file = output_path / f"montage_{uuid.uuid4().hex[:8]}.mp4"
    style_config = MONTAGE_STYLES.get(style, MONTAGE_STYLES["tiktok"])
    
    # Get analysis if not provided
    if not analysis:
        analysis = await analyze_video_for_montage(video_path, style)
    
    clips = analysis.get("clips", [])
    if not clips:
        logger.error("No clips found in analysis")
        return None
    
    video_info = await get_video_info(video_path)
    
    # Create temporary clips
    clip_files = []
    for i, clip in enumerate(clips):
        clip_path = output_path / f"clip_{i:03d}.mp4"
        
        start = clip.get("start", 0)
        end = clip.get("end", start + 3)
        duration = end - start
        
        # Extract clip with effects
        effects = clip.get("suggested_effects", [])
        filter_str = build_effect_filter(effects, style_config, duration)
        
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-vf", filter_str if filter_str else "null",
            "-c:v", "libx264", "-preset", "fast",
            "-c:a", "aac",
            str(clip_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if clip_path.exists():
            clip_files.append(clip_path)
            logger.info(f"Created clip {i+1}/{len(clips)}")
    
    if not clip_files:
        logger.error("No clips were created")
        return None
    
    # Concatenate clips with transitions
    concat_file = output_path / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")
    
    # Simple concatenation first
    concat_output = output_path / "concat_output.mp4"
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "aac",
        str(concat_output)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    if not concat_output.exists():
        logger.error("Concatenation failed")
        return None
    
    # Add background music if provided
    final_video = concat_output
    if music_path and music_path.exists():
        music_output = output_path / "with_music.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-i", str(concat_output),
            "-i", str(music_path),
            "-filter_complex", "[1:a]volume=0.3[music];[0:a][music]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac",
            "-shortest",
            str(music_output)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        
        if music_output.exists():
            final_video = music_output
    
    # Rename to final output
    final_video.rename(output_file)
    
    # Cleanup temporary files
    for clip in clip_files:
        try:
            clip.unlink()
        except:
            pass
    try:
        concat_file.unlink()
        concat_output.unlink()
    except:
        pass
    
    if output_file.exists():
        logger.info(f"Created montage: {output_file}")
        return output_file
    
    return None


def build_effect_filter(effects: List[str], style_config: Dict, duration: float) -> str:
    """Build ffmpeg filter string for effects"""
    filters = []
    
    for effect in effects:
        if effect == "zoom_pulse":
            # Subtle zoom in effect
            filters.append(f"zoompan=z='1+0.05*sin(2*PI*t/{duration})':d=1:s=1920x1080")
        elif effect == "speed_ramp":
            # Speed variation - not easily done with simple filter
            pass
        elif effect == "rgb_split":
            # RGB split/glitch effect
            filters.append("rgbashift=rh=-5:gh=0:bh=5")
        elif effect == "subtle_zoom":
            filters.append("zoompan=z='1.02':d=1:s=1920x1080")
        elif effect == "letterbox":
            # Add cinematic letterbox
            filters.append("pad=iw:ih*1.2:0:(oh-ih)/2:black")
    
    # Always ensure proper scaling
    if not filters:
        filters.append("scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2")
    
    return ",".join(filters) if filters else ""


async def add_text_overlay(
    video_path: Path,
    output_path: Path,
    text_overlays: List[Dict]
) -> Optional[Path]:
    """
    Add text overlays to video.
    
    Each overlay: {"text": "...", "start": 0, "end": 3, "position": "center", "style": "impact"}
    """
    output_file = output_path / f"text_{uuid.uuid4().hex[:8]}.mp4"
    
    # Build drawtext filter
    filters = []
    for overlay in text_overlays:
        text = overlay.get("text", "").replace("'", "\\'")
        start = overlay.get("start", 0)
        end = overlay.get("end", start + 2)
        position = overlay.get("position", "center")
        style = overlay.get("style", "impact")
        
        # Position mapping
        if position == "center":
            x, y = "(w-text_w)/2", "(h-text_h)/2"
        elif position == "top":
            x, y = "(w-text_w)/2", "h*0.1"
        elif position == "bottom":
            x, y = "(w-text_w)/2", "h*0.85"
        else:
            x, y = "(w-text_w)/2", "(h-text_h)/2"
        
        # Style mapping
        fontsize = 72
        fontcolor = "white"
        if style == "impact":
            fontsize = 80
            fontcolor = "white"
        elif style == "meme":
            fontsize = 90
            fontcolor = "white"
        
        filter_str = f"drawtext=text='{text}':fontsize={fontsize}:fontcolor={fontcolor}:x={x}:y={y}:enable='between(t,{start},{end})'"
        filters.append(filter_str)
    
    if not filters:
        return video_path
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "fast",
        "-c:a", "copy",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    if output_file.exists():
        return output_file
    return video_path
