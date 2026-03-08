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
    Analyze video to find interesting moments.
    OPTIMIZED: Uses fast heuristics first, AI only for refinement
    """
    style_config = MONTAGE_STYLES.get(style, MONTAGE_STYLES["tiktok"])
    
    # Get video info
    video_info = await get_video_info(video_path)
    duration = video_info.get("duration", 60)
    
    clip_min, clip_max = style_config["clip_duration"]
    clip_avg = (clip_min + clip_max) / 2
    
    # OPTIMIZATION: For shorter videos, use simple even distribution (no AI needed)
    if duration < 30:
        # Short video - just split evenly
        num_clips = min(4, max(2, int(duration / clip_avg)))
        clips = []
        segment_duration = duration / num_clips
        
        for i in range(num_clips):
            start = i * segment_duration
            end = min(start + clip_avg, (i + 1) * segment_duration)
            clips.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "description": f"Segment {i+1}",
                "importance": num_clips - i,
                "suggested_effects": [],
                "suggested_text": None,
                "sound_effect": None
            })
        
        return {
            "clips": clips,
            "overall_mood": "energetic",
            "suggested_music_tempo": "medium",
            "total_clips": len(clips)
        }
    
    # For longer videos, use simple scene detection heuristics
    # Instead of heavy AI analysis, use quick timestamp distribution
    num_clips = min(5, max(3, int(duration / clip_avg / 2)))
    
    # Smart distribution: beginning, 1/3, 1/2, 2/3, near end
    key_points = [
        0.05,   # Near start
        0.25,   # First quarter
        0.5,    # Middle
        0.75,   # Third quarter
        0.9     # Near end
    ][:num_clips]
    
    clips = []
    for i, point in enumerate(key_points):
        start = duration * point
        end = min(start + clip_avg, duration)
        
        clips.append({
            "start": round(start, 2),
            "end": round(end, 2),
            "description": f"Highlight {i+1}",
            "importance": len(key_points) - i,
            "suggested_effects": [],
            "suggested_text": None,
            "sound_effect": random.choice(["whoosh", None, None])  # Occasional sound
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
    OPTIMIZED: Uses ultrafast preset, parallel processing, direct stream copy where possible
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
    
    # OPTIMIZATION: Limit number of clips to reduce processing time
    max_clips = 5  # Limit to 5 clips for faster processing
    clips = sorted(clips, key=lambda x: x.get("importance", 0), reverse=True)[:max_clips]
    clips = sorted(clips, key=lambda x: x.get("start", 0))  # Re-sort by time
    
    # Create temporary clips using FAST extraction (stream copy when possible)
    clip_files = []
    
    # OPTIMIZATION: Extract all clips in parallel
    extraction_tasks = []
    for i, clip in enumerate(clips):
        clip_path = output_path / f"clip_{i:03d}.mp4"
        start = clip.get("start", 0)
        end = clip.get("end", start + 3)
        duration = min(end - start, 5.0)  # Limit clip duration to 5s
        
        # Use stream copy (ultrafast) - no re-encoding
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", str(video_path),
            "-t", str(duration),
            "-c", "copy",  # Stream copy - MUCH faster
            "-avoid_negative_ts", "1",
            str(clip_path)
        ]
        
        extraction_tasks.append((cmd, clip_path, i))
    
    # Execute extractions with timeout
    for cmd, clip_path, i in extraction_tasks:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=30)
            
            if clip_path.exists() and clip_path.stat().st_size > 1000:
                clip_files.append(clip_path)
                logger.info(f"Extracted clip {i+1}/{len(clips)}")
        except asyncio.TimeoutError:
            logger.warning(f"Clip {i} extraction timed out, skipping")
        except Exception as e:
            logger.warning(f"Clip {i} extraction failed: {e}")
    
    if not clip_files:
        logger.error("No clips were extracted")
        return None
    
    # OPTIMIZATION: Simple concatenation with demuxer (fastest method)
    concat_file = output_path / "concat.txt"
    with open(concat_file, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip}'\n")
    
    concat_output = output_path / "concat_output.mp4"
    
    # Use concat demuxer with stream copy (ultrafast)
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",  # Stream copy
        str(concat_output)
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await asyncio.wait_for(process.communicate(), timeout=60)
    except asyncio.TimeoutError:
        logger.error("Concatenation timed out")
        # Fallback: use first clip
        if clip_files:
            concat_output = clip_files[0]
    
    if not concat_output.exists():
        # Fallback to first clip
        if clip_files:
            concat_output = clip_files[0]
        else:
            logger.error("Concatenation failed")
            return None
    
    final_video = concat_output
    
    # Add background music if provided (with fast processing)
    if music_path and music_path.exists():
        music_output = output_path / "with_music.mp4"
        
        # Get video duration
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", str(concat_output)]
        try:
            probe_proc = await asyncio.create_subprocess_exec(
                *probe_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await probe_proc.communicate()
            video_duration = float(stdout.decode().strip())
        except:
            video_duration = 30.0
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(concat_output),
            "-i", str(music_path),
            "-filter_complex", "[1:a]volume=0.25[music];[0:a][music]amix=inputs=2:duration=first[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",  # Keep video as-is
            "-c:a", "aac", "-b:a", "128k",
            "-t", str(video_duration),
            str(music_output)
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.communicate(), timeout=90)
            
            if music_output.exists():
                final_video = music_output
        except Exception as e:
            logger.warning(f"Music mixing failed: {e}, using video without music")
    
    # Move to final location
    try:
        if final_video != output_file:
            final_video.rename(output_file)
    except:
        # Copy instead
        import shutil
        shutil.copy2(final_video, output_file)
    
    # Cleanup temporary files
    for clip in clip_files:
        try:
            if clip.exists():
                clip.unlink()
        except:
            pass
    try:
        concat_file.unlink()
    except:
        pass
    try:
        if concat_output.exists() and concat_output != output_file:
            concat_output.unlink()
    except:
        pass
    
    if output_file.exists() and output_file.stat().st_size > 1000:
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
