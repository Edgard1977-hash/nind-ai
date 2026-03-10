"""
PROFESSIONAL VIDEO EFFECTS SYSTEM v4
Based on analysis of real promo videos (Airbnb, Notion, Cal.com style)

Key features:
- Camera movements (pan, zoom, parallax)
- Professional text animations (typewriter, wobble, shimmer)
- Animated gradients with shimmer
- UI elements (inputs, buttons, charts)
- Scene transitions (slide, fade, morph)
"""

import math
import uuid
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any, Union
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import logging
import asyncio

logger = logging.getLogger(__name__)

# Video dimensions (9:16 vertical)
WIDTH = 1080
HEIGHT = 1920
FPS = 30


def get_font(size: int, bold: bool = False, thin: bool = False) -> ImageFont.FreeTypeFont:
    """Get system font with weight options"""
    if thin:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    elif bold:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


# =============================================================
# EASING FUNCTIONS
# =============================================================

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_quart(t: float) -> float:
    return 1 - pow(1 - t, 4)

def ease_out_quint(t: float) -> float:
    return 1 - pow(1 - t, 5)

def ease_in_out_cubic(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

def spring(t: float, tension: float = 0.5) -> float:
    """Spring animation"""
    return 1 - math.exp(-8 * t) * math.cos(10 * t * (1 - tension))


# =============================================================
# CAMERA SYSTEM
# =============================================================

class Camera:
    """Camera for pan, zoom, and parallax effects"""
    
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.x = 0  # Pan X offset
        self.y = 0  # Pan Y offset
        self.zoom = 1.0  # Zoom level
        self.rotation = 0  # Rotation in degrees
    
    def set_pan(self, x: float, y: float):
        self.x = x
        self.y = y
    
    def set_zoom(self, zoom: float):
        self.zoom = max(0.5, min(3.0, zoom))
    
    def apply_to_image(self, img: Image.Image) -> Image.Image:
        """Apply camera transform to image"""
        if self.zoom == 1.0 and self.x == 0 and self.y == 0 and self.rotation == 0:
            return img
        
        # Calculate new dimensions for zoom
        new_w = int(img.width * self.zoom)
        new_h = int(img.height * self.zoom)
        
        # Resize for zoom
        if self.zoom != 1.0:
            img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Calculate crop position (centered with pan offset)
        left = (new_w - self.width) // 2 + int(self.x)
        top = (new_h - self.height) // 2 + int(self.y)
        
        # Clamp to valid range
        left = max(0, min(left, new_w - self.width))
        top = max(0, min(top, new_h - self.height))
        
        # Crop to original size
        if new_w > self.width or new_h > self.height:
            img = img.crop((left, top, left + self.width, top + self.height))
        
        return img


def animate_camera(
    start_pos: Tuple[float, float, float],  # (x, y, zoom)
    end_pos: Tuple[float, float, float],
    progress: float,
    easing: str = "ease_out"
) -> Tuple[float, float, float]:
    """Animate camera between positions"""
    if easing == "ease_out":
        t = ease_out_quart(progress)
    elif easing == "ease_in_out":
        t = ease_in_out_cubic(progress)
    else:
        t = progress
    
    x = start_pos[0] + (end_pos[0] - start_pos[0]) * t
    y = start_pos[1] + (end_pos[1] - start_pos[1]) * t
    zoom = start_pos[2] + (end_pos[2] - start_pos[2]) * t
    
    return (x, y, zoom)


# =============================================================
# ANIMATED BACKGROUNDS
# =============================================================

def create_soft_gradient(
    width: int,
    height: int,
    colors: List[Tuple[int, int, int]] = None,
    angle: float = 0,  # degrees
    time: float = 0  # for animation
) -> Image.Image:
    """Soft gradient background (Airbnb/Cal.com style)"""
    img = Image.new("RGB", (width, height))
    
    if not colors or len(colors) < 2:
        colors = [(255, 245, 240), (255, 230, 220)]  # Soft pink/peach
    
    # Create gradient with slight animation wave
    for y in range(height):
        # Add subtle wave animation
        wave = math.sin(y / height * math.pi + time * math.pi * 2) * 0.03
        t = max(0, min(1, y / height + wave))
        
        # Multi-color interpolation
        num_colors = len(colors)
        segment = t * (num_colors - 1)
        idx = min(int(segment), num_colors - 2)
        local_t = segment - idx
        
        c1 = colors[idx]
        c2 = colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    
    # Add subtle glow in center
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    center_x, center_y = width // 2, height // 2
    for radius in range(400, 0, -5):
        alpha = int(10 * (400 - radius) / 400)
        glow_draw.ellipse(
            (center_x - radius, center_y - radius,
             center_x + radius, center_y + radius),
            fill=(255, 255, 255, alpha)
        )
    
    img = Image.alpha_composite(img.convert("RGBA"), glow).convert("RGB")
    return img


def create_dark_gradient(
    width: int,
    height: int,
    colors: List[Tuple[int, int, int]] = None,
    radial: bool = False
) -> Image.Image:
    """Dark gradient (Notion style dashboard)"""
    if colors is None:
        colors = [(15, 15, 25), (25, 25, 45)]
    
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    if radial:
        # Radial gradient from center
        center_x, center_y = width // 2, height // 2
        max_dist = math.sqrt(center_x**2 + center_y**2)
        
        for i in range(50, 0, -1):
            ratio = i / 50
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
    else:
        # Linear vertical
        for y in range(height):
            t = y / height
            r = int(colors[0][0] * (1 - t) + colors[-1][0] * t)
            g = int(colors[0][1] * (1 - t) + colors[-1][1] * t)
            b = int(colors[0][2] * (1 - t) + colors[-1][2] * t)
            draw.line((0, y, width, y), fill=(r, g, b))
    
    return img


# =============================================================
# TEXT ANIMATIONS - Professional Style
# =============================================================

def draw_text_typewriter(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    font_size: int = 48,
    color: Tuple[int, int, int] = (0, 0, 0),
    progress: float = 1.0,  # 0-1 how much text visible
    show_cursor: bool = True,
    cursor_blink: bool = True,
    frame: int = 0
) -> Image.Image:
    """Typewriter effect with cursor"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, thin=True)
    
    # Calculate visible characters
    visible_chars = int(len(text) * progress)
    visible_text = text[:visible_chars]
    
    x, y = position
    draw.text((x, y), visible_text, font=font, fill=(*color, 255))
    
    # Cursor
    if show_cursor and progress < 1.0:
        cursor_visible = True
        if cursor_blink:
            cursor_visible = (frame // 8) % 2 == 0
        
        if cursor_visible:
            bbox = draw.textbbox((x, y), visible_text, font=font)
            cursor_x = bbox[2] + 2
            draw.rectangle(
                (cursor_x, y + 5, cursor_x + 3, y + font_size - 5),
                fill=(*color, 255)
            )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_fade_scale(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int = 80,
    color: Tuple[int, int, int] = (255, 255, 255),
    progress: float = 1.0,
    blur_in: bool = True
) -> Image.Image:
    """Text fades in with scale and optional blur"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Animation
    scale = 0.7 + 0.3 * ease_out_back(progress)
    alpha = int(255 * ease_out_cubic(progress))
    
    actual_size = max(20, int(font_size * scale))
    font = get_font(actual_size, bold=True)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = center[0] - text_w // 2
    y = center[1] - text_h // 2
    
    # Shadow
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, alpha // 4))
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    # Blur effect for early animation
    if blur_in and progress < 0.5:
        blur_amount = int((1 - progress / 0.5) * 8)
        if blur_amount > 0:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=blur_amount))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_gradient(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int = 80,
    gradient_colors: List[Tuple[int, int, int]] = None,
    progress: float = 1.0,
    shimmer_offset: float = 0,  # Animated shimmer
    wobble: bool = False,
    wobble_amount: float = 0
) -> Image.Image:
    """Text with animated gradient fill (like in videos)"""
    if gradient_colors is None:
        gradient_colors = [(180, 100, 255), (255, 100, 180)]  # Purple to pink
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    font = get_font(font_size, bold=True)
    
    # Measure
    temp_draw = ImageDraw.Draw(layer)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = center[0] - text_w // 2
    y = center[1] - text_h // 2
    
    # Apply wobble
    if wobble and wobble_amount > 0:
        y += int(math.sin(wobble_amount * math.pi * 4) * 10 * (1 - progress))
    
    # Create gradient strip
    gradient_img = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
    
    for px in range(text_w + 20):
        # Shimmer animation
        t = ((px / (text_w + 20)) + shimmer_offset) % 1.0
        
        num_colors = len(gradient_colors)
        segment = t * (num_colors - 1)
        idx = min(int(segment), num_colors - 2)
        local_t = segment - idx
        
        c1 = gradient_colors[idx]
        c2 = gradient_colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        for py in range(text_h + 20):
            gradient_img.putpixel((px, py), (r, g, b, 255))
    
    # Create mask
    mask = Image.new("L", (text_w + 20, text_h + 20), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10, 10), text, font=font, fill=255)
    
    gradient_img.putalpha(mask)
    
    # Alpha animation
    alpha = int(255 * ease_out_cubic(progress))
    if alpha < 255:
        r, g, b, a = gradient_img.split()
        a = a.point(lambda p: int(p * progress))
        gradient_img = Image.merge("RGBA", (r, g, b, a))
    
    layer.paste(gradient_img, (x - 10, y - 10), gradient_img)
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_word_by_word(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int = 60,
    color: Tuple[int, int, int] = (0, 0, 0),
    progress: float = 1.0,
    highlight_words: List[int] = None,  # Indices of words to highlight
    highlight_colors: List[Tuple[int, int, int]] = None
) -> Image.Image:
    """Words appear one by one"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    words = text.split()
    if not words:
        return img
    
    # Calculate how many words to show
    words_to_show = int(len(words) * progress) + 1
    words_to_show = min(words_to_show, len(words))
    
    # Calculate total width
    total_text = " ".join(words[:words_to_show])
    bbox = draw.textbbox((0, 0), total_text, font=font)
    total_w = bbox[2] - bbox[0]
    
    start_x = center[0] - total_w // 2
    y = center[1] - font_size // 2
    
    current_x = start_x
    for i, word in enumerate(words[:words_to_show]):
        # Calculate word progress
        word_start = i / len(words)
        word_end = (i + 1) / len(words)
        word_progress = max(0, min(1, (progress - word_start) / (word_end - word_start)))
        
        # Determine color
        word_color = color
        if highlight_words and i in highlight_words and highlight_colors:
            idx = highlight_words.index(i) % len(highlight_colors)
            word_color = highlight_colors[idx]
        
        # Animation for current word
        alpha = int(255 * ease_out_cubic(min(1, word_progress * 2)))
        scale = 0.8 + 0.2 * ease_out_back(word_progress)
        
        word_font = get_font(int(font_size * scale), bold=True)
        
        draw.text((current_x, y), word, font=word_font, fill=(*word_color, alpha))
        
        bbox = draw.textbbox((0, 0), word + " ", font=font)
        current_x += bbox[2] - bbox[0]
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# UI ELEMENTS
# =============================================================

def draw_rounded_rect(
    draw: ImageDraw.Draw,
    bounds: Tuple[int, int, int, int],
    radius: int,
    fill: Tuple[int, int, int, int],
    outline: Tuple[int, int, int, int] = None,
    outline_width: int = 0
):
    """Draw rounded rectangle"""
    x1, y1, x2, y2 = bounds
    
    # Main body
    draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill)
    draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill)
    
    # Corners
    draw.ellipse((x1, y1, x1 + radius * 2, y1 + radius * 2), fill=fill)
    draw.ellipse((x2 - radius * 2, y1, x2, y1 + radius * 2), fill=fill)
    draw.ellipse((x1, y2 - radius * 2, x1 + radius * 2, y2), fill=fill)
    draw.ellipse((x2 - radius * 2, y2 - radius * 2, x2, y2), fill=fill)
    
    # Outline
    if outline and outline_width > 0:
        draw.rounded_rectangle(bounds, radius=radius, outline=outline, width=outline_width)


def draw_input_field(
    img: Image.Image,
    x: int, y: int,
    width: int, height: int,
    placeholder: str = "",
    progress: float = 1.0
) -> Image.Image:
    """iOS-style input field"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    alpha = int(255 * ease_out_cubic(progress))
    
    # Slide in from right
    offset_x = int((1 - ease_out_quart(progress)) * 100)
    x += offset_x
    
    radius = height // 2
    
    # Background
    draw_rounded_rect(draw, (x, y, x + width, y + height), radius, (50, 50, 55, alpha))
    
    # Placeholder
    if placeholder:
        font = get_font(height // 2 - 4)
        draw.text((x + 25, y + height // 4), placeholder, font=font, fill=(150, 150, 155, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_button(
    img: Image.Image,
    x: int, y: int,
    width: int, height: int,
    text: str,
    bg_color: Tuple[int, int, int] = (0, 122, 255),
    text_color: Tuple[int, int, int] = (255, 255, 255),
    progress: float = 1.0,
    shimmer: bool = False,
    shimmer_offset: float = 0
) -> Image.Image:
    """Button with optional shimmer"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    alpha = int(255 * ease_out_cubic(progress))
    scale = ease_out_back(progress)
    
    # Scale from center
    actual_w = int(width * scale)
    actual_h = int(height * scale)
    actual_x = x + (width - actual_w) // 2
    actual_y = y + (height - actual_h) // 2
    
    radius = actual_h // 2
    
    # Shadow
    draw_rounded_rect(draw, 
        (actual_x + 3, actual_y + 3, actual_x + actual_w + 3, actual_y + actual_h + 3),
        radius, (0, 0, 0, alpha // 4))
    
    # Button
    draw_rounded_rect(draw, 
        (actual_x, actual_y, actual_x + actual_w, actual_y + actual_h),
        radius, (*bg_color, alpha))
    
    # Shimmer overlay
    if shimmer:
        shimmer_x = int((shimmer_offset % 1.0) * actual_w * 2 - actual_w // 2)
        for sx in range(max(0, shimmer_x), min(actual_w, shimmer_x + 80)):
            shimmer_alpha = int(30 * (1 - abs(sx - shimmer_x - 40) / 40))
            for sy in range(actual_h):
                px = actual_x + sx
                py = actual_y + sy
                if 0 <= px < img.size[0] and 0 <= py < img.size[1]:
                    old = layer.getpixel((px, py))
                    if old[3] > 0:
                        new_r = min(255, old[0] + shimmer_alpha)
                        new_g = min(255, old[1] + shimmer_alpha)
                        new_b = min(255, old[2] + shimmer_alpha)
                        layer.putpixel((px, py), (new_r, new_g, new_b, old[3]))
    
    # Text
    font = get_font(actual_h // 2 - 4, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    text_x = actual_x + (actual_w - text_w) // 2
    text_y = actual_y + (actual_h - text_h) // 2 - 3
    
    draw.text((text_x, text_y), text, font=font, fill=(*text_color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_message_bubble(
    img: Image.Image,
    text: str,
    y: int,
    is_sender: bool,
    progress: float = 1.0
) -> Tuple[Image.Image, int]:
    """iMessage-style bubble with animation"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Colors
    if is_sender:
        bubble_color = (0, 122, 255)
        text_color = (255, 255, 255)
    else:
        bubble_color = (235, 235, 240)
        text_color = (0, 0, 0)
    
    font_size = 44
    font = get_font(font_size)
    
    # Wrap text
    max_width = int(WIDTH * 0.65)
    padding_x = 28
    padding_y = 20
    
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
    
    if not lines:
        lines = [text]
    
    line_height = font_size + 8
    text_height = len(lines) * line_height
    text_width = max((draw.textbbox((0, 0), line, font=font)[2] for line in lines), default=100)
    
    bubble_w = text_width + padding_x * 2
    bubble_h = text_height + padding_y * 2
    
    margin = 45
    if is_sender:
        bubble_x = WIDTH - bubble_w - margin
    else:
        bubble_x = margin
    
    # Animation
    alpha = int(255 * ease_out_cubic(progress))
    scale = 0.5 + 0.5 * ease_out_back(progress)
    
    # Slide from side
    if progress < 1:
        offset = int((1 - ease_out_quart(progress)) * 150)
        if is_sender:
            bubble_x += offset
        else:
            bubble_x -= offset
    
    radius = 22
    
    # Shadow
    draw_rounded_rect(draw,
        (bubble_x + 3, y + 3, bubble_x + bubble_w + 3, y + bubble_h + 3),
        radius, (0, 0, 0, alpha // 6))
    
    # Bubble
    draw_rounded_rect(draw,
        (bubble_x, y, bubble_x + bubble_w, y + bubble_h),
        radius, (*bubble_color, alpha))
    
    # Tail
    if progress > 0.7:
        tail_alpha = int(alpha * ((progress - 0.7) / 0.3))
        tail_size = 10
        if is_sender:
            tail_points = [
                (bubble_x + bubble_w - 10, y + bubble_h - 8),
                (bubble_x + bubble_w + tail_size, y + bubble_h + 5),
                (bubble_x + bubble_w - 3, y + bubble_h)
            ]
        else:
            tail_points = [
                (bubble_x + 10, y + bubble_h - 8),
                (bubble_x - tail_size, y + bubble_h + 5),
                (bubble_x + 3, y + bubble_h)
            ]
        draw.polygon(tail_points, fill=(*bubble_color, tail_alpha))
    
    # Text
    text_y = y + padding_y
    text_alpha = int(alpha * min(1, progress * 2 - 0.3))
    for line in lines:
        text_x = bubble_x + padding_x
        draw.text((text_x, text_y), line, font=font, fill=(*text_color, text_alpha))
        text_y += line_height
    
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result, bubble_h + 18


def draw_typing_indicator(
    img: Image.Image,
    y: int,
    frame: int
) -> Image.Image:
    """Animated typing indicator"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    bubble_color = (235, 235, 240)
    bubble_w = 85
    bubble_h = 48
    margin = 45
    bubble_x = margin
    
    radius = 22
    
    draw_rounded_rect(draw,
        (bubble_x, y, bubble_x + bubble_w, y + bubble_h),
        radius, (*bubble_color, 255))
    
    # Dots
    dot_radius = 6
    dot_spacing = 18
    base_x = bubble_x + bubble_w // 2 - dot_spacing
    base_y = y + bubble_h // 2
    
    for i in range(3):
        phase = (frame * 0.12 + i * 0.5) % (math.pi * 2)
        bounce = math.sin(phase) * 5
        
        dot_x = base_x + i * dot_spacing
        dot_y = int(base_y + bounce)
        
        draw.ellipse(
            (dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius),
            fill=(140, 140, 145, 255)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# SCENE RENDERING
# =============================================================

async def render_professional_video(
    scenes: List[Dict],
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render video with professional effects.
    
    Scene format:
    {
        "type": "text" | "gradient_text" | "word_by_word" | "chat" | "ui_form",
        "duration": 3.0,
        "transition": "fade" | "slide_left" | "slide_right" | "slide_up" | "zoom",
        "background": "light" | "dark" | [colors],
        "content": {...}
    }
    """
    output_path = output_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Calculate timings
    scene_timings = []
    current_time = 0.0
    
    for scene in scenes:
        duration = scene.get("duration", 3.0)
        scene_timings.append({
            "start": current_time,
            "end": current_time + duration,
            "scene": scene
        })
        current_time += duration
    
    total_duration = current_time
    total_frames = int(fps * total_duration)
    
    logger.info(f"Rendering {total_frames} frames, {len(scenes)} scenes")
    
    camera = Camera(WIDTH, HEIGHT)
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        global_progress = frame_num / total_frames
        
        # Find active scene
        active_scene = None
        scene_progress = 0
        local_time = 0
        
        for timing in scene_timings:
            if timing["start"] <= time_sec < timing["end"]:
                active_scene = timing["scene"]
                local_time = time_sec - timing["start"]
                scene_progress = local_time / (timing["end"] - timing["start"])
                break
        
        if not active_scene:
            continue
        
        # Background
        bg_type = active_scene.get("background", "light")
        if bg_type == "dark":
            bg = create_dark_gradient(WIDTH, HEIGHT, radial=True)
        elif bg_type == "black":
            bg = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        elif isinstance(bg_type, list):
            colors = [tuple(c) for c in bg_type]
            bg = create_soft_gradient(WIDTH, HEIGHT, colors, time=global_progress)
        else:
            bg = create_soft_gradient(WIDTH, HEIGHT, time=global_progress)
        
        bg = bg.convert("RGBA")
        
        # Transition in/out
        trans_in = active_scene.get("transition_in", 0.4)
        trans_out = active_scene.get("transition_out", 0.3)
        duration = active_scene.get("duration", 3.0)
        
        if local_time < trans_in:
            visibility = local_time / trans_in
        elif local_time > duration - trans_out:
            visibility = (duration - local_time) / trans_out
        else:
            visibility = 1.0
        
        visibility = ease_out_cubic(max(0, min(1, visibility)))
        
        scene_type = active_scene.get("type", "text")
        content = active_scene.get("content", {})
        
        # Render scene type
        if scene_type == "text":
            text = content.get("text", "")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 85)
            y_pos = content.get("y_position", HEIGHT // 2 - 50)
            effect = content.get("effect", "fade_scale")
            
            if effect == "typewriter":
                bg = draw_text_typewriter(bg, text, (100, y_pos), font_size, color, visibility, True, True, frame_num)
            else:
                bg = draw_text_fade_scale(bg, text, (WIDTH // 2, y_pos), font_size, color, visibility)
        
        elif scene_type == "gradient_text":
            text = content.get("text", "")
            font_size = content.get("font_size", 85)
            y_pos = content.get("y_position", HEIGHT // 2 - 50)
            colors = [tuple(c) for c in content.get("gradient_colors", [[180, 100, 255], [255, 100, 180]])]
            shimmer = content.get("shimmer", True)
            wobble = content.get("wobble", False)
            
            shimmer_offset = global_progress * 2 if shimmer else 0
            bg = draw_text_gradient(bg, text, (WIDTH // 2, y_pos), font_size, colors, visibility, shimmer_offset, wobble, local_time)
        
        elif scene_type == "word_by_word":
            text = content.get("text", "")
            font_size = content.get("font_size", 60)
            color = tuple(content.get("color", [0, 0, 0]))
            y_pos = content.get("y_position", HEIGHT // 2)
            highlight_words = content.get("highlight_words", [])
            highlight_colors = [tuple(c) for c in content.get("highlight_colors", [[180, 100, 255]])]
            
            bg = draw_text_word_by_word(bg, text, (WIDTH // 2, y_pos), font_size, color, visibility, highlight_words, highlight_colors)
        
        elif scene_type == "ui_form":
            fields = content.get("fields", ["Email"])
            button_text = content.get("button_text", "Submit")
            button_color = tuple(content.get("button_color", [0, 122, 255]))
            y_start = content.get("y_start", 500)
            
            field_w = 700
            field_h = 65
            spacing = 20
            x = (WIDTH - field_w) // 2
            
            current_y = y_start
            for i, placeholder in enumerate(fields):
                field_progress = max(0, min(1, (visibility * (len(fields) + 1) - i) / 1.0))
                if field_progress > 0:
                    bg = draw_input_field(bg, x, current_y, field_w, field_h, placeholder, field_progress)
                current_y += field_h + spacing
            
            btn_progress = max(0, min(1, (visibility * (len(fields) + 1) - len(fields)) / 1.0))
            if btn_progress > 0:
                bg = draw_button(bg, x, current_y + 15, field_w, 70, button_text, button_color, progress=btn_progress, shimmer=True, shimmer_offset=global_progress * 2)
        
        elif scene_type == "chat":
            messages = content.get("messages", [])
            
            # Center chat
            total_msgs = len(messages)
            estimated_height = total_msgs * 90
            start_y = max(200, (HEIGHT - estimated_height) // 2)
            
            current_y = start_y
            
            for i, msg in enumerate(messages):
                msg_start = i * 0.15
                msg_visibility = max(0, min(1, (visibility * len(messages) - i) / 1.0))
                
                if msg_visibility > 0:
                    # Show typing before message
                    if msg_visibility < 0.4 and not msg.get("sender", False):
                        bg = draw_typing_indicator(bg, current_y, frame_num)
                    else:
                        bg, height = draw_message_bubble(
                            bg,
                            msg.get("text", ""),
                            current_y,
                            msg.get("sender", False),
                            min(1, (msg_visibility - 0.3) / 0.7) if not msg.get("sender") else msg_visibility
                        )
                        current_y += height
        
        # Apply camera
        bg = camera.apply_to_image(bg)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
        
        if frame_num % 30 == 0:
            logger.info(f"Rendered frame {frame_num}/{total_frames}")
    
    # Encode
    logger.info("Encoding video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        await asyncio.wait_for(process.communicate(), timeout=180)
    except asyncio.TimeoutError:
        process.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Video: {output_path}")
        return str(output_path)
    
    return ""


# Backward compatible
async def render_universal_video(script_data: Dict, output_dir: Path, fps: int = 30) -> str:
    """Convert old format to new scene format"""
    elements = script_data.get("elements", [])
    scenes = []
    
    for elem in elements:
        elem_type = elem.get("type", "text")
        duration = elem.get("duration", 3.0)
        
        scene = {
            "type": elem_type,
            "duration": duration,
            "transition_in": 0.4,
            "transition_out": 0.3,
            "background": "black" if elem_type in ["text", "gradient_text"] else "light",
            "content": {}
        }
        
        if elem_type == "text":
            scene["content"] = {
                "text": elem.get("content", ""),
                "color": elem.get("color", [255, 255, 255]),
                "font_size": elem.get("font_size", 120),  # Larger default
                "effect": elem.get("effect", "fade_scale")
            }
        elif elem_type == "gradient_text":
            scene["content"] = {
                "text": elem.get("content", ""),
                "font_size": elem.get("font_size", 120),  # Larger default
                "gradient_colors": elem.get("gradient_colors", [[180, 100, 255], [255, 100, 180]]),
                "shimmer": elem.get("shimmer", True)
            }
        elif elem_type == "ui_form":
            scene["content"] = {
                "fields": elem.get("fields", ["Field"]),
                "button_text": elem.get("button_text", "Submit"),
                "button_color": elem.get("button_color", [0, 122, 255])
            }
            scene["background"] = "light"
        elif elem_type == "chat":
            scene["content"] = {"messages": elem.get("messages", [])}
            scene["background"] = "light"
        
        scenes.append(scene)
    
    if not scenes:
        scenes = [{"type": "text", "duration": 3.0, "background": "black", "content": {"text": "Hello"}}]
    
    return await render_professional_video(scenes, output_dir, fps)
