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

async def render_chat_animation(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render professional iMessage-style chat animation.
    
    Features:
    - Black background
    - Rounded message bubbles with shadows
    - Slide-in animations
    - Typing indicator with animated dots
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # Colors
    BG_COLOR = (0, 0, 0)
    RECEIVED_COLOR = hex_to_rgb("#007AFF")  # Blue
    SENT_COLOR = hex_to_rgb("#3A3A3C")  # Dark gray
    TEXT_COLOR = (255, 255, 255)
    HEADER_COLOR = (28, 28, 30)
    SUBTLE_TEXT = (142, 142, 147)
    
    # Layout
    HEADER_HEIGHT = 90
    BUBBLE_RADIUS = 20
    BUBBLE_PADDING_H = 16
    BUBBLE_PADDING_V = 12
    MESSAGE_MARGIN = 20
    BUBBLE_MAX_WIDTH = WIDTH - 140
    
    participants = script_data.get("participants", [
        {"name": "Клиент", "side": "left"},
        {"name": "Я", "side": "right"}
    ])
    messages = script_data.get("messages", [])
    
    # Calculate animation timeline
    current_time = 0.5  # Start delay
    message_events = []
    
    for msg in messages:
        typing_start = current_time
        typing_duration = msg.get("typing_duration", 0.8)
        typing_end = typing_start + typing_duration
        appear_time = typing_end
        
        message_events.append({
            "typing_start": typing_start,
            "typing_end": typing_end,
            "appear_time": appear_time,
            "text": msg.get("text", ""),
            "sender": msg.get("sender", 0),
            "is_received": participants[msg.get("sender", 0)].get("side", "left") == "left"
        })
        
        current_time = appear_time + msg.get("delay", 1.2)
    
    total_duration = current_time + 1.5
    total_frames = int(total_duration * FPS)
    
    # Font
    font_message = get_font(28)
    font_header = get_font(20, bold=True)
    font_time = get_font(14)
    font_dots = get_font(36, bold=True)
    
    contact_name = participants[0].get("name", "Контакт") if participants else "Контакт"
    
    # Track visible messages and their positions
    visible_messages = []
    
    logger.info(f"Rendering {total_frames} frames for chat animation...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        # Create frame
        img = Image.new('RGBA', (WIDTH, HEIGHT), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Draw header
        draw.rectangle((0, 0, WIDTH, HEADER_HEIGHT), fill=HEADER_COLOR)
        
        # Time text
        time_text = "Сейчас"
        time_bbox = draw.textbbox((0, 0), time_text, font=font_time)
        time_width = time_bbox[2] - time_bbox[0]
        draw.text(((WIDTH - time_width) // 2, 12), time_text, fill=SUBTLE_TEXT, font=font_time)
        
        # Contact name
        name_bbox = draw.textbbox((0, 0), contact_name, font=font_header)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text(((WIDTH - name_width) // 2, 45), contact_name, fill=TEXT_COLOR, font=font_header)
        
        # Calculate which messages are visible and their states
        y_position = HEADER_HEIGHT + 30
        
        for i, event in enumerate(message_events):
            # Check if message should be visible
            if current_sec < event["appear_time"]:
                # Check if we should show typing indicator
                if event["is_received"] and event["typing_start"] <= current_sec < event["typing_end"]:
                    # Draw typing indicator
                    typing_progress = (current_sec - event["typing_start"]) / (event["typing_end"] - event["typing_start"])
                    
                    # Typing bubble
                    bubble_width = 80
                    bubble_height = 44
                    bubble_x = MESSAGE_MARGIN
                    bubble_y = y_position
                    
                    draw_rounded_rectangle(
                        draw,
                        (bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height),
                        radius=BUBBLE_RADIUS,
                        fill=RECEIVED_COLOR,
                        shadow=True
                    )
                    
                    # Animated dots
                    dot_y = bubble_y + bubble_height // 2
                    for dot_idx in range(3):
                        dot_x = bubble_x + 20 + dot_idx * 18
                        # Pulsing animation
                        phase = (current_sec * 3 + dot_idx * 0.3) % 1.0
                        alpha = int(100 + 155 * ease_in_out_sine(phase))
                        dot_color = (255, 255, 255, alpha)
                        draw.ellipse(
                            (dot_x - 5, dot_y - 8, dot_x + 5, dot_y + 2),
                            fill=dot_color
                        )
                continue
            
            # Message is visible - calculate slide animation
            time_since_appear = current_sec - event["appear_time"]
            slide_duration = 0.3
            
            if time_since_appear < slide_duration:
                # Sliding in
                progress = ease_out_cubic(time_since_appear / slide_duration)
            else:
                progress = 1.0
            
            text = event["text"]
            is_received = event["is_received"]
            
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
            line_height = 32
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font_message)
                max_line_width = max(max_line_width, bbox[2] - bbox[0])
            
            bubble_width = max_line_width + BUBBLE_PADDING_H * 2
            bubble_height = len(lines) * line_height + BUBBLE_PADDING_V * 2
            
            # Position based on sender
            if is_received:
                # Slide from left
                final_x = MESSAGE_MARGIN
                start_x = -bubble_width - 20
                bubble_x = int(start_x + (final_x - start_x) * progress)
                bubble_color = RECEIVED_COLOR
            else:
                # Slide from right
                final_x = WIDTH - MESSAGE_MARGIN - bubble_width
                start_x = WIDTH + 20
                bubble_x = int(start_x + (final_x - start_x) * progress)
                bubble_color = SENT_COLOR
            
            bubble_y = y_position
            
            # Draw bubble with shadow
            draw_rounded_rectangle(
                draw,
                (bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height),
                radius=BUBBLE_RADIUS,
                fill=bubble_color,
                shadow=True,
                shadow_offset=3
            )
            
            # Draw text
            text_x = bubble_x + BUBBLE_PADDING_H
            text_y = bubble_y + BUBBLE_PADDING_V
            for line in lines:
                draw.text((text_x, text_y), line, fill=TEXT_COLOR, font=font_message)
                text_y += line_height
            
            # Update y position for next message
            y_position += bubble_height + 12
        
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
    
    Features:
    - Icon reveal with scale animation
    - Brand name fade in
    - Tagline appearance
    - Glow effect
    """
    output_file = output_path / f"logo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    brand_name = script_data.get("brand_name", "Brand")
    tagline = script_data.get("tagline", "")
    bg_color = hex_to_rgb(script_data.get("bg_color", "#7289da"))
    text_color = hex_to_rgb(script_data.get("text_color", "#ffffff"))
    
    total_duration = 4.0
    total_frames = int(total_duration * FPS)
    
    font_brand = get_font(64, bold=True)
    font_tagline = get_font(28)
    
    # Animation timeline
    ICON_START = 0.3
    ICON_DURATION = 0.5
    TEXT_START = 1.2
    TEXT_DURATION = 0.4
    TAGLINE_START = 2.0
    TAGLINE_DURATION = 0.4
    
    logger.info(f"Rendering {total_frames} frames for logo animation...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        img = Image.new('RGBA', (WIDTH, HEIGHT), bg_color + (255,))
        draw = ImageDraw.Draw(img)
        
        center_x = WIDTH // 2
        center_y = HEIGHT // 2 - 50
        
        # Icon (simple circle/shape)
        if current_sec >= ICON_START:
            icon_progress = min(1.0, (current_sec - ICON_START) / ICON_DURATION)
            icon_progress = ease_out_cubic(icon_progress)
            
            icon_size = int(80 * icon_progress)
            icon_opacity = int(255 * icon_progress)
            
            if icon_size > 0:
                # Draw glow
                for glow_size in range(3, 0, -1):
                    glow_radius = icon_size + glow_size * 8
                    glow_alpha = int(30 * icon_progress / glow_size)
                    draw.ellipse(
                        (center_x - glow_radius, center_y - glow_radius,
                         center_x + glow_radius, center_y + glow_radius),
                        fill=text_color + (glow_alpha,)
                    )
                
                # Draw icon
                draw.ellipse(
                    (center_x - icon_size, center_y - icon_size,
                     center_x + icon_size, center_y + icon_size),
                    fill=text_color + (icon_opacity,)
                )
        
        # Brand name
        if current_sec >= TEXT_START:
            text_progress = min(1.0, (current_sec - TEXT_START) / TEXT_DURATION)
            text_progress = ease_out_cubic(text_progress)
            
            text_opacity = int(255 * text_progress)
            text_y_offset = int(20 * (1 - text_progress))  # Slide up
            
            bbox = draw.textbbox((0, 0), brand_name, font=font_brand)
            text_width = bbox[2] - bbox[0]
            text_x = (WIDTH - text_width) // 2
            text_y = center_y + 120 + text_y_offset
            
            draw.text((text_x, text_y), brand_name, fill=text_color + (text_opacity,), font=font_brand)
        
        # Tagline
        if tagline and current_sec >= TAGLINE_START:
            tagline_progress = min(1.0, (current_sec - TAGLINE_START) / TAGLINE_DURATION)
            tagline_progress = ease_out_cubic(tagline_progress)
            
            tagline_opacity = int(200 * tagline_progress)
            
            bbox = draw.textbbox((0, 0), tagline, font=font_tagline)
            tagline_width = bbox[2] - bbox[0]
            tagline_x = (WIDTH - tagline_width) // 2
            tagline_y = center_y + 200
            
            draw.text((tagline_x, tagline_y), tagline, fill=text_color + (tagline_opacity,), font=font_tagline)
        
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
