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
    Render iMessage-style chat animation with camera following messages.
    
    Features:
    - Camera smoothly pans to each new message
    - High quality rendering
    - Proper iMessage bubble style
    - Dynamic feel
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # Higher quality settings
    RENDER_WIDTH = 1080  # Higher resolution
    RENDER_HEIGHT = 1920
    RENDER_FPS = 30
    
    # Colors - exact iMessage
    BG_COLOR = (0, 0, 0)
    RECEIVED_COLOR = (55, 55, 57)  # Gray
    SENT_COLOR = (0, 122, 255)  # Blue
    TEXT_COLOR = (255, 255, 255)
    READ_COLOR = (130, 130, 134)
    
    # Layout
    PADDING = 20
    BUBBLE_H_PAD = 18
    BUBBLE_V_PAD = 12
    MAX_BUBBLE_WIDTH = int(RENDER_WIDTH * 0.75)
    BUBBLE_RADIUS = 22
    MESSAGE_GAP = 10
    
    participants = script_data.get("participants", [
        {"name": "Собеседник", "side": "left"},
        {"name": "Я", "side": "right"}
    ])
    messages = script_data.get("messages", [])
    
    # Pre-calculate all message layouts
    try:
        font_msg = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 32)
        font_read = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 15)
    except:
        font_msg = ImageFont.load_default()
        font_read = ImageFont.load_default()
    
    # Calculate message data
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    message_data = []
    canvas_y = 150  # Start position on canvas
    
    for idx, msg in enumerate(messages):
        sender_idx = msg.get("sender", 0)
        is_left = participants[sender_idx].get("side", "left") == "left"
        text = msg.get("text", "")
        
        # Word wrap
        words = text.split()
        lines = []
        current_line = ""
        for word in words:
            test = current_line + (" " if current_line else "") + word
            bbox = temp_draw.textbbox((0, 0), test, font=font_msg)
            if bbox[2] - bbox[0] <= MAX_BUBBLE_WIDTH - BUBBLE_H_PAD * 2:
                current_line = test
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        if not lines:
            lines = [text]
        
        # Calculate bubble dimensions
        line_h = 40
        max_w = 0
        for line in lines:
            bbox = temp_draw.textbbox((0, 0), line, font=font_msg)
            max_w = max(max_w, bbox[2] - bbox[0])
        
        bubble_w = max_w + BUBBLE_H_PAD * 2
        bubble_h = len(lines) * line_h + BUBBLE_V_PAD * 2
        
        # X position
        if is_left:
            bubble_x = PADDING
        else:
            bubble_x = RENDER_WIDTH - PADDING - bubble_w
        
        message_data.append({
            "text": text,
            "lines": lines,
            "is_left": is_left,
            "bubble_x": bubble_x,
            "bubble_y": canvas_y,
            "bubble_w": bubble_w,
            "bubble_h": bubble_h,
            "typing_duration": msg.get("typing_duration", 0.9) if is_left else 0,
            "delay": msg.get("delay", 1.5)
        })
        
        canvas_y += bubble_h + MESSAGE_GAP + 25
    
    # Calculate timeline
    time_cursor = 0.8
    for md in message_data:
        md["typing_start"] = time_cursor if md["is_left"] else time_cursor
        md["typing_end"] = md["typing_start"] + md["typing_duration"]
        md["appear_time"] = md["typing_end"] + 0.15
        time_cursor = md["appear_time"] + md["delay"]
    
    total_duration = time_cursor + 2.0
    total_frames = int(total_duration * RENDER_FPS)
    
    # Camera tracking
    camera_y = 0  # Current camera Y offset
    camera_target_y = 0
    
    logger.info(f"Rendering {total_frames} HQ frames...")
    
    for frame_idx in range(total_frames):
        current_time = frame_idx / RENDER_FPS
        
        # Find which message camera should focus on
        for md in message_data:
            if current_time >= md["appear_time"] - 0.3:
                # Camera target: center the message in view
                msg_center_y = md["bubble_y"] + md["bubble_h"] / 2
                camera_target_y = max(0, msg_center_y - RENDER_HEIGHT * 0.4)
        
        # Smooth camera movement
        camera_speed = 0.08
        camera_y += (camera_target_y - camera_y) * camera_speed
        
        # Create frame
        img = Image.new('RGBA', (RENDER_WIDTH, RENDER_HEIGHT), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Draw messages
        for i, md in enumerate(message_data):
            # Screen position (with camera offset)
            screen_y = md["bubble_y"] - camera_y
            
            # Skip if off screen
            if screen_y > RENDER_HEIGHT + 100 or screen_y < -md["bubble_h"] - 100:
                continue
            
            is_left = md["is_left"]
            
            # === Typing indicator ===
            if md["is_left"] and md["typing_start"] <= current_time < md["typing_end"]:
                typing_progress = (current_time - md["typing_start"]) / max(0.01, md["typing_duration"])
                
                # Typing bubble
                t_w, t_h = 80, 44
                t_x = PADDING
                t_y = screen_y
                
                # Scale in
                t_scale = min(1.0, typing_progress * 3) if typing_progress < 0.33 else 1.0
                
                if t_scale > 0.1:
                    # Draw typing bubble
                    scaled_w = int(t_w * t_scale)
                    scaled_h = int(t_h * t_scale)
                    offset_x = (t_w - scaled_w) // 2
                    offset_y = (t_h - scaled_h) // 2
                    
                    draw.rounded_rectangle(
                        (t_x + offset_x, t_y + offset_y, 
                         t_x + offset_x + scaled_w, t_y + offset_y + scaled_h),
                        radius=int(BUBBLE_RADIUS * t_scale),
                        fill=SENT_COLOR
                    )
                    
                    # Animated dots
                    if t_scale > 0.5:
                        for dot_i in range(3):
                            dot_x = t_x + 20 + dot_i * 20
                            dot_y = t_y + t_h // 2
                            phase = (current_time * 5 + dot_i * 0.3) % 1.0
                            dot_r = int(5 * (0.6 + 0.4 * math.sin(phase * math.pi)))
                            if dot_r > 0:
                                draw.ellipse(
                                    (dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r),
                                    fill=TEXT_COLOR
                                )
                continue
            
            # === Message bubble ===
            if current_time < md["appear_time"]:
                continue
            
            time_since = current_time - md["appear_time"]
            anim_dur = 0.35
            
            # Animation progress
            if time_since < anim_dur:
                prog = time_since / anim_dur
                # Smooth ease out
                prog = 1 - (1 - prog) ** 3
                opacity = int(255 * min(1.0, prog * 1.5))
                
                # Slide from side
                if is_left:
                    slide_x = int(-100 * (1 - prog))
                else:
                    slide_x = int(100 * (1 - prog))
                
                # Scale
                scale = 0.7 + 0.3 * prog
            else:
                opacity = 255
                slide_x = 0
                scale = 1.0
            
            if opacity < 10:
                continue
            
            # Calculate final bubble position
            bx = md["bubble_x"] + slide_x
            by = screen_y
            bw = md["bubble_w"]
            bh = md["bubble_h"]
            
            # Apply scale from bottom-corner
            scaled_w = int(bw * scale)
            scaled_h = int(bh * scale)
            
            if is_left:
                final_x = bx
            else:
                final_x = bx + (bw - scaled_w)
            final_y = by + (bh - scaled_h)
            
            # Draw bubble
            bubble_color = RECEIVED_COLOR if is_left else SENT_COLOR
            
            # Shadow
            shadow_offset = 3
            draw.rounded_rectangle(
                (final_x + shadow_offset, final_y + shadow_offset,
                 final_x + scaled_w + shadow_offset, final_y + scaled_h + shadow_offset),
                radius=int(BUBBLE_RADIUS * scale),
                fill=(0, 0, 0, 50)
            )
            
            # Main bubble
            draw.rounded_rectangle(
                (final_x, final_y, final_x + scaled_w, final_y + scaled_h),
                radius=int(BUBBLE_RADIUS * scale),
                fill=bubble_color + (opacity,)
            )
            
            # Draw tail
            tail_size = int(12 * scale)
            if is_left:
                tail_pts = [
                    (final_x + 8, final_y + scaled_h - 8),
                    (final_x - tail_size + 2, final_y + scaled_h + tail_size - 5),
                    (final_x + 20, final_y + scaled_h - 2)
                ]
            else:
                tail_pts = [
                    (final_x + scaled_w - 8, final_y + scaled_h - 8),
                    (final_x + scaled_w + tail_size - 2, final_y + scaled_h + tail_size - 5),
                    (final_x + scaled_w - 20, final_y + scaled_h - 2)
                ]
            draw.polygon(tail_pts, fill=bubble_color + (opacity,))
            
            # Draw text
            if scale > 0.5:
                text_alpha = int(opacity * min(1.0, (scale - 0.5) / 0.5))
                text_x = final_x + int(BUBBLE_H_PAD * scale)
                text_y = final_y + int(BUBBLE_V_PAD * scale)
                
                for line in md["lines"]:
                    draw.text(
                        (text_x, text_y),
                        line,
                        fill=TEXT_COLOR + (text_alpha,),
                        font=font_msg
                    )
                    text_y += int(40 * scale)
            
            # "Read" indicator
            if not is_left and time_since > 0.6:
                is_last_sent = True
                for j in range(i + 1, len(message_data)):
                    if not message_data[j]["is_left"] and current_time >= message_data[j]["appear_time"]:
                        is_last_sent = False
                        break
                
                if is_last_sent:
                    read_alpha = int(255 * min(1.0, (time_since - 0.6) / 0.3))
                    read_text = "Read"
                    r_bbox = draw.textbbox((0, 0), read_text, font=font_read)
                    r_w = r_bbox[2] - r_bbox[0]
                    r_x = final_x + scaled_w - r_w
                    r_y = final_y + scaled_h + 8
                    draw.text((r_x, r_y), read_text, fill=READ_COLOR + (read_alpha,), font=font_read)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
        img.save(frame_path, "PNG", optimize=False)
        
        if frame_idx % 60 == 0:
            logger.info(f"Frame {frame_idx}/{total_frames}")
    
    # Compile to video - high quality
    logger.info("Compiling HQ video...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(RENDER_FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",  # Higher quality
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
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
        logger.info(f"Created HQ chat animation: {output_file}")
        return output_file
    
    logger.error("Chat animation failed")
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
