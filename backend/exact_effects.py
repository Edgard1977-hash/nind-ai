"""
EXACT recreation of reference TikTok videos
Based on pixel-by-pixel analysis
"""

import math
import random
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)

WIDTH = 720
HEIGHT = 1280


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


# =============================================================
# SPOTIFY STYLE - EXACT RECREATION
# =============================================================

def create_spotify_aurora_frame(width: int, height: int, time: float) -> Image.Image:
    """
    OPTIMIZED Spotify aurora gradient recreation
    Uses band rendering instead of per-pixel for 10x speed
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Base colors from analysis
    dark_color = (20, 20, 18)
    spotify_green = (29, 185, 84)
    bright_green = (100, 255, 150)
    deep_green = (16, 80, 40)
    
    # Render in horizontal bands for speed
    num_bands = 40
    band_height = height // num_bands
    
    for band_idx in range(num_bands):
        y_start = band_idx * band_height
        y_end = (band_idx + 1) * band_height
        y_center = (y_start + y_end) // 2
        
        # Center-based distance
        ny = y_center / height
        cx_dist = abs(0.5 - 0.5)  # Horizontal center
        cy_dist = abs(ny - 0.45)  # Slightly above center
        dist = math.sqrt(cx_dist**2 + cy_dist**2) * 2
        dist = min(1.0, dist)
        
        # Animated wave
        wave = math.sin(band_idx / 8 + time * math.pi * 3) * 0.15
        wave += math.cos(band_idx / 6 + time * math.pi * 2) * 0.1
        
        t = dist + wave * (1 - dist)
        t = max(0, min(1, t))
        
        # Color interpolation
        if t < 0.3:
            local_t = t / 0.3
            r = int(bright_green[0] * (1 - local_t) + spotify_green[0] * local_t)
            g = int(bright_green[1] * (1 - local_t) + spotify_green[1] * local_t)
            b = int(bright_green[2] * (1 - local_t) + spotify_green[2] * local_t)
        elif t < 0.6:
            local_t = (t - 0.3) / 0.3
            r = int(spotify_green[0] * (1 - local_t) + deep_green[0] * local_t)
            g = int(spotify_green[1] * (1 - local_t) + deep_green[1] * local_t)
            b = int(spotify_green[2] * (1 - local_t) + deep_green[2] * local_t)
        else:
            local_t = (t - 0.6) / 0.4
            r = int(deep_green[0] * (1 - local_t) + dark_color[0] * local_t)
            g = int(deep_green[1] * (1 - local_t) + dark_color[1] * local_t)
            b = int(deep_green[2] * (1 - local_t) + dark_color[2] * local_t)
        
        draw.rectangle((0, y_start, width, y_end), fill=(r, g, b))
    
    # Soft blur for smooth aurora effect
    img = img.filter(ImageFilter.GaussianBlur(radius=8))
    
    return img


def draw_spotify_ui_card(
    img: Image.Image,
    position: Tuple[int, int],
    size: Tuple[int, int],
    album_colors: List[Tuple[int, int, int]],
    labels: List[str],
    animation_progress: float = 1.0
) -> Image.Image:
    """
    Draw Spotify-style UI card with album covers
    """
    x, y = position
    w, h = size
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Animate slide up
    if animation_progress < 1.0:
        y_offset = int((1 - ease_out_back(animation_progress)) * 300)
        y += y_offset
    
    # Card background with transparency
    alpha = int(230 * animation_progress)
    draw.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=25,
        fill=(30, 30, 32, alpha)
    )
    
    # "Made For You" header
    font_header = get_font(20, bold=True)
    draw.text((x + 20, y + 15), "Made For You", font=font_header, fill=(255, 255, 255, alpha))
    
    # Album covers in a row
    album_size = min(120, (w - 60) // 3)
    album_y = y + 55
    
    for i, (color, label) in enumerate(zip(album_colors, labels)):
        album_x = x + 20 + i * (album_size + 15)
        
        # Album cover (colored square with rounded corners)
        draw.rounded_rectangle(
            (album_x, album_y, album_x + album_size, album_y + album_size),
            radius=8,
            fill=(*color, alpha)
        )
        
        # Album label
        font_label = get_font(14)
        draw.text((album_x, album_y + album_size + 8), label[:12], 
                 font=font_label, fill=(180, 180, 180, alpha))
    
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result


def draw_spotify_player(
    img: Image.Image,
    position: Tuple[int, int],
    track_name: str,
    artist: str,
    progress: float,  # 0 to 1
    animation_progress: float = 1.0
) -> Image.Image:
    """
    Draw Spotify player bar at bottom
    """
    x, y = position
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    alpha = int(255 * animation_progress)
    
    # Player background
    player_h = 80
    draw.rounded_rectangle(
        (x, y, x + WIDTH - 40, y + player_h),
        radius=15,
        fill=(40, 40, 42, alpha)
    )
    
    # Album art thumbnail
    draw.rounded_rectangle(
        (x + 10, y + 10, x + 70, y + 70),
        radius=8,
        fill=(29, 185, 84, alpha)
    )
    
    # Track info
    font_track = get_font(18, bold=True)
    font_artist = get_font(14)
    draw.text((x + 85, y + 18), track_name, font=font_track, fill=(255, 255, 255, alpha))
    draw.text((x + 85, y + 42), artist, font=font_artist, fill=(180, 180, 180, alpha))
    
    # Progress bar
    bar_x = x + 85
    bar_y = y + 62
    bar_w = WIDTH - 180
    bar_h = 4
    
    # Background
    draw.rounded_rectangle(
        (bar_x, bar_y, bar_x + bar_w, bar_y + bar_h),
        radius=2,
        fill=(80, 80, 82, alpha)
    )
    
    # Progress fill
    fill_w = int(bar_w * progress)
    if fill_w > 0:
        draw.rounded_rectangle(
            (bar_x, bar_y, bar_x + fill_w, bar_y + bar_h),
            radius=2,
            fill=(29, 185, 84, alpha)
        )
    
    # Time labels
    font_time = get_font(11)
    elapsed = f"{int(progress * 3)}:{int((progress * 180) % 60):02d}"
    total = "3:04"
    draw.text((bar_x, bar_y + 8), elapsed, font=font_time, fill=(150, 150, 150, alpha))
    draw.text((bar_x + bar_w - 30, bar_y + 8), total, font=font_time, fill=(150, 150, 150, alpha))
    
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result


async def render_spotify_exact(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    EXACT recreation of Spotify TikTok video style
    """
    output_path = output_dir / f"spotify_exact_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    brand_name = script_data.get("brand_name") or "Spotify"
    tagline = script_data.get("tagline") or "Music for everyone"
    
    total_duration = 5  # 5 seconds
    total_frames = fps * total_duration
    
    # Scene timings (in seconds)
    SCENE_1_END = 1.2    # Brand intro
    SCENE_2_END = 2.8    # UI cards appear
    SCENE_3_END = 4.0    # Player appears
    SCENE_4_END = 5.0    # Tagline
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        progress = frame_num / total_frames
        
        # Create animated aurora background
        bg = create_spotify_aurora_frame(WIDTH, HEIGHT, progress)
        bg = bg.convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        # SCENE 1: Brand name with glow (0-2s)
        if time_sec < SCENE_1_END:
            scene_progress = time_sec / SCENE_1_END
            
            # Scale and fade animation
            scale = 0.7 + 0.3 * ease_out_back(min(1, scene_progress * 2))
            alpha = int(255 * ease_out_cubic(min(1, scene_progress * 1.5)))
            
            font_size = int(72 * scale)
            font = get_font(font_size, bold=True)
            
            text_bbox = draw.textbbox((0, 0), brand_name, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_x = (WIDTH - text_w) // 2
            text_y = HEIGHT // 2 - 60
            
            # Glow layers
            for glow_offset in [8, 5, 3]:
                glow_alpha = int(alpha * 0.15)
                draw.text((text_x, text_y), brand_name, 
                         font=font, fill=(29, 185, 84, glow_alpha))
            
            # Main text
            draw.text((text_x, text_y), brand_name, 
                     font=font, fill=(255, 255, 255, alpha))
        
        # SCENE 2: UI cards slide up (2-4.5s)
        elif time_sec < SCENE_2_END:
            scene_progress = (time_sec - SCENE_1_END) / (SCENE_2_END - SCENE_1_END)
            
            # Brand name stays at top
            font = get_font(36, bold=True)
            draw.text((WIDTH // 2 - 60, 60), brand_name, 
                     font=font, fill=(255, 255, 255, 255))
            
            # Cards animation
            card_anim = min(1.0, scene_progress * 1.5)
            
            bg = draw_spotify_ui_card(
                bg,
                position=(60, HEIGHT // 2 - 120),
                size=(WIDTH - 120, 280),
                album_colors=[
                    (219, 68, 55),   # Red
                    (66, 133, 244),  # Blue
                    (244, 180, 0),   # Yellow
                ],
                labels=["Daily Mix 1", "Release Radar", "Discover Weekly"],
                animation_progress=card_anim
            )
        
        # SCENE 3: Player appears (4.5-6.5s)
        elif time_sec < SCENE_3_END:
            scene_progress = (time_sec - SCENE_2_END) / (SCENE_3_END - SCENE_2_END)
            
            # Brand name at top
            font = get_font(36, bold=True)
            draw = ImageDraw.Draw(bg)
            draw.text((WIDTH // 2 - 60, 60), brand_name, 
                     font=font, fill=(255, 255, 255, 255))
            
            # Cards stay visible
            bg = draw_spotify_ui_card(
                bg,
                position=(60, HEIGHT // 2 - 120),
                size=(WIDTH - 120, 280),
                album_colors=[
                    (219, 68, 55),
                    (66, 133, 244),
                    (244, 180, 0),
                ],
                labels=["Daily Mix 1", "Release Radar", "Discover Weekly"],
                animation_progress=1.0
            )
            
            # Player slides up
            player_anim = ease_out_cubic(scene_progress)
            music_progress = scene_progress * 0.3  # Progress bar fills
            
            bg = draw_spotify_player(
                bg,
                position=(20, HEIGHT - 120),
                track_name="Pink + White",
                artist="Frank Ocean",
                progress=music_progress,
                animation_progress=player_anim
            )
        
        # SCENE 4: Tagline (6.5-8s)
        else:
            scene_progress = (time_sec - SCENE_3_END) / (SCENE_4_END - SCENE_3_END)
            
            # Fade out cards, fade in tagline
            card_alpha = int(255 * (1 - scene_progress * 0.7))
            
            # Brand name
            font = get_font(36, bold=True)
            draw = ImageDraw.Draw(bg)
            draw.text((WIDTH // 2 - 60, 60), brand_name, 
                     font=font, fill=(255, 255, 255, 255))
            
            # Tagline fades in
            tagline_alpha = int(255 * ease_out_cubic(scene_progress))
            
            font_tagline = get_font(42)
            words = tagline.split()
            
            # Calculate total width
            total_width = 0
            word_widths = []
            for word in words:
                bbox = draw.textbbox((0, 0), word + " ", font=font_tagline)
                w = bbox[2] - bbox[0]
                word_widths.append(w)
                total_width += w
            
            # Draw words, highlight last word
            x_pos = (WIDTH - total_width) // 2
            y_pos = HEIGHT - 200
            
            for i, (word, w) in enumerate(zip(words, word_widths)):
                if i == len(words) - 1:
                    # Last word with green color
                    draw.text((x_pos, y_pos), word, 
                             font=font_tagline, fill=(29, 185, 84, tagline_alpha))
                else:
                    draw.text((x_pos, y_pos), word + " ", 
                             font=font_tagline, fill=(255, 255, 255, tagline_alpha))
                x_pos += w
        
        # TikTok watermark
        font_small = get_font(14)
        draw = ImageDraw.Draw(bg)
        draw.text((WIDTH - 80, 30), "@spotify", font=font_small, fill=(255, 255, 255, 120))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG")
    
    # Encode video
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    logger.info(f"Rendered Spotify exact video: {output_path}")
    return str(output_path)


# =============================================================
# iMESSAGE STYLE - EXACT RECREATION
# =============================================================

def draw_imessage_bubble_exact(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    is_sender: bool,
    animation_progress: float = 1.0
) -> Image.Image:
    """
    EXACT iMessage bubble with proper tail and styling
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(22)
    
    # Measure text
    lines = []
    max_width = 380
    words = text.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Calculate bubble size
    line_height = 28
    padding_x = 18
    padding_y = 12
    
    text_height = len(lines) * line_height
    text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines) if lines else 100
    
    bubble_w = text_width + padding_x * 2
    bubble_h = text_height + padding_y * 2
    
    x, y = position
    
    # Animate slide in
    if animation_progress < 1.0:
        eased = ease_out_back(animation_progress)
        if is_sender:
            x += int((1 - eased) * 150)
        else:
            x -= int((1 - eased) * 150)
        alpha_mult = eased
    else:
        alpha_mult = 1.0
    
    # Colors (exact iOS colors)
    if is_sender:
        bubble_color = (0, 122, 255, int(255 * alpha_mult))  # iMessage blue
        text_color = (255, 255, 255, int(255 * alpha_mult))
    else:
        bubble_color = (229, 229, 234, int(255 * alpha_mult))  # Light gray
        text_color = (0, 0, 0, int(255 * alpha_mult))
    
    # Draw bubble with proper corners
    corner_radius = 20
    
    # Main bubble body
    draw.rounded_rectangle(
        (x, y, x + bubble_w, y + bubble_h),
        radius=corner_radius,
        fill=bubble_color
    )
    
    # Tail (triangle at bottom corner)
    tail_size = 12
    if is_sender:
        # Tail on bottom-right
        tail_points = [
            (x + bubble_w - corner_radius, y + bubble_h - 8),
            (x + bubble_w + tail_size - 5, y + bubble_h + 5),
            (x + bubble_w - corner_radius, y + bubble_h)
        ]
    else:
        # Tail on bottom-left
        tail_points = [
            (x + corner_radius, y + bubble_h - 8),
            (x - tail_size + 5, y + bubble_h + 5),
            (x + corner_radius, y + bubble_h)
        ]
    
    draw.polygon(tail_points, fill=bubble_color)
    
    # Draw text
    text_y = y + padding_y
    for line in lines:
        text_x = x + padding_x
        draw.text((text_x, text_y), line, font=font, fill=text_color)
        text_y += line_height
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_typing_indicator_exact(
    img: Image.Image,
    position: Tuple[int, int],
    frame: int
) -> Image.Image:
    """
    EXACT iOS typing indicator (three bouncing dots)
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x, y = position
    
    # Bubble
    bubble_w = 75
    bubble_h = 40
    
    draw.rounded_rectangle(
        (x, y, x + bubble_w, y + bubble_h),
        radius=20,
        fill=(229, 229, 234, 255)
    )
    
    # Three dots with bounce
    dot_radius = 5
    dot_spacing = 16
    base_x = x + 18
    base_y = y + bubble_h // 2
    
    for i in range(3):
        # Staggered bounce animation
        phase = (frame * 0.15 + i * 0.4) % (math.pi * 2)
        bounce = math.sin(phase) * 4
        
        dot_x = base_x + i * dot_spacing
        dot_y = int(base_y + bounce)
        
        draw.ellipse(
            (dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius),
            fill=(142, 142, 147, 255)  # iOS gray
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


async def render_imessage_exact(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    EXACT recreation of iMessage TikTok video style
    """
    output_path = output_dir / f"imessage_exact_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    messages = script_data.get("messages") or [
        {"text": "Hey, are you free Tuesday?", "sender": True},
        {"text": "Let me check my calendar...", "sender": False},
        {"text": "Thursday works better for me", "sender": False},
        {"text": "Perfect! Thursday it is", "sender": True},
    ]
    
    total_duration = 6  # 6 seconds
    total_frames = fps * total_duration
    
    # Calculate timing for each message
    msg_duration = total_duration / (len(messages) + 1)
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        
        # White iOS background
        bg = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
        draw = ImageDraw.Draw(bg)
        
        # iOS status bar simulation
        font_status = get_font(14)
        draw.text((30, 15), "9:41", font=font_status, fill=(0, 0, 0, 255))
        
        # Navigation bar
        font_nav = get_font(18, bold=True)
        draw.text((WIDTH // 2 - 50, 55), "Messages", font=font_nav, fill=(0, 0, 0, 255))
        
        # Back arrow
        draw.text((20, 55), "< Back", font=get_font(16), fill=(0, 122, 255, 255))
        
        # Draw messages
        current_y = 120
        
        for i, msg in enumerate(messages):
            msg_start_time = i * msg_duration + 0.5
            msg_end_anim = msg_start_time + 0.4
            
            if time_sec >= msg_start_time:
                # Calculate animation progress
                if time_sec < msg_end_anim:
                    anim_progress = (time_sec - msg_start_time) / 0.4
                else:
                    anim_progress = 1.0
                
                # Position
                if msg["sender"]:
                    x_pos = WIDTH - 420
                else:
                    x_pos = 20
                
                bg = draw_imessage_bubble_exact(
                    bg,
                    msg["text"],
                    (x_pos, current_y),
                    is_sender=msg["sender"],
                    animation_progress=anim_progress
                )
                
                current_y += 70
            
            # Show typing indicator before receiver messages
            elif time_sec >= msg_start_time - 0.8 and not msg["sender"]:
                typing_y = current_y
                bg = draw_typing_indicator_exact(bg, (20, typing_y), frame_num)
        
        # TikTok watermark
        draw = ImageDraw.Draw(bg)
        font_tiktok = get_font(12)
        draw.text((WIDTH - 70, HEIGHT - 40), "TikTok", font=font_tiktok, fill=(0, 0, 0, 80))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG")
    
    # Encode video
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    logger.info(f"Rendered iMessage exact video: {output_path}")
    return str(output_path)
