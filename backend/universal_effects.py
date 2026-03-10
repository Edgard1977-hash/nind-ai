"""
PROFESSIONAL VIDEO EFFECTS v6 - Apple Style Animations
Based on detailed analysis of reference videos:
1. Word-by-word text reveal with scale + fade + slide
2. Logo animation with rotation + scale + ease-out-back
3. Underline animations
4. Smooth transitions between scenes
"""

import math
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import logging
import asyncio

logger = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920


def get_font(size: int, weight: str = "semibold") -> ImageFont.FreeTypeFont:
    """Get Inter font with specific weight"""
    weight_map = {
        "thin": "/usr/share/fonts/opentype/inter/Inter-Thin.otf",
        "light": "/usr/share/fonts/opentype/inter/Inter-Light.otf",
        "regular": "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
        "medium": "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
        "semibold": "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
        "bold": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
        "extrabold": "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
        "black": "/usr/share/fonts/opentype/inter/Inter-Black.otf",
    }
    
    paths = [
        weight_map.get(weight, weight_map["semibold"]),
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()


# =============================================================
# EASING FUNCTIONS - Critical for smooth animations
# =============================================================

def ease_linear(t: float) -> float:
    return t

def ease_in_quad(t: float) -> float:
    return t * t

def ease_out_quad(t: float) -> float:
    return 1 - (1 - t) * (1 - t)

def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_in_out_cubic(t: float) -> float:
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

def ease_out_quart(t: float) -> float:
    return 1 - pow(1 - t, 4)

def ease_out_back(t: float) -> float:
    """Overshoot effect - like a bounce back"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_out_elastic(t: float) -> float:
    """Elastic bounce effect"""
    if t == 0 or t == 1:
        return t
    c4 = (2 * math.pi) / 3
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * c4) + 1


# =============================================================
# BACKGROUNDS
# =============================================================

def create_solid_bg(w: int, h: int, color: Tuple[int, int, int]) -> Image.Image:
    """Solid color background"""
    return Image.new("RGB", (w, h), color)


def create_gradient_bg(w: int, h: int, colors: List[Tuple[int, int, int]], time: float = 0, vertical: bool = True) -> Image.Image:
    """Animated gradient background"""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(100, 80, 200), (80, 120, 220)]
    
    size = h if vertical else w
    
    for i in range(size):
        t = i / size
        # Add subtle wave animation
        wave = math.sin(t * 2 + time * math.pi * 2) * 0.03
        t = max(0, min(1, t + wave))
        
        idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
        local_t = (t * (len(colors) - 1)) - idx
        
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        if vertical:
            draw.line((0, i, w, i), fill=(r, g, b))
        else:
            draw.line((i, 0, i, h), fill=(r, g, b))
    
    return img


# =============================================================
# SHAPE ANIMATIONS - Circles, Rectangles, etc.
# =============================================================

def draw_gradient_circle(
    img: Image.Image,
    progress: float,
    colors: List[Tuple[int, int, int]],
    size: int = 400,
    glow: bool = True
) -> Image.Image:
    """
    Animated gradient circle with scale + glow effect
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    if len(colors) < 2:
        colors = [(255, 100, 150), (100, 150, 255)]
    
    # Animation: scale up with bounce
    scale = ease_out_back(min(1, progress * 1.3))
    alpha = int(255 * ease_out_quad(min(1, progress * 2)))
    
    actual_size = int(size * scale)
    if actual_size < 10:
        return img
    
    # Create gradient circle
    circle = Image.new("RGBA", (actual_size, actual_size), (0, 0, 0, 0))
    
    center = actual_size // 2
    
    for y in range(actual_size):
        for x in range(actual_size):
            dx = x - center
            dy = y - center
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist <= center:
                # Radial gradient
                t = dist / center
                idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
                local_t = (t * (len(colors) - 1)) - idx
                
                c1, c2 = colors[idx], colors[idx + 1]
                r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
                g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
                b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
                
                # Soft edge
                edge_fade = 1.0
                if dist > center * 0.85:
                    edge_fade = 1 - ((dist - center * 0.85) / (center * 0.15))
                
                pixel_alpha = int(alpha * edge_fade)
                circle.putpixel((x, y), (r, g, b, pixel_alpha))
    
    # Add glow effect
    if glow and scale > 0.5:
        glow_layer = circle.copy()
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=30))
        # Make glow brighter
        r, g, b, a = glow_layer.split()
        a = a.point(lambda p: min(255, int(p * 0.6)))
        glow_layer = Image.merge("RGBA", (r, g, b, a))
        
        glow_x = (WIDTH - glow_layer.width) // 2
        glow_y = (HEIGHT - glow_layer.height) // 2
        layer.paste(glow_layer, (glow_x, glow_y), glow_layer)
    
    # Paste circle
    cx = (WIDTH - actual_size) // 2
    cy = (HEIGHT - actual_size) // 2
    layer.paste(circle, (cx, cy), circle)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_gradient_rect(
    img: Image.Image,
    progress: float,
    colors: List[Tuple[int, int, int]],
    width: int = 600,
    height: int = 400,
    corner_radius: int = 50,
    rotation: float = 0
) -> Image.Image:
    """
    Animated gradient rectangle with rounded corners
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    if len(colors) < 2:
        colors = [(100, 200, 255), (200, 100, 255)]
    
    # Animation
    scale = ease_out_back(min(1, progress * 1.3))
    alpha = int(255 * ease_out_quad(min(1, progress * 2)))
    
    actual_w = int(width * scale)
    actual_h = int(height * scale)
    
    if actual_w < 20 or actual_h < 20:
        return img
    
    # Create gradient rectangle
    rect = Image.new("RGBA", (actual_w, actual_h), (0, 0, 0, 0))
    rect_draw = ImageDraw.Draw(rect)
    
    # Draw gradient lines
    for y in range(actual_h):
        t = y / actual_h
        idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
        local_t = (t * (len(colors) - 1)) - idx
        
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        rect_draw.line((0, y, actual_w, y), fill=(r, g, b, alpha))
    
    # Create rounded corners mask
    mask = Image.new("L", (actual_w, actual_h), 0)
    mask_draw = ImageDraw.Draw(mask)
    radius = min(corner_radius, actual_w // 2, actual_h // 2)
    mask_draw.rounded_rectangle((0, 0, actual_w - 1, actual_h - 1), radius=radius, fill=255)
    
    rect.putalpha(mask)
    
    # Rotate if needed
    if rotation != 0:
        rot_progress = ease_out_quad(min(1, progress * 1.5))
        current_rot = rotation * (1 - rot_progress)
        rect = rect.rotate(current_rot, expand=True, resample=Image.Resampling.BICUBIC)
    
    # Center position
    rx = (WIDTH - rect.width) // 2
    ry = (HEIGHT - rect.height) // 2
    
    layer.paste(rect, (rx, ry), rect)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_multiple_shapes(
    img: Image.Image,
    progress: float,
    shapes: List[Dict]
) -> Image.Image:
    """
    Draw multiple shapes with staggered animation
    shapes: [{"type": "circle", "colors": [...], "size": 200, "x": 0, "y": -100}, ...]
    """
    result = img.convert("RGBA")
    
    for i, shape in enumerate(shapes):
        # Staggered animation
        shape_delay = i * 0.15
        shape_progress = max(0, min(1, (progress - shape_delay) / (1 - shape_delay * len(shapes) / 2)))
        
        if shape_progress <= 0:
            continue
        
        shape_type = shape.get("type", "circle")
        colors = [tuple(c) for c in shape.get("colors", [[255, 100, 150], [100, 150, 255]])]
        x_offset = shape.get("x", 0)
        y_offset = shape.get("y", 0)
        
        if shape_type == "circle":
            size = shape.get("size", 300)
            # Create temp image for this shape
            temp = Image.new("RGBA", result.size, (0, 0, 0, 0))
            temp = draw_gradient_circle(temp, shape_progress, colors, size, glow=shape.get("glow", True))
            
            # Apply offset by shifting
            if x_offset != 0 or y_offset != 0:
                shifted = Image.new("RGBA", result.size, (0, 0, 0, 0))
                shifted.paste(temp, (x_offset, y_offset), temp)
                temp = shifted
            
            result = Image.alpha_composite(result, temp)
        
        elif shape_type == "rect":
            w = shape.get("width", 400)
            h = shape.get("height", 300)
            radius = shape.get("radius", 30)
            
            temp = Image.new("RGBA", result.size, (0, 0, 0, 0))
            temp = draw_gradient_rect(temp, shape_progress, colors, w, h, radius)
            
            if x_offset != 0 or y_offset != 0:
                shifted = Image.new("RGBA", result.size, (0, 0, 0, 0))
                shifted.paste(temp, (x_offset, y_offset), temp)
                temp = shifted
            
            result = Image.alpha_composite(result, temp)
    
    return result


# =============================================================
# TEXT ANIMATIONS - Apple Style
# =============================================================

def draw_text_word_by_word(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_size: int = 120,
    y_offset: int = 0,
    underline_word: Optional[str] = None
) -> Image.Image:
    """
    Apple-style word-by-word text animation
    Each word: fade in + scale up (0.95->1.0) + slide from right
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    words = text.split()
    if not words:
        return img
    
    font = get_font(font_size, "semibold")
    
    # Calculate total text width and positions
    word_data = []
    total_width = 0
    space_width = font_size // 3
    
    for word in words:
        bbox = draw.textbbox((0, 0), word, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        word_data.append({"word": word, "width": w, "height": h})
        total_width += w + space_width
    
    total_width -= space_width  # Remove last space
    
    # Center starting position
    start_x = (WIDTH - total_width) // 2
    y = HEIGHT // 2 + y_offset
    
    # Animation timing per word
    word_duration = 0.8 / len(words) if len(words) > 1 else 0.8
    
    current_x = start_x
    
    for i, wd in enumerate(word_data):
        word = wd["word"]
        word_w = wd["width"]
        word_h = wd["height"]
        
        # Calculate this word's progress
        word_start = i * word_duration
        word_end = word_start + word_duration + 0.2  # Overlap
        
        if progress < word_start:
            word_progress = 0
        elif progress >= word_end:
            word_progress = 1
        else:
            word_progress = (progress - word_start) / (word_end - word_start)
        
        if word_progress > 0:
            # Animation: scale + fade + slide
            scale = 0.95 + 0.05 * ease_out_back(min(1, word_progress * 1.5))
            alpha = int(255 * ease_out_quad(min(1, word_progress * 2)))
            slide_x = int((1 - ease_out_cubic(word_progress)) * 30)
            
            # Calculate scaled font
            scaled_size = int(font_size * scale)
            scaled_font = get_font(scaled_size, "semibold")
            
            # Draw word
            bbox = draw.textbbox((0, 0), word, font=scaled_font)
            actual_w = bbox[2] - bbox[0]
            actual_h = bbox[3] - bbox[1]
            
            wx = current_x + slide_x + (word_w - actual_w) // 2
            wy = y - actual_h // 2
            
            draw.text((wx, wy), word, font=scaled_font, fill=(*color, alpha))
            
            # Underline animation for specific word
            if underline_word and word.lower().replace(".", "").replace(",", "") == underline_word.lower():
                if word_progress > 0.5:
                    underline_progress = (word_progress - 0.5) / 0.5
                    line_width = int(actual_w * ease_out_quad(underline_progress))
                    line_y = wy + actual_h + 10
                    line_alpha = int(alpha * underline_progress)
                    draw.line(
                        (wx, line_y, wx + line_width, line_y),
                        fill=(*color, line_alpha),
                        width=4
                    )
        
        current_x += word_w + space_width
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_scale_fade(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    y_offset: int = 0
) -> Image.Image:
    """
    Simple scale + fade text animation for single phrases
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Animation parameters
    scale = 0.9 + 0.1 * ease_out_back(min(1, progress * 1.3))
    alpha = int(255 * ease_out_quad(min(1, progress * 2)))
    
    scaled_size = int(font_size * scale)
    font = get_font(scaled_size, "semibold")
    
    # Auto-fit text to 70% of screen width
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    target_width = int(WIDTH * 0.7)
    
    while text_w > target_width and scaled_size > 60:
        scaled_size -= 5
        font = get_font(scaled_size, "semibold")
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
    
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 + y_offset
    
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_gradient_text(
    img: Image.Image,
    text: str,
    progress: float,
    colors: List[Tuple[int, int, int]],
    font_size: int = 140,
    shimmer_offset: float = 0,
    y_offset: int = 0
) -> Image.Image:
    """
    Text with gradient fill and optional shimmer animation
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    scale = 0.9 + 0.1 * ease_out_back(min(1, progress * 1.3))
    scaled_size = int(font_size * scale)
    font = get_font(scaled_size, "bold")
    
    # Measure text
    temp_draw = ImageDraw.Draw(layer)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Auto-fit
    target_width = int(WIDTH * 0.7)
    while text_w > target_width and scaled_size > 60:
        scaled_size -= 5
        font = get_font(scaled_size, "bold")
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 + y_offset
    
    # Create gradient image
    grad = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    
    if len(colors) < 2:
        colors = [(100, 180, 255), (200, 100, 255)]
    
    for px in range(text_w + 20):
        t = ((px / (text_w + 20)) + shimmer_offset) % 1.0
        idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
        local_t = (t * (len(colors) - 1)) - idx
        
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        grad_draw.line((px, 0, px, text_h + 20), fill=(r, g, b, 255))
    
    # Create mask from text
    mask = Image.new("L", (text_w + 20, text_h + 20), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10, 10), text, font=font, fill=255)
    
    grad.putalpha(mask)
    
    # Apply animation alpha
    alpha = ease_out_quad(min(1, progress * 2))
    if alpha < 1:
        r, g, b, a = grad.split()
        a = a.point(lambda p: int(p * alpha))
        grad = Image.merge("RGBA", (r, g, b, a))
    
    layer.paste(grad, (x - 10, y - 10), grad)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# LOGO ANIMATION - Discord style (CORRECT)
# =============================================================

async def render_logo_animation(
    logo_path: str,
    brand_name: str,
    bg_color: Tuple[int, int, int],
    output_dir: Path,
    fps: int = 30,
    duration: float = 3.0
) -> str:
    """
    Professional logo animation based on Discord reference:
    Phase 1 (0-0.5s): Logo appears from scale 0, rotation -90° → 0° with overshoot
    Phase 2 (0.5-1.5s): Logo bounces/settles (overshoot scale 1.2 → 1.0)
    Phase 3 (1.5-2.5s): Text appears with rotation -90° → 0° and scale up
    """
    output_path = output_dir / f"logo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    total_frames = int(fps * duration)
    
    # Load logo
    try:
        logo = Image.open(logo_path).convert("RGBA")
        max_size = 300
        ratio = min(max_size / logo.width, max_size / logo.height)
        new_size = (int(logo.width * ratio), int(logo.height * ratio))
        logo = logo.resize(new_size, Image.Resampling.LANCZOS)
    except Exception as e:
        logger.error(f"Failed to load logo: {e}")
        logo = Image.new("RGBA", (300, 300), (255, 255, 255, 255))
        draw = ImageDraw.Draw(logo)
        draw.ellipse((30, 30, 270, 270), fill=(200, 200, 200, 255))
    
    # Text color (white on dark, black on light)
    brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
    text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        
        bg = create_solid_bg(WIDTH, HEIGHT, bg_color).convert("RGBA")
        
        # =============================================
        # PHASE 1 & 2: LOGO ANIMATION (0 - 1.5s)
        # =============================================
        
        if time_sec < 1.5:
            # Phase 1: Initial appearance (0 - 0.5s)
            if time_sec < 0.5:
                t = time_sec / 0.5  # 0 to 1
                
                # Rotation: -90° → 0° with overshoot to +10°
                rotation = -90 + 100 * ease_out_back(t)  # Goes to +10° overshoot
                
                # Scale: 0 → 1.2 (overshoot)
                scale = 1.2 * ease_out_back(t)
                
                # Alpha: 0 → 1
                logo_alpha = ease_out_quad(t)
            
            # Phase 2: Settle (0.5 - 1.5s)
            else:
                settle_time = (time_sec - 0.5) / 1.0  # 0 to 1
                
                # Rotation settles from +10° to 0°
                rotation = 10 * (1 - ease_out_quad(settle_time))
                
                # Scale settles from 1.2 to 1.0
                scale = 1.2 - 0.2 * ease_out_quad(settle_time)
                
                logo_alpha = 1.0
        else:
            # Logo is settled
            rotation = 0
            scale = 1.0
            logo_alpha = 1.0
        
        # Apply logo transformations
        if scale > 0.01:
            scaled_w = int(logo.width * scale)
            scaled_h = int(logo.height * scale)
            
            if scaled_w > 0 and scaled_h > 0:
                scaled_logo = logo.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                rotated_logo = scaled_logo.rotate(rotation, expand=True, resample=Image.Resampling.BICUBIC)
                
                # Apply alpha
                r, g, b, a = rotated_logo.split()
                a = a.point(lambda p: int(p * logo_alpha))
                rotated_logo = Image.merge("RGBA", (r, g, b, a))
                
                # Center position, slightly above middle
                logo_x = (WIDTH - rotated_logo.width) // 2
                logo_y = (HEIGHT - rotated_logo.height) // 2 - 150
                
                bg.paste(rotated_logo, (logo_x, logo_y), rotated_logo)
        
        # =============================================
        # PHASE 3: TEXT ANIMATION (1.0 - 2.5s)
        # =============================================
        
        if time_sec > 1.0 and brand_name:
            text_time = (time_sec - 1.0) / 1.5  # 0 to 1 over 1.5 seconds
            text_time = min(1.0, text_time)
            
            layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            
            font_size = 80
            font = get_font(font_size, "bold")
            
            # Measure text
            temp_draw = ImageDraw.Draw(layer)
            bbox = temp_draw.textbbox((0, 0), brand_name, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            # Create text image
            text_img = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)
            
            # Text animation: rotation -90° → 0°, scale 0 → 1, slide up
            text_rotation = -90 * (1 - ease_out_back(text_time))
            text_scale = ease_out_back(text_time)
            text_alpha = int(255 * ease_out_quad(min(1, text_time * 2)))
            slide_y = int(50 * (1 - ease_out_quad(text_time)))
            
            # Draw text
            text_draw.text((10, 10), brand_name, font=font, fill=(*text_color, 255))
            
            # Scale
            if text_scale > 0.01:
                new_w = max(1, int(text_img.width * text_scale))
                new_h = max(1, int(text_img.height * text_scale))
                text_img = text_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                # Rotate
                text_img = text_img.rotate(text_rotation, expand=True, resample=Image.Resampling.BICUBIC)
                
                # Apply alpha
                r, g, b, a = text_img.split()
                a = a.point(lambda p: int(p * text_alpha / 255))
                text_img = Image.merge("RGBA", (r, g, b, a))
                
                # Position below logo
                tx = (WIDTH - text_img.width) // 2
                ty = HEIGHT // 2 + 100 + slide_y
                
                layer.paste(text_img, (tx, ty), text_img)
            
            bg = Image.alpha_composite(bg, layer)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
    
    # Encode
    logger.info("Encoding logo animation...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-shortest",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        await asyncio.wait_for(proc.communicate(), timeout=90)
    except:
        proc.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Logo animation done: {output_path}")
        return str(output_path)
    return ""


# =============================================================
# CHAT BUBBLES - iMessage Style
# =============================================================

def draw_chat_bubble(
    img: Image.Image,
    text: str,
    is_sender: bool,
    progress: float
) -> Image.Image:
    """Large centered chat bubble with smooth animation"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Colors
    if is_sender:
        bubble_color = (0, 132, 255)  # iMessage blue
        text_color = (255, 255, 255)
    else:
        bubble_color = (235, 235, 240)
        text_color = (0, 0, 0)
    
    font_size = 64
    font = get_font(font_size, "semibold")
    
    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Auto-fit long text
    while text_w > WIDTH * 0.7 and font_size > 36:
        font_size -= 4
        font = get_font(font_size, "semibold")
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
    # Padding
    pad_x = 50
    pad_y = 35
    
    bubble_w = text_w + pad_x * 2
    bubble_h = text_h + pad_y * 2
    
    # Animation
    scale = 0.7 + 0.3 * ease_out_back(min(1, progress * 1.4))
    alpha = int(255 * ease_out_quad(min(1, progress * 2)))
    
    actual_w = int(bubble_w * scale)
    actual_h = int(bubble_h * scale)
    actual_x = (WIDTH - actual_w) // 2
    actual_y = (HEIGHT - actual_h) // 2
    
    radius = min(40, actual_h // 2)
    
    # Shadow
    shadow_offset = 8
    draw.rounded_rectangle(
        (actual_x + shadow_offset, actual_y + shadow_offset, 
         actual_x + actual_w + shadow_offset, actual_y + actual_h + shadow_offset),
        radius=radius, fill=(0, 0, 0, alpha // 6)
    )
    
    # Bubble
    draw.rounded_rectangle(
        (actual_x, actual_y, actual_x + actual_w, actual_y + actual_h),
        radius=radius, fill=(*bubble_color, alpha)
    )
    
    # Tail
    if progress > 0.5:
        tail_alpha = int(alpha * min(1, (progress - 0.5) * 2))
        tail_size = 20
        if is_sender:
            tail = [
                (actual_x + actual_w - 25, actual_y + actual_h - 15),
                (actual_x + actual_w + tail_size, actual_y + actual_h + 10),
                (actual_x + actual_w - 8, actual_y + actual_h)
            ]
        else:
            tail = [
                (actual_x + 25, actual_y + actual_h - 15),
                (actual_x - tail_size, actual_y + actual_h + 10),
                (actual_x + 8, actual_y + actual_h)
            ]
        draw.polygon(tail, fill=(*bubble_color, tail_alpha))
    
    # Text
    text_alpha = int(alpha * min(1, progress * 2))
    scaled_font_size = int(font_size * scale)
    scaled_font = get_font(scaled_font_size, "semibold")
    
    bbox = draw.textbbox((0, 0), text, font=scaled_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    tx = actual_x + (actual_w - tw) // 2
    ty = actual_y + (actual_h - th) // 2
    
    draw.text((tx, ty), text, font=scaled_font, fill=(*text_color, text_alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# UI FORM
# =============================================================

def draw_ui_form(
    img: Image.Image,
    fields: List[str],
    button_text: str,
    button_color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Form with animated field appearance"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    field_w = 750
    field_h = 75
    spacing = 22
    
    total_h = len(fields) * (field_h + spacing) + 100
    start_y = (HEIGHT - total_h) // 2
    x = (WIDTH - field_w) // 2
    
    current_y = start_y
    num_elements = len(fields) + 1
    
    for i, placeholder in enumerate(fields):
        elem_progress = max(0, min(1, (progress * num_elements - i)))
        
        if elem_progress > 0:
            anim_progress = ease_out_back(min(1, elem_progress * 1.5))
            alpha = int(255 * ease_out_quad(min(1, elem_progress * 2)))
            offset_x = int((1 - anim_progress) * 100)
            scale = 0.95 + 0.05 * anim_progress
            
            actual_w = int(field_w * scale)
            actual_h = int(field_h * scale)
            fx = (WIDTH - actual_w) // 2 + offset_x
            fy = current_y
            
            radius = actual_h // 2
            draw.rounded_rectangle(
                (fx, fy, fx + actual_w, fy + actual_h),
                radius=radius, fill=(50, 50, 60, alpha)
            )
            
            font = get_font(32, "regular")
            draw.text((fx + 30, fy + 18), placeholder, font=font, fill=(150, 150, 160, alpha))
        
        current_y += field_h + spacing
    
    # Button
    btn_progress = max(0, min(1, (progress * num_elements - len(fields))))
    
    if btn_progress > 0:
        btn_anim = ease_out_back(min(1, btn_progress * 1.5))
        btn_alpha = int(255 * ease_out_quad(min(1, btn_progress * 2)))
        
        btn_scale = 0.9 + 0.1 * btn_anim
        btn_w = int(field_w * btn_scale)
        btn_h = int(80 * btn_scale)
        btn_x = (WIDTH - btn_w) // 2
        
        # Shadow
        draw.rounded_rectangle(
            (btn_x + 4, current_y + 4 + 20, btn_x + btn_w + 4, current_y + btn_h + 4 + 20),
            radius=btn_h // 2, fill=(0, 0, 0, btn_alpha // 5)
        )
        
        # Button
        draw.rounded_rectangle(
            (btn_x, current_y + 20, btn_x + btn_w, current_y + btn_h + 20),
            radius=btn_h // 2, fill=(*button_color, btn_alpha)
        )
        
        # Text
        btn_font = get_font(int(36 * btn_scale), "semibold")
        bbox = draw.textbbox((0, 0), button_text, font=btn_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        
        draw.text(
            (btn_x + (btn_w - tw) // 2, current_y + 20 + (btn_h - th) // 2 - 2),
            button_text, font=btn_font, fill=(255, 255, 255, btn_alpha)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# MAIN RENDER ENGINE
# =============================================================

async def render_professional_video(
    scenes: List[Dict],
    output_dir: Path,
    fps: int = 30
) -> str:
    """Render video with professional Apple-style effects"""
    output_path = output_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Calculate timings
    timings = []
    current = 0.0
    
    for scene in scenes:
        dur = scene.get("duration", 2.5)
        timings.append({"start": current, "end": current + dur, "scene": scene})
        current += dur
    
    total_dur = current
    total_frames = int(fps * total_dur)
    
    logger.info(f"Rendering {total_frames} frames, {len(scenes)} scenes, {total_dur}s")
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        global_progress = frame_num / total_frames
        
        # Find active scene
        active = None
        scene_progress = 0
        local_time = 0
        
        for t in timings:
            if t["start"] <= time_sec < t["end"]:
                active = t["scene"]
                local_time = time_sec - t["start"]
                scene_progress = local_time / (t["end"] - t["start"])
                break
        
        if not active:
            continue
        
        # Background
        bg_type = active.get("background", "white")
        if bg_type == "black" or bg_type == "dark":
            bg = create_solid_bg(WIDTH, HEIGHT, (10, 10, 15))
        elif bg_type == "gradient":
            colors = [tuple(c) for c in active.get("bg_colors", [[80, 60, 180], [60, 100, 200]])]
            bg = create_gradient_bg(WIDTH, HEIGHT, colors, global_progress)
        elif isinstance(bg_type, (list, tuple)) and len(bg_type) == 3:
            bg = create_solid_bg(WIDTH, HEIGHT, tuple(bg_type))
        else:
            bg = create_solid_bg(WIDTH, HEIGHT, (255, 255, 255))
        
        bg = bg.convert("RGBA")
        
        # Transition timing
        trans_in = active.get("trans_in", 0.25)
        trans_out = active.get("trans_out", 0.15)
        dur = active.get("duration", 2.5)
        
        if local_time < trans_in:
            vis = local_time / trans_in
        elif local_time > dur - trans_out:
            vis = (dur - local_time) / trans_out
        else:
            vis = 1.0
        
        vis = max(0, min(1, vis))
        
        scene_type = active.get("type", "text")
        content = active.get("content", {})
        
        # === TEXT - Word by word ===
        if scene_type == "text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [0, 0, 0]))
            underline = content.get("underline")
            
            # Determine if on dark or light bg for color
            if bg_type in ["black", "dark"]:
                color = (255, 255, 255)
            
            bg = draw_text_word_by_word(bg, text, vis, color, underline_word=underline)
        
        # === GRADIENT TEXT ===
        elif scene_type == "gradient_text":
            text = content.get("text", "Hello")
            colors = [tuple(c) for c in content.get("colors", [[0, 180, 255], [100, 220, 255]])]
            shimmer = global_progress * 2 if content.get("shimmer", True) else 0
            bg = draw_gradient_text(bg, text, vis, colors, shimmer_offset=shimmer)
        
        # === CHAT ===
        elif scene_type == "chat":
            text = content.get("text", "Hello")
            is_sender = content.get("sender", True)
            bg = draw_chat_bubble(bg, text, is_sender, vis)
        
        # === UI FORM ===
        elif scene_type == "ui_form":
            fields = content.get("fields", ["Email"])
            btn_text = content.get("button", "Submit")
            btn_color = tuple(content.get("btn_color", [0, 122, 255]))
            bg = draw_ui_form(bg, fields, btn_text, btn_color, vis)
        
        # === SIMPLE SCALE TEXT (for single word/phrase) ===
        elif scene_type == "scale_text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            bg = draw_text_scale_fade(bg, text, vis, color)
        
        # === CIRCLE SHAPE ===
        elif scene_type == "circle":
            size = content.get("size", 400)
            colors = [tuple(c) for c in content.get("colors", [[255, 100, 150], [100, 150, 255]])]
            glow = content.get("glow", True)
            bg = draw_gradient_circle(bg, vis, colors, size, glow)
        
        # === RECTANGLE SHAPE ===
        elif scene_type == "rect":
            width = content.get("width", 500)
            height = content.get("height", 300)
            radius = content.get("radius", 40)
            colors = [tuple(c) for c in content.get("colors", [[100, 200, 255], [200, 100, 255]])]
            rotation = content.get("rotation", 0)
            bg = draw_gradient_rect(bg, vis, colors, width, height, radius, rotation)
        
        # === MULTIPLE SHAPES ===
        elif scene_type == "shapes":
            shapes = content.get("shapes", [])
            bg = draw_multiple_shapes(bg, vis, shapes)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
        
        if frame_num % 30 == 0:
            logger.info(f"Frame {frame_num}/{total_frames}")
    
    # Encode
    logger.info("Encoding video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-shortest",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        await asyncio.wait_for(proc.communicate(), timeout=120)
    except:
        proc.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Done: {output_path}")
        return str(output_path)
    return ""


# =============================================================
# UNIVERSAL RENDER (Backward compatible)
# =============================================================

async def render_universal_video(script_data: Dict, output_dir: Path, fps: int = 30) -> str:
    """Convert script_data to scenes and render - supports ALL visual types"""
    elements = script_data.get("elements", [])
    scenes = []
    
    for idx, elem in enumerate(elements):
        t = elem.get("type", "text")
        dur = elem.get("duration", 2.5)
        
        # Determine background based on content type
        if t in ["gradient_text", "scale_text", "circle", "rect", "shapes"]:
            bg = "black"  # Shapes look better on dark
        elif t == "text":
            bg = "white"
        else:
            bg = elem.get("background", "white")
        
        # Override with explicit background if provided
        if "background" in elem:
            bg = elem["background"]
        if "bg_colors" in elem:
            bg = "gradient"
        
        scene = {
            "type": t,
            "duration": dur,
            "trans_in": 0.25,
            "trans_out": 0.15,
            "background": bg,
            "bg_colors": elem.get("bg_colors"),
            "content": {}
        }
        
        # === TEXT TYPES ===
        if t == "text":
            text_color = [0, 0, 0] if bg == "white" else [255, 255, 255]
            scene["content"] = {
                "text": elem.get("content", ""),
                "color": elem.get("color", text_color),
                "underline": elem.get("underline")
            }
        
        elif t == "gradient_text":
            scene["content"] = {
                "text": elem.get("content", ""),
                "colors": elem.get("gradient_colors", [[0, 180, 255], [100, 220, 255]]),
                "shimmer": elem.get("shimmer", True)
            }
            scene["background"] = "black"
        
        elif t == "scale_text":
            scene["content"] = {
                "text": elem.get("content", ""),
                "color": elem.get("color", [255, 255, 255])
            }
            scene["background"] = "black"
        
        # === SHAPE TYPES ===
        elif t == "circle":
            scene["content"] = {
                "size": elem.get("size", 400),
                "colors": elem.get("colors", [[255, 100, 150], [100, 150, 255]]),
                "glow": elem.get("glow", True)
            }
            scene["background"] = "black"
        
        elif t == "rect":
            scene["content"] = {
                "width": elem.get("width", 500),
                "height": elem.get("height", 300),
                "radius": elem.get("radius", 40),
                "colors": elem.get("colors", [[100, 200, 255], [200, 100, 255]]),
                "rotation": elem.get("rotation", 0)
            }
            scene["background"] = "black"
        
        elif t == "shapes":
            scene["content"] = {
                "shapes": elem.get("shapes", [])
            }
            scene["background"] = "black"
        
        # === UI TYPES ===
        elif t == "chat":
            msgs = elem.get("messages", [])
            for msg in msgs:
                scenes.append({
                    "type": "chat",
                    "duration": 2.0,
                    "trans_in": 0.25,
                    "trans_out": 0.15,
                    "background": "white",
                    "content": {
                        "text": msg.get("text", ""),
                        "sender": msg.get("sender", True)
                    }
                })
            continue
        
        elif t == "ui_form":
            scene["content"] = {
                "fields": elem.get("fields", ["Field"]),
                "button": elem.get("button_text", "Submit"),
                "btn_color": elem.get("button_color", [0, 122, 255])
            }
            scene["background"] = "white"
        
        scenes.append(scene)
    
    if not scenes:
        scenes = [{"type": "text", "duration": 2.5, "background": "white", "content": {"text": "Hello World"}}]
    
    return await render_professional_video(scenes, output_dir, fps)
