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
    """Add audio track to video - video length is preserved, audio loops if needed"""
    output_file = output_path / f"with_audio_{uuid.uuid4().hex[:8]}.mp4"
    
    # Get video duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)
    ]
    
    video_duration = 5.0  # Default
    try:
        probe_process = await asyncio.create_subprocess_exec(
            *probe_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await probe_process.communicate()
        video_duration = float(stdout.decode().strip())
    except:
        pass
    
    # Add audio to video - keep video duration, don't cut
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-t", str(video_duration),  # Keep video duration
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
    """
    Create animated chat/message conversation video in iMessage style.
    
    Style based on analysis:
    - Background: Black (#000000)
    - Sent messages: Dark gray (#292929) - right side
    - Received messages: Blue (#007AFF) - left side  
    - Text: White, ~18px sans-serif
    - Bubbles: Rounded corners ~18px, padding 15px
    - Animation: Slide-in from side + fade, ~300ms
    - Typing indicator: 3 dots
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    
    participants = script_data.get("participants", [
        {"name": "Собеседник", "side": "left", "avatar_color": "#007AFF"},
        {"name": "Я", "side": "right", "avatar_color": "#292929"}
    ])
    messages = script_data.get("messages", [])
    title = script_data.get("title", "Чат")
    
    # iMessage color scheme
    BG_COLOR = "#000000"
    SENT_BUBBLE = "#292929"      # Dark gray for sent (right)
    RECEIVED_BUBBLE = "#007AFF"  # Blue for received (left)
    TEXT_COLOR = "#FFFFFF"
    HEADER_BG = "#1c1c1e"
    
    # Calculate timing
    current_time = 1.5  # Initial delay
    message_timings = []
    
    for msg in messages:
        delay = msg.get("delay", 1.2)
        typing_dur = msg.get("typing_duration", 0.6)
        
        # Typing indicator appears
        typing_start = current_time
        typing_end = typing_start + typing_dur
        
        # Message appears after typing
        msg_appear = typing_end + 0.1
        
        message_timings.append({
            "typing_start": typing_start,
            "typing_end": typing_end,
            "msg_appear": msg_appear,
            "text": msg.get("text", ""),
            "sender": msg.get("sender", 0)
        })
        
        current_time = msg_appear + delay
    
    total_duration = max(current_time + 2.0, 12.0)  # Minimum 12 seconds
    
    # Build filter chain
    filters = []
    
    # Screen dimensions
    W, H = 720, 1280
    MARGIN = 20
    BUBBLE_PADDING = 18
    FONT_SIZE = 32
    LINE_HEIGHT = 50
    BUBBLE_RADIUS = 18
    
    # Header bar
    header_height = 90
    filters.append(f"drawbox=x=0:y=0:w={W}:h={header_height}:color={HEADER_BG}:t=fill")
    
    # Time display (fake)
    filters.append(f"drawtext=text='Сейчас':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:fontsize=14:fontcolor=#8e8e93:x=(w-tw)/2:y=15")
    
    # Contact name in header
    contact_name = participants[0].get("name", "Чат") if participants else "Чат"
    filters.append(f"drawtext=text='{contact_name}':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:fontsize=20:fontcolor=#ffffff:x=(w-tw)/2:y=50")
    
    # Calculate message positions
    y_pos = header_height + 30
    
    for i, timing in enumerate(message_timings):
        text = timing["text"].replace("'", "'\\''").replace(":", "\\:")
        sender_idx = timing["sender"]
        participant = participants[sender_idx] if sender_idx < len(participants) else participants[0]
        is_received = participant.get("side", "left") == "left"
        
        msg_appear = timing["msg_appear"]
        typing_start = timing["typing_start"]
        typing_end = timing["typing_end"]
        
        # Bubble color based on sender
        bubble_color = RECEIVED_BUBBLE if is_received else SENT_BUBBLE
        
        # Text width estimation (rough)
        text_len = len(text)
        est_width = min(text_len * 18 + BUBBLE_PADDING * 2, W - MARGIN * 4)
        bubble_height = LINE_HEIGHT + BUBBLE_PADDING
        
        # Position: left for received, right for sent
        if is_received:
            bubble_x = MARGIN
        else:
            bubble_x = W - est_width - MARGIN
        
        # Typing indicator (3 dots) - only for received messages
        if is_received:
            typing_x = MARGIN + 20
            typing_y = y_pos + 15
            
            # Draw typing bubble
            filters.append(
                f"drawbox=x={MARGIN}:y={y_pos}:w=80:h=45:color={bubble_color}@0.9:t=fill:"
                f"enable='between(t,{typing_start},{typing_end})'"
            )
            
            # Animated dots (simple version - 3 static dots that appear)
            for dot_idx in range(3):
                dot_x = typing_x + dot_idx * 18
                dot_delay = typing_start + dot_idx * 0.15
                filters.append(
                    f"drawtext=text='.':fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                    f"fontsize=30:fontcolor=#ffffff:x={dot_x}:y={typing_y}:"
                    f"enable='between(t,{dot_delay},{typing_end})'"
                )
        
        # Message bubble background
        # Use drawbox for bubble (ffmpeg doesn't support rounded corners easily)
        filters.append(
            f"drawbox=x={bubble_x}:y={y_pos}:w={est_width}:h={bubble_height}:"
            f"color={bubble_color}@0.95:t=fill:enable='gte(t,{msg_appear})'"
        )
        
        # Message text
        text_x = bubble_x + BUBBLE_PADDING
        text_y = y_pos + BUBBLE_PADDING
        
        filters.append(
            f"drawtext=text='{text}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"fontsize={FONT_SIZE}:fontcolor={TEXT_COLOR}:"
            f"x={text_x}:y={text_y}:"
            f"enable='gte(t,{msg_appear})'"
        )
        
        # Move to next row
        y_pos += bubble_height + 15
        
        # Reset if too low
        if y_pos > H - 200:
            y_pos = header_height + 30
    
    # Combine all filters
    filter_str = ",".join(filters)
    
    # Base video command
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={BG_COLOR}:s={W}x{H}:d={total_duration}",
        "-f", "lavfi", 
        "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "fast",
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
    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=180)
    
    if output_file.exists() and output_file.stat().st_size > 1000:
        logger.info(f"Created chat animation video: {output_file}")
        return output_file
    
    logger.error(f"Chat animation creation failed: {stderr.decode()}")
    return None



async def create_apple_text_animation(script_data: dict, output_path: Path) -> Optional[Path]:
    """
    Create Apple-style minimalist text animation.
    
    Style based on analysis:
    - Background: Alternating white (#FFFFFF) ↔ black (#000000)
    - Text: Bold sans-serif, large, centered
    - Animation: Word-by-word, almost instant appearance
    - Underline for emphasis on key words
    """
    output_file = output_path / f"apple_text_{uuid.uuid4().hex[:8]}.mp4"
    
    phrases = script_data.get("phrases", [
        {"text": "Let's create", "bg": "white"},
        {"text": "Some amazing content", "bg": "white"},
        {"text": "Just like Apple.", "bg": "black"},
        {"text": "Simple. Clean. Bold.", "bg": "black", "underline": "Bold"},
    ])
    
    W, H = 720, 1280
    FONT_SIZE = 56
    PHRASE_DURATION = 1.8
    
    total_duration = len(phrases) * PHRASE_DURATION + 2.0
    
    # Build complex filter with background switching
    filter_parts = []
    
    for i, phrase in enumerate(phrases):
        text = phrase.get("text", "").replace("'", "'\\''").replace(":", "\\:")
        bg = phrase.get("bg", "white")
        underline_word = phrase.get("underline", None)
        
        start_time = i * PHRASE_DURATION + 1.0
        end_time = start_time + PHRASE_DURATION
        
        bg_color = "#ffffff" if bg == "white" else "#000000"
        text_color = "#000000" if bg == "white" else "#ffffff"
        
        # Background for this phrase
        filter_parts.append(
            f"drawbox=x=0:y=0:w={W}:h={H}:color={bg_color}:t=fill:"
            f"enable='between(t,{start_time},{end_time})'"
        )
        
        # Main text - centered
        filter_parts.append(
            f"drawtext=text='{text}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={FONT_SIZE}:fontcolor={text_color}:"
            f"x=(w-tw)/2:y=(h-th)/2:"
            f"enable='between(t,{start_time},{end_time})'"
        )
        
        # Add underline if specified
        if underline_word:
            # Simple underline under center of text
            filter_parts.append(
                f"drawbox=x=(w/2-100):y=(h/2+40):w=200:h=4:color={text_color}:t=fill:"
                f"enable='between(t,{start_time},{end_time})'"
            )
    
    # Initial white background
    filter_parts.insert(0, f"drawbox=x=0:y=0:w={W}:h={H}:color=#ffffff:t=fill:enable='lt(t,1)'")
    
    filter_str = ",".join(filter_parts)
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#ffffff:s={W}x{H}:d={total_duration}",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "fast",
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
        logger.info(f"Created Apple text animation: {output_file}")
        return output_file
    
    logger.error(f"Apple text animation failed: {stderr.decode()}")
    return None


async def create_kinetic_typography(script_data: dict, output_path: Path) -> Optional[Path]:
    """
    Create kinetic typography animation - word by word reveal.
    
    Style:
    - Words appear sequentially with slight delay
    - Clean sans-serif font
    - Centered layout
    - Smooth appearance
    """
    output_file = output_path / f"kinetic_{uuid.uuid4().hex[:8]}.mp4"
    
    # Parse script into words
    full_text = script_data.get("full_script", "This is an amazing kinetic typography animation")
    words = full_text.split()
    
    bg_color = script_data.get("bg_color", "#000000")
    text_color = script_data.get("text_color", "#ffffff") 
    
    W, H = 720, 1280
    FONT_SIZE = 48
    WORD_DELAY = 0.25  # Delay between words
    WORD_DURATION = 0.15  # How long word takes to appear
    
    total_duration = len(words) * WORD_DELAY + 5.0
    
    filter_parts = []
    
    # Calculate word positions for multi-line layout
    words_per_line = 4
    line_height = 70
    start_y = H // 2 - (len(words) // words_per_line) * line_height // 2
    
    current_time = 1.0
    
    for i, word in enumerate(words):
        word_clean = word.replace("'", "'\\''").replace(":", "\\:")
        
        line_num = i // words_per_line
        word_in_line = i % words_per_line
        
        # Calculate position
        y_pos = start_y + line_num * line_height
        
        # Center words in line
        x_expr = f"(w-tw)/2+{(word_in_line - words_per_line/2) * 100}"
        
        appear_time = current_time + i * WORD_DELAY
        
        # Word appears and stays
        filter_parts.append(
            f"drawtext=text='{word_clean}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"fontsize={FONT_SIZE}:fontcolor={text_color}:"
            f"x={x_expr}:y={y_pos}:"
            f"enable='gte(t,{appear_time})'"
        )
    
    filter_str = ",".join(filter_parts) if filter_parts else "null"
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={W}x{H}:d={total_duration}",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "fast",
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
        logger.info(f"Created kinetic typography: {output_file}")
        return output_file
    
    logger.error(f"Kinetic typography failed: {stderr.decode()}")
    return None


async def create_logo_animation(script_data: dict, output_path: Path) -> Optional[Path]:
    """
    Create simple logo animation with text reveal.
    
    Style based on Discord analysis:
    - Solid background color
    - Icon/shape appears with subtle animation
    - Text slides in and rotates into place
    """
    output_file = output_path / f"logo_{uuid.uuid4().hex[:8]}.mp4"
    
    brand_name = script_data.get("brand_name", "Brand")
    tagline = script_data.get("tagline", "")
    bg_color = script_data.get("bg_color", "#7289da")  # Discord purple as default
    text_color = script_data.get("text_color", "#ffffff")
    
    W, H = 720, 1280
    total_duration = 5.0
    
    filter_parts = []
    
    # Phase 1: Icon/shape appears (using a simple circle as placeholder)
    # Simulated with growing circle
    filter_parts.append(
        f"drawbox=x={(W-100)//2}:y={(H-100)//2}:w=100:h=100:color={text_color}@0.9:t=fill:"
        f"enable='gte(t,0.5)'"
    )
    
    # Phase 2: Brand name appears
    filter_parts.append(
        f"drawtext=text='{brand_name}':"
        f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
        f"fontsize=64:fontcolor={text_color}:"
        f"x=(w-tw)/2:y=(h/2+80):"
        f"enable='gte(t,1.5)'"
    )
    
    # Phase 3: Tagline appears (if provided)
    if tagline:
        tagline_clean = tagline.replace("'", "'\\''").replace(":", "\\:")
        filter_parts.append(
            f"drawtext=text='{tagline_clean}':"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            f"fontsize=28:fontcolor={text_color}@0.8:"
            f"x=(w-tw)/2:y=(h/2+160):"
            f"enable='gte(t,2.5)'"
        )
    
    filter_str = ",".join(filter_parts)
    
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={bg_color}:s={W}x{H}:d={total_duration}",
        "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", filter_str,
        "-c:v", "libx264",
        "-preset", "fast",
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
        logger.info(f"Created logo animation: {output_file}")
        return output_file
    
    logger.error(f"Logo animation failed: {stderr.decode()}")
    return None
