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
    Render iMessage-style chat animation - EXACT replica.
    
    Key behaviors from analysis:
    - 2-3 messages visible at a time in bottom half of screen
    - New message: scale up from bottom + fade in (200-300ms, ease-out)
    - Old messages: slide up smoothly (NO fade)
    - View is FIXED - messages scroll up within it
    - Messages compact, close together
    - Typing indicator below last received message
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # High quality settings
    W = 1080
    H = 1920
    FPS = 30
    
    # Colors - exact iMessage
    BG_COLOR = (0, 0, 0)
    SENT_COLOR = (50, 50, 52)  # Dark gray - LEFT side (we send)
    RECEIVED_COLOR = (0, 122, 255)  # Blue - RIGHT side (they send)
    TEXT_COLOR = (255, 255, 255)
    READ_COLOR = (130, 130, 134)
    
    # Layout - compact messages in bottom half
    PADDING = 24
    BUBBLE_H_PAD = 16
    BUBBLE_V_PAD = 10
    MAX_BUBBLE_W = int(W * 0.72)
    BUBBLE_RADIUS = 18
    MSG_GAP = 8  # Small gap between messages
    
    # Messages positioned in bottom portion of screen
    CHAT_BOTTOM = H - 120  # Bottom of chat area
    CHAT_TOP = H * 0.35  # Messages don't go above this
    
    participants = script_data.get("participants", [
        {"name": "Я", "side": "left"},  # We are on left (gray)
        {"name": "Собеседник", "side": "right"}  # They are on right (blue)
    ])
    messages = script_data.get("messages", [])
    
    # Font
    try:
        font_msg = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 30)
        font_read = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 14)
    except:
        font_msg = ImageFont.load_default()
        font_read = ImageFont.load_default()
    
    # Pre-calculate message layouts
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    
    message_data = []
    
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
            if bbox[2] - bbox[0] <= MAX_BUBBLE_W - BUBBLE_H_PAD * 2:
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
        line_h = 38
        max_w = 0
        for line in lines:
            bbox = temp_draw.textbbox((0, 0), line, font=font_msg)
            max_w = max(max_w, bbox[2] - bbox[0])
        
        bubble_w = max_w + BUBBLE_H_PAD * 2
        bubble_h = len(lines) * line_h + BUBBLE_V_PAD * 2
        
        message_data.append({
            "text": text,
            "lines": lines,
            "is_left": is_left,
            "bubble_w": bubble_w,
            "bubble_h": bubble_h,
            "typing_duration": msg.get("typing_duration", 1.2) if not is_left else 0,
            "delay": msg.get("delay", 2.0)
        })
    
    # Calculate timeline
    time_cursor = 0.8
    for md in message_data:
        md["typing_start"] = time_cursor
        md["typing_end"] = md["typing_start"] + md["typing_duration"]
        md["appear_time"] = md["typing_end"] + 0.1
        time_cursor = md["appear_time"] + md["delay"]
    
    total_duration = time_cursor + 2.0
    total_frames = int(total_duration * FPS)
    
    # Animation constants
    MSG_APPEAR_DURATION = 0.28  # 280ms for message to appear
    SCROLL_DURATION = 0.35  # How long old messages take to slide up
    
    logger.info(f"Rendering {total_frames} frames (exact iMessage style)...")
    
    for frame_idx in range(total_frames):
        current_time = frame_idx / FPS
        
        # Create frame
        img = Image.new('RGBA', (W, H), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Calculate scroll offset - how much to push messages up
        # Each new message pushes previous ones up
        scroll_offset = 0
        
        for i, md in enumerate(message_data):
            if current_time >= md["appear_time"]:
                time_since = current_time - md["appear_time"]
                # Smooth scroll animation
                scroll_progress = min(1.0, time_since / SCROLL_DURATION)
                scroll_progress = 1 - (1 - scroll_progress) ** 3  # ease-out
                
                # Add this message's height to scroll offset
                scroll_offset += (md["bubble_h"] + MSG_GAP + 20) * scroll_progress
        
        # Draw visible messages from bottom up
        current_y = CHAT_BOTTOM
        
        # First, figure out which messages are visible and their positions
        visible_messages = []
        
        for i in range(len(message_data) - 1, -1, -1):
            md = message_data[i]
            
            if current_time < md["appear_time"]:
                continue
            
            # This message's position (from bottom)
            msg_bottom_y = current_y
            
            # Calculate how much this message has been scrolled up
            msgs_after = 0
            for j in range(i + 1, len(message_data)):
                if current_time >= message_data[j]["appear_time"]:
                    time_since_next = current_time - message_data[j]["appear_time"]
                    scroll_prog = min(1.0, time_since_next / SCROLL_DURATION)
                    scroll_prog = 1 - (1 - scroll_prog) ** 3
                    msgs_after += (message_data[j]["bubble_h"] + MSG_GAP + 20) * scroll_prog
            
            final_y = msg_bottom_y - md["bubble_h"] - msgs_after
            
            # Skip if above visible area
            if final_y < CHAT_TOP - 100:
                continue
            
            visible_messages.append((i, md, final_y))
            current_y = final_y - MSG_GAP - 20
        
        # Draw messages (oldest first so newest is on top)
        for i, md, base_y in reversed(visible_messages):
            is_left = md["is_left"]
            time_since = current_time - md["appear_time"]
            
            # Appearance animation - scale from bottom + fade
            if time_since < MSG_APPEAR_DURATION:
                progress = time_since / MSG_APPEAR_DURATION
                # Ease-out cubic
                progress = 1 - (1 - progress) ** 3
                
                scale = 0.3 + 0.7 * progress
                opacity = int(255 * progress)
            else:
                scale = 1.0
                opacity = 255
            
            # Calculate bubble position
            bubble_w = md["bubble_w"]
            bubble_h = md["bubble_h"]
            
            # X position
            if is_left:
                bubble_x = PADDING
            else:
                bubble_x = W - PADDING - bubble_w
            
            # Y position with scale from bottom
            scaled_h = int(bubble_h * scale)
            scaled_w = int(bubble_w * scale)
            
            # Scale from bottom of bubble
            bubble_y = base_y + (bubble_h - scaled_h)
            
            if is_left:
                final_x = bubble_x
            else:
                final_x = W - PADDING - scaled_w
            
            bubble_color = SENT_COLOR if is_left else RECEIVED_COLOR
            
            # Draw shadow
            if opacity > 50:
                draw.rounded_rectangle(
                    (final_x + 2, bubble_y + 2, final_x + scaled_w + 2, bubble_y + scaled_h + 2),
                    radius=int(BUBBLE_RADIUS * scale),
                    fill=(0, 0, 0, int(40 * opacity / 255))
                )
            
            # Draw bubble
            draw.rounded_rectangle(
                (final_x, bubble_y, final_x + scaled_w, bubble_y + scaled_h),
                radius=int(BUBBLE_RADIUS * scale),
                fill=bubble_color + (opacity,)
            )
            
            # Draw tail
            if scale > 0.5:
                tail_size = int(10 * scale)
                tail_opacity = int(opacity * min(1.0, (scale - 0.5) / 0.5))
                
                if is_left:
                    # Tail on left bottom
                    tail_pts = [
                        (final_x + 6, bubble_y + scaled_h - 6),
                        (final_x - tail_size + 2, bubble_y + scaled_h + tail_size - 3),
                        (final_x + 18, bubble_y + scaled_h - 2)
                    ]
                else:
                    # Tail on right bottom
                    tail_pts = [
                        (final_x + scaled_w - 6, bubble_y + scaled_h - 6),
                        (final_x + scaled_w + tail_size - 2, bubble_y + scaled_h + tail_size - 3),
                        (final_x + scaled_w - 18, bubble_y + scaled_h - 2)
                    ]
                
                draw.polygon(tail_pts, fill=bubble_color + (tail_opacity,))
            
            # Draw text
            if scale > 0.4 and opacity > 50:
                text_opacity = int(opacity * min(1.0, (scale - 0.4) / 0.6))
                text_x = final_x + int(BUBBLE_H_PAD * scale)
                text_y = bubble_y + int(BUBBLE_V_PAD * scale)
                
                for line in md["lines"]:
                    draw.text(
                        (text_x, text_y),
                        line,
                        fill=TEXT_COLOR + (text_opacity,),
                        font=font_msg
                    )
                    text_y += int(38 * scale)
            
            # "Read" indicator for sent messages (left side)
            if is_left and scale == 1.0 and time_since > 0.5:
                # Only show on last visible sent message
                is_last_sent = True
                for j in range(i + 1, len(message_data)):
                    if message_data[j]["is_left"] and current_time >= message_data[j]["appear_time"]:
                        is_last_sent = False
                        break
                
                if is_last_sent:
                    read_alpha = int(255 * min(1.0, (time_since - 0.5) / 0.3))
                    read_text = "Read"
                    r_bbox = draw.textbbox((0, 0), read_text, font=font_read)
                    r_w = r_bbox[2] - r_bbox[0]
                    draw.text(
                        (final_x + scaled_w - r_w, bubble_y + scaled_h + 6),
                        read_text,
                        fill=READ_COLOR + (read_alpha,),
                        font=font_read
                    )
        
        # Draw typing indicator
        for i, md in enumerate(message_data):
            if not md["is_left"] and md["typing_start"] <= current_time < md["typing_end"]:
                typing_progress = (current_time - md["typing_start"]) / max(0.01, md["typing_duration"])
                
                # Position: below last visible message
                typing_y = CHAT_BOTTOM - 60
                typing_x = W - PADDING - 80
                
                # Scale in animation
                t_scale = min(1.0, typing_progress * 4) if typing_progress < 0.25 else 1.0
                t_scale = 1 - (1 - t_scale) ** 3
                
                if t_scale > 0.1:
                    t_w = int(75 * t_scale)
                    t_h = int(42 * t_scale)
                    
                    # Draw typing bubble
                    draw.rounded_rectangle(
                        (typing_x, typing_y, typing_x + t_w, typing_y + t_h),
                        radius=int(BUBBLE_RADIUS * t_scale),
                        fill=RECEIVED_COLOR
                    )
                    
                    # Animated dots
                    if t_scale > 0.5:
                        for dot_i in range(3):
                            dot_x = typing_x + 18 + dot_i * 18
                            dot_y = typing_y + t_h // 2
                            
                            # Sequential pulse animation
                            phase = (current_time * 4 + dot_i * 0.33) % 1.0
                            dot_r = int(5 * (0.5 + 0.5 * math.sin(phase * math.pi)))
                            
                            if dot_r > 0:
                                draw.ellipse(
                                    (dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r),
                                    fill=TEXT_COLOR
                                )
                break
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
        img.save(frame_path, "PNG", optimize=False)
        
        if frame_idx % 60 == 0:
            logger.info(f"Frame {frame_idx}/{total_frames}")
    
    # Compile to high quality video
    logger.info("Compiling HQ video...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "17",
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
        logger.info(f"Created exact iMessage animation: {output_file}")
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
        
        # Check for gradient colors
        gradient_colors = phrase.get("gradient_colors")
        
        if gradient_colors and len(gradient_colors) >= 2 and opacity > 0:
            # Render gradient text
            try:
                color1 = hex_to_rgb(gradient_colors[0])
                color2 = hex_to_rgb(gradient_colors[1])
                
                # Create gradient text by drawing character by character with interpolated colors
                text_img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
                text_draw = ImageDraw.Draw(text_img)
                
                char_x = text_x
                for i, char in enumerate(text):
                    # Interpolate color based on position
                    t = i / max(len(text) - 1, 1)
                    r = int(color1[0] + (color2[0] - color1[0]) * t)
                    g = int(color1[1] + (color2[1] - color1[1]) * t)
                    b = int(color1[2] + (color2[2] - color1[2]) * t)
                    
                    char_color = (r, g, b, opacity)
                    text_draw.text((char_x, text_y), char, fill=char_color, font=font_large)
                    
                    # Move to next character position
                    char_bbox = text_draw.textbbox((0, 0), char, font=font_large)
                    char_x += char_bbox[2] - char_bbox[0]
                
                img = Image.alpha_composite(img.convert('RGBA'), text_img).convert('RGB')
            except Exception as e:
                # Fallback to regular text
                draw.text((text_x, text_y), text, fill=text_color, font=font_large)
        elif opacity < 255:
            # Apply opacity by creating overlay
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


# ==================== PRODUCT ADVERTISEMENT ====================

async def render_product_advertisement(
    script_data: dict,
    output_path: Path,
    product_images: List[Path] = None,
    logo_path: Path = None
) -> Optional[Path]:
    """
    Render professional product advertisement video like Apple MacBook Neo ads.
    
    Structure:
    1. Product shots (with optional hands) - from uploaded or AI-generated images
    2. Multiple angles with smooth transitions
    3. Brand reveal with logo + gradient text
    4. Optional tagline fade-in
    
    Key visual features:
    - Pure white background
    - High-quality product images
    - Smooth zoom/pan camera movements
    - Apple-style text reveal with gradient
    """
    output_file = output_path / f"product_ad_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # High quality settings (1080x1920 for 9:16)
    W = 1080
    H = 1920
    FPS = 30
    
    # Colors
    BG_COLOR = (255, 255, 255)  # Pure white
    TEXT_COLOR = (0, 0, 0)  # Black text
    
    scenes = script_data.get("scenes", [])
    brand_name = script_data.get("brand_name", "Brand")
    product_name = script_data.get("product_name", "Product")
    tagline = script_data.get("tagline", "")
    
    # Calculate total duration
    total_duration = sum(s.get("duration", 1.5) for s in scenes) + 1.0  # +1s for outro
    total_frames = int(total_duration * FPS)
    
    # Fonts
    try:
        font_brand = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 72)
        font_product = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 56)
        font_tagline = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 24)
    except:
        font_brand = ImageFont.load_default()
        font_product = ImageFont.load_default()
        font_tagline = ImageFont.load_default()
    
    # Pre-calculate scene timings
    scene_timings = []
    current_time = 0
    for scene in scenes:
        duration = scene.get("duration", 1.5)
        scene_timings.append({
            "start": current_time,
            "end": current_time + duration,
            "duration": duration,
            **scene
        })
        current_time += duration
    
    # Transition duration between scenes
    TRANSITION_DURATION = 0.3
    
    logger.info(f"Rendering {total_frames} frames for product advertisement...")
    
    for frame_idx in range(total_frames):
        current_time = frame_idx / FPS
        
        # Create frame with white background
        img = Image.new('RGBA', (W, H), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Find active scene
        active_scene = None
        scene_progress = 0
        next_scene = None
        transition_progress = 0
        
        for i, st in enumerate(scene_timings):
            if st["start"] <= current_time < st["end"]:
                active_scene = st
                scene_progress = (current_time - st["start"]) / st["duration"]
                
                # Check if we're in transition to next scene
                time_to_end = st["end"] - current_time
                if time_to_end < TRANSITION_DURATION and i < len(scene_timings) - 1:
                    next_scene = scene_timings[i + 1]
                    transition_progress = 1 - (time_to_end / TRANSITION_DURATION)
                break
        
        if not active_scene:
            # We're past all scenes - show final brand frame
            active_scene = scene_timings[-1] if scene_timings else None
            scene_progress = 1.0
        
        if active_scene:
            text_overlay = active_scene.get("text_overlay")
            
            if text_overlay:
                # Brand reveal scene
                render_brand_reveal(
                    draw, img, W, H,
                    text_overlay.get("brand_name", brand_name),
                    text_overlay.get("product_name", product_name),
                    scene_progress,
                    font_brand, font_product,
                    text_overlay.get("gradient_colors", ["#00ff00", "#ffffff"]),
                    logo_path
                )
            else:
                # Product image scene
                # For now, render a placeholder product visualization
                # In production, this would load actual product images
                image_prompt = active_scene.get("image_prompt", "")
                camera_movement = active_scene.get("camera_movement", "static")
                needs_hands = active_scene.get("needs_hands", False)
                
                render_product_scene(
                    draw, img, W, H,
                    scene_progress,
                    camera_movement,
                    product_images,
                    active_scene.get("scene_number", 1) - 1  # 0-indexed
                )
        
        # Draw tagline if we're near the end
        if tagline and current_time > total_duration - 1.5:
            tagline_progress = min(1.0, (current_time - (total_duration - 1.5)) / 0.5)
            tagline_progress = ease_out_cubic(tagline_progress)
            tagline_opacity = int(180 * tagline_progress)
            
            tagline_bbox = draw.textbbox((0, 0), tagline, font=font_tagline)
            tagline_width = tagline_bbox[2] - tagline_bbox[0]
            tagline_x = (W - tagline_width) // 2
            tagline_y = H - 150
            
            draw.text(
                (tagline_x, tagline_y),
                tagline,
                fill=(100, 100, 100, tagline_opacity),
                font=font_tagline
            )
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_idx:05d}.png"
        img.save(frame_path, "PNG")
        
        if frame_idx % 60 == 0:
            logger.info(f"Frame {frame_idx}/{total_frames}")
    
    # Compile to high quality video
    logger.info("Compiling product advertisement video...")
    
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "17",
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
        logger.info(f"Created product advertisement: {output_file}")
        return output_file
    
    return None


def render_brand_reveal(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    W: int, H: int,
    brand_name: str,
    product_name: str,
    progress: float,
    font_brand: ImageFont.FreeTypeFont,
    font_product: ImageFont.FreeTypeFont,
    gradient_colors: List[str],
    logo_path: Path = None
):
    """
    Render the brand reveal scene with Apple-style animation.
    - Logo appears first (if provided)
    - Logo slides left, brand name appears to the right
    - Product name fades in with gradient effect
    """
    center_x = W // 2
    center_y = H // 2 - 50
    
    # Animation phases
    logo_appear_end = 0.3
    logo_slide_start = 0.3
    logo_slide_end = 0.5
    text_appear_start = 0.4
    text_appear_end = 0.7
    product_appear_start = 0.6
    
    # Calculate brand name dimensions
    brand_bbox = draw.textbbox((0, 0), brand_name, font=font_brand)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_height = brand_bbox[3] - brand_bbox[1]
    
    # Logo settings
    logo_size = 80
    gap = 30
    
    # Final positions (logo left, text right, centered together)
    total_width = logo_size * 2 + gap + brand_width
    final_logo_x = (W - total_width) // 2 + logo_size
    final_text_x = final_logo_x + logo_size + gap
    
    # Phase 1: Logo appears in center
    logo_x = center_x
    logo_scale = 0
    logo_opacity = 0
    
    if progress < logo_appear_end:
        # Logo appearing
        p = progress / logo_appear_end
        p = ease_out_cubic(p)
        logo_scale = p
        logo_opacity = int(255 * p)
    elif progress < logo_slide_end:
        # Logo sliding to final position
        p = (progress - logo_slide_start) / (logo_slide_end - logo_slide_start)
        p = ease_out_cubic(max(0, min(1, p)))
        logo_x = center_x + (final_logo_x - center_x) * p
        logo_scale = 1.0
        logo_opacity = 255
    else:
        # Logo at final position
        logo_x = final_logo_x
        logo_scale = 1.0
        logo_opacity = 255
    
    # Draw logo (circle placeholder or actual logo)
    if logo_scale > 0:
        scaled_size = int(logo_size * logo_scale)
        
        # Draw Apple-style logo circle
        if logo_path and logo_path.exists():
            # Load and draw actual logo
            try:
                logo_img = Image.open(logo_path).convert('RGBA')
                logo_img = logo_img.resize((scaled_size * 2, scaled_size * 2), Image.Resampling.LANCZOS)
                # Center logo
                paste_x = int(logo_x) - scaled_size
                paste_y = center_y - scaled_size
                img.paste(logo_img, (paste_x, paste_y), logo_img)
            except Exception as e:
                logger.warning(f"Failed to load logo: {e}")
                # Fallback to circle
                draw.ellipse(
                    (int(logo_x) - scaled_size, center_y - scaled_size,
                     int(logo_x) + scaled_size, center_y + scaled_size),
                    fill=(0, 0, 0, logo_opacity)
                )
        else:
            # Draw placeholder circle logo
            draw.ellipse(
                (int(logo_x) - scaled_size, center_y - scaled_size,
                 int(logo_x) + scaled_size, center_y + scaled_size),
                fill=(0, 0, 0, logo_opacity)
            )
    
    # Phase 2: Brand name appears
    if progress >= text_appear_start:
        text_p = min(1.0, (progress - text_appear_start) / (text_appear_end - text_appear_start))
        text_p = ease_out_cubic(text_p)
        text_opacity = int(255 * text_p)
        text_y_offset = int(20 * (1 - text_p))
        
        text_y = center_y - brand_height // 2 + text_y_offset
        draw.text(
            (final_text_x, text_y),
            brand_name,
            fill=(0, 0, 0, text_opacity),
            font=font_brand
        )
    
    # Phase 3: Product name with gradient effect
    if progress >= product_appear_start:
        prod_p = min(1.0, (progress - product_appear_start) / (1.0 - product_appear_start))
        prod_p = ease_out_cubic(prod_p)
        
        # Calculate product name position (below brand name)
        prod_bbox = draw.textbbox((0, 0), product_name, font=font_product)
        prod_width = prod_bbox[2] - prod_bbox[0]
        prod_x = (W - prod_width) // 2
        prod_y = center_y + logo_size + 40
        
        # Create gradient text effect
        if len(gradient_colors) >= 2:
            # Parse gradient colors
            try:
                color1 = hex_to_rgb(gradient_colors[0])
                color2 = hex_to_rgb(gradient_colors[1])
                
                # Interpolate colors based on progress
                r = int(color1[0] + (color2[0] - color1[0]) * prod_p)
                g = int(color1[1] + (color2[1] - color1[1]) * prod_p)
                b = int(color1[2] + (color2[2] - color1[2]) * prod_p)
                
                prod_opacity = int(255 * prod_p)
                prod_y_offset = int(15 * (1 - prod_p))
                
                draw.text(
                    (prod_x, prod_y + prod_y_offset),
                    product_name,
                    fill=(r, g, b, prod_opacity),
                    font=font_product
                )
            except:
                draw.text(
                    (prod_x, prod_y),
                    product_name,
                    fill=(0, 0, 0, int(255 * prod_p)),
                    font=font_product
                )
        else:
            draw.text(
                (prod_x, prod_y),
                product_name,
                fill=(0, 0, 0, int(255 * prod_p)),
                font=font_product
            )


def render_product_scene(
    draw: ImageDraw.ImageDraw,
    img: Image.Image,
    W: int, H: int,
    progress: float,
    camera_movement: str,
    product_images: List[Path] = None,
    scene_index: int = 0
):
    """
    Render a product scene with camera movement.
    Uses uploaded images if available, otherwise draws a placeholder.
    """
    # If we have product images, use them
    if product_images and len(product_images) > scene_index:
        try:
            prod_img_path = product_images[scene_index]
            if prod_img_path.exists():
                prod_img = Image.open(prod_img_path).convert('RGBA')
                
                # Apply camera movement
                if camera_movement == "subtle_zoom_in":
                    # Zoom from 95% to 100%
                    scale = 0.95 + 0.05 * ease_out_cubic(progress)
                elif camera_movement == "subtle_zoom_out":
                    scale = 1.0 - 0.05 * ease_out_cubic(progress)
                else:
                    scale = 1.0
                
                # Scale image
                new_w = int(W * scale)
                new_h = int(H * scale)
                prod_img = prod_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Center and crop
                paste_x = (W - new_w) // 2
                paste_y = (H - new_h) // 2
                
                # Create composite
                temp = Image.new('RGBA', (W, H), (255, 255, 255, 255))
                temp.paste(prod_img, (paste_x, paste_y), prod_img if prod_img.mode == 'RGBA' else None)
                img.paste(temp, (0, 0))
                return
        except Exception as e:
            logger.warning(f"Failed to load product image: {e}")
    
    # Fallback: Draw placeholder product visualization
    center_x = W // 2
    center_y = H // 2
    
    # Apply camera movement to placeholder
    if camera_movement == "subtle_zoom_in":
        scale = 0.9 + 0.1 * ease_out_cubic(progress)
    elif camera_movement == "subtle_zoom_out":
        scale = 1.0 - 0.1 * ease_out_cubic(progress)
    else:
        scale = 1.0
    
    # Draw a stylized product placeholder (rounded rectangle like a device)
    product_w = int(400 * scale)
    product_h = int(280 * scale)
    
    x1 = center_x - product_w // 2
    y1 = center_y - product_h // 2
    x2 = center_x + product_w // 2
    y2 = center_y + product_h // 2
    
    # Shadow
    draw.rounded_rectangle(
        (x1 + 8, y1 + 8, x2 + 8, y2 + 8),
        radius=20,
        fill=(200, 200, 200, 100)
    )
    
    # Main product shape
    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=20,
        fill=(80, 80, 80, 255)
    )
    
    # Screen area
    screen_padding = 15
    draw.rounded_rectangle(
        (x1 + screen_padding, y1 + screen_padding, 
         x2 - screen_padding, y2 - screen_padding),
        radius=10,
        fill=(40, 40, 40, 255)
    )
    
    # Subtle screen glow
    glow_size = int(5 * scale)
    for i in range(3):
        alpha = 30 - i * 10
        draw.rounded_rectangle(
            (x1 + screen_padding - i, y1 + screen_padding - i,
             x2 - screen_padding + i, y2 - screen_padding + i),
            radius=10 + i,
            outline=(100, 150, 255, alpha)
        )
