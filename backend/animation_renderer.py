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
import random
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


# ==================== CHAT ANIMATION (iMessage Style + Dynamic Effects) ====================

async def render_chat_animation(
    script_data: dict,
    output_path: Path
) -> Optional[Path]:
    """
    Render iMessage-style chat animation with dynamic effects.
    
    Based on analysis of example videos:
    - Messages: scale-up + fade-in (NOT slide)
    - Dark background with soft shadows
    - Scrolling upward when new messages appear
    - OVERLAY EFFECTS: falling money, emojis, memes appearing
    - Reactions/stickers appearing next to messages
    """
    output_file = output_path / f"chat_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # High quality settings
    W = 1080
    H = 1920
    FPS = 30
    
    # Colors - dark chat style (from analysis)
    BG_COLOR = (18, 18, 20)  # Very dark, almost black
    SENT_COLOR = (58, 58, 62)  # Dark gray with subtle gradient feel
    RECEIVED_COLOR = (0, 122, 255)  # Blue for received
    TEXT_COLOR = (255, 255, 255)
    READ_COLOR = (130, 130, 134)
    
    # Layout - compact messages in bottom portion
    PADDING = 28
    BUBBLE_H_PAD = 18
    BUBBLE_V_PAD = 12
    MAX_BUBBLE_W = int(W * 0.70)
    BUBBLE_RADIUS = 20
    MSG_GAP = 12
    
    # Messages positioned in bottom 60% of screen
    CHAT_BOTTOM = H - 150
    CHAT_TOP = H * 0.3
    
    participants = script_data.get("participants", [
        {"name": "Я", "side": "left"},
        {"name": "Собеседник", "side": "right"}
    ])
    messages = script_data.get("messages", [])
    
    # Dynamic effects configuration
    overlay_effects = script_data.get("overlay_effects", [])
    # Default falling money effect if conversation is about money/buying
    if not overlay_effects:
        full_text = " ".join([m.get("text", "") for m in messages]).lower()
        if any(word in full_text for word in ["купить", "деньг", "плат", "цена", "buy", "money", "pay", "price", "$"]):
            overlay_effects = [{"type": "falling_money", "start": 0.5, "duration": 10.0}]
    
    # Font
    try:
        font_msg = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 32)
        font_read = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 14)
        font_emoji = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", 48)
    except:
        font_msg = ImageFont.load_default()
        font_read = ImageFont.load_default()
        font_emoji = ImageFont.load_default()
    
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
        line_h = 40
        max_w = 0
        for line in lines:
            bbox = temp_draw.textbbox((0, 0), line, font=font_msg)
            max_w = max(max_w, bbox[2] - bbox[0])
        
        bubble_w = max_w + BUBBLE_H_PAD * 2
        bubble_h = len(lines) * line_h + BUBBLE_V_PAD * 2
        
        # Reaction emoji (appears next to message)
        reaction = msg.get("reaction")  # e.g., "👀", "💰", "😱"
        
        message_data.append({
            "text": text,
            "lines": lines,
            "is_left": is_left,
            "bubble_w": bubble_w,
            "bubble_h": bubble_h,
            "typing_duration": msg.get("typing_duration", 1.0) if not is_left else 0,
            "delay": msg.get("delay", 1.8),
            "reaction": reaction
        })
    
    # Calculate timeline
    time_cursor = 0.6
    for md in message_data:
        md["typing_start"] = time_cursor
        md["typing_end"] = md["typing_start"] + md["typing_duration"]
        md["appear_time"] = md["typing_end"] + 0.05
        md["reaction_time"] = md["appear_time"] + 0.4  # Reaction appears 0.4s after message
        time_cursor = md["appear_time"] + md["delay"]
    
    total_duration = time_cursor + 2.0
    total_frames = int(total_duration * FPS)
    
    # Animation constants
    MSG_APPEAR_DURATION = 0.22  # 220ms - fast pop
    SCROLL_DURATION = 0.30
    REACTION_APPEAR_DURATION = 0.18
    
    # Pre-generate falling particles for overlay
    particles = []
    if any(e.get("type") == "falling_money" for e in overlay_effects):
        for i in range(30):
            particles.append({
                "x": (i * 73 + 100) % W,
                "y": -100 - i * 80,
                "speed": 180 + (i % 5) * 40,
                "rotation": i * 30,
                "rot_speed": 60 + (i % 3) * 30,
                "size": 50 + (i % 3) * 15
            })
    
    logger.info(f"Rendering {total_frames} frames (iMessage + dynamic effects)...")
    
    for frame_idx in range(total_frames):
        current_time = frame_idx / FPS
        
        # Create frame with dark background
        img = Image.new('RGBA', (W, H), BG_COLOR + (255,))
        draw = ImageDraw.Draw(img)
        
        # Calculate visible messages and their positions
        visible_messages = []
        current_y = CHAT_BOTTOM
        
        for i in range(len(message_data) - 1, -1, -1):
            md = message_data[i]
            
            if current_time < md["appear_time"]:
                continue
            
            # Calculate scroll offset from messages appearing after this one
            scroll_offset = 0
            for j in range(i + 1, len(message_data)):
                if current_time >= message_data[j]["appear_time"]:
                    time_since_next = current_time - message_data[j]["appear_time"]
                    scroll_prog = min(1.0, time_since_next / SCROLL_DURATION)
                    scroll_prog = 1 - (1 - scroll_prog) ** 3  # ease-out
                    scroll_offset += (message_data[j]["bubble_h"] + MSG_GAP + 24) * scroll_prog
            
            final_y = current_y - md["bubble_h"] - scroll_offset
            
            # Skip if above visible area
            if final_y < CHAT_TOP - 150:
                continue
            
            visible_messages.append((i, md, final_y))
            current_y = final_y - MSG_GAP - 24
        
        # Draw messages (oldest first)
        for i, md, base_y in reversed(visible_messages):
            is_left = md["is_left"]
            time_since = current_time - md["appear_time"]
            
            # Appearance animation - SCALE UP + FADE (like in example)
            if time_since < MSG_APPEAR_DURATION:
                progress = time_since / MSG_APPEAR_DURATION
                progress = 1 - (1 - progress) ** 3  # ease-out
                
                scale = 0.4 + 0.6 * progress
                opacity = int(255 * progress)
                # Slight bounce at end
                if progress > 0.7:
                    bounce = math.sin((progress - 0.7) / 0.3 * math.pi) * 0.03
                    scale += bounce
            else:
                scale = 1.0
                opacity = 255
            
            bubble_w = md["bubble_w"]
            bubble_h = md["bubble_h"]
            
            # X position
            if is_left:
                bubble_x = PADDING
            else:
                bubble_x = W - PADDING - bubble_w
            
            # Apply scale from center-bottom
            scaled_h = int(bubble_h * scale)
            scaled_w = int(bubble_w * scale)
            
            bubble_y = base_y + (bubble_h - scaled_h)
            
            if is_left:
                final_x = bubble_x
            else:
                final_x = W - PADDING - scaled_w
            
            bubble_color = SENT_COLOR if is_left else RECEIVED_COLOR
            
            # Soft shadow (like in example)
            if opacity > 50:
                for shadow_i in range(3):
                    shadow_alpha = int(25 * opacity / 255) - shadow_i * 7
                    if shadow_alpha > 0:
                        draw.rounded_rectangle(
                            (final_x + 3 + shadow_i, bubble_y + 3 + shadow_i, 
                             final_x + scaled_w + 3 + shadow_i, bubble_y + scaled_h + 3 + shadow_i),
                            radius=int(BUBBLE_RADIUS * scale),
                            fill=(0, 0, 0, shadow_alpha)
                        )
            
            # Draw bubble
            draw.rounded_rectangle(
                (final_x, bubble_y, final_x + scaled_w, bubble_y + scaled_h),
                radius=int(BUBBLE_RADIUS * scale),
                fill=bubble_color + (opacity,)
            )
            
            # Draw text
            if scale > 0.5 and opacity > 80:
                text_opacity = int(opacity * min(1.0, (scale - 0.5) / 0.5))
                text_x = final_x + int(BUBBLE_H_PAD * scale)
                text_y = bubble_y + int(BUBBLE_V_PAD * scale)
                
                scaled_font_size = int(32 * scale)
                try:
                    scaled_font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSans.ttf", max(12, scaled_font_size))
                except:
                    scaled_font = font_msg
                
                for line in md["lines"]:
                    draw.text(
                        (text_x, text_y),
                        line,
                        fill=TEXT_COLOR + (text_opacity,),
                        font=scaled_font
                    )
                    text_y += int(40 * scale)
            
            # Draw reaction emoji (appears next to message with pop animation)
            reaction = md.get("reaction")
            if reaction and current_time >= md.get("reaction_time", 999):
                reaction_since = current_time - md["reaction_time"]
                
                if reaction_since < REACTION_APPEAR_DURATION:
                    r_prog = reaction_since / REACTION_APPEAR_DURATION
                    r_prog = 1 - (1 - r_prog) ** 3
                    r_scale = 0.2 + 1.0 * r_prog
                    # Overshoot bounce
                    if r_prog > 0.6:
                        r_scale += math.sin((r_prog - 0.6) / 0.4 * math.pi) * 0.2
                    r_opacity = int(255 * r_prog)
                else:
                    r_scale = 1.0
                    r_opacity = 255
                
                # Position reaction to the side of message
                if is_left:
                    r_x = final_x + scaled_w + 12
                else:
                    r_x = final_x - 50
                r_y = bubble_y + scaled_h // 2 - 20
                
                # Draw reaction with scale
                r_size = int(40 * r_scale)
                draw.text(
                    (r_x, r_y),
                    reaction,
                    fill=(255, 255, 255, r_opacity),
                    font=font_emoji
                )
            
            # "Read" indicator
            if is_left and scale == 1.0 and time_since > 0.6:
                is_last_sent = all(
                    not message_data[j]["is_left"] or current_time < message_data[j]["appear_time"]
                    for j in range(i + 1, len(message_data))
                )
                
                if is_last_sent:
                    read_alpha = int(255 * min(1.0, (time_since - 0.6) / 0.3))
                    draw.text(
                        (final_x + scaled_w - 35, bubble_y + scaled_h + 6),
                        "Read",
                        fill=READ_COLOR + (read_alpha,),
                        font=font_read
                    )
        
        # Draw typing indicator
        for i, md in enumerate(message_data):
            if not md["is_left"] and md["typing_start"] <= current_time < md["typing_end"]:
                typing_progress = (current_time - md["typing_start"]) / max(0.01, md["typing_duration"])
                
                typing_y = CHAT_BOTTOM - 55
                typing_x = W - PADDING - 85
                
                t_scale = min(1.0, typing_progress * 5) if typing_progress < 0.2 else 1.0
                t_scale = 1 - (1 - t_scale) ** 3
                
                if t_scale > 0.1:
                    t_w = int(78 * t_scale)
                    t_h = int(44 * t_scale)
                    
                    draw.rounded_rectangle(
                        (typing_x, typing_y, typing_x + t_w, typing_y + t_h),
                        radius=int(BUBBLE_RADIUS * t_scale),
                        fill=RECEIVED_COLOR
                    )
                    
                    if t_scale > 0.5:
                        for dot_i in range(3):
                            dot_x = typing_x + 20 + dot_i * 16
                            dot_y = typing_y + t_h // 2
                            
                            phase = (current_time * 4.5 + dot_i * 0.35) % 1.0
                            dot_r = int(5 * (0.6 + 0.4 * math.sin(phase * math.pi)))
                            
                            if dot_r > 0:
                                draw.ellipse(
                                    (dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r),
                                    fill=TEXT_COLOR
                                )
                break
        
        # Draw overlay effects (falling money, emojis, etc.)
        for effect in overlay_effects:
            effect_start = effect.get("start", 0)
            effect_duration = effect.get("duration", 5.0)
            
            if effect_start <= current_time <= effect_start + effect_duration:
                effect_time = current_time - effect_start
                
                if effect.get("type") == "falling_money":
                    # Draw falling dollar signs / money symbols
                    for p in particles:
                        p_y = p["y"] + p["speed"] * effect_time
                        p_y = p_y % (H + 200) - 100  # Loop
                        
                        p_x = p["x"] + math.sin(effect_time * 0.5 + p["x"] * 0.01) * 30
                        p_rot = p["rotation"] + p["rot_speed"] * effect_time
                        
                        # Draw money symbol with glow
                        money_text = "$"
                        text_size = p["size"]
                        
                        # Glow effect
                        glow_color = (0, 200, 0, 60)
                        draw.text((int(p_x) - 2, int(p_y) - 2), money_text, fill=glow_color, font=font_emoji)
                        draw.text((int(p_x) + 2, int(p_y) + 2), money_text, fill=glow_color, font=font_emoji)
                        
                        # Main symbol
                        draw.text((int(p_x), int(p_y)), money_text, fill=(0, 255, 100, 200), font=font_emoji)
        
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
    
    Based on analysis of example:
    - Word-by-word reveal with fade-in + subtle scale up
    - Clean white/black backgrounds
    - Smooth transitions between phrases
    - Gradient text support (like MacBook Neo: blue→purple)
    - Underline for emphasis
    """
    output_file = output_path / f"apple_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_path / "frames"
    frames_dir.mkdir(exist_ok=True)
    
    # High quality settings
    W = 1080
    H = 1920
    FPS = 30
    
    phrases = script_data.get("phrases", [
        {"text": "Let's create", "bg": "white"},
        {"text": "Something amazing", "bg": "white"},
        {"text": "Just like Apple.", "bg": "black"},
    ])
    
    logger.info(f"Apple text animation - phrases received: {phrases}")
    
    # Timing configuration
    PHRASE_DURATION = 2.2  # Time per phrase
    WORD_APPEAR_DURATION = 0.15  # 150ms per word
    WORD_DELAY = 0.12  # Delay between words
    FADE_OUT_DURATION = 0.35
    
    total_duration = len(phrases) * PHRASE_DURATION + 1.0
    total_frames = int(total_duration * FPS)
    
    # Font - bold, large, modern
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf", 80)
    except:
        font_large = ImageFont.load_default()
    
    logger.info(f"Rendering {total_frames} frames for Apple text animation (word-by-word)...")
    
    for frame_num in range(total_frames):
        current_sec = frame_num / FPS
        
        # Determine which phrase is active
        phrase_idx = min(int(current_sec / PHRASE_DURATION), len(phrases) - 1)
        phrase = phrases[phrase_idx]
        
        time_in_phrase = current_sec - (phrase_idx * PHRASE_DURATION)
        
        # Background color
        bg_white = phrase.get("bg", "white") == "white"
        bg_color = (255, 255, 255) if bg_white else (0, 0, 0)
        default_text_color = (0, 0, 0) if bg_white else (255, 255, 255)
        
        img = Image.new('RGBA', (W, H), bg_color + (255,))
        draw = ImageDraw.Draw(img)
        
        text = phrase.get("text", "")
        words = text.split()
        
        # Check for gradient colors
        gradient_colors = phrase.get("gradient_colors")
        
        # Calculate total text width for centering
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        
        word_widths = []
        total_width = 0
        space_width = 20
        
        for i, word in enumerate(words):
            bbox = temp_draw.textbbox((0, 0), word, font=font_large)
            w = bbox[2] - bbox[0]
            word_widths.append(w)
            total_width += w
            if i < len(words) - 1:
                total_width += space_width
        
        text_bbox = temp_draw.textbbox((0, 0), text, font=font_large)
        text_height = text_bbox[3] - text_bbox[1]
        
        start_x = (W - total_width) // 2
        text_y = (H - text_height) // 2
        
        # Calculate fade out (at end of phrase)
        phrase_fade_out = 1.0
        if time_in_phrase > PHRASE_DURATION - FADE_OUT_DURATION:
            phrase_fade_out = (PHRASE_DURATION - time_in_phrase) / FADE_OUT_DURATION
            phrase_fade_out = max(0, phrase_fade_out)
        
        # Draw each word with staggered animation
        current_x = start_x
        
        for i, word in enumerate(words):
            # Calculate when this word should appear
            word_start_time = i * (WORD_APPEAR_DURATION + WORD_DELAY)
            word_time = time_in_phrase - word_start_time
            
            if word_time < 0:
                # Word hasn't appeared yet
                current_x += word_widths[i] + space_width
                continue
            
            # Word appearance animation
            if word_time < WORD_APPEAR_DURATION:
                progress = word_time / WORD_APPEAR_DURATION
                progress = 1 - (1 - progress) ** 3  # ease-out
                
                word_opacity = int(255 * progress * phrase_fade_out)
                word_scale = 0.85 + 0.15 * progress
                # Subtle upward movement
                y_offset = int(12 * (1 - progress))
            else:
                word_opacity = int(255 * phrase_fade_out)
                word_scale = 1.0
                y_offset = 0
            
            if word_opacity <= 0:
                current_x += word_widths[i] + space_width
                continue
            
            word_y = text_y + y_offset
            
            # Determine text color (gradient or solid)
            if gradient_colors and len(gradient_colors) >= 2:
                # Gradient text - color based on character position in whole phrase
                try:
                    color1 = hex_to_rgb(gradient_colors[0])
                    color2 = hex_to_rgb(gradient_colors[1])
                    
                    logger.info(f"Applying gradient: {gradient_colors} to word '{word}'")
                    
                    # For single word, use character position within that word
                    char_x = current_x
                    word_len = len(word)
                    
                    for ci, char in enumerate(word):
                        # Interpolate color based on position in word
                        t = ci / max(word_len - 1, 1)
                        
                        r = int(color1[0] + (color2[0] - color1[0]) * t)
                        g = int(color1[1] + (color2[1] - color1[1]) * t)
                        b = int(color1[2] + (color2[2] - color1[2]) * t)
                        
                        char_color = (r, g, b, word_opacity)
                        draw.text((char_x, word_y), char, fill=char_color, font=font_large)
                        
                        char_bbox = draw.textbbox((0, 0), char, font=font_large)
                        char_x += char_bbox[2] - char_bbox[0]
                except Exception as e:
                    logger.warning(f"Gradient rendering failed: {e}")
                    draw.text((current_x, word_y), word, fill=default_text_color + (word_opacity,), font=font_large)
            else:
                # Solid color
                draw.text((current_x, word_y), word, fill=default_text_color + (word_opacity,), font=font_large)
            
            current_x += word_widths[i] + space_width
        
        # Draw underline if specified
        underline_word = phrase.get("underline")
        if underline_word and phrase_fade_out > 0.5:
            # Find underline word position
            underline_start_time = len(words) * (WORD_APPEAR_DURATION + WORD_DELAY) + 0.2
            
            if time_in_phrase > underline_start_time:
                underline_progress = min(1.0, (time_in_phrase - underline_start_time) / 0.25)
                underline_progress = 1 - (1 - underline_progress) ** 3
                
                # Calculate underline position
                underline_y = text_y + text_height + 12
                underline_width = int(total_width * 0.5 * underline_progress)
                underline_x = (W - underline_width) // 2
                
                underline_opacity = int(200 * underline_progress * phrase_fade_out)
                
                draw.rectangle(
                    (underline_x, underline_y, underline_x + underline_width, underline_y + 5),
                    fill=default_text_color + (underline_opacity,)
                )
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        img.convert('RGB').save(frame_path, "PNG")
    
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
    output_path: Path,
    logo_image_path: Path = None
) -> Optional[Path]:
    """
    Render logo/brand animation.
    
    Animation sequence:
    1. Logo icon appears in center (fade + scale) - uses uploaded image if provided
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
    
    # Load uploaded logo image if provided
    logo_img = None
    if logo_image_path and logo_image_path.exists():
        try:
            logo_img = Image.open(logo_image_path).convert("RGBA")
            logger.info(f"Loaded logo image: {logo_image_path}")
        except Exception as e:
            logger.warning(f"Failed to load logo image: {e}")
            logo_img = None
    
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
        
        # Draw logo (uploaded image or circle with glow effect)
        if logo_scale > 0:
            scaled_size = int(logo_size * logo_scale)
            
            if logo_img is not None:
                # Use uploaded logo image
                logo_display_size = scaled_size * 2
                resized_logo = logo_img.resize(
                    (logo_display_size, logo_display_size),
                    Image.Resampling.LANCZOS
                )
                
                # Apply opacity
                if logo_opacity < 255:
                    alpha = resized_logo.split()[3] if resized_logo.mode == 'RGBA' else None
                    if alpha:
                        alpha = alpha.point(lambda p: int(p * logo_opacity / 255))
                        resized_logo.putalpha(alpha)
                
                # Center the logo
                paste_x = int(logo_x) - logo_display_size // 2
                paste_y = int(logo_y) - logo_display_size // 2
                
                # Paste logo onto frame
                img.paste(resized_logo, (paste_x, paste_y), resized_logo)
            else:
                # Fallback: Draw circle with glow effect
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
    brand_name = script_data.get("brand_name") or "Brand"
    product_name = script_data.get("product_name") or "Product"
    tagline = script_data.get("tagline") or ""
    
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
    # Ensure strings are not None
    brand_name = brand_name or "Brand"
    product_name = product_name or "Product"
    
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



# ==================== SPOTIFY/PRODUCT DEMO STYLE ====================

async def render_spotify_demo(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render Spotify/Product demo style video - SIMPLIFIED VERSION
    """
    from advanced_effects import create_gradient_background, GRADIENT_PRESETS
    
    output_path = output_dir / f"spotify_demo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Extract data
    brand_name = script_data.get("brand_name") or "Spotify"
    tagline = script_data.get("tagline") or "Music for everyone"
    brand_color = script_data.get("brand_color") or "#1DB954"
    
    # Simple gradient
    if brand_name and "spotify" in brand_name.lower():
        gradient_colors = ["#1DB954", "#121212"]
    else:
        gradient_colors = [brand_color, "#121212"]
    
    # Only 45 frames (1.5 sec at 30fps) for quick render
    total_frames = 45
    
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        
        # Create simple gradient background
        bg = Image.new("RGBA", (WIDTH, HEIGHT), (18, 18, 18, 255))
        draw = ImageDraw.Draw(bg)
        
        # Add gradient effect manually (simplified)
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(29 * (1-t) + 18 * t)
            g = int(185 * (1-t) + 18 * t)
            b = int(84 * (1-t) + 18 * t)
            draw.line([(0, y), (WIDTH, y)], fill=(r, g, b))
        
        # Brand name with fade in
        alpha = min(255, int(255 * progress * 2))
        font = get_font(64, bold=True)
        text_bbox = draw.textbbox((0, 0), brand_name, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_x = (WIDTH - text_w) // 2
        
        draw.text((text_x, HEIGHT // 2 - 80), brand_name, 
                 font=font, fill=(255, 255, 255, alpha))
        
        # Tagline
        if progress > 0.3:
            font_small = get_font(36)
            tag_bbox = draw.textbbox((0, 0), tagline, font=font_small)
            tag_w = tag_bbox[2] - tag_bbox[0]
            tag_x = (WIDTH - tag_w) // 2
            draw.text((tag_x, HEIGHT // 2 + 20), tagline, 
                     font=font_small, fill=(255, 255, 255, int(alpha * 0.8)))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.save(frame_path, "PNG")
    
    # Fast encode
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-framerate", "30",
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "30",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)
    
    # Cleanup
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    return str(output_path)


# ==================== SAAS/DASHBOARD DEMO STYLE ====================

async def render_saas_demo(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render SaaS/Dashboard demo style video
    Features:
    - Light gradient background
    - Animated cursor
    - Typewriter text effect
    - Dashboard cards with charts
    - Smooth scale/fade transitions
    """
    from advanced_effects import (
        create_gradient_background,
        ease_out_cubic,
        ease_out_back,
        GRADIENT_PRESETS
    )
    
    output_path = output_dir / f"saas_demo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Extract data
    headline = script_data.get("headline", "Build something amazing.")
    features = script_data.get("features", ["Track", "Analyze", "Grow"])
    accent_color = script_data.get("accent_color", "#6366F1")
    
    gradient_colors = script_data.get("gradient", GRADIENT_PRESETS["notion"])
    
    total_frames = 15 * 4  # 4 seconds at 15fps
    
    cursor_x, cursor_y = WIDTH // 2, HEIGHT // 2
    cursor_target_x, cursor_target_y = WIDTH // 2, HEIGHT // 2
    
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        
        # Create background
        bg = create_gradient_background(
            WIDTH, HEIGHT,
            gradient_colors,
            direction="diagonal",
            noise=0.005
        ).convert("RGBA")
        
        draw = ImageDraw.Draw(bg)
        
        # Phase 1: Typewriter headline (0-0.3)
        if progress < 0.3:
            type_progress = progress / 0.3
            visible_chars = int(len(headline) * type_progress)
            visible_text = headline[:visible_chars]
            
            font = get_font(56, bold=True)
            text_bbox = draw.textbbox((0, 0), visible_text, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_x = (WIDTH - text_w) // 2
            text_y = HEIGHT // 2 - 100
            
            draw.text((text_x, text_y), visible_text, 
                     font=font, fill=(30, 30, 30))
            
            # Cursor blink
            if frame_num % 30 < 15:
                cursor_offset = text_w + 5
                draw.rectangle(
                    (text_x + cursor_offset, text_y + 5, 
                     text_x + cursor_offset + 3, text_y + 55),
                    fill=(30, 30, 30)
                )
        
        # Phase 2: Dashboard cards appear (0.3-0.7)
        elif progress < 0.7:
            card_progress = (progress - 0.3) / 0.4
            
            # Keep headline
            font = get_font(42, bold=True)
            text_bbox = draw.textbbox((0, 0), headline, font=font)
            text_x = (WIDTH - (text_bbox[2] - text_bbox[0])) // 2
            draw.text((text_x, 80), headline, font=font, fill=(30, 30, 30))
            
            # Dashboard cards
            card_w, card_h = 280, 200
            cards_data = [
                {"value": "$12,543", "label": "Revenue", "change": "+12%"},
                {"value": "1,234", "label": "Users", "change": "+8%"},
                {"value": "89%", "label": "Conversion", "change": "+3%"}
            ]
            
            for i, card in enumerate(cards_data):
                # Staggered animation
                card_delay = i * 0.15
                if card_progress > card_delay:
                    local_progress = min(1, (card_progress - card_delay) / 0.3)
                    
                    # Card position with bounce
                    start_y = HEIGHT + 100
                    end_y = 250 + i * 60
                    card_y = int(start_y + (end_y - start_y) * ease_out_back(local_progress))
                    card_x = 60 + i * 220
                    
                    # Shadow
                    draw.rounded_rectangle(
                        (card_x + 5, card_y + 8, card_x + card_w + 5, card_y + card_h + 8),
                        radius=16,
                        fill=(0, 0, 0, 30)
                    )
                    
                    # Card
                    draw.rounded_rectangle(
                        (card_x, card_y, card_x + card_w, card_y + card_h),
                        radius=16,
                        fill=(255, 255, 255, 250)
                    )
                    
                    # Value
                    val_font = get_font(36, bold=True)
                    draw.text((card_x + 20, card_y + 20), card["value"], 
                             font=val_font, fill=(30, 30, 30))
                    
                    # Label
                    label_font = get_font(18)
                    draw.text((card_x + 20, card_y + 70), card["label"], 
                             font=label_font, fill=(100, 100, 100))
                    
                    # Change indicator
                    change_color = (34, 197, 94) if "+" in card["change"] else (239, 68, 68)
                    draw.text((card_x + 20, card_y + 100), card["change"], 
                             font=label_font, fill=change_color)
                    
                    # Mini chart
                    chart_y_base = card_y + card_h - 30
                    chart_x_base = card_x + 20
                    points = [random.randint(20, 50) for _ in range(8)]
                    for j in range(len(points) - 1):
                        x1 = chart_x_base + j * 30
                        y1 = chart_y_base - points[j]
                        x2 = chart_x_base + (j + 1) * 30
                        y2 = chart_y_base - points[j + 1]
                        draw.line([(x1, y1), (x2, y2)], 
                                 fill=hex_to_rgb(accent_color), width=2)
            
            # Animated cursor
            if card_progress > 0.5:
                cursor_target_x = 300
                cursor_target_y = 400
            cursor_x += (cursor_target_x - cursor_x) * 0.1
            cursor_y += (cursor_target_y - cursor_y) * 0.1
            
            # Draw cursor
            draw.polygon([
                (int(cursor_x), int(cursor_y)),
                (int(cursor_x), int(cursor_y) + 20),
                (int(cursor_x) + 6, int(cursor_y) + 16),
                (int(cursor_x) + 10, int(cursor_y) + 24),
                (int(cursor_x) + 14, int(cursor_y) + 22),
                (int(cursor_x) + 10, int(cursor_y) + 14),
                (int(cursor_x) + 16, int(cursor_y) + 14)
            ], fill=(30, 30, 30))
        
        # Phase 3: Features list (0.7-1.0)
        else:
            feat_progress = (progress - 0.7) / 0.3
            
            # Background stays
            # Features animate in
            font_feat = get_font(32, bold=True)
            
            for i, feat in enumerate(features):
                feat_delay = i * 0.2
                if feat_progress > feat_delay:
                    local_progress = min(1, (feat_progress - feat_delay) / 0.3)
                    
                    feat_x = int(-200 + (WIDTH // 2 - 50) * ease_out_cubic(local_progress))
                    feat_y = HEIGHT // 2 + i * 60
                    
                    # Bullet point
                    draw.ellipse(
                        (feat_x - 30, feat_y + 8, feat_x - 14, feat_y + 24),
                        fill=hex_to_rgb(accent_color)
                    )
                    
                    draw.text((feat_x, feat_y), feat, 
                             font=font_feat, fill=(30, 30, 30))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.save(frame_path)
    
    # Encode video
    import subprocess
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        str(output_path)
    ]
    
    subprocess.run(cmd, capture_output=True)
    
    # Cleanup
    import shutil
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    return str(output_path)
