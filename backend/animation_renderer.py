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

def draw_imessage_bubble(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    x: int, y: int,
    width: int, height: int,
    color: Tuple[int, int, int],
    is_left: bool,
    shadow: bool = True
):
    """Draw iMessage-style bubble with tail"""
    radius = 22
    tail_size = 12
    
    # Create bubble with alpha for smooth edges
    bubble = Image.new('RGBA', (width + tail_size + 10, height + 10), (0, 0, 0, 0))
    bubble_draw = ImageDraw.Draw(bubble)
    
    # Shadow
    if shadow:
        shadow_offset = 3
        bubble_draw.rounded_rectangle(
            (shadow_offset + (0 if is_left else tail_size), shadow_offset, 
             width + shadow_offset + (0 if is_left else tail_size), height + shadow_offset),
            radius=radius,
            fill=(0, 0, 0, 40)
        )
    
    # Main bubble
    bubble_x_offset = 0 if is_left else tail_size
    bubble_draw.rounded_rectangle(
        (bubble_x_offset, 0, width + bubble_x_offset, height),
        radius=radius,
        fill=color + (255,)
    )
    
    # Draw tail (triangle)
    if is_left:
        # Tail on left bottom
        tail_points = [
            (bubble_x_offset + 5, height - 10),
            (bubble_x_offset - tail_size + 2, height + 2),
            (bubble_x_offset + 15, height - 2)
        ]
    else:
        # Tail on right bottom
        tail_points = [
            (width + bubble_x_offset - 5, height - 10),
            (width + bubble_x_offset + tail_size - 2, height + 2),
            (width + bubble_x_offset - 15, height - 2)
        ]
    
    bubble_draw.polygon(tail_points, fill=color + (255,))
    
    # Paste bubble onto main image
    paste_x = x - (tail_size if is_left else 0)
    img.paste(bubble, (paste_x, y), bubble)


async def render_chat_animation(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render professional iMessage-style chat animation.
    
    Based on reference image:
    - Gray bubbles for received (left)
    - Blue bubbles for sent (right)
    - Bubble tails
    - "Read" indicator
    - Typing indicator in blue bubble
    - No header - pure chat view
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # Colors - matching iMessage exactly
    BG_COLOR = (0, 0, 0)
    RECEIVED_COLOR = (58, 58, 60)  # Gray for received (left)
    SENT_COLOR = (0, 122, 255)  # Blue for sent (right) 
    TEXT_COLOR = (255, 255, 255)
    READ_COLOR = (142, 142, 147)  # Gray for "Read"
    
    # Layout
    BUBBLE_PADDING_H = 18
    BUBBLE_PADDING_V = 14
    MESSAGE_MARGIN = 24
    BUBBLE_MAX_WIDTH = WIDTH - 160
    VERTICAL_SPACING = 8
    
    participants = script_data.get("participants", [
        {"name": "Собеседник", "side": "left"},
        {"name": "Я", "side": "right"}
    ])
    messages = script_data.get("messages", [])
    
    # Calculate animation timeline
    current_time = 0.8
    message_events = []
    
    for msg in messages:
        sender_idx = msg.get("sender", 0)
        is_received = participants[sender_idx].get("side", "left") == "left"
        
        typing_start = current_time
        typing_duration = msg.get("typing_duration", 0.8) if is_received else 0
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
        
        current_time = appear_time + msg.get("delay", 1.5)
    
    total_duration = current_time + 2.0
    total_frames = int(total_duration * FPS)
    
    # Font
    font_message = get_font(30)
    font_read = get_font(14)
    font_dots = get_font(40, bold=True)
    
    logger.info(f"Rendering {total_frames} frames for chat animation...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        # Create frame
        img = Image.new('RGBA', (WIDTH, HEIGHT), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Start position (no header, pure chat)
        y_position = 120
        
        last_sent_bubble_bottom = 0
        last_sent_bubble_right = 0
        
        for i, event in enumerate(message_events):
            is_received = event["is_received"]
            
            # Check if we should show typing indicator
            if current_sec < event["appear_time"]:
                if is_received and event["typing_start"] <= current_sec < event["typing_end"]:
                    # Draw typing indicator bubble
                    typing_bubble_width = 90
                    typing_bubble_height = 50
                    typing_x = MESSAGE_MARGIN
                    typing_y = y_position
                    
                    draw_imessage_bubble(
                        draw, img,
                        typing_x, typing_y,
                        typing_bubble_width, typing_bubble_height,
                        SENT_COLOR,  # Blue typing indicator
                        is_left=True,
                        shadow=True
                    )
                    
                    # Animated dots
                    for dot_idx in range(3):
                        dot_x = typing_x + 22 + dot_idx * 20
                        dot_y = typing_y + typing_bubble_height // 2
                        
                        # Pulsing animation
                        phase = (current_sec * 2.5 + dot_idx * 0.25) % 1.0
                        scale = 0.6 + 0.4 * ease_in_out_sine(phase)
                        dot_radius = int(6 * scale)
                        
                        draw.ellipse(
                            (dot_x - dot_radius, dot_y - dot_radius,
                             dot_x + dot_radius, dot_y + dot_radius),
                            fill=TEXT_COLOR
                        )
                continue
            
            # Message is visible
            time_since_appear = current_sec - event["appear_time"]
            slide_duration = 0.25
            
            if time_since_appear < slide_duration:
                progress = ease_out_cubic(time_since_appear / slide_duration)
                opacity = int(255 * progress)
            else:
                progress = 1.0
                opacity = 255
            
            text = event["text"]
            
            # Calculate text wrapping
            words = text.split()
            lines = []
            current_line = ""
            
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                bbox = draw.textbbox((0, 0), test_line, font=font_message)
                if bbox[2] - bbox[0] <= BUBBLE_MAX_WIDTH - BUBBLE_PADDING_H * 2:
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
            max_line_width = 0
            line_height = 36
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_message)
                max_line_width = max(max_line_width, bbox[2] - bbox[0])
            
            bubble_width = max_line_width + BUBBLE_PADDING_H * 2
            bubble_height = len(lines) * line_height + BUBBLE_PADDING_V * 2
            
            # Position and colors based on sender
            if is_received:
                # Left side - gray
                final_x = MESSAGE_MARGIN
                start_x = -bubble_width - 50
                bubble_x = int(start_x + (final_x - start_x) * progress)
                bubble_color = RECEIVED_COLOR
            else:
                # Right side - blue
                final_x = WIDTH - MESSAGE_MARGIN - bubble_width
                start_x = WIDTH + 50
                bubble_x = int(start_x + (final_x - start_x) * progress)
                bubble_color = SENT_COLOR
                last_sent_bubble_bottom = y_position + bubble_height
                last_sent_bubble_right = final_x + bubble_width
            
            bubble_y = y_position
            
            # Draw bubble
            draw_imessage_bubble(
                draw, img,
                bubble_x, bubble_y,
                bubble_width, bubble_height,
                bubble_color,
                is_left=is_received,
                shadow=True
            )
            
            # Draw text
            text_x = bubble_x + BUBBLE_PADDING_H
            text_y = bubble_y + BUBBLE_PADDING_V
            for line in lines:
                # Apply opacity
                text_color_alpha = TEXT_COLOR + (opacity,)
                draw.text((text_x, text_y), line, fill=text_color_alpha, font=font_message)
                text_y += line_height
            
            # Draw "Read" indicator for sent messages (after last one)
            if not is_received and progress == 1.0:
                # Check if this is the last visible sent message
                is_last_sent = True
                for j in range(i + 1, len(message_events)):
                    if not message_events[j]["is_received"] and current_sec >= message_events[j]["appear_time"]:
                        is_last_sent = False
                        break
                
                if is_last_sent and time_since_appear > 0.5:
                    read_text = "Read"
                    read_bbox = draw.textbbox((0, 0), read_text, font=font_read)
                    read_width = read_bbox[2] - read_bbox[0]
                    read_x = bubble_x + bubble_width - read_width
                    read_y = bubble_y + bubble_height + 4
                    draw.text((read_x, read_y), read_text, fill=READ_COLOR, font=font_read)
            
            # Update y position
            y_position += bubble_height + VERTICAL_SPACING + (20 if not is_received else 8)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        img.save(frame_path, "PNG")
        
        if frame_num % 30 == 0:
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
        "-crf", "23",
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
