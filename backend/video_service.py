"""
Video Assembly Service - Creates real video files using ffmpeg
"""
import os
import subprocess
import asyncio
import logging
import uuid
import httpx
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

# Directory for video processing
WORK_DIR = Path("/app/backend/video_work")
WORK_DIR.mkdir(exist_ok=True)

# Gameplay video URLs (stock footage or generated)
GAMEPLAY_VIDEOS = {
    "minecraft_parkour": "https://www.pexels.com/download/video/6469335/",  # Gaming footage
    "subway_surfers": "https://www.pexels.com/download/video/6469335/",
    "soap_cutting": "https://www.pexels.com/download/video/4057808/",  # Satisfying
    "satisfying": "https://www.pexels.com/download/video/4057808/",
    "slime_asmr": "https://www.pexels.com/download/video/4057808/",
    "cooking": "https://www.pexels.com/download/video/4253165/",  # Cooking
}


async def download_youtube_clip(youtube_url: str, output_path: Path, duration: int = 30) -> Optional[Path]:
    """Download a clip from YouTube video or create a placeholder"""
    video_path = output_path / f"yt_{uuid.uuid4().hex[:8]}.mp4"
    
    # Try to download with yt-dlp first
    try:
        cmd = [
            "yt-dlp",
            "-f", "best[height<=720]",
            "--no-playlist",
            "-o", str(video_path),
            "--external-downloader", "ffmpeg",
            "--external-downloader-args", f"ffmpeg_i:-t {duration}",
            youtube_url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
        
        if video_path.exists() and video_path.stat().st_size > 1000:
            logger.info(f"Downloaded YouTube clip: {video_path}")
            return video_path
    except Exception as e:
        logger.warning(f"yt-dlp failed: {e}")
    
    # Create a colorful placeholder with YouTube branding
    logger.info("Creating YouTube placeholder clip")
    placeholder_path = output_path / f"yt_placeholder_{uuid.uuid4().hex[:8]}.mp4"
    
    # Create red/dark gradient placeholder for YouTube section
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#cc0000:s=720x768:d={duration}",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-t", str(duration),
        str(placeholder_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(process.communicate(), timeout=60)
    
    if placeholder_path.exists() and placeholder_path.stat().st_size > 1000:
        return placeholder_path
    return None


async def download_file(url: str, output_path: Path) -> Optional[Path]:
    """Download a file from URL"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=60) as client:
            response = await client.get(url)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
    except Exception as e:
        logger.error(f"Download error: {e}")
    return None


async def create_gameplay_clip(gameplay_type: str, output_path: Path, duration: int = 30) -> Optional[Path]:
    """Create gameplay clip with colored background"""
    gameplay_path = output_path / f"gameplay_{uuid.uuid4().hex[:8]}.mp4"
    
    # Colors for different gameplay types
    colors = {
        "minecraft_parkour": "#2d5a27",
        "subway_surfers": "#4a90d9", 
        "soap_cutting": "#ffd700",
        "satisfying": "#ff69b4",
        "slime_asmr": "#00ff7f",
        "cooking": "#ff6347",
    }
    color = colors.get(gameplay_type, "#333333")
    
    # Create simple colored video
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s=720x512:d={duration}",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-t", str(duration),
        str(gameplay_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(process.communicate(), timeout=60)
    
    if gameplay_path.exists() and gameplay_path.stat().st_size > 1000:
        return gameplay_path
    return None


async def create_image_video(image_url: str, output_path: Path, duration: float = 4.0, animation: str = "zoom_in") -> Optional[Path]:
    """Create a video from an image with Ken Burns effect"""
    video_path = output_path / f"scene_{uuid.uuid4().hex[:8]}.mp4"
    
    # Download image first
    image_path = output_path / f"img_{uuid.uuid4().hex[:8]}.png"
    downloaded = await download_file(image_url, image_path)
    
    if not downloaded or not image_path.exists():
        # Create a placeholder colored frame
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", f"color=c=0x1a1a2e:s=720x1280:d={duration}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            str(video_path)
        ]
    else:
        # Ken Burns effect based on animation type
        if animation == "zoom_in":
            zoompan = f"zoompan=z='min(zoom+0.001,1.2)':d={int(duration*25)}:s=720x1280:fps=25"
        elif animation == "zoom_out":
            zoompan = f"zoompan=z='if(lte(zoom,1.0),1.2,max(1.001,zoom-0.001))':d={int(duration*25)}:s=720x1280:fps=25"
        elif animation == "pan_left":
            zoompan = f"zoompan=z='1.1':x='iw/2-(iw/zoom/2)+on/({duration}*25)*(iw/zoom/10)':d={int(duration*25)}:s=720x1280:fps=25"
        else:  # pan_right
            zoompan = f"zoompan=z='1.1':x='iw/2-(iw/zoom/2)-on/({duration}*25)*(iw/zoom/10)':d={int(duration*25)}:s=720x1280:fps=25"
        
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-vf", f"scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,{zoompan}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            str(video_path)
        ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=60)
    
    # Cleanup
    if image_path.exists():
        image_path.unlink()
    
    if video_path.exists():
        return video_path
    
    logger.error(f"Failed to create image video: {stderr.decode()}")
    return None


async def add_subtitles_to_video(video_path: Path, subtitles: List[dict], output_path: Path) -> Optional[Path]:
    """Add subtitles overlay to video"""
    output_file = output_path / f"subtitled_{uuid.uuid4().hex[:8]}.mp4"
    
    # Create ASS subtitle file
    ass_path = output_path / f"subs_{uuid.uuid4().hex[:8]}.ass"
    
    ass_content = """[Script Info]
Title: Subtitles
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3,2,2,20,20,120,1
Style: Highlight,Arial,52,&H0000FFFF,&H000000FF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,4,2,2,20,20,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    for sub in subtitles:
        start = sub.get("timestamp_start", 0)
        end = sub.get("timestamp_end", start + 3)
        text = sub.get("text", "").replace("\n", "\\N")
        style = "Highlight" if sub.get("highlight") else "Default"
        
        start_str = f"{int(start//3600)}:{int((start%3600)//60):02d}:{start%60:05.2f}"
        end_str = f"{int(end//3600)}:{int((end%3600)//60):02d}:{end%60:05.2f}"
        
        ass_content += f"Dialogue: 0,{start_str},{end_str},{style},,0,0,0,,{text}\n"
    
    with open(ass_path, "w", encoding="utf-8") as f:
        f.write(ass_content)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vf", f"ass={ass_path}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "copy",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(process.communicate(), timeout=120)
    
    # Cleanup
    ass_path.unlink(missing_ok=True)
    
    if output_file.exists():
        return output_file
    return None


async def create_split_screen_video(
    top_video: Path,
    bottom_video: Path,
    output_path: Path,
    subtitles: List[dict] = None
) -> Optional[Path]:
    """Create a split-screen video (60% top, 40% bottom)"""
    output_file = output_path / f"split_{uuid.uuid4().hex[:8]}.mp4"
    
    # Create split screen: 60% top (YouTube), 40% bottom (gameplay)
    filter_complex = "[0:v]scale=720:768,setsar=1[top];[1:v]scale=720:512,setsar=1[bottom];[top][bottom]vstack=inputs=2[v]"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(top_video),
        "-i", str(bottom_video),
        "-filter_complex", filter_complex,
        "-map", "[v]",
        "-map", "0:a?",
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-shortest",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
    
    if output_file.exists():
        # Add subtitles if provided
        if subtitles:
            subtitled = await add_subtitles_to_video(output_file, subtitles, output_path)
            if subtitled:
                output_file.unlink()
                return subtitled
        return output_file
    
    logger.error(f"Split screen creation failed: {stderr.decode()}")
    return None


async def concatenate_videos(video_paths: List[Path], output_path: Path) -> Optional[Path]:
    """Concatenate multiple videos into one"""
    if not video_paths:
        return None
    
    output_file = output_path / f"final_{uuid.uuid4().hex[:8]}.mp4"
    concat_file = output_path / f"concat_{uuid.uuid4().hex[:8]}.txt"
    
    # Create concat file
    with open(concat_file, "w") as f:
        for vp in video_paths:
            f.write(f"file '{vp}'\n")
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(process.communicate(), timeout=180)
    
    # Cleanup
    concat_file.unlink(missing_ok=True)
    
    if output_file.exists():
        return output_file
    return None


async def add_audio_to_video(video_path: Path, audio_path: Path, output_path: Path) -> Optional[Path]:
    """Add audio track to video"""
    output_file = output_path / f"with_audio_{uuid.uuid4().hex[:8]}.mp4"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(process.communicate(), timeout=120)
    
    if output_file.exists():
        return output_file
    return None


def cleanup_work_dir(work_dir: Path, keep_final: Path = None):
    """Clean up temporary files"""
    for f in work_dir.glob("*"):
        if f != keep_final and f.is_file():
            try:
                f.unlink()
            except:
                pass


async def create_chat_animation_video(script_data: dict, output_path: Path) -> Optional[Path]:
    """Create animated chat/message conversation video"""
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    
    participants = script_data.get("participants", [
        {"name": "User 1", "side": "left", "avatar_color": "#4a90d9"},
        {"name": "User 2", "side": "right", "avatar_color": "#27ae60"}
    ])
    messages = script_data.get("messages", [])
    bg_colors = script_data.get("background_colors", ["#1a1a2e", "#16213e"])
    
    # Calculate total duration based on messages
    total_duration = 2.0  # Start delay
    for msg in messages:
        total_duration += msg.get("delay", 1.0) + msg.get("typing_duration", 0.5) + 1.0
    total_duration = max(total_duration, 10.0)  # Minimum 10 seconds
    
    # Create complex filter for animated chat
    # Generate drawtext filters for each message with appearance timing
    
    drawtext_filters = []
    current_time = 1.0
    y_position = 300  # Starting Y position
    
    for i, msg in enumerate(messages):
        sender_idx = msg.get("sender", 0)
        text = msg.get("text", "").replace("'", "'\\''").replace(":", r"\:")
        delay = msg.get("delay", 1.0)
        
        current_time += delay
        
        # Determine position (left or right)
        participant = participants[sender_idx] if sender_idx < len(participants) else participants[0]
        is_left = participant.get("side", "left") == "left"
        
        # Message bubble colors
        if is_left:
            box_color = "#e5e5ea"  # Light gray for left (received)
            text_color = "#000000"
            x_pos = "50"
        else:
            box_color = "#0b93f6"  # Blue for right (sent)  
            text_color = "#ffffff"
            x_pos = "w-tw-70"
        
        # Add message with fade-in effect
        appear_time = current_time
        filter_str = f"drawtext=text='{text}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontsize=28:fontcolor={text_color}:x={x_pos}:y={y_position}:enable='gte(t,{appear_time})':box=1:boxcolor={box_color}@0.9:boxborderw=15"
        drawtext_filters.append(filter_str)
        
        # Move to next line
        y_position += 70
        current_time += msg.get("typing_duration", 0.5) + 0.5
        
        # Reset position if too low
        if y_position > 1100:
            y_position = 300
    
    # Build filter complex
    bg_color = bg_colors[0] if bg_colors else "#1a1a2e"
    
    # Create base video with gradient background
    base_filter = f"color=c={bg_color}:s=720x1280:d={total_duration}"
    
    # Add header (phone top bar simulation)
    header_filter = f"drawbox=x=0:y=0:w=720:h=100:color=#000000@0.3:t=fill,drawtext=text='{participants[0].get('name', 'Chat')}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=36:fontcolor=#ffffff:x=(w-tw)/2:y=40"
    
    # Combine all filters
    all_filters = ",".join([header_filter] + drawtext_filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", base_filter,
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", all_filters,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-t", str(total_duration),
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=120)
    
    if output_file.exists() and output_file.stat().st_size > 1000:
        logger.info(f"Created chat animation video: {output_file}")
        return output_file
    
    logger.error(f"Chat animation creation failed: {stderr.decode()}")
    return None
