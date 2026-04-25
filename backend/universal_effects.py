"""
PROFESSIONAL VIDEO EFFECTS v7 - Fixed Version
Based on detailed frame-by-frame analysis of reference videos.

FIXES:
1. Text never goes outside screen bounds
2. Proper centering and alignment
3. Correct layering (no text hidden by background)
4. Zoom in/out effects
5. 3D device mockups
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

# Safe margins to prevent text going outside screen
SAFE_MARGIN_X = 60  # 60px from left/right edges
SAFE_MARGIN_Y = 100  # 100px from top/bottom edges
MAX_TEXT_WIDTH = WIDTH - (SAFE_MARGIN_X * 2)  # Maximum text width


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


def fit_text_to_width(
    text: str,
    max_width: int,
    initial_size: int,
    weight: str = "bold",
    min_size: int = 40
) -> Tuple[ImageFont.FreeTypeFont, int]:
    """
    Auto-fit text to maximum width by reducing font size if needed.
    Returns (font, final_size)
    """
    font_size = initial_size
    font = get_font(font_size, weight)
    
    # Measure text width
    temp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(temp)
    
    while font_size >= min_size:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            return font, font_size
        
        font_size -= 5
        font = get_font(font_size, weight)
    
    return font, min_size


def safe_draw_text(
    img: Image.Image,
    text: str,
    position: Tuple[float, float],  # (x_ratio, y_ratio) 0-1
    color: Tuple[int, int, int, int],
    font_size: int = 100,
    weight: str = "bold",
    align: str = "center",  # center, left, right
    max_width_ratio: float = 0.85
) -> Image.Image:
    """
    Draw text safely - never goes outside screen bounds.
    position is (x_ratio, y_ratio) where 0.5, 0.5 is center.
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Calculate max width
    max_width = int(WIDTH * max_width_ratio)
    
    # Auto-fit font size
    font, final_size = fit_text_to_width(text, max_width, font_size, weight)
    
    # Measure final text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Calculate position based on alignment
    y = int(HEIGHT * position[1]) - text_h // 2
    
    if align == "center":
        x = (WIDTH - text_w) // 2
    elif align == "left":
        x = SAFE_MARGIN_X
    else:  # right
        x = WIDTH - text_w - SAFE_MARGIN_X
    
    # Clamp to safe bounds
    x = max(SAFE_MARGIN_X, min(x, WIDTH - text_w - SAFE_MARGIN_X))
    y = max(SAFE_MARGIN_Y, min(y, HEIGHT - text_h - SAFE_MARGIN_Y))
    
    # Draw text
    draw.text((x, y), text, font=font, fill=color)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


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

def ease_out_bounce(t: float) -> float:
    """Bounce effect for emphasized text"""
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
# CAL.COM STYLE ANIMATIONS - Exact replication
# Based on frame-by-frame analysis of reference video
# =============================================================

# Purple accent color from Cal.com video
CALCOM_PURPLE = (138, 43, 226)  # Vibrant purple for emphasis
CALCOM_BLUE = (59, 130, 246)    # Blue for chat bubbles


def draw_calcom_text(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_size: int = 100,
    y_position: float = 0.5,
    emphasis_word: str = None,
    emphasis_color: Tuple[int, int, int] = None
) -> Image.Image:
    """
    Cal.com style text animation:
    - Fade in from 0 to full opacity
    - Slight upward slide (30px)
    - Scale from 0.9 to 1.0
    - Optional: emphasis word in different color with bounce
    - SAFE: text never goes outside screen bounds
    """
    if emphasis_color is None:
        emphasis_color = CALCOM_PURPLE
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Animation timing - appears in first 50% of scene duration
    if progress < 0.5:
        anim_t = progress / 0.5
    else:
        anim_t = 1.0
    
    # Easing
    eased = ease_out_cubic(anim_t)
    
    # Alpha: 0 -> 255
    alpha = int(255 * eased)
    
    # Slide up: 30px -> 0px
    slide_y = int(30 * (1 - eased))
    
    # Scale: 0.9 -> 1.0
    scale = 0.9 + 0.1 * eased
    scaled_size = int(font_size * scale)
    
    # FIRST: Auto-fit the FULL text to screen width
    max_width = MAX_TEXT_WIDTH
    temp_draw = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    font = get_font(scaled_size, "bold")
    
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    while text_w > max_width and scaled_size > 40:
        scaled_size -= 5
        font = get_font(scaled_size, "bold")
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
    # Calculate centered Y position with slide
    y = int(HEIGHT * y_position) - text_h // 2 + slide_y
    
    # Clamp Y to safe bounds
    y = max(SAFE_MARGIN_Y, min(y, HEIGHT - text_h - SAFE_MARGIN_Y))
    
    # Check for emphasis word
    if emphasis_word and emphasis_word in text:
        # Split text around emphasis word
        parts = text.split(emphasis_word, 1)
        
        before_text = parts[0]
        after_text = parts[1] if len(parts) > 1 else ""
        
        # Calculate widths with current font
        before_bbox = temp_draw.textbbox((0, 0), before_text, font=font) if before_text else (0, 0, 0, 0)
        emph_bbox = temp_draw.textbbox((0, 0), emphasis_word, font=font)
        after_bbox = temp_draw.textbbox((0, 0), after_text, font=font) if after_text else (0, 0, 0, 0)
        
        before_w = before_bbox[2] - before_bbox[0]
        emph_w = emph_bbox[2] - emph_bbox[0]
        after_w = after_bbox[2] - after_bbox[0]
        total_w = before_w + emph_w + after_w
        
        # Center position, clamped to safe bounds
        start_x = (WIDTH - total_w) // 2
        start_x = max(SAFE_MARGIN_X, min(start_x, WIDTH - total_w - SAFE_MARGIN_X))
        
        # Draw before text
        if before_text:
            draw.text((start_x, y), before_text, font=font, fill=(*color, alpha))
        
        # Draw emphasis word with bounce effect
        emph_x = start_x + before_w
        
        if progress > 0.3:
            emph_t = (progress - 0.3) / 0.4
            emph_t = min(1.0, emph_t)
            bounce = ease_out_bounce(emph_t)
            emph_scale = 0.8 + 0.2 * bounce
            emph_alpha = int(255 * min(1.0, emph_t * 1.5))
            
            emph_font = get_font(int(scaled_size * emph_scale), "bold")
            draw.text((emph_x, y), emphasis_word, font=emph_font, fill=(*emphasis_color, emph_alpha))
        
        # Draw after text
        if after_text:
            draw.text((emph_x + emph_w, y), after_text, font=font, fill=(*color, alpha))
    else:
        # Simple text without emphasis
        x = (WIDTH - text_w) // 2
        x = max(SAFE_MARGIN_X, min(x, WIDTH - text_w - SAFE_MARGIN_X))
        
        draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_calcom_chat_bubble(
    img: Image.Image,
    text: str,
    progress: float,
    is_sender: bool = True,  # True = blue (right), False = gray (left)
    y_position: float = 0.5
) -> Image.Image:
    """
    Cal.com/iMessage style chat bubble:
    - Slides in from left (receiver) or right (sender)
    - Text types in character by character
    - Bubble has rounded corners and tail
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Colors
    if is_sender:
        bubble_color = CALCOM_BLUE  # Blue for sender
        text_color = (255, 255, 255)
    else:
        bubble_color = (229, 229, 234)  # Light gray for receiver
        text_color = (0, 0, 0)
    
    # Animation timing
    # Phase 1 (0-0.3): Bubble slides in
    # Phase 2 (0.3-1.0): Text types in
    
    if progress < 0.3:
        slide_t = progress / 0.3
        slide_t = ease_out_cubic(slide_t)
        bubble_alpha = int(255 * slide_t)
        text_progress = 0
    else:
        slide_t = 1.0
        bubble_alpha = 255
        text_progress = (progress - 0.3) / 0.7
    
    # Typing effect
    visible_chars = int(len(text) * ease_out_quad(text_progress))
    display_text = text[:visible_chars] if visible_chars > 0 else ""
    
    if not display_text and progress < 0.3:
        display_text = " "  # Show empty bubble
    
    # Font
    font_size = 48
    font = get_font(font_size, "medium")
    
    # Measure text (full text for consistent bubble size)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Bubble dimensions
    padding_h = 30
    padding_v = 20
    bubble_w = text_w + padding_h * 2
    bubble_h = text_h + padding_v * 2
    corner_radius = 25
    
    # Position - slide from edge
    if is_sender:
        final_x = WIDTH - bubble_w - 60
        start_x = WIDTH + 50
        bubble_x = int(start_x + (final_x - start_x) * slide_t)
    else:
        final_x = 60
        start_x = -bubble_w - 50
        bubble_x = int(start_x + (final_x - start_x) * slide_t)
    
    bubble_y = int(HEIGHT * y_position) - bubble_h // 2
    
    # Draw shadow
    shadow_offset = 4
    draw.rounded_rectangle(
        (bubble_x + shadow_offset, bubble_y + shadow_offset, 
         bubble_x + bubble_w + shadow_offset, bubble_y + bubble_h + shadow_offset),
        radius=corner_radius,
        fill=(0, 0, 0, 20)
    )
    
    # Draw bubble
    draw.rounded_rectangle(
        (bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h),
        radius=corner_radius,
        fill=(*bubble_color, bubble_alpha)
    )
    
    # Draw text
    text_x = bubble_x + padding_h
    text_y = bubble_y + padding_v
    text_alpha = int(255 * min(1.0, text_progress * 2)) if display_text.strip() else 0
    
    if display_text.strip():
        draw.text((text_x, text_y), display_text, font=font, fill=(*text_color, text_alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# ZOOM / CAMERA EFFECTS
# =============================================================

def apply_zoom_effect(
    img: Image.Image,
    zoom: float,  # 1.0 = normal, 1.5 = 50% zoom in, 0.8 = 20% zoom out
    center: Tuple[float, float] = (0.5, 0.5)  # Center point for zoom (0-1)
) -> Image.Image:
    """
    Apply zoom effect to image.
    zoom > 1.0 = zoom in (closer)
    zoom < 1.0 = zoom out (farther)
    """
    if zoom == 1.0:
        return img
    
    w, h = img.size
    
    # Calculate new size
    new_w = int(w * zoom)
    new_h = int(h * zoom)
    
    # Resize
    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Calculate crop/paste position based on center
    cx = int(center[0] * new_w)
    cy = int(center[1] * new_h)
    
    if zoom > 1.0:
        # Zoom in - crop the center
        left = cx - w // 2
        top = cy - h // 2
        right = left + w
        bottom = top + h
        
        # Clamp to bounds
        left = max(0, min(left, new_w - w))
        top = max(0, min(top, new_h - h))
        
        return resized.crop((left, top, left + w, top + h))
    else:
        # Zoom out - paste on larger canvas
        result = Image.new("RGB", (w, h), (255, 255, 255))
        paste_x = (w - new_w) // 2
        paste_y = (h - new_h) // 2
        result.paste(resized, (paste_x, paste_y))
        return result


def animate_zoom(
    progress: float,
    start_zoom: float = 1.0,
    end_zoom: float = 1.2,
    easing: str = "ease_out"
) -> float:
    """Calculate zoom value for current progress"""
    if easing == "ease_out":
        t = ease_out_cubic(progress)
    elif easing == "ease_in":
        t = ease_in_cubic(progress)
    else:
        t = progress
    
    return start_zoom + (end_zoom - start_zoom) * t


# =============================================================
# 3D DEVICE MOCKUPS
# =============================================================

def create_iphone_16_frame(
    screen_content: Image.Image,
    frame_width: int = 420,
    frame_height: int = 860
) -> Image.Image:
    """
    Create a realistic iPhone 16 frame with titanium look.
    Screen content is placed inside the frame.
    """
    img = Image.new('RGBA', (frame_width, frame_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # iPhone 16 dimensions
    corner_radius = 58
    bezel = 12
    
    # Titanium frame (natural titanium color)
    frame_color = (195, 195, 200)
    
    # Outer frame with subtle gradient effect
    draw.rounded_rectangle(
        [0, 0, frame_width-1, frame_height-1],
        radius=corner_radius,
        fill=frame_color
    )
    
    # Inner edge (darker for depth)
    edge_color = (60, 60, 62)
    draw.rounded_rectangle(
        [bezel-2, bezel-2, frame_width-bezel+1, frame_height-bezel+1],
        radius=corner_radius - bezel + 3,
        fill=edge_color
    )
    
    # Screen bezel (true black)
    bezel_color = (15, 15, 17)
    draw.rounded_rectangle(
        [bezel, bezel, frame_width-bezel-1, frame_height-bezel-1],
        radius=corner_radius - bezel,
        fill=bezel_color
    )
    
    # Screen area
    screen_margin = bezel + 4
    screen_radius = corner_radius - bezel - 2
    screen_w = frame_width - screen_margin * 2
    screen_h = frame_height - screen_margin * 2
    
    # Resize and place screen content
    content_resized = screen_content.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    # Create rounded mask for screen
    screen_mask = Image.new('L', (screen_w, screen_h), 0)
    mask_draw = ImageDraw.Draw(screen_mask)
    mask_draw.rounded_rectangle(
        [0, 0, screen_w-1, screen_h-1],
        radius=screen_radius,
        fill=255
    )
    
    # Paste screen with rounded corners
    screen_layer = Image.new('RGBA', (screen_w, screen_h), (0, 0, 0, 0))
    screen_layer.paste(content_resized, (0, 0))
    screen_layer.putalpha(screen_mask)
    img.paste(screen_layer, (screen_margin, screen_margin), screen_layer)
    
    # Dynamic Island
    island_width = 126
    island_height = 37
    island_x = (frame_width - island_width) // 2
    island_y = screen_margin + 12
    draw.rounded_rectangle(
        [island_x, island_y, island_x + island_width, island_y + island_height],
        radius=island_height // 2,
        fill=(10, 10, 12)
    )
    
    # Camera lens in Dynamic Island
    lens_size = 12
    lens_x = island_x + island_width - 30
    lens_y = island_y + (island_height - lens_size) // 2
    draw.ellipse(
        [lens_x, lens_y, lens_x + lens_size, lens_y + lens_size],
        fill=(25, 25, 30)
    )
    
    # Side button (power - right side)
    button_w = 4
    button_h = 70
    button_y = frame_height // 3 - 20
    draw.rectangle(
        [frame_width - 3, button_y, frame_width, button_y + button_h],
        fill=(170, 170, 175)
    )
    
    # Volume buttons (left side)
    for y_off in [frame_height // 4 - 10, frame_height // 4 + 45]:
        draw.rectangle(
            [0, y_off, 3, y_off + 45],
            fill=(170, 170, 175)
        )
    
    # Action button (left, above volume)
    action_y = frame_height // 4 - 55
    draw.rounded_rectangle(
        [0, action_y, 3, action_y + 35],
        radius=2,
        fill=(170, 170, 175)
    )
    
    return img


def create_3d_phone_mockup(
    screen_content: Image.Image,
    rotation_x: float = 0,  # Tilt forward/backward (degrees)
    rotation_y: float = 15,  # Rotate left/right (degrees)
    device_color: Tuple[int, int, int] = (40, 40, 40),
    shadow: bool = True,
    float_offset_y: float = 0  # For floating animation
) -> Image.Image:
    """
    Create a 3D iPhone mockup with screen content and floating animation.
    """
    # Create the iPhone frame with screen
    phone = create_iphone_16_frame(screen_content)
    
    # Add padding for transforms and shadow
    padding = 120
    canvas_w = phone.width + padding * 2
    canvas_h = phone.height + padding * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    
    # Position phone with float offset
    phone_x = padding
    phone_y = padding + int(float_offset_y)
    canvas.paste(phone, (phone_x, phone_y), phone)
    
    # Apply 3D perspective transform
    if rotation_y != 0 or rotation_x != 0:
        width, height = canvas.size
        
        # Calculate perspective distortion
        skew_y = math.tan(math.radians(rotation_y)) * 0.08
        skew_x = math.tan(math.radians(rotation_x)) * 0.05
        
        # Source corners
        src = [(0, 0), (width, 0), (width, height), (0, height)]
        
        # Destination corners with perspective
        if rotation_y > 0:
            # Rotated right - left side closer
            dst = [
                (int(width * skew_y * 0.3), int(height * 0.03)),
                (width, int(height * 0.01)),
                (width, int(height * 0.99)),
                (int(width * skew_y * 0.3), int(height * 0.97))
            ]
        elif rotation_y < 0:
            # Rotated left - right side closer
            dst = [
                (0, int(height * 0.01)),
                (int(width - width * abs(skew_y) * 0.3), int(height * 0.03)),
                (int(width - width * abs(skew_y) * 0.3), int(height * 0.97)),
                (0, int(height * 0.99))
            ]
        else:
            dst = src
        
        coeffs = find_perspective_coeffs(src, dst)
        canvas = canvas.transform((width, height), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    
    # Add soft shadow
    if shadow:
        shadow_img = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        
        # Shadow under phone
        shadow_y = padding + phone.height - 30 + int(float_offset_y)
        shadow_w = int(phone.width * 0.7)
        shadow_x = (canvas_w - shadow_w) // 2
        
        # Elliptical shadow
        for i in range(40, 0, -2):
            alpha = int(25 * (i / 40))
            expand = (40 - i) * 2
            shadow_draw.ellipse(
                [shadow_x - expand, shadow_y - 10, shadow_x + shadow_w + expand, shadow_y + 30 + expand//3],
                fill=(0, 0, 0, alpha)
            )
        
        # Blur shadow
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=15))
        
        # Composite shadow under phone
        result = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        result.paste(shadow_img, (0, 0), shadow_img)
        result.paste(canvas, (0, 0), canvas)
        canvas = result
    
    return canvas


async def render_video_on_device(
    video_path: str,
    output_dir: Path,
    device_type: str = "phone",
    rotation_y: float = 12,
    fps: int = 30,
    duration: float = None,
    bg_color: Tuple[int, int, int] = (35, 40, 35),
    use_3d_model: bool = True,
    animation_style: str = "reference",  # "reference", "center", "dramatic", "phone_text"
    text: str = "",
    phone_position: str = "right",
    aspect_ratio: str = "16:9"  # "16:9" (landscape) or "9:16" (portrait)
) -> str:
    """
    Render video playing on a 3D iPhone 16 mockup with smooth animation.
    
    Args:
        video_path: Path to the video to display on device
        output_dir: Directory for output
        device_type: "phone", "tablet", "laptop"
        rotation_y: Base 3D rotation angle in degrees
        fps: Output FPS
        duration: Max duration (None = full video length)
        bg_color: Background color (gradient base)
        use_3d_model: If True, use real 3D iPhone model
        animation_style: "reference", "center", "dramatic", or "phone_text"
        text: Text to show alongside phone (for phone_text)
        phone_position: "left" or "right" (for phone_text)
        aspect_ratio: "16:9" for landscape or "9:16" for portrait
    
    Returns:
        Path to rendered video with device mockup
    """
    from iphone_compositor import (
        create_simple_float_frame, 
        create_animated_iphone_frame,
        create_phone_with_text_frame,
        render_dynamic_phone
    )
    
    # Determine output dimensions based on aspect ratio
    if aspect_ratio == "16:9":
        output_width = 1920
        output_height = 1080
    else:  # 9:16
        output_width = 1080
        output_height = 1920
    
    output_size = (output_width, output_height)
    
    output_path = output_dir / f"device_video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"device_frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    video_frames_dir = output_dir / f"video_frames_{uuid.uuid4().hex[:8]}"
    video_frames_dir.mkdir(exist_ok=True)
    
    # Get video info
    try:
        probe_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", 
                     "-of", "default=noprint_wrappers=1:nokey=1", video_path]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        video_duration = float(result.stdout.strip())
    except:
        video_duration = 5.0
    
    if duration:
        video_duration = min(duration, video_duration)
    
    total_frames = int(video_duration * fps)
    
    # Extract frames from input video
    logger.info(f"Extracting {total_frames} frames from input video...")
    extract_cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-vf", f"fps={fps}",
        str(video_frames_dir / "vf%05d.png")
    ]
    proc = subprocess.run(extract_cmd, capture_output=True)
    
    # Get list of extracted frames
    video_frame_files = sorted(video_frames_dir.glob("vf*.png"))
    
    if not video_frame_files:
        logger.error("No frames extracted from input video")
        shutil.rmtree(frames_dir, ignore_errors=True)
        shutil.rmtree(video_frames_dir, ignore_errors=True)
        return ""
    
    # Check if 3D iPhone 16 renders exist (from Blender)
    iphone_16_renders_exist = Path("/app/backend/iphone_16_renders/iphone16_angle_0.png").exists()
    
    if use_3d_model and device_type == "phone" and iphone_16_renders_exist:
        logger.info(f"Creating {total_frames} frames with 3D iPhone 16 ({animation_style} animation, {aspect_ratio})...")
        
        for i in range(total_frames):
            time_seconds = i / fps
            time_progress = i / total_frames
            
            # Get video frame
            vf_idx = i % len(video_frame_files)
            video_frame = Image.open(video_frame_files[vf_idx]).convert("RGB")
            
            if animation_style == "phone_text":
                # Phone + text layout
                frame = create_phone_with_text_frame(
                    video_frame=video_frame,
                    text=text or "Your Text Here",
                    time_progress=time_progress,
                    output_size=output_size,
                    bg_color=bg_color,
                    phone_position=phone_position
                )
            elif animation_style == "camera" or animation_style == "reference":
                # Camera movement animation (zoom + rotate) like reference video
                frame = render_dynamic_phone(
                    video_frame=video_frame,
                    time_progress=time_progress,
                    output_size=output_size,
                    bg_color=bg_color,
                    animation_style="camera",
                    position=phone_position if phone_position in ["center", "left", "right"] else "center"
                )
            elif animation_style == "float":
                # Simple floating animation
                frame = render_dynamic_phone(
                    video_frame=video_frame,
                    time_progress=time_progress,
                    output_size=output_size,
                    bg_color=bg_color,
                    animation_style="float",
                    position=phone_position if phone_position in ["center", "left", "right"] else "center"
                )
            else:
                # Static or default
                frame = render_dynamic_phone(
                    video_frame=video_frame,
                    time_progress=time_progress,
                    output_size=output_size,
                    bg_color=bg_color,
                    animation_style="float",
                    position="center"
                )
            
            # Save frame
            frame_path = frames_dir / f"frame_{i:05d}.png"
            frame.save(frame_path, "PNG")
            
            if i % 30 == 0:
                logger.info(f"Frame {i}/{total_frames}")
    else:
        # Fallback to PIL-based mockup
        logger.info(f"Using PIL-based mockup, creating {total_frames} frames ({aspect_ratio})...")
        
        float_amplitude = 25
        float_period = 3.5
        rotation_amplitude = 4
        
        for i in range(total_frames):
            time_seconds = i / fps
            
            float_offset = math.sin(time_seconds * 2 * math.pi / float_period) * float_amplitude
            rotation_offset = math.sin(time_seconds * 2 * math.pi / (float_period * 1.3)) * rotation_amplitude
            current_rotation = rotation_y + rotation_offset
            
            vf_idx = i % len(video_frame_files)
            screen_frame = Image.open(video_frame_files[vf_idx]).convert("RGB")
            
            if device_type == "phone":
                mockup = create_3d_phone_mockup(
                    screen_frame, 
                    rotation_y=current_rotation,
                    float_offset_y=float_offset
                )
            elif device_type == "tablet":
                mockup = create_3d_tablet_mockup(screen_frame, rotation_y=current_rotation)
            else:
                mockup = create_3d_laptop_mockup(screen_frame, rotation_y=current_rotation)
            
            bg = create_solid_bg(output_width, output_height, bg_color)
            mockup_x = (output_width - mockup.width) // 2
            mockup_y = (output_height - mockup.height) // 2
            bg.paste(mockup, (mockup_x, mockup_y), mockup)
            
            frame_path = frames_dir / f"frame_{i:05d}.png"
            bg.save(frame_path, "PNG", optimize=True)
            
            if i % 30 == 0:
                logger.info(f"Frame {i}/{total_frames}")
    
    # Encode video
    logger.info("Encoding device mockup video...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        await asyncio.wait_for(proc.communicate(), timeout=300)
    except asyncio.TimeoutError:
        proc.kill()
    
    # Cleanup
    shutil.rmtree(frames_dir, ignore_errors=True)
    shutil.rmtree(video_frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Device mockup video done: {output_path}")
        return str(output_path)
    return ""


def create_3d_tablet_mockup(
    screen_content: Image.Image,
    rotation_y: float = 10,
    device_color: Tuple[int, int, int] = (50, 50, 50)
) -> Image.Image:
    """Create 3D tablet mockup (iPad-like)"""
    tablet_w = 600
    tablet_h = 820
    bezel = 30
    corner_radius = 30
    
    tablet = Image.new("RGBA", (tablet_w + 100, tablet_h + 100), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tablet)
    
    # Shadow
    draw.rounded_rectangle(
        (50 + 12, 50 + 12, 50 + tablet_w + 12, 50 + tablet_h + 12),
        radius=corner_radius, fill=(0, 0, 0, 50)
    )
    
    # Body
    draw.rounded_rectangle(
        (50, 50, 50 + tablet_w, 50 + tablet_h),
        radius=corner_radius, fill=(*device_color, 255)
    )
    
    # Screen
    screen_x = 50 + bezel
    screen_y = 50 + bezel
    screen_w = tablet_w - bezel * 2
    screen_h = tablet_h - bezel * 2
    
    content_resized = screen_content.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    tablet.paste(content_resized, (screen_x, screen_y))
    
    # Apply perspective
    if rotation_y != 0:
        skew = math.tan(math.radians(rotation_y)) * 0.08
        width, height = tablet.size
        coeffs = find_perspective_coeffs(
            [(0, 0), (width, 0), (width, height), (0, height)],
            [
                (int(width * abs(skew) if rotation_y > 0 else 0), int(height * 0.03)),
                (int(width - width * abs(skew) if rotation_y < 0 else width), int(height * 0.03)),
                (int(width - width * abs(skew) if rotation_y < 0 else width), int(height * 0.97)),
                (int(width * abs(skew) if rotation_y > 0 else 0), int(height * 0.97))
            ]
        )
        tablet = tablet.transform((width, height), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    
    return tablet


def create_3d_laptop_mockup(
    screen_content: Image.Image,
    rotation_y: float = 5,
    device_color: Tuple[int, int, int] = (180, 180, 185)
) -> Image.Image:
    """Create 3D laptop mockup (MacBook-like)"""
    screen_w = 800
    screen_h = 500
    bezel = 25
    base_h = 30
    
    total_w = screen_w + 100
    total_h = screen_h + base_h + 100
    
    laptop = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(laptop)
    
    # Screen frame (lid)
    lid_x, lid_y = 50, 50
    draw.rounded_rectangle(
        (lid_x, lid_y, lid_x + screen_w, lid_y + screen_h),
        radius=15, fill=(*device_color, 255)
    )
    
    # Screen content
    inner_x = lid_x + bezel
    inner_y = lid_y + bezel
    inner_w = screen_w - bezel * 2
    inner_h = screen_h - bezel * 2
    
    content_resized = screen_content.resize((inner_w, inner_h), Image.Resampling.LANCZOS)
    laptop.paste(content_resized, (inner_x, inner_y))
    
    # Base/keyboard
    base_y = lid_y + screen_h
    draw.rounded_rectangle(
        (lid_x - 10, base_y, lid_x + screen_w + 10, base_y + base_h),
        radius=5, fill=(150, 150, 155, 255)
    )
    
    return laptop


def find_perspective_coeffs(source_coords, target_coords):
    """Calculate perspective transform coefficients"""
    import numpy as np
    
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    
    A = np.matrix(matrix, dtype=float)
    B = np.array([s for p in source_coords for s in p]).reshape(8)
    
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8).tolist()


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
# ADVANCED TEXT EFFECTS - Based on Video Analysis
# =============================================================

def draw_smooth_fade_text(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    y_position: float = 0.5,  # 0-1, relative to screen height
    x_align: str = "center",  # center, left, right
    slide_from: str = "none",  # none, left, right, bottom
    scale_effect: bool = True
) -> Image.Image:
    """
    Smooth text appearance with fade + optional scale + optional slide.
    Based on Cal.com video analysis - clean, professional text reveals.
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Easing for smooth appearance
    fade_progress = ease_out_cubic(min(1, progress * 1.5))
    alpha = int(255 * fade_progress)
    
    # Scale effect (0.95 -> 1.0)
    if scale_effect:
        scale = 0.95 + 0.05 * ease_out_cubic(min(1, progress * 1.2))
    else:
        scale = 1.0
    
    scaled_size = int(font_size * scale)
    font = get_font(scaled_size, "semibold")
    
    # Measure and auto-fit text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    max_width = int(WIDTH * 0.85)
    while text_w > max_width and scaled_size > 40:
        scaled_size -= 4
        font = get_font(scaled_size, "semibold")
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
    # Calculate position
    if x_align == "center":
        x = (WIDTH - text_w) // 2
    elif x_align == "left":
        x = int(WIDTH * 0.1)
    else:  # right
        x = int(WIDTH * 0.9) - text_w
    
    y = int(HEIGHT * y_position) - text_h // 2
    
    # Slide animation
    slide_distance = 50
    slide_progress = ease_out_cubic(min(1, progress * 1.3))
    
    if slide_from == "left":
        x -= int(slide_distance * (1 - slide_progress))
    elif slide_from == "right":
        x += int(slide_distance * (1 - slide_progress))
    elif slide_from == "bottom":
        y += int(slide_distance * (1 - slide_progress))
    
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_animated_gradient_text(
    img: Image.Image,
    text: str,
    time: float,  # 0-1 for animation cycle
    base_color: Tuple[int, int, int] = (255, 255, 255),
    gradient_colors: List[Tuple[int, int, int]] = None,
    font_size: int = 160,
    y_position: float = 0.5,
    gradient_width: float = 0.5  # Width of gradient band (0-1)
) -> Image.Image:
    """
    Text with animated gradient sweep (like MacBook Neo video).
    Gradient moves horizontally across text from left to right.
    Colors: purple (#5A4D7C) -> blue (#6A8BC4) -> white (#F0EFF4)
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    if gradient_colors is None:
        # Default: dramatic purple to white (from video analysis)
        gradient_colors = [
            (120, 80, 200),   # Vibrant purple
            (150, 120, 220),  # Light purple
            (200, 180, 240),  # Pale purple
            (240, 240, 255),  # Near white
            (255, 255, 255),  # White
        ]
    
    font = get_font(font_size, "bold")
    
    # Measure text
    temp_draw = ImageDraw.Draw(layer)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Auto-fit
    max_width = int(WIDTH * 0.85)
    while text_w > max_width and font_size > 60:
        font_size -= 5
        font = get_font(font_size, "bold")
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
    x = (WIDTH - text_w) // 2
    y = int(HEIGHT * y_position) - text_h // 2
    
    # Create text image with gradient
    text_img = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # Calculate gradient position (sweeping left to right)
    # time 0->1 means gradient moves from left to right of text
    gradient_center = -gradient_width + time * (1 + gradient_width * 2)
    
    for px in range(text_w + 20):
        rel_x = px / (text_w + 20)
        
        # Distance from gradient center
        dist = abs(rel_x - gradient_center)
        
        if dist < gradient_width:
            # Inside gradient band - use gradient colors
            t = 1 - (dist / gradient_width)  # 0 at edge, 1 at center
            t = ease_out_quad(t)
            
            # Interpolate through gradient colors
            color_t = t
            idx = min(int(color_t * (len(gradient_colors) - 1)), len(gradient_colors) - 2)
            local_t = (color_t * (len(gradient_colors) - 1)) - idx
            
            c1, c2 = gradient_colors[idx], gradient_colors[idx + 1]
            r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
            g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
            b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        else:
            # Outside gradient - use base color
            r, g, b = base_color
        
        text_draw.line((px, 0, px, text_h + 20), fill=(r, g, b, 255))
    
    # Create mask from text
    mask = Image.new("L", text_img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10, 10), text, font=font, fill=255)
    
    text_img.putalpha(mask)
    
    layer.paste(text_img, (x - 10, y - 10), text_img)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_multiline_text_sequential(
    img: Image.Image,
    lines: List[str],
    progress: float,
    colors: List[Tuple[int, int, int]] = None,
    font_sizes: List[int] = None,
    y_start: float = 0.35,
    line_spacing: int = 80,
    stagger_delay: float = 0.2
) -> Image.Image:
    """
    Sequential multi-line text animation.
    Each line appears with fade + scale, staggered timing.
    Based on full animation video analysis.
    """
    if colors is None:
        colors = [(255, 255, 255)] * len(lines)
    if font_sizes is None:
        font_sizes = [140] * len(lines)
    
    result = img.convert("RGBA")
    
    for i, line in enumerate(lines):
        # Calculate timing for this line
        line_start = i * stagger_delay
        line_progress = max(0, min(1, (progress - line_start) / (1 - stagger_delay * (len(lines) - 1))))
        
        if line_progress <= 0:
            continue
        
        color = colors[i] if i < len(colors) else (255, 255, 255)
        font_size = font_sizes[i] if i < len(font_sizes) else 140
        
        y_pos = y_start + (i * line_spacing / HEIGHT)
        
        result = draw_smooth_fade_text(
            result,
            line,
            line_progress,
            color=color,
            font_size=font_size,
            y_position=y_pos,
            scale_effect=True,
            slide_from="right" if i % 2 == 0 else "left"
        )
    
    return result


def draw_chat_bubble(
    img: Image.Image,
    text: str,
    progress: float,
    is_sender: bool = True,
    y_position: float = 0.5,
    bubble_color: Tuple[int, int, int] = None,
    text_color: Tuple[int, int, int] = (255, 255, 255),
    typing_effect: bool = True
) -> Image.Image:
    """
    iMessage-style chat bubble with typing animation.
    Based on Cal.com video - text types in character by character.
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    if bubble_color is None:
        bubble_color = (59, 130, 246) if is_sender else (75, 85, 99)  # Blue or gray
    
    # Animation
    bubble_alpha = int(255 * ease_out_cubic(min(1, progress * 2)))
    
    # Typing effect - reveal characters progressively
    if typing_effect:
        char_progress = ease_out_quad(min(1, progress * 1.5))
        visible_chars = int(len(text) * char_progress)
        display_text = text[:visible_chars]
    else:
        display_text = text
    
    if not display_text:
        return img
    
    font_size = 48
    font = get_font(font_size, "medium")
    
    # Measure text
    bbox = draw.textbbox((0, 0), display_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Bubble dimensions
    padding = 30
    bubble_w = text_w + padding * 2
    bubble_h = text_h + padding * 2
    corner_radius = 25
    
    # Position
    if is_sender:
        bubble_x = WIDTH - bubble_w - 60
    else:
        bubble_x = 60
    
    bubble_y = int(HEIGHT * y_position) - bubble_h // 2
    
    # Slide in animation
    slide_progress = ease_out_cubic(min(1, progress * 1.5))
    slide_offset = int(100 * (1 - slide_progress))
    if is_sender:
        bubble_x += slide_offset
    else:
        bubble_x -= slide_offset
    
    # Draw bubble with shadow
    shadow_offset = 4
    shadow_color = (0, 0, 0, 30)
    draw.rounded_rectangle(
        (bubble_x + shadow_offset, bubble_y + shadow_offset, 
         bubble_x + bubble_w + shadow_offset, bubble_y + bubble_h + shadow_offset),
        radius=corner_radius,
        fill=shadow_color
    )
    
    # Draw bubble
    draw.rounded_rectangle(
        (bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h),
        radius=corner_radius,
        fill=(*bubble_color, bubble_alpha)
    )
    
    # Draw text
    text_x = bubble_x + padding
    text_y = bubble_y + padding
    text_alpha = int(255 * ease_out_quad(min(1, progress * 2)))
    draw.text((text_x, text_y), display_text, font=font, fill=(*text_color, text_alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# LOGO ANIMATION - HORIZONTAL: Logo LEFT, Text RIGHT
# Like Discord reference video
# =============================================================

async def render_logo_animation(
    logo_path: str,
    brand_name: str,
    bg_color: Tuple[int, int, int],
    output_dir: Path,
    fps: int = 30,
    duration: float = 4.0,
    outro_effect: str = "none",
    outro_repeat: int = 1
) -> str:
    """
    Logo animation like Discord:
    1. Logo appears in CENTER alone
    2. Logo moves LEFT
    3. Text appears on RIGHT
    Final: [LOGO] [TEXT] - horizontal, same line, fits within screen
    """
    output_path = output_dir / f"logo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    total_frames = int(fps * duration)
    
    # Text color
    brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
    text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
    
    # Load original logo
    try:
        logo_orig = Image.open(logo_path).convert("RGBA")
    except Exception as e:
        logger.error(f"Failed to load logo: {e}")
        logo_orig = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
        d = ImageDraw.Draw(logo_orig)
        d.ellipse((10, 10, 190, 190), fill=(200, 200, 200, 255))
    
    # Target: composition should fill ~85% of screen WIDTH
    TARGET_WIDTH_PERCENT = 0.85
    target_total_width = int(WIDTH * TARGET_WIDTH_PERCENT)
    
    # FIXED APPROACH: Set MINIMUM font size first, then size logo to match
    MIN_FONT_SIZE = 180  # Minimum font size for readability on 1920px screen
    
    # Initial sizing - logo height ~20% of screen for more impact
    logo_target_height = int(HEIGHT * 0.20)
    ratio = logo_target_height / logo_orig.height
    logo = logo_orig.resize((int(logo_orig.width * ratio), logo_target_height), Image.Resampling.LANCZOS)
    
    # If logo is too wide (landscape orientation), resize to max width
    max_logo_width = int(WIDTH * 0.35)  # Logo should not exceed 35% of width
    if logo.width > max_logo_width:
        ratio = max_logo_width / logo.width
        logo = logo.resize((max_logo_width, int(logo.height * ratio)), Image.Resampling.LANCZOS)
    
    # Gap between logo and text
    gap = int(logo.height * 0.4)  # Gap based on height, not width
    
    # Font size - start with MIN_FONT_SIZE
    font_size = max(MIN_FONT_SIZE, int(logo.height * 0.85))
    font = get_font(font_size, "bold")
    
    # Measure text
    temp = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp)
    bbox = temp_draw.textbbox((0, 0), brand_name, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Calculate total width
    total_w = logo.width + gap + text_w
    
    # Scale down if exceeds target width - but PROTECT text size
    if total_w > target_total_width:
        # Calculate how much we need to shrink
        scale_factor = target_total_width / total_w
        
        # If scale would make font too small, shrink ONLY the logo
        new_font_size = int(font_size * scale_factor)
        if new_font_size < MIN_FONT_SIZE:
            # Keep font at minimum, shrink only logo
            font_size = MIN_FONT_SIZE
            font = get_font(font_size, "bold")
            bbox = temp_draw.textbbox((0, 0), brand_name, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            # Available width for logo and gap
            available = target_total_width - text_w - int(20)  # small gap
            gap = 50
            new_logo_w = available - gap
            if new_logo_w > 50:
                ratio = new_logo_w / logo.width
                new_logo_h = int(logo.height * ratio)
                logo = logo.resize((new_logo_w, max(50, new_logo_h)), Image.Resampling.LANCZOS)
        else:
            # Scale both proportionally
            new_logo_w = int(logo.width * scale_factor)
            new_logo_h = int(logo.height * scale_factor)
            logo = logo.resize((new_logo_w, new_logo_h), Image.Resampling.LANCZOS)
            font_size = new_font_size
            font = get_font(font_size, "bold")
            bbox = temp_draw.textbbox((0, 0), brand_name, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            gap = int(logo.height * 0.4)
        
        total_w = logo.width + gap + text_w
    
    # Final positions (centered as a group)
    start_x = (WIDTH - total_w) // 2
    center_y = HEIGHT // 2
    
    final_logo_x = start_x
    final_logo_y = center_y - logo.height // 2
    final_text_x = start_x + logo.width + gap
    final_text_y = center_y - text_h // 2
    
    # Logo starts at center
    logo_center_x = (WIDTH - logo.width) // 2
    
    # Timings
    phase1_end = 1.0      # Logo appears alone
    phase2_end = 2.0      # Logo moves left, text appears
    outro_start = 2.5
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        
        bg = create_solid_bg(WIDTH, HEIGHT, bg_color).convert("RGBA")
        
        # ===================
        # PHASE 1: Logo appears in CENTER (alone)
        # ===================
        if time_sec < phase1_end:
            t = time_sec / phase1_end
            
            logo_scale = ease_out_cubic(t)
            logo_alpha = ease_out_quad(t)
            logo_x = logo_center_x
            logo_y = center_y - int(logo.height * logo_scale) // 2
            
            text_alpha = 0
            text_x = final_text_x
        
        # ===================
        # PHASE 2: Logo moves LEFT, text fades in on RIGHT
        # ===================
        elif time_sec < phase2_end:
            t = (time_sec - phase1_end) / (phase2_end - phase1_end)
            
            logo_scale = 1.0
            logo_alpha = 1.0
            logo_x = int(logo_center_x + (final_logo_x - logo_center_x) * ease_out_cubic(t))
            logo_y = final_logo_y
            
            text_alpha = ease_out_cubic(t)
            text_x = final_text_x
        
        # ===================
        # PHASE 3: Static + outro effects
        # ===================
        else:
            logo_scale = 1.0
            logo_alpha = 1.0
            logo_x = final_logo_x
            logo_y = final_logo_y
            
            text_alpha = 1.0
            text_x = final_text_x
            
            # Outro effects
            if time_sec >= outro_start and outro_effect != "none":
                outro_dur = (duration - outro_start) / max(1, outro_repeat)
                cycle = (time_sec - outro_start) % outro_dur
                et = cycle / outro_dur
                
                if outro_effect == "bounce":
                    bounce = math.sin(et * math.pi * 2) * 15
                    logo_y = final_logo_y + int(bounce)
                elif outro_effect == "pulse":
                    logo_scale = 1.0 + 0.05 * math.sin(et * math.pi * 2)
        
        # Draw logo
        if logo_alpha > 0:
            scaled_w = int(logo.width * logo_scale)
            scaled_h = int(logo.height * logo_scale)
            
            if scaled_w > 0 and scaled_h > 0:
                scaled_logo = logo.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
                
                r, g, b, a = scaled_logo.split()
                a = a.point(lambda p: int(p * logo_alpha))
                scaled_logo = Image.merge("RGBA", (r, g, b, a))
                
                # Center adjustment for scale
                adj_x = logo_x - (scaled_w - logo.width) // 2
                adj_y = logo_y - (scaled_h - logo.height) // 2
                
                bg.paste(scaled_logo, (adj_x, adj_y), scaled_logo)
        
        # Draw text
        if text_alpha > 0:
            text_layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_layer)
            text_draw.text((text_x, final_text_y), brand_name, font=font, fill=(*text_color, int(255 * text_alpha)))
            bg = Image.alpha_composite(bg, text_layer)
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
    
    # Encode
    logger.info(f"Encoding logo animation")
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
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
            logger.error(f"ffmpeg error: {stderr.decode()}")
    except asyncio.TimeoutError:
        logger.error("ffmpeg timeout")
        proc.kill()
    except Exception as e:
        logger.error(f"ffmpeg exception: {e}")
        proc.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Logo animation done: {output_path}")
        return str(output_path)
    logger.error(f"Logo animation failed, output not found: {output_path}")
    return ""

# =============================================================
# CHAT BUBBLES - iMessage Style (Centered Version)
# =============================================================

def draw_chat_bubble_centered(
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
        bg_color = active.get("bg_color")  # [r, g, b] list
        
        if bg_color and isinstance(bg_color, (list, tuple)) and len(bg_color) == 3:
            bg = create_solid_bg(WIDTH, HEIGHT, tuple(bg_color))
        elif bg_type == "black" or bg_type == "dark":
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

        # === FORCE-REDIRECT legacy text scene types → motion_* engine ===
        # Older code paths and LLM responses sometimes still produce "text", "calcom_text",
        # "apple_text", "zoom_text", "gradient_text". Map them to motion_* so every
        # text scene uses the new cinematic typography.
        LEGACY_TEXT_REMAP = {
            "text": "motion_apple_scale",
            "calcom_text": "motion_char_fade",
            "apple_text": "motion_blur_in",
            "zoom_text": "motion_apple_scale",
            "gradient_text": "motion_char_fade",
            "gradient_sweep": "motion_blur_in",
        }
        if scene_type in LEGACY_TEXT_REMAP and content.get("text"):
            scene_type = LEGACY_TEXT_REMAP[scene_type]
            # Default sensible motion params per redirected type
            content.setdefault("by_char", True)
            content.setdefault("use_gradient", True)
            content.setdefault("shadow", True)

        # Skip text-bearing scenes that have no real text (avoids placeholder "Hello" rendering)
        TEXT_SCENE_TYPES = {
            "text", "gradient_text", "gradient_sweep", "apple_text", "calcom_text",
            "calcom_chat", "zoom_text", "chat",
            "motion_blur_in", "motion_char_fade", "motion_apple_scale",
            "motion_word_slide", "motion_fade_underline",
            "motion_word_slide_right", "motion_word_slide_up",
            "motion_word_slide_down", "motion_line_slide_up",
        }
        if scene_type in TEXT_SCENE_TYPES:
            _txt = (content.get("text") or "").strip()
            if not _txt:
                # No text → render plain background, do not draw default "Hello"
                if frame_num == 0:
                    logger.warning(f"Skipping text rendering: empty text for scene type {scene_type}")
                # Fall through; bg remains the plain background already created
                scene_type = "_skip_text"
                content = {}
        
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
            bg = draw_chat_bubble_centered(bg, text, is_sender, vis)
        
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
        
        # === SMOOTH FADE TEXT (professional reveal) ===
        elif scene_type == "smooth_text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 140)
            y_pos = content.get("y_position", 0.5)
            slide = content.get("slide_from", "none")
            bg = draw_smooth_fade_text(bg, text, vis, color, font_size, y_pos, "center", slide, True)
        
        # === ANIMATED GRADIENT TEXT (MacBook Neo style) ===
        elif scene_type == "gradient_sweep":
            text = content.get("text", "Hello")
            base_color = tuple(content.get("base_color", [100, 100, 100]))
            font_size = content.get("font_size", 160)
            # Animate gradient sweep - one full sweep per scene
            sweep_time = vis  # 0->1 as scene progresses
            bg = draw_animated_gradient_text(bg, text, sweep_time, base_color, None, font_size, 0.5)
        
        # === MULTI-LINE SEQUENTIAL TEXT ===
        elif scene_type == "multiline":
            lines = content.get("lines", ["Line 1", "Line 2"])
            colors = [tuple(c) for c in content.get("colors", [[255,255,255]] * len(lines))]
            font_sizes = content.get("font_sizes", [140] * len(lines))
            bg = draw_multiline_text_sequential(bg, lines, vis, colors, font_sizes)
        
        # === CHAT CONVERSATION (typing effect) ===
        elif scene_type == "chat_typing":
            text = content.get("text", "Hello")
            is_sender = content.get("sender", True)
            y_pos = content.get("y_position", 0.5)
            bg = draw_chat_bubble(bg, text, vis, is_sender, y_pos, typing_effect=True)
        
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
        
        # === APPLE TEXT REVEAL (single scene) ===
        elif scene_type == "apple_text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 140)
            emphasis = content.get("emphasis", False)
            bg = draw_apple_text_reveal(bg, text, vis, color, font_size, emphasis)

        # === MOTION 1: BLUR-IN ===
        elif scene_type == "motion_blur_in":
            from motion_text_effects import draw_text_blur_in
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [0, 0, 0]))
            font_size = content.get("font_size", 160)
            weight = content.get("weight", "bold")
            by_char = content.get("by_char", True)
            # Use full scene_progress (0..1 across the whole scene), capped slightly
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_blur_in(bg, text, mp, color, font_size, weight, by_char)

        # === MOTION 2: CHAR FADE + SLIDE (with optional gradient emphasis) ===
        elif scene_type == "motion_char_fade":
            from motion_text_effects import draw_text_char_fade_slide
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 130)
            weight = content.get("weight", "bold")
            emphasis_word = content.get("emphasis_word")
            use_gradient = content.get("use_gradient", True)
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_char_fade_slide(bg, text, mp, color, font_size, weight, emphasis_word, use_gradient)

        # === MOTION 3: APPLE SCALE + SLIDE-LEFT ===
        elif scene_type == "motion_apple_scale":
            from motion_text_effects import draw_text_apple_scale_slide
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 150)
            weight = content.get("weight", "bold")
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_apple_scale_slide(bg, text, mp, color, font_size, weight)

        # === MOTION 4: WORD SLIDE-LEFT WITH SHADOW ===
        elif scene_type == "motion_word_slide":
            from motion_text_effects import draw_text_word_slide_left
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 130)
            weight = content.get("weight", "bold")
            shadow = content.get("shadow", True)
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_word_slide_left(bg, text, mp, color, font_size, weight, shadow)

        # === MOTION 5: FADE + SCALE-UP + DRAW UNDERLINE ===
        elif scene_type == "motion_fade_underline":
            from motion_text_effects import draw_text_fade_scale_up_underline
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [0, 0, 0]))
            font_size = content.get("font_size", 150)
            weight = content.get("weight", "bold")
            emphasis_words = content.get("emphasis_words") or content.get("emphasis_word")
            if isinstance(emphasis_words, str):
                emphasis_words = [emphasis_words]
            mp = min(1.0, scene_progress * 1.3)
            bg = draw_text_fade_scale_up_underline(bg, text, mp, color, font_size, weight, emphasis_words)

        # === MOTION 6: WORD SLIDE-FROM-RIGHT ===
        elif scene_type == "motion_word_slide_right":
            from motion_text_effects import draw_text_word_slide_right
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 140)
            weight = content.get("weight", "bold")
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_word_slide_right(bg, text, mp, color, font_size, weight)

        # === MOTION 7: WORD SLIDE-UP (from below) ===
        elif scene_type == "motion_word_slide_up":
            from motion_text_effects import draw_text_word_slide_up
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 140)
            weight = content.get("weight", "bold")
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_word_slide_up(bg, text, mp, color, font_size, weight)

        # === MOTION 8: WORD SLIDE-DOWN (from above) ===
        elif scene_type == "motion_word_slide_down":
            from motion_text_effects import draw_text_word_slide_down
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 140)
            weight = content.get("weight", "bold")
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_word_slide_down(bg, text, mp, color, font_size, weight)

        # === MOTION 9: WHOLE-LINE SLIDE-UP ===
        elif scene_type == "motion_line_slide_up":
            from motion_text_effects import draw_text_line_slide_up
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            font_size = content.get("font_size", 150)
            weight = content.get("weight", "bold")
            mp = min(1.0, scene_progress * 1.4)
            bg = draw_text_line_slide_up(bg, text, mp, color, font_size, weight)
        
        # === CALCOM TEXT (with emphasis word) ===
        elif scene_type == "calcom_text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [0, 0, 0]))  # Black on white
            font_size = content.get("font_size", 100)
            emphasis_word = content.get("emphasis_word")
            emphasis_color = content.get("emphasis_color")
            if emphasis_color:
                emphasis_color = tuple(emphasis_color)
            bg = draw_calcom_text(bg, text, vis, color, font_size, 0.5, emphasis_word, emphasis_color)
        
        # === CALCOM CHAT BUBBLE ===
        elif scene_type == "calcom_chat":
            text = content.get("text", "Hello")
            is_sender = content.get("sender", True)
            y_pos = content.get("y_position", 0.5)
            bg = draw_calcom_chat_bubble(bg, text, vis, is_sender, y_pos)
        
        # === ZOOM TEXT (text with zoom in/out effect) ===
        elif scene_type == "zoom_text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [0, 0, 0]))
            font_size = content.get("font_size", 120)
            start_zoom = content.get("start_zoom", 0.8)
            end_zoom = content.get("end_zoom", 1.0)
            
            # Draw text first
            bg = draw_calcom_text(bg, text, 1.0, color, font_size, 0.5)  # Full opacity
            
            # Apply zoom animation
            current_zoom = animate_zoom(vis, start_zoom, end_zoom)
            bg = apply_zoom_effect(bg, current_zoom)
        
        # === 3D DEVICE MOCKUP ===
        elif scene_type == "device_mockup":
            device_type = content.get("device", "phone")
            video_path = content.get("video_path")
            rotation = content.get("rotation", 15)
            
            # For now, use solid color as screen content
            # TODO: Load video frames for screen content
            screen = Image.new("RGB", (360, 780), (100, 150, 255))
            
            mockup = create_3d_phone_mockup(screen, rotation_y=rotation)
            
            # Center mockup on background
            mockup_x = (WIDTH - mockup.width) // 2
            mockup_y = (HEIGHT - mockup.height) // 2
            bg.paste(mockup, (mockup_x, mockup_y), mockup)
        
        # === LOGO REVEAL (logo left, brand name right) ===
        elif scene_type == "logo_reveal":
            brand_name = content.get("brand_name", "Brand")
            logo_path_str = content.get("logo_path")
            bg_color = tuple(content.get("bg_color", [88, 101, 242]))
            
            # Draw logo reveal animation inline
            bg = create_solid_bg(WIDTH, HEIGHT, bg_color)
            bg = draw_logo_reveal_frame(bg, brand_name, logo_path_str, vis)
        
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
# APPLE-STYLE TEXT ANIMATION - Multiple scenes with text reveals
# Based on video analysis: Logo -> Text scenes -> Final logo
# =============================================================

async def render_apple_text_sequence(
    texts: List[str],
    output_dir: Path,
    fps: int = 30,
    bg_colors: List[Tuple[int, int, int]] = None,
    text_colors: List[Tuple[int, int, int]] = None,
    final_title: str = None,
    scene_duration: float = 1.2
) -> str:
    """
    Apple-style text animation sequence:
    1. Each text appears with fade + scale animation
    2. Background color can change between scenes
    3. Final title appears at the end
    
    Based on: @adobebasics TikTok video analysis
    """
    output_path = output_dir / f"apple_text_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Default colors - alternating black/white like the reference
    if bg_colors is None:
        bg_colors = []
        for i in range(len(texts)):
            bg_colors.append((0, 0, 0) if i % 2 == 0 else (255, 255, 255))
    
    if text_colors is None:
        text_colors = []
        for bg in bg_colors:
            # White text on dark, black text on light
            if sum(bg) < 384:
                text_colors.append((255, 255, 255))
            else:
                text_colors.append((0, 0, 0))
    
    # Calculate total duration
    total_duration = len(texts) * scene_duration
    if final_title:
        total_duration += scene_duration  # Extra time for final title
    
    total_frames = int(total_duration * fps)
    frames_per_scene = int(scene_duration * fps)
    
    frame_num = 0
    
    for scene_idx, text in enumerate(texts):
        bg_color = bg_colors[scene_idx % len(bg_colors)]
        text_color = text_colors[scene_idx % len(text_colors)]
        
        for f in range(frames_per_scene):
            # Scene progress 0->1
            progress = f / frames_per_scene
            
            # Create background
            bg = create_solid_bg(WIDTH, HEIGHT, bg_color)
            
            # Draw text with Apple-style animation (fade + scale + slight slide up)
            bg = draw_apple_text_reveal(bg, text, progress, text_color)
            
            # Save frame
            frame_path = frames_dir / f"frame_{frame_num:05d}.png"
            bg.convert("RGB").save(frame_path, "PNG", optimize=True)
            frame_num += 1
    
    # Final title scene (if provided)
    if final_title:
        for f in range(frames_per_scene):
            progress = f / frames_per_scene
            
            # Black background for final title
            bg = create_solid_bg(WIDTH, HEIGHT, (0, 0, 0))
            
            # Draw final title with special emphasis
            bg = draw_apple_text_reveal(bg, final_title, progress, (255, 255, 255), font_size=180, emphasis=True)
            
            frame_path = frames_dir / f"frame_{frame_num:05d}.png"
            bg.convert("RGB").save(frame_path, "PNG", optimize=True)
            frame_num += 1
    
    # Encode video
    logger.info("Encoding Apple text animation...")
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
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
            logger.error(f"ffmpeg error: {stderr.decode()}")
    except asyncio.TimeoutError:
        logger.error("ffmpeg timeout")
        proc.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Apple text animation done: {output_path}")
        return str(output_path)
    return ""


def draw_apple_text_reveal(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    emphasis: bool = False
) -> Image.Image:
    """
    Apple-style text reveal:
    - Fade in (0 -> 255 alpha)
    - Scale up (0.85 -> 1.0)
    - Slight slide up (20px -> 0px)
    - Easing: ease_out_cubic for smooth feel
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Animation timing - text appears in first 60% of scene, holds rest
    if progress < 0.6:
        anim_progress = progress / 0.6
    else:
        anim_progress = 1.0
    
    # Apply easing
    eased = ease_out_cubic(anim_progress)
    
    # Alpha: 0 -> 255
    alpha = int(255 * eased)
    
    # Scale: 0.85 -> 1.0
    scale = 0.85 + 0.15 * eased
    
    # Slide: 30px -> 0px (moves up)
    slide_y = int(30 * (1 - eased))
    
    # Calculate font size with scale
    scaled_font_size = int(font_size * scale)
    font = get_font(scaled_font_size, "bold" if emphasis else "semibold")
    
    # Measure text
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Auto-fit to screen width (85% max)
    max_width = int(WIDTH * 0.85)
    while text_w > max_width and scaled_font_size > 40:
        scaled_font_size -= 5
        font = get_font(scaled_font_size, "bold" if emphasis else "semibold")
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
    
    # Position: centered, with slide offset
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 + slide_y
    
    # Draw text with alpha
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_logo_reveal_frame(
    img: Image.Image,
    brand_name: str,
    logo_path: str,
    progress: float
) -> Image.Image:
    """
    Logo reveal animation frame:
    Phase 1 (0-0.3): Logo appears in center with scale
    Phase 2 (0.3-0.6): Logo moves left
    Phase 3 (0.6-1.0): Brand name fades in on right
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Text color (white on any background)
    text_color = (255, 255, 255)
    
    # Load logo or create placeholder
    logo_size = int(HEIGHT * 0.15)
    logo = None
    
    if logo_path:
        try:
            from pathlib import Path
            p = Path(logo_path) if not logo_path.startswith("/api") else Path(f"/app/backend/uploads/{logo_path.split('/')[-1]}")
            if p.exists():
                logo = Image.open(p).convert("RGBA")
                ratio = logo_size / max(logo.width, logo.height)
                logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)), Image.Resampling.LANCZOS)
        except Exception as e:
            logger.warning(f"Failed to load logo: {e}")
    
    if logo is None:
        # Create placeholder circle logo
        logo = Image.new("RGBA", (logo_size, logo_size), (0, 0, 0, 0))
        logo_draw = ImageDraw.Draw(logo)
        logo_draw.ellipse((5, 5, logo_size-5, logo_size-5), fill=(255, 255, 255, 200))
    
    # Font for brand name
    font_size = int(logo.height * 0.8)
    font = get_font(font_size, "bold")
    bbox = draw.textbbox((0, 0), brand_name, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Calculate positions
    center_x = WIDTH // 2
    center_y = HEIGHT // 2
    
    gap = int(logo.width * 0.4)
    total_w = logo.width + gap + text_w
    
    final_logo_x = (WIDTH - total_w) // 2
    final_text_x = final_logo_x + logo.width + gap
    
    # Animation phases
    if progress < 0.3:
        # Phase 1: Logo appears in center
        p = progress / 0.3
        p = ease_out_cubic(p)
        logo_scale = 0.5 + 0.5 * p
        logo_alpha = int(255 * p)
        logo_x = center_x - logo.width // 2
        text_alpha = 0
    elif progress < 0.6:
        # Phase 2: Logo moves left
        p = (progress - 0.3) / 0.3
        p = ease_out_cubic(p)
        logo_scale = 1.0
        logo_alpha = 255
        logo_x = int(center_x - logo.width // 2 + (final_logo_x - (center_x - logo.width // 2)) * p)
        text_alpha = 0
    else:
        # Phase 3: Brand name appears
        p = (progress - 0.6) / 0.4
        p = ease_out_cubic(p)
        logo_scale = 1.0
        logo_alpha = 255
        logo_x = final_logo_x
        text_alpha = int(255 * p)
    
    # Draw logo
    if logo_scale != 1.0:
        new_size = (int(logo.width * logo_scale), int(logo.height * logo_scale))
        scaled_logo = logo.resize(new_size, Image.Resampling.LANCZOS)
        logo_x = logo_x + (logo.width - new_size[0]) // 2
        logo_y = center_y - new_size[1] // 2
    else:
        scaled_logo = logo
        logo_y = center_y - logo.height // 2
    
    # Apply alpha to logo
    if logo_alpha < 255:
        alpha_mask = scaled_logo.split()[3].point(lambda x: int(x * logo_alpha / 255))
        scaled_logo.putalpha(alpha_mask)
    
    layer.paste(scaled_logo, (logo_x, logo_y), scaled_logo)
    
    # Draw brand name
    if text_alpha > 0:
        text_y = center_y - text_h // 2
        draw.text((final_text_x, text_y), brand_name, font=font, fill=(*text_color, text_alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# UNIVERSAL RENDER - Handles ANY scene type from AI
# =============================================================

async def render_universal_video(script_data: Dict, output_dir: Path, fps: int = 30) -> str:
    """
    UNIVERSAL VIDEO RENDERER
    Accepts scenes from AI and renders each one appropriately.
    Supports: apple_text, logo_reveal, gradient_text, chat, shapes, etc.
    """
    # Get scenes from script_data (new format uses "scenes", old format uses "elements")
    raw_scenes = script_data.get("scenes", []) or script_data.get("elements", [])

    if not raw_scenes:
        # Fallback — use original user prompt if available, otherwise empty (no placeholder text)
        user_prompt = (script_data.get("user_prompt") or script_data.get("prompt") or "").strip()
        if user_prompt:
            raw_scenes = [{"type": "motion_apple_scale", "text": user_prompt[:80],
                           "bg": "white", "duration": 1.8}]
        else:
            raw_scenes = []
    
    scenes = []
    logo_path = script_data.get("logo_path")
    brand_name = script_data.get("brand_name")
    
    for idx, elem in enumerate(raw_scenes):
        scene_type = elem.get("type", "apple_text")
        duration = elem.get("duration", 1.5)
        bg = elem.get("bg", elem.get("background", "black"))
        
        # Convert bg string to background format
        if bg == "black" or bg == "dark":
            background = "black"
        elif bg == "white" or bg == "light":
            background = "white"
        elif isinstance(bg, list):
            background = bg
        else:
            background = "white"
        
        # Determine text color based on background
        if background == "black":
            text_color = [255, 255, 255]
        else:
            text_color = [0, 0, 0]
        
        scene = {
            "type": scene_type,
            "duration": duration,
            "trans_in": 0.2,
            "trans_out": 0.15,
            "background": background,
            "content": {}
        }
        
        # === APPLE TEXT (fade + scale + slide) ===
        if scene_type == "apple_text":
            scene["content"] = {
                "text": elem.get("text", ""),
                "color": elem.get("color", text_color),
                "font_size": elem.get("font_size", 140),
                "emphasis": elem.get("emphasis", False)
            }

        # === MOTION TYPES (9 cinematic text animations) ===
        elif scene_type in ("motion_blur_in", "motion_char_fade", "motion_apple_scale",
                            "motion_word_slide", "motion_fade_underline",
                            "motion_word_slide_right", "motion_word_slide_up",
                            "motion_word_slide_down", "motion_line_slide_up"):
            scene["content"] = {
                "text": elem.get("text", ""),
                "color": elem.get("color", text_color),
                "font_size": elem.get("font_size", 150),
                "weight": elem.get("weight", "bold"),
                "by_char": elem.get("by_char", True),
                "emphasis_word": elem.get("emphasis_word"),
                "emphasis_words": elem.get("emphasis_words"),
                "use_gradient": elem.get("use_gradient", True),
                "shadow": elem.get("shadow", True),
            }
        
        # === CALCOM TEXT (with emphasis word) ===
        elif scene_type == "calcom_text":
            scene["content"] = {
                "text": elem.get("text", ""),
                "color": text_color,
                "font_size": elem.get("font_size", 100),
                "emphasis_word": elem.get("emphasis_word"),
                "emphasis_color": elem.get("emphasis_color")
            }
        
        # === CALCOM CHAT BUBBLE ===
        elif scene_type == "calcom_chat":
            scene["content"] = {
                "text": elem.get("text", ""),
                "sender": elem.get("sender", True),
                "y_position": elem.get("y_position", 0.5)
            }
        
        # === LOGO REVEAL (logo left, text right) ===
        elif scene_type == "logo_reveal":
            # This will be handled specially - render logo animation
            scene["type"] = "logo_reveal"
            scene["content"] = {
                "brand_name": elem.get("brand_name", brand_name or "Brand"),
                "logo_path": elem.get("logo_path", logo_path),
                "bg_color": elem.get("bg_color", [88, 101, 242])  # Discord blue default
            }
            scene["duration"] = max(duration, 3.0)  # Logo needs at least 3s
        
        # === GRADIENT TEXT (animated sweep) ===
        elif scene_type == "gradient_text" or scene_type == "gradient_sweep":
            scene["type"] = "gradient_sweep"
            scene["content"] = {
                "text": elem.get("text", ""),
                "base_color": elem.get("base_color", [100, 100, 100]),
                "font_size": elem.get("font_size", 160)
            }
            scene["background"] = "black"
        
        # === SIMPLE TEXT (word-by-word reveal) ===
        elif scene_type == "text":
            scene["content"] = {
                "text": elem.get("text", elem.get("content", "")),
                "color": elem.get("color", text_color),
                "underline": elem.get("underline")
            }
        
        # === CHAT BUBBLE ===
        elif scene_type == "chat":
            scene["content"] = {
                "text": elem.get("text", ""),
                "sender": elem.get("sender", True)
            }
            scene["background"] = "white"
        
        # === SHAPES ===
        elif scene_type in ["circle", "rect", "shapes"]:
            scene["content"] = elem.get("content", elem)
            scene["background"] = "black"
        
        scenes.append(scene)
    
    # Render all scenes
    return await render_professional_video(scenes, output_dir, fps)
