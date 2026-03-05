"""
Professional Animation Renderer using PIL/Pillow
Creates frame-by-frame animations with proper graphics:
- Rounded corners
- Shadows
- Smooth slide-in animations
- Typing indicators
"""

import asyncio
import uuid
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

# Screen dimensions (9:16 vertical video)
WIDTH = 720
HEIGHT = 1280
FPS = 30

# Font paths
FONT_REGULAR = "/usr/share/fonts/truetype/freefont/FreeSans.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get font with fallback"""
    try:
        return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)
    except:
        return ImageFont.load_default()


def draw_rounded_rectangle(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    radius: int,
    fill: str,
    shadow: bool = False,
    shadow_offset: int = 4
):
    """Draw a rounded rectangle with optional shadow"""
    x1, y1, x2, y2 = xy
    
    # Draw shadow first
    if shadow:
        shadow_color = (0, 0, 0, 60)
        draw.rounded_rectangle(
            (x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset),
            radius=radius,
            fill=shadow_color
        )
    
    # Draw main rectangle
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def ease_out_cubic(t: float) -> float:
    """Ease out cubic easing function for smooth animations"""
    return 1 - pow(1 - t, 3)


def ease_in_out_sine(t: float) -> float:
    """Ease in-out sine for smooth pulse"""
    return -(math.cos(math.pi * t) - 1) / 2


# ==================== CHAT ANIMATION (iMessage Style) ====================

def draw_imessage_bubble_v2(
    img: Image.Image,
    x: int, y: int,
    width: int, height: int,
    color: Tuple[int, int, int],
    is_left: bool,
    opacity: int = 255,
    scale: float = 1.0
):
    """Draw iMessage-style bubble with tail - improved version"""
    if scale <= 0 or opacity <= 0:
        return
    
    # Apply scale from center
    scaled_width = int(width * scale)
    scaled_height = int(height * scale)
    
    # Offset for scaling from center
    x_offset = (width - scaled_width) // 2
    y_offset = (height - scaled_height) // 2
    
    radius = int(20 * scale)
    tail_width = int(10 * scale)
    tail_height = int(15 * scale)
    
    # Create bubble with transparency
    bubble_img = Image.new('RGBA', (scaled_width + tail_width + 4, scaled_height + tail_height + 4), (0, 0, 0, 0))
    bubble_draw = ImageDraw.Draw(bubble_img)
    
    # Bubble position within the bubble image
    bx = tail_width if is_left else 0
    by = 0
    
    # Draw shadow first
    shadow_offset = 2
    shadow_color = (0, 0, 0, int(40 * opacity / 255))
    bubble_draw.rounded_rectangle(
        (bx + shadow_offset, by + shadow_offset, bx + scaled_width + shadow_offset, by + scaled_height + shadow_offset),
        radius=radius,
        fill=shadow_color
    )
    
    # Draw main bubble
    bubble_color = color + (opacity,)
    bubble_draw.rounded_rectangle(
        (bx, by, bx + scaled_width, by + scaled_height),
        radius=radius,
        fill=bubble_color
    )
    
    # Draw tail
    if is_left:
        # Tail pointing left-down
        tail_points = [
            (bx, by + scaled_height - radius),
            (0, by + scaled_height + tail_height - 2),
            (bx + radius, by + scaled_height - 2)
        ]
    else:
        # Tail pointing right-down
        tail_points = [
            (bx + scaled_width, by + scaled_height - radius),
            (bx + scaled_width + tail_width, by + scaled_height + tail_height - 2),
            (bx + scaled_width - radius, by + scaled_height - 2)
        ]
    
    bubble_draw.polygon(tail_points, fill=bubble_color)
    
    # Paste onto main image
    paste_x = x + x_offset - (tail_width if is_left else 0)
    paste_y = y + y_offset
    img.paste(bubble_img, (paste_x, paste_y), bubble_img)


def ease_out_back(t: float) -> float:
    """Ease out with overshoot (bounce back effect)"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


def ease_out_elastic(t: float) -> float:
    """Elastic ease out for bouncy effect"""
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


async def render_chat_animation(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render professional iMessage-style chat animation.
    
    Features:
    - Dynamic bounce animations
    - Scale + slide effects
    - Proper alignment
    - Typing indicator with pulsing dots
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # Colors - exact iMessage style
    BG_COLOR = (0, 0, 0)
    RECEIVED_COLOR = (58, 58, 62)  # Dark gray for received (left)
    SENT_COLOR = (0, 122, 255)  # Blue for sent (right)
    TEXT_COLOR = (255, 255, 255)
    READ_COLOR = (138, 138, 142)
    
    # Layout - precise positioning
    SCREEN_PADDING = 16
    BUBBLE_PADDING_H = 16
    BUBBLE_PADDING_V = 10
    BUBBLE_MAX_WIDTH = int(WIDTH * 0.72)  # Max 72% of screen width
    VERTICAL_GAP = 6
    
    participants = script_data.get("participants", [
        {"name": "Собеседник", "side": "left"},
        {"name": "Я", "side": "right"}
    ])
    messages = script_data.get("messages", [])
    
    # Animation timeline
    current_time = 0.5
    message_events = []
    
    for msg in messages:
        sender_idx = msg.get("sender", 0)
        is_received = participants[sender_idx].get("side", "left") == "left"
        
        # Typing only for received messages
        typing_duration = msg.get("typing_duration", 1.0) if is_received else 0
        typing_start = current_time if is_received else current_time
        typing_end = typing_start + typing_duration
        appear_time = typing_end + 0.1
        
        message_events.append({
            "typing_start": typing_start,
            "typing_end": typing_end,
            "appear_time": appear_time,
            "text": msg.get("text", ""),
            "sender": sender_idx,
            "is_received": is_received
        })
        
        current_time = appear_time + msg.get("delay", 1.8)
    
    total_duration = current_time + 2.5
    total_frames = int(total_duration * FPS)
    
    # Font
    try:
        font_message = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 28)
        font_read = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 13)
    except:
        font_message = ImageFont.load_default()
        font_read = ImageFont.load_default()
    
    logger.info(f"Rendering {total_frames} frames for chat animation...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        # Create frame
        img = Image.new('RGBA', (WIDTH, HEIGHT), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Start position
        y_position = 100
        
        for i, event in enumerate(message_events):
            is_received = event["is_received"]
            
            # === TYPING INDICATOR ===
            if current_sec < event["appear_time"]:
                if is_received and event["typing_start"] <= current_sec < event["typing_end"]:
                    typing_progress = (current_sec - event["typing_start"]) / max(0.01, event["typing_end"] - event["typing_start"])
                    
                    # Typing bubble
                    typing_width = 75
                    typing_height = 40
                    typing_x = SCREEN_PADDING
                    typing_y = y_position
                    
                    # Animate typing bubble appearance
                    if typing_progress < 0.3:
                        t_scale = ease_out_back(typing_progress / 0.3)
                    else:
                        t_scale = 1.0
                    
                    draw_imessage_bubble_v2(
                        img, typing_x, typing_y,
                        typing_width, typing_height,
                        SENT_COLOR, is_left=True,
                        opacity=255, scale=t_scale
                    )
                    
                    # Animated pulsing dots
                    if t_scale > 0.5:
                        for dot_idx in range(3):
                            dot_x = typing_x + 18 + dot_idx * 18
                            dot_y = typing_y + typing_height // 2
                            
                            # Wave animation
                            phase = (current_sec * 4 + dot_idx * 0.4) % 1.0
                            dot_scale = 0.5 + 0.5 * math.sin(phase * math.pi)
                            dot_radius = int(5 * dot_scale)
                            dot_alpha = int(150 + 105 * dot_scale)
                            
                            if dot_radius > 0:
                                draw.ellipse(
                                    (dot_x - dot_radius, dot_y - dot_radius - 5,
                                     dot_x + dot_radius, dot_y + dot_radius - 5),
                                    fill=(255, 255, 255, dot_alpha)
                                )
                continue
            
            # === MESSAGE BUBBLE ===
            time_since_appear = current_sec - event["appear_time"]
            
            # Animation parameters
            anim_duration = 0.4
            
            if time_since_appear < anim_duration:
                progress = time_since_appear / anim_duration
                # Use bounce easing for dynamic feel
                scale_progress = ease_out_back(min(1.0, progress * 1.2))
                slide_progress = ease_out_cubic(progress)
                opacity = int(255 * min(1.0, progress * 2))
            else:
                scale_progress = 1.0
                slide_progress = 1.0
                opacity = 255
            
            text = event["text"]
            
            # Text wrapping
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                bbox = draw.textbbox((0, 0), test_line, font=font_message)
                line_width = bbox[2] - bbox[0]
                if line_width <= BUBBLE_MAX_WIDTH - BUBBLE_PADDING_H * 2:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
            
            if not lines:
                lines = [text]
            
            # Calculate bubble size
            line_height = 34
            max_line_width = 0
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_message)
                max_line_width = max(max_line_width, bbox[2] - bbox[0])
            
            bubble_width = max_line_width + BUBBLE_PADDING_H * 2
            bubble_height = len(lines) * line_height + BUBBLE_PADDING_V * 2
            
            # Position calculation with slide animation
            if is_received:
                # Left side - slide from left
                final_x = SCREEN_PADDING
                start_x = -bubble_width - 30
                bubble_x = int(start_x + (final_x - start_x) * slide_progress)
                bubble_color = RECEIVED_COLOR
            else:
                # Right side - slide from right
                final_x = WIDTH - SCREEN_PADDING - bubble_width
                start_x = WIDTH + 30
                bubble_x = int(start_x + (final_x - start_x) * slide_progress)
                bubble_color = SENT_COLOR
            
            bubble_y = y_position
            
            # Draw bubble with scale
            draw_imessage_bubble_v2(
                img, bubble_x, bubble_y,
                bubble_width, bubble_height,
                bubble_color, is_left=is_received,
                opacity=opacity, scale=scale_progress
            )
            
            # Draw text (only if scale is sufficient)
            if scale_progress > 0.3:
                text_opacity = int(opacity * min(1.0, (scale_progress - 0.3) / 0.7))
                
                # Calculate scaled text position
                scaled_width = int(bubble_width * scale_progress)
                scaled_height = int(bubble_height * scale_progress)
                x_off = (bubble_width - scaled_width) // 2
                y_off = (bubble_height - scaled_height) // 2
                
                text_x = bubble_x + BUBBLE_PADDING_H + x_off
                text_y = bubble_y + BUBBLE_PADDING_V + y_off
                
                for line in lines:
                    text_color_alpha = TEXT_COLOR + (text_opacity,)
                    draw.text((text_x, text_y), line, fill=text_color_alpha, font=font_message)
                    text_y += int(line_height * scale_progress)
            
            # "Read" indicator for sent messages
            if not is_received and slide_progress == 1.0 and time_since_appear > 0.8:
                # Check if this is the last visible sent message so far
                is_last_sent = True
                for j in range(i + 1, len(message_events)):
                    if not message_events[j]["is_received"] and current_sec >= message_events[j]["appear_time"]:
                        is_last_sent = False
                        break
                
                if is_last_sent:
                    read_alpha = int(255 * min(1.0, (time_since_appear - 0.8) / 0.3))
                    read_text = "Read"
                    read_bbox = draw.textbbox((0, 0), read_text, font=font_read)
                    read_width = read_bbox[2] - read_bbox[0]
                    read_x = bubble_x + bubble_width - read_width
                    read_y = bubble_y + bubble_height + 6
                    draw.text((read_x, read_y), read_text, fill=READ_COLOR + (read_alpha,), font=font_read)
            
            # Update y position
            y_position += bubble_height + VERTICAL_GAP + 16
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        img.save(frame_path, "PNG")
        
        if frame_num % 60 == 0:
            logger.info(f"Rendered frame {frame_num}/{total_frames}")
    
    # Compile frames to video
    logger.info("Compiling frames to video...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-crf", "20",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Cleanup frames
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()
    
    if output_file.exists() and output_file.stat().st_size > 1000:
        logger.info(f"Created chat animation: {output_file}")
        return output_file
    
    logger.error("Chat animation creation failed")
    return None


# ==================== APPLE TEXT ANIMATION ====================

async def render_apple_text_animation(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render Apple-style minimalist text animation.
    
    Features:
    - Clean white/black backgrounds
    - Large bold text
    - Smooth fade transitions
    - Underline for emphasis
    """
    output_file = output_path / f"apple_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    phrases = script_data.get("phrases", [
        {"text": "Создаём", "bg": "white"},
        {"text": "Невероятное", "bg": "white"},
        {"text": "Просто.", "bg": "black"},
        {"text": "Как Apple.", "bg": "white", "underline": "Apple"}
    ])
    
    PHRASE_DURATION = 1.8
    FADE_DURATION = 0.3
    
    total_duration = len(phrases) * PHRASE_DURATION + 1.0
    total_frames = int(total_duration * FPS)
    
    font_large = get_font(72, bold=True)
    
    logger.info(f"Rendering {total_frames} frames for Apple text animation...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        # Determine which phrase is active
        phrase_idx = min(int(current_sec / PHRASE_DURATION), len(phrases) - 1)
        phrase = phrases[phrase_idx]
        
        time_in_phrase = current_sec - (phrase_idx * PHRASE_DURATION)
        
        # Background color
        bg_white = phrase.get("bg", "white") == "white"
        bg_color = (255, 255, 255) if bg_white else (0, 0, 0)
        text_color = (0, 0, 0) if bg_white else (255, 255, 255)
        
        img = Image.new('RGB', (WIDTH, HEIGHT), bg_color)
        draw = ImageDraw.Draw(img)
        
        text = phrase.get("text", "")
        
        # Calculate fade
        if time_in_phrase < FADE_DURATION:
            # Fade in
            opacity = int(255 * (time_in_phrase / FADE_DURATION))
        elif time_in_phrase > PHRASE_DURATION - FADE_DURATION:
            # Fade out
            opacity = int(255 * ((PHRASE_DURATION - time_in_phrase) / FADE_DURATION))
        else:
            opacity = 255
        
        # Create text with opacity
        text_bbox = draw.textbbox((0, 0), text, font=font_large)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        text_x = (WIDTH - text_width) // 2
        text_y = (HEIGHT - text_height) // 2
        
        # Apply opacity by creating overlay
        if opacity < 255:
            text_color_with_alpha = text_color + (opacity,)
            overlay = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.text((text_x, text_y), text, fill=text_color_with_alpha, font=font_large)
            img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        else:
            draw.text((text_x, text_y), text, fill=text_color, font=font_large)
        
        # Draw underline if specified
        underline_word = phrase.get("underline")
        if underline_word and opacity > 200:
            # Simple underline under center of text
            draw = ImageDraw.Draw(img)
            underline_y = text_y + text_height + 8
            underline_width = int(text_width * 0.6)
            underline_x = (WIDTH - underline_width) // 2
            draw.rectangle(
                (underline_x, underline_y, underline_x + underline_width, underline_y + 4),
                fill=text_color
            )
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        img.save(frame_path, "PNG")
    
    # Compile frames
    logger.info("Compiling Apple text animation...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Cleanup
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()
    
    if output_file.exists() and output_file.stat().st_size > 1000:
        logger.info(f"Created Apple text animation: {output_file}")
        return output_file
    
    return None


# ==================== KINETIC TYPOGRAPHY ====================

async def render_kinetic_typography(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render kinetic typography - word by word animation.
    
    Features:
    - Words appear one by one
    - Scale and fade animations
    - Clean layout
    """
    output_file = output_path / f"kinetic_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    full_text = script_data.get("full_script", "Каждое большое достижение начинается с решения попробовать")
    words = full_text.split()
    
    bg_color = hex_to_rgb(script_data.get("bg_color", "#000000"))
    text_color = hex_to_rgb(script_data.get("text_color", "#ffffff"))
    
    WORD_DELAY = 0.25
    WORD_ANIM_DURATION = 0.2
    
    total_duration = len(words) * WORD_DELAY + 3.0
    total_frames = int(total_duration * FPS)
    
    font = get_font(48, bold=True)
    
    # Pre-calculate word positions
    words_per_line = 4
    line_height = 70
    word_positions = []
    
    for i, word in enumerate(words):
        line = i // words_per_line
        pos_in_line = i % words_per_line
        word_positions.append({
            "word": word,
            "line": line,
            "pos": pos_in_line,
            "appear_time": 0.5 + i * WORD_DELAY
        })
    
    num_lines = (len(words) - 1) // words_per_line + 1
    start_y = (HEIGHT - num_lines * line_height) // 2
    
    logger.info(f"Rendering {total_frames} frames for kinetic typography...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        img = Image.new('RGBA', (WIDTH, HEIGHT), bg_color + (255,))
        draw = ImageDraw.Draw(img)
        
        # Calculate visible words and their states
        line_words = {}  # Group words by line for centering
        
        for wp in word_positions:
            if current_sec < wp["appear_time"]:
                continue
            
            time_since_appear = current_sec - wp["appear_time"]
            
            if time_since_appear < WORD_ANIM_DURATION:
                # Animating in
                progress = ease_out_cubic(time_since_appear / WORD_ANIM_DURATION)
                scale = 0.5 + 0.5 * progress
                opacity = int(255 * progress)
            else:
                scale = 1.0
                opacity = 255
            
            line = wp["line"]
            if line not in line_words:
                line_words[line] = []
            
            line_words[line].append({
                "word": wp["word"],
                "scale": scale,
                "opacity": opacity,
                "pos": wp["pos"]
            })
        
        # Render words line by line (centered)
        for line, words_in_line in line_words.items():
            # Calculate total width of this line
            total_width = 0
            word_widths = []
            
            for w in sorted(words_in_line, key=lambda x: x["pos"]):
                bbox = draw.textbbox((0, 0), w["word"], font=font)
                word_width = bbox[2] - bbox[0]
                word_widths.append(word_width)
                total_width += word_width
            
            total_width += (len(words_in_line) - 1) * 20  # spacing
            
            # Start x for centering
            x = (WIDTH - total_width) // 2
            y = start_y + line * line_height
            
            for i, w in enumerate(sorted(words_in_line, key=lambda x: x["pos"])):
                color_with_alpha = text_color + (w["opacity"],)
                
                # Scale effect (simple - just draw at position)
                draw.text((x, y), w["word"], fill=color_with_alpha, font=font)
                
                x += word_widths[i] + 20
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        img.save(frame_path, "PNG")
    
    # Compile frames
    logger.info("Compiling kinetic typography...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Cleanup
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()
    
    if output_file.exists() and output_file.stat().st_size > 1000:
        logger.info(f"Created kinetic typography: {output_file}")
        return output_file
    
    return None


# ==================== LOGO ANIMATION ====================

async def render_logo_animation(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render logo/brand animation.
    
    Animation sequence:
    1. Logo icon appears in center (fade + scale)
    2. Logo slides to the left
    3. Brand name appears to the right of logo (where logo was)
    4. Optional tagline fades in below
    """
    output_file = output_path / f"logo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    brand_name = script_data.get("brand_name", "Brand")
    tagline = script_data.get("tagline", "")
    bg_color = hex_to_rgb(script_data.get("bg_color", "#7289da"))
    text_color = hex_to_rgb(script_data.get("text_color", "#ffffff"))
    
    total_duration = 5.0
    total_frames = int(total_duration * FPS)
    
    font_brand = get_font(56, bold=True)
    font_tagline = get_font(24)
    
    # Animation timeline
    LOGO_APPEAR_START = 0.3
    LOGO_APPEAR_DURATION = 0.6
    LOGO_HOLD = 1.0  # Time logo stays in center
    LOGO_SLIDE_START = LOGO_APPEAR_START + LOGO_APPEAR_DURATION + LOGO_HOLD
    LOGO_SLIDE_DURATION = 0.5
    TEXT_APPEAR_START = LOGO_SLIDE_START + 0.2
    TEXT_APPEAR_DURATION = 0.4
    TAGLINE_START = TEXT_APPEAR_START + TEXT_APPEAR_DURATION + 0.3
    TAGLINE_DURATION = 0.4
    
    # Pre-calculate positions
    logo_size = 80
    center_x = WIDTH // 2
    center_y = HEIGHT // 2 - 30
    
    # Calculate brand name width
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    brand_bbox = temp_draw.textbbox((0, 0), brand_name, font=font_brand)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_height = brand_bbox[3] - brand_bbox[1]
    
    # Final positions (logo left, text right, both centered together)
    gap = 30  # Gap between logo and text
    total_width = logo_size * 2 + gap + brand_width
    final_logo_x = (WIDTH - total_width) // 2 + logo_size
    final_text_x = final_logo_x + logo_size + gap
    
    logger.info(f"Rendering {total_frames} frames for logo animation...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        img = Image.new('RGBA', (WIDTH, HEIGHT), bg_color + (255,))
        draw = ImageDraw.Draw(img)
        
        # Phase 1: Logo appears in center
        logo_x = center_x
        logo_y = center_y
        logo_scale = 0
        logo_opacity = 0
        
        if current_sec >= LOGO_APPEAR_START:
            if current_sec < LOGO_APPEAR_START + LOGO_APPEAR_DURATION:
                # Logo appearing
                progress = (current_sec - LOGO_APPEAR_START) / LOGO_APPEAR_DURATION
                progress = ease_out_cubic(progress)
                logo_scale = progress
                logo_opacity = int(255 * progress)
            elif current_sec < LOGO_SLIDE_START:
                # Logo holding in center
                logo_scale = 1.0
                logo_opacity = 255
            elif current_sec < LOGO_SLIDE_START + LOGO_SLIDE_DURATION:
                # Logo sliding left
                progress = (current_sec - LOGO_SLIDE_START) / LOGO_SLIDE_DURATION
                progress = ease_out_cubic(progress)
                logo_x = center_x + (final_logo_x - center_x) * progress
                logo_scale = 1.0
                logo_opacity = 255
            else:
                # Logo at final position
                logo_x = final_logo_x
                logo_scale = 1.0
                logo_opacity = 255
        
        # Draw logo (circle with glow effect)
        if logo_scale > 0:
            scaled_size = int(logo_size * logo_scale)
            
            # Glow effect
            if logo_opacity > 100:
                for glow_layer in range(4, 0, -1):
                    glow_size = scaled_size + glow_layer * 12
                    glow_alpha = int(20 * (logo_opacity / 255) / glow_layer)
                    draw.ellipse(
                        (int(logo_x) - glow_size, int(logo_y) - glow_size,
                         int(logo_x) + glow_size, int(logo_y) + glow_size),
                        fill=text_color + (glow_alpha,)
                    )
            
            # Main logo circle
            draw.ellipse(
                (int(logo_x) - scaled_size, int(logo_y) - scaled_size,
                 int(logo_x) + scaled_size, int(logo_y) + scaled_size),
                fill=text_color + (logo_opacity,)
            )
        
        # Phase 2: Brand name appears
        if current_sec >= TEXT_APPEAR_START:
            if current_sec < TEXT_APPEAR_START + TEXT_APPEAR_DURATION:
                text_progress = (current_sec - TEXT_APPEAR_START) / TEXT_APPEAR_DURATION
                text_progress = ease_out_cubic(text_progress)
                text_opacity = int(255 * text_progress)
                text_y_offset = int(20 * (1 - text_progress))
            else:
                text_opacity = 255
                text_y_offset = 0
            
            text_y = center_y - brand_height // 2 + text_y_offset
            draw.text(
                (final_text_x, text_y),
                brand_name,
                fill=text_color + (text_opacity,),
                font=font_brand
            )
        
        # Phase 3: Tagline appears
        if tagline and current_sec >= TAGLINE_START:
            if current_sec < TAGLINE_START + TAGLINE_DURATION:
                tagline_progress = (current_sec - TAGLINE_START) / TAGLINE_DURATION
                tagline_progress = ease_out_cubic(tagline_progress)
                tagline_opacity = int(200 * tagline_progress)
            else:
                tagline_opacity = 200
            
            tagline_bbox = draw.textbbox((0, 0), tagline, font=font_tagline)
            tagline_width = tagline_bbox[2] - tagline_bbox[0]
            tagline_x = (WIDTH - tagline_width) // 2
            tagline_y = center_y + logo_size + 50
            
            draw.text(
                (tagline_x, tagline_y),
                tagline,
                fill=text_color + (tagline_opacity,),
                font=font_tagline
            )
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        img.save(frame_path, "PNG")
    
    # Compile frames
    logger.info("Compiling logo animation...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        str(output_file)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await process.communicate()
    
    # Cleanup
    for f in frames_dir.glob("*.png"):
        f.unlink()
    frames_dir.rmdir()
    
    if output_file.exists() and output_file.stat().st_size > 1000:
        logger.info(f"Created logo animation: {output_file}")
        return output_file
    
    return None
