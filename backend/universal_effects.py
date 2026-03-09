"""
UNIVERSAL EFFECTS SYSTEM
Динамическая система эффектов для AI видео-генерации
Текстовые эффекты, градиенты, сообщения, карточки
"""

import math
import random
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import logging
import asyncio

logger = logging.getLogger(__name__)

# Video dimensions (9:16 vertical)
WIDTH = 1080
HEIGHT = 1920


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get font with fallback"""
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


# =============================================================
# EASING FUNCTIONS
# =============================================================

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

def ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

def ease_out_bounce(t: float) -> float:
    n1 = 7.5625
    d1 = 2.75
    if t < 1 / d1:
        return n1 * t * t
    elif t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


# =============================================================
# GRADIENT BACKGROUNDS
# =============================================================

def create_gradient_background(
    width: int, 
    height: int, 
    colors: List[Tuple[int, int, int]],
    gradient_type: str = "linear",  # linear, radial, aurora
    time: float = 0.0,  # For animated gradients
    angle: float = 0.0  # For linear gradients
) -> Image.Image:
    """
    Create animated gradient background
    
    gradient_type:
    - linear: Top to bottom (or at angle)
    - radial: Center outward
    - aurora: Animated wavy aurora effect
    - diagonal: Corner to corner
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(30, 30, 30), (60, 60, 80)]
    
    if gradient_type == "aurora":
        return create_aurora_gradient(width, height, colors, time)
    
    elif gradient_type == "radial":
        # Radial gradient from center
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        # Draw in bands for performance
        num_bands = 50
        for i in range(num_bands, 0, -1):
            ratio = i / num_bands
            t = 1 - ratio
            
            r = int(colors[0][0] * (1 - t) + colors[-1][0] * t)
            g = int(colors[0][1] * (1 - t) + colors[-1][1] * t)
            b = int(colors[0][2] * (1 - t) + colors[-1][2] * t)
            
            radius = int(max_dist * ratio)
            draw.ellipse(
                (center_x - radius, center_y - radius, 
                 center_x + radius, center_y + radius),
                fill=(r, g, b)
            )
    
    elif gradient_type == "diagonal":
        # Diagonal gradient
        for y in range(height):
            for x in range(0, width, 4):  # Step for performance
                t = (x + y) / (width + height)
                
                r = int(colors[0][0] * (1 - t) + colors[-1][0] * t)
                g = int(colors[0][1] * (1 - t) + colors[-1][1] * t)
                b = int(colors[0][2] * (1 - t) + colors[-1][2] * t)
                
                draw.rectangle((x, y, x + 4, y + 1), fill=(r, g, b))
    
    else:  # linear (default)
        # Vertical linear gradient
        for y in range(height):
            t = y / height
            
            # Interpolate between colors
            r = int(colors[0][0] * (1 - t) + colors[-1][0] * t)
            g = int(colors[0][1] * (1 - t) + colors[-1][1] * t)
            b = int(colors[0][2] * (1 - t) + colors[-1][2] * t)
            
            draw.line((0, y, width, y), fill=(r, g, b))
    
    return img


def create_aurora_gradient(
    width: int, 
    height: int, 
    colors: List[Tuple[int, int, int]],
    time: float
) -> Image.Image:
    """
    Animated aurora/shimmer gradient effect
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(100, 50, 200), (50, 150, 255), (100, 255, 200)]
    
    # Render in horizontal bands for speed
    num_bands = 60
    band_height = height // num_bands
    
    for band_idx in range(num_bands):
        y_start = band_idx * band_height
        y_end = (band_idx + 1) * band_height
        
        # Normalized position
        ny = band_idx / num_bands
        
        # Animated waves
        wave1 = math.sin(ny * 4 + time * math.pi * 2) * 0.2
        wave2 = math.cos(ny * 3 + time * math.pi * 1.5) * 0.15
        wave3 = math.sin(ny * 5 + time * math.pi * 2.5) * 0.1
        
        # Combined position for color
        t = ny + wave1 + wave2 + wave3
        t = max(0, min(1, t))
        
        # Multi-color interpolation
        num_colors = len(colors)
        segment = t * (num_colors - 1)
        idx = int(segment)
        local_t = segment - idx
        
        if idx >= num_colors - 1:
            idx = num_colors - 2
            local_t = 1.0
        
        c1 = colors[idx]
        c2 = colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        draw.rectangle((0, y_start, width, y_end), fill=(r, g, b))
    
    # Soft blur for smooth effect
    img = img.filter(ImageFilter.GaussianBlur(radius=15))
    
    return img


# =============================================================
# TEXT EFFECTS
# =============================================================

def draw_text_popup(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    font_size: int = 72,
    color: Tuple[int, int, int] = (255, 255, 255),
    animation_progress: float = 1.0,
    effect: str = "scale_up"  # scale_up, slide_up, fade, bounce
) -> Image.Image:
    """
    Draw text with popup animation
    
    Effects:
    - scale_up: Scale from 0 to 100%
    - slide_up: Slide from bottom
    - fade: Fade in
    - bounce: Bounce in with overshoot
    - elastic: Elastic spring effect
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x, y = position
    
    # Apply animation
    if effect == "scale_up":
        scale = ease_out_back(animation_progress)
        actual_size = int(font_size * scale)
        alpha = int(255 * animation_progress)
    
    elif effect == "slide_up":
        offset = int((1 - ease_out_cubic(animation_progress)) * 200)
        y += offset
        actual_size = font_size
        alpha = int(255 * ease_out_cubic(animation_progress))
    
    elif effect == "bounce":
        scale = ease_out_bounce(animation_progress)
        actual_size = int(font_size * scale)
        alpha = 255
    
    elif effect == "elastic":
        scale = ease_out_elastic(animation_progress)
        actual_size = int(font_size * max(0.1, scale))
        alpha = 255
    
    else:  # fade
        actual_size = font_size
        alpha = int(255 * ease_out_cubic(animation_progress))
    
    if actual_size < 10:
        actual_size = 10
    
    font = get_font(actual_size, bold=True)
    
    # Center text at position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    draw_x = x - text_w // 2
    draw_y = y - text_h // 2
    
    # Draw shadow
    shadow_offset = max(2, actual_size // 20)
    draw.text((draw_x + shadow_offset, draw_y + shadow_offset), text, 
              font=font, fill=(0, 0, 0, alpha // 2))
    
    # Draw main text
    draw.text((draw_x, draw_y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_typewriter_text(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    font_size: int = 48,
    color: Tuple[int, int, int] = (255, 255, 255),
    chars_visible: int = 0,
    show_cursor: bool = True,
    cursor_blink: bool = True,
    frame: int = 0
) -> Image.Image:
    """
    Typewriter effect - text appears character by character
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=False)
    visible_text = text[:chars_visible]
    
    x, y = position
    
    # Draw visible text
    draw.text((x, y), visible_text, font=font, fill=(*color, 255))
    
    # Draw cursor
    if show_cursor:
        cursor_visible = True
        if cursor_blink:
            cursor_visible = (frame // 15) % 2 == 0
        
        if cursor_visible:
            bbox = draw.textbbox((x, y), visible_text, font=font)
            cursor_x = bbox[2] + 2
            cursor_h = font_size
            
            draw.rectangle(
                (cursor_x, y, cursor_x + 3, y + cursor_h),
                fill=(*color, 255)
            )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_word_by_word(
    img: Image.Image,
    words: List[str],
    position: Tuple[int, int],
    font_size: int = 64,
    color: Tuple[int, int, int] = (255, 255, 255),
    words_visible: int = 0,
    current_word_progress: float = 1.0,
    highlight_current: bool = True,
    highlight_color: Tuple[int, int, int] = (100, 200, 255)
) -> Image.Image:
    """
    Word by word animation - each word appears with effect
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    x, y = position
    current_x = x
    line_height = font_size + 20
    max_width = img.size[0] - x * 2
    
    for i, word in enumerate(words):
        if i >= words_visible:
            break
        
        # Check if word fits on current line
        bbox = draw.textbbox((0, 0), word + " ", font=font)
        word_width = bbox[2] - bbox[0]
        
        if current_x + word_width > x + max_width:
            current_x = x
            y += line_height
        
        # Determine color and animation
        if i == words_visible - 1 and highlight_current:
            # Current word - apply animation
            word_color = highlight_color
            scale = ease_out_back(current_word_progress)
            alpha = int(255 * current_word_progress)
            
            # Scale effect
            word_font = get_font(int(font_size * scale), bold=True)
            offset_y = int((1 - scale) * font_size / 2)
        else:
            word_color = color
            alpha = 255
            word_font = font
            offset_y = 0
        
        draw.text((current_x, y + offset_y), word, font=word_font, fill=(*word_color, alpha))
        
        # Move to next position
        bbox = draw.textbbox((0, 0), word + " ", font=font)
        current_x += bbox[2] - bbox[0]
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_gradient_text(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    font_size: int = 72,
    gradient_colors: List[Tuple[int, int, int]] = None,
    animation_progress: float = 1.0,
    shimmer_offset: float = 0.0  # For animated shimmer
) -> Image.Image:
    """
    Text with gradient fill and optional shimmer animation
    """
    if gradient_colors is None:
        gradient_colors = [(0, 150, 255), (150, 50, 255), (255, 50, 150)]
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    x, y = position
    
    # Get text dimensions
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Create gradient image
    gradient = Image.new("RGBA", (text_w + 20, text_h + 20))
    gradient_draw = ImageDraw.Draw(gradient)
    
    # Draw gradient
    num_colors = len(gradient_colors)
    for gx in range(text_w + 20):
        # Add shimmer offset for animation
        t = ((gx / (text_w + 20)) + shimmer_offset) % 1.0
        
        segment = t * (num_colors - 1)
        idx = int(segment)
        local_t = segment - idx
        
        if idx >= num_colors - 1:
            idx = num_colors - 2
            local_t = 1.0
        
        c1 = gradient_colors[idx]
        c2 = gradient_colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        gradient_draw.line((gx, 0, gx, text_h + 20), fill=(r, g, b, 255))
    
    # Create text mask
    mask = Image.new("L", (text_w + 20, text_h + 20), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10, 10), text, font=font, fill=255)
    
    # Apply mask to gradient
    gradient.putalpha(mask)
    
    # Apply animation
    alpha = int(255 * animation_progress)
    if alpha < 255:
        r, g, b, a = gradient.split()
        a = a.point(lambda p: int(p * animation_progress))
        gradient = Image.merge("RGBA", (r, g, b, a))
    
    # Paste onto layer
    layer.paste(gradient, (x - 10, y - 10), gradient)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# CHAT/MESSAGE BUBBLES
# =============================================================

def draw_chat_bubble(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    is_sender: bool = True,
    animation_progress: float = 1.0,
    style: str = "imessage",  # imessage, whatsapp, telegram, modern
    bubble_color: Tuple[int, int, int] = None,
    text_color: Tuple[int, int, int] = None
) -> Tuple[Image.Image, int]:
    """
    Draw chat bubble with animation
    Returns (image, bubble_height) for positioning next bubble
    
    Styles:
    - imessage: iOS blue/gray
    - whatsapp: WhatsApp green/white
    - telegram: Telegram blue/white
    - modern: Rounded modern style
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Style-specific colors
    if style == "imessage":
        if bubble_color is None:
            bubble_color = (0, 132, 255) if is_sender else (235, 235, 240)
        if text_color is None:
            text_color = (255, 255, 255) if is_sender else (0, 0, 0)
    elif style == "whatsapp":
        if bubble_color is None:
            bubble_color = (37, 211, 102) if is_sender else (255, 255, 255)
        if text_color is None:
            text_color = (255, 255, 255) if is_sender else (0, 0, 0)
    elif style == "telegram":
        if bubble_color is None:
            bubble_color = (58, 139, 216) if is_sender else (255, 255, 255)
        if text_color is None:
            text_color = (255, 255, 255) if is_sender else (0, 0, 0)
    else:  # modern
        if bubble_color is None:
            bubble_color = (100, 100, 255) if is_sender else (50, 50, 60)
        if text_color is None:
            text_color = (255, 255, 255)
    
    # Large, readable font
    font_size = 42
    font = get_font(font_size)
    
    # Wrap text
    max_width = int(img.size[0] * 0.7)
    lines = []
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
    line_height = font_size + 12
    padding_x = 32
    padding_y = 24
    
    text_height = len(lines) * line_height
    text_width = max((draw.textbbox((0, 0), line, font=font)[2] for line in lines), default=100)
    
    bubble_w = text_width + padding_x * 2
    bubble_h = text_height + padding_y * 2
    
    x, y = position
    
    # Animation
    if animation_progress < 1.0:
        eased = ease_out_back(animation_progress)
        scale = 0.3 + 0.7 * eased
        alpha = int(255 * eased)
        
        # Slide from side
        if is_sender:
            x += int((1 - eased) * 200)
        else:
            x -= int((1 - eased) * 200)
    else:
        scale = 1.0
        alpha = 255
    
    # Position based on sender
    if is_sender:
        bubble_x = img.size[0] - bubble_w - 40
    else:
        bubble_x = 40
    
    # Draw bubble shadow
    shadow_offset = 8
    draw.rounded_rectangle(
        (bubble_x + shadow_offset, y + shadow_offset, 
         bubble_x + bubble_w + shadow_offset, y + bubble_h + shadow_offset),
        radius=28,
        fill=(0, 0, 0, alpha // 4)
    )
    
    # Draw bubble
    draw.rounded_rectangle(
        (bubble_x, y, bubble_x + bubble_w, y + bubble_h),
        radius=28,
        fill=(*bubble_color, alpha)
    )
    
    # Draw tail
    tail_size = 16
    if is_sender:
        tail_x = bubble_x + bubble_w - 20
        tail_points = [
            (tail_x, y + bubble_h - 15),
            (tail_x + tail_size + 10, y + bubble_h + 8),
            (tail_x + 15, y + bubble_h)
        ]
    else:
        tail_x = bubble_x + 20
        tail_points = [
            (tail_x, y + bubble_h - 15),
            (tail_x - tail_size - 10, y + bubble_h + 8),
            (tail_x - 15, y + bubble_h)
        ]
    
    draw.polygon(tail_points, fill=(*bubble_color, alpha))
    
    # Draw text
    text_y = y + padding_y
    for line in lines:
        text_x = bubble_x + padding_x
        draw.text((text_x, text_y), line, font=font, fill=(*text_color, alpha))
        text_y += line_height
    
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result, bubble_h + 30  # Return height for positioning


def draw_typing_indicator(
    img: Image.Image,
    position: Tuple[int, int],
    frame: int,
    style: str = "imessage"
) -> Image.Image:
    """
    Animated typing indicator (three bouncing dots)
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x, y = position
    
    # Bubble style colors
    if style == "imessage":
        bubble_color = (235, 235, 240)
        dot_color = (150, 150, 155)
    else:
        bubble_color = (50, 50, 60)
        dot_color = (150, 150, 150)
    
    # Bubble
    bubble_w = 100
    bubble_h = 55
    
    draw.rounded_rectangle(
        (x, y, x + bubble_w, y + bubble_h),
        radius=25,
        fill=(*bubble_color, 255)
    )
    
    # Three animated dots
    dot_radius = 8
    dot_spacing = 22
    base_x = x + 25
    base_y = y + bubble_h // 2
    
    for i in range(3):
        phase = (frame * 0.2 + i * 0.5) % (math.pi * 2)
        bounce = math.sin(phase) * 8
        
        dot_x = base_x + i * dot_spacing
        dot_y = int(base_y + bounce)
        
        draw.ellipse(
            (dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius),
            fill=(*dot_color, 255)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# UI ELEMENTS
# =============================================================

def draw_card(
    img: Image.Image,
    position: Tuple[int, int],
    size: Tuple[int, int],
    content: Dict,  # {title, subtitle, icon_color}
    animation_progress: float = 1.0,
    style: str = "glass"  # glass, solid, gradient
) -> Image.Image:
    """
    Draw animated card element
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x, y = position
    w, h = size
    
    # Animation
    if animation_progress < 1.0:
        eased = ease_out_back(animation_progress)
        y_offset = int((1 - eased) * 150)
        y += y_offset
        alpha = int(230 * eased)
        scale = 0.8 + 0.2 * eased
    else:
        alpha = 230
        scale = 1.0
    
    # Background style
    if style == "glass":
        bg_color = (255, 255, 255, alpha // 4)
        border_color = (255, 255, 255, alpha // 2)
    elif style == "gradient":
        bg_color = (100, 100, 255, alpha)
        border_color = None
    else:  # solid
        bg_color = (40, 40, 50, alpha)
        border_color = None
    
    # Draw card
    draw.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=24,
        fill=bg_color,
        outline=border_color,
        width=2 if border_color else 0
    )
    
    # Content
    title = content.get("title", "")
    subtitle = content.get("subtitle", "")
    icon_color = content.get("icon_color", (100, 150, 255))
    
    # Icon circle
    icon_size = 60
    icon_x = x + 25
    icon_y = y + (h - icon_size) // 2
    draw.ellipse(
        (icon_x, icon_y, icon_x + icon_size, icon_y + icon_size),
        fill=(*icon_color, alpha)
    )
    
    # Title
    if title:
        font_title = get_font(28, bold=True)
        draw.text((icon_x + icon_size + 20, y + h // 2 - 25), title,
                 font=font_title, fill=(255, 255, 255, alpha))
    
    # Subtitle
    if subtitle:
        font_sub = get_font(20)
        draw.text((icon_x + icon_size + 20, y + h // 2 + 8), subtitle,
                 font=font_sub, fill=(180, 180, 180, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# MAIN RENDER FUNCTION
# =============================================================

async def render_universal_video(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Universal video renderer based on AI-generated script
    
    script_data format:
    {
        "background": {
            "type": "aurora" | "linear" | "radial" | "solid",
            "colors": [[r,g,b], [r,g,b], ...]
        },
        "elements": [
            {
                "type": "text" | "chat" | "card" | "gradient_text",
                "content": "...",
                "start_time": 0.0,
                "duration": 2.0,
                "effect": "scale_up" | "slide_up" | "typewriter" | "word_by_word",
                "position": "center" | "top" | "bottom" | [x, y],
                ...
            }
        ],
        "duration": 10.0
    }
    """
    output_path = output_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Parse script
    bg_config = script_data.get("background", {})
    bg_type = bg_config.get("type", "aurora")
    bg_colors = bg_config.get("colors", [[50, 50, 80], [100, 50, 150], [50, 100, 200]])
    bg_colors = [tuple(c) for c in bg_colors]
    
    elements = script_data.get("elements", [])
    total_duration = script_data.get("duration", 8.0)
    total_frames = int(fps * total_duration)
    
    logger.info(f"Rendering {total_frames} frames, duration: {total_duration}s")
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        progress = frame_num / total_frames
        
        # Create background
        if bg_type == "aurora":
            bg = create_aurora_gradient(WIDTH, HEIGHT, bg_colors, progress)
        else:
            bg = create_gradient_background(WIDTH, HEIGHT, bg_colors, bg_type, progress)
        
        bg = bg.convert("RGBA")
        
        # Render each element
        for elem in elements:
            elem_type = elem.get("type", "text")
            start_time = elem.get("start_time", 0)
            duration = elem.get("duration", 2.0)
            end_time = start_time + duration
            
            # Skip if not yet visible
            if time_sec < start_time:
                continue
            
            # Calculate animation progress
            anim_duration = elem.get("anim_duration", 0.5)
            if time_sec < start_time + anim_duration:
                anim_progress = (time_sec - start_time) / anim_duration
            else:
                anim_progress = 1.0
            
            # Fade out at end
            fade_duration = elem.get("fade_duration", 0.3)
            if time_sec > end_time - fade_duration:
                fade_progress = (end_time - time_sec) / fade_duration
                anim_progress = min(anim_progress, max(0, fade_progress))
            
            # Get position
            pos = elem.get("position", "center")
            if isinstance(pos, str):
                if pos == "center":
                    x, y = WIDTH // 2, HEIGHT // 2
                elif pos == "top":
                    x, y = WIDTH // 2, 200
                elif pos == "bottom":
                    x, y = WIDTH // 2, HEIGHT - 300
                else:
                    x, y = WIDTH // 2, HEIGHT // 2
            else:
                x, y = pos
            
            # Render element
            if elem_type == "text":
                content = elem.get("content", "")
                font_size = elem.get("font_size", 72)
                color = tuple(elem.get("color", [255, 255, 255]))
                effect = elem.get("effect", "scale_up")
                
                bg = draw_text_popup(bg, content, (x, y), font_size, color, anim_progress, effect)
            
            elif elem_type == "typewriter":
                content = elem.get("content", "")
                font_size = elem.get("font_size", 48)
                color = tuple(elem.get("color", [255, 255, 255]))
                
                # Calculate visible characters
                char_time = (time_sec - start_time) / max(0.1, duration - anim_duration)
                chars_visible = int(len(content) * min(1, char_time * 1.5))
                
                bg = draw_typewriter_text(bg, content, (100, y), font_size, color, 
                                         chars_visible, True, True, frame_num)
            
            elif elem_type == "word_by_word":
                content = elem.get("content", "")
                words = content.split()
                font_size = elem.get("font_size", 64)
                color = tuple(elem.get("color", [255, 255, 255]))
                highlight_color = tuple(elem.get("highlight_color", [100, 200, 255]))
                
                word_time = (time_sec - start_time) / max(0.1, duration)
                words_count = len(words)
                words_visible = int(words_count * min(1, word_time * 1.2)) + 1
                words_visible = min(words_visible, words_count)
                
                current_progress = (word_time * words_count) % 1.0
                
                bg = draw_word_by_word(bg, words, (100, y - 100), font_size, color,
                                      words_visible, current_progress, True, highlight_color)
            
            elif elem_type == "gradient_text":
                content = elem.get("content", "")
                font_size = elem.get("font_size", 72)
                gradient_colors = [tuple(c) for c in elem.get("gradient_colors", 
                                  [[0, 150, 255], [150, 50, 255], [255, 50, 150]])]
                
                shimmer = elem.get("shimmer", False)
                shimmer_offset = progress * 2 if shimmer else 0
                
                bg = draw_gradient_text(bg, content, (x - 200, y), font_size,
                                       gradient_colors, anim_progress, shimmer_offset)
            
            elif elem_type == "chat":
                messages = elem.get("messages", [])
                style = elem.get("style", "imessage")
                
                current_y = 250
                msg_time = (time_sec - start_time) / max(0.1, duration)
                msgs_to_show = int(len(messages) * min(1, msg_time * 1.3)) + 1
                
                for i, msg in enumerate(messages[:msgs_to_show]):
                    # Individual message animation
                    msg_start = start_time + (i / len(messages)) * duration * 0.7
                    if time_sec >= msg_start:
                        msg_progress = min(1.0, (time_sec - msg_start) / 0.4)
                    else:
                        continue
                    
                    # Show typing indicator before non-sender messages
                    if i < msgs_to_show - 1 or msg.get("sender", True):
                        bg, height = draw_chat_bubble(
                            bg,
                            msg.get("text", ""),
                            (0, current_y),
                            msg.get("sender", True),
                            msg_progress,
                            style
                        )
                        current_y += height
                    else:
                        # Show typing indicator
                        bg = draw_typing_indicator(bg, (40, current_y), frame_num, style)
            
            elif elem_type == "card":
                cards = elem.get("cards", [])
                
                card_y = 300
                for i, card in enumerate(cards):
                    card_start = start_time + i * 0.3
                    if time_sec >= card_start:
                        card_progress = min(1.0, (time_sec - card_start) / 0.5)
                        
                        bg = draw_card(
                            bg,
                            (60, card_y),
                            (WIDTH - 120, 120),
                            card,
                            card_progress
                        )
                        card_y += 150
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
        
        if frame_num % 30 == 0:
            logger.info(f"Rendered frame {frame_num}/{total_frames}")
    
    # Encode video with ffmpeg
    logger.info("Encoding video with ffmpeg...")
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
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        await asyncio.wait_for(process.communicate(), timeout=120)
    except asyncio.TimeoutError:
        process.kill()
        logger.error("Video encoding timed out")
    
    # Cleanup frames
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Video rendered: {output_path} ({output_path.stat().st_size} bytes)")
        return str(output_path)
    else:
        logger.error("Video encoding failed")
        return ""
