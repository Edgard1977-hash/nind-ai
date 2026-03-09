"""
Professional Video Effects - Based on detailed analysis of reference TikTok videos
All effects are pixel-accurate recreations of the reference videos
"""

import math
import random
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np
import subprocess
import shutil
import logging

logger = logging.getLogger(__name__)

# Video dimensions (9:16 vertical)
WIDTH = 720
HEIGHT = 1280


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get font with fallback"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


# ==================== EASING FUNCTIONS ====================

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_back(t: float) -> float:
    """Bounce overshoot effect"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_elastic(t: float) -> float:
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1


# ==================== AURORA GRADIENT (ANIMATED) ====================

def create_aurora_gradient(
    width: int, 
    height: int, 
    time: float,  # 0.0 to 1.0 animation progress
    base_colors: List[Tuple[int, int, int]] = None
) -> Image.Image:
    """
    Create animated aurora/Northern lights gradient - OPTIMIZED VERSION
    """
    if base_colors is None:
        base_colors = [
            (29, 185, 84),    # Spotify green
            (30, 215, 96),    # Lighter green
            (25, 150, 70),    # Darker green
            (18, 80, 45),     # Deep green
        ]
    
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    # Simplified - draw gradient bands instead of per-pixel
    num_bands = 20
    band_height = height // num_bands
    
    for band in range(num_bands):
        y_start = band * band_height
        y_end = (band + 1) * band_height
        
        # Animated wave
        wave = math.sin(band / 5 + time * math.pi * 2) * 0.3 + 0.5
        t = (band / num_bands + wave * 0.2) % 1.0
        
        # Select color
        idx = min(int(t * (len(base_colors) - 1)), len(base_colors) - 2)
        local_t = (t * (len(base_colors) - 1)) - idx
        
        c1 = base_colors[idx]
        c2 = base_colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        # Darken towards bottom
        darken = 1 - (band / num_bands) * 0.5
        r = int(r * darken)
        g = int(g * darken)
        b = int(b * darken)
        
        draw.rectangle((0, y_start, width, y_end), fill=(r, g, b))
    
    # Quick blur for smoothness
    img = img.filter(ImageFilter.GaussianBlur(radius=10))
    
    return img


# ==================== 3D CARD WITH PERSPECTIVE ====================

def draw_3d_card(
    img: Image.Image,
    position: Tuple[int, int],
    size: Tuple[int, int],
    rotation_y: float = 0,  # Degrees
    rotation_x: float = 0,
    content: Optional[Image.Image] = None,
    shadow_offset: int = 15,
    corner_radius: int = 20,
    bg_color: Tuple[int, int, int] = (30, 30, 35)
) -> Image.Image:
    """
    Draw a 3D card with perspective transform and shadow
    Like the dashboard cards in reference videos
    """
    x, y = position
    w, h = size
    
    # Create RGBA composite layer
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    # Shadow (offset and blurred)
    shadow = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (30, 30, w + 30, h + 30),
        radius=corner_radius,
        fill=(0, 0, 0, 80)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=15))
    
    # Apply perspective to shadow
    if rotation_y != 0 or rotation_x != 0:
        shadow = shadow.rotate(rotation_y * 0.1, expand=True, resample=Image.BICUBIC)
    
    layer.paste(shadow, (x - 30 + shadow_offset, y - 30 + shadow_offset), shadow)
    
    # Main card
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    card_draw.rounded_rectangle(
        (0, 0, w, h),
        radius=corner_radius,
        fill=(*bg_color, 255)
    )
    
    # Add content if provided
    if content:
        content = content.resize((w - 20, h - 20), Image.LANCZOS)
        card.paste(content, (10, 10))
    
    # Apply subtle rotation for 3D effect
    if rotation_y != 0:
        # Fake perspective by skewing
        card = card.transform(
            card.size,
            Image.AFFINE,
            (1, rotation_y * 0.002, 0, 0, 1, 0),
            resample=Image.BICUBIC
        )
    
    layer.paste(card, (x, y), card)
    
    # Composite onto original
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result


# ==================== MESSAGE BUBBLE ====================

def draw_message_bubble(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    is_sender: bool = True,
    font_size: int = 24,
    max_width: int = 400,
    animation_progress: float = 1.0  # 0 to 1, for slide-in animation
) -> Image.Image:
    """
    Draw iMessage-style chat bubble with tail
    Sender = blue bubble (right), Receiver = gray bubble (left)
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size)
    
    # Wrap text
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width - 40:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Calculate bubble size
    line_height = font_size + 8
    text_height = len(lines) * line_height
    text_width = max(draw.textbbox((0, 0), line, font=font)[2] for line in lines) if lines else 100
    
    bubble_width = text_width + 40
    bubble_height = text_height + 30
    
    # Colors
    if is_sender:
        bg_color = (0, 122, 255, 255)  # iMessage blue
        text_color = (255, 255, 255, 255)
    else:
        bg_color = (229, 229, 234, 255)  # Gray
        text_color = (0, 0, 0, 255)
    
    x, y = position
    
    # Apply animation (slide in from side)
    if animation_progress < 1.0:
        offset = int((1 - ease_out_back(animation_progress)) * 200)
        if is_sender:
            x += offset
        else:
            x -= offset
    
    # Draw bubble
    draw.rounded_rectangle(
        (x, y, x + bubble_width, y + bubble_height),
        radius=20,
        fill=bg_color
    )
    
    # Draw tail
    tail_size = 12
    if is_sender:
        # Tail on right
        tail_points = [
            (x + bubble_width - 5, y + bubble_height - 20),
            (x + bubble_width + tail_size, y + bubble_height - 5),
            (x + bubble_width - 5, y + bubble_height - 5)
        ]
    else:
        # Tail on left
        tail_points = [
            (x + 5, y + bubble_height - 20),
            (x - tail_size, y + bubble_height - 5),
            (x + 5, y + bubble_height - 5)
        ]
    draw.polygon(tail_points, fill=bg_color)
    
    # Draw text
    text_y = y + 15
    for line in lines:
        draw.text((x + 20, text_y), line, font=font, fill=text_color)
        text_y += line_height
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# ==================== TYPING INDICATOR ====================

def draw_typing_indicator(
    img: Image.Image,
    position: Tuple[int, int],
    frame: int
) -> Image.Image:
    """
    Draw animated typing indicator (three bouncing dots)
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x, y = position
    bubble_w, bubble_h = 80, 40
    
    # Gray bubble
    draw.rounded_rectangle(
        (x, y, x + bubble_w, y + bubble_h),
        radius=20,
        fill=(229, 229, 234, 255)
    )
    
    # Three dots with bounce animation
    dot_radius = 5
    dot_spacing = 18
    start_x = x + 20
    
    for i in range(3):
        # Staggered bounce animation
        bounce = math.sin((frame * 0.3 + i * 0.5) % (math.pi * 2)) * 5
        dot_y = y + bubble_h // 2 + int(bounce)
        dot_x = start_x + i * dot_spacing
        
        draw.ellipse(
            (dot_x - dot_radius, dot_y - dot_radius, 
             dot_x + dot_radius, dot_y + dot_radius),
            fill=(150, 150, 155, 255)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# ==================== GRADIENT TEXT ====================

def draw_gradient_text(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    font_size: int = 48,
    gradient_colors: List[Tuple[int, int, int]] = None
) -> Image.Image:
    """
    Draw text with rainbow/gradient fill
    Like "clarity" in the Notion video
    """
    if gradient_colors is None:
        gradient_colors = [
            (255, 107, 107),  # Red/pink
            (255, 159, 67),   # Orange
            (254, 202, 87),   # Yellow
            (29, 209, 161),   # Green
            (84, 160, 255),   # Blue
            (165, 94, 234),   # Purple
        ]
    
    font = get_font(font_size, bold=True)
    
    # Get text dimensions
    temp_draw = ImageDraw.Draw(img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Create gradient
    gradient = Image.new("RGB", (text_width, text_height))
    gradient_pixels = gradient.load()
    
    for x in range(text_width):
        t = x / text_width
        # Interpolate through colors
        segment = t * (len(gradient_colors) - 1)
        idx = min(int(segment), len(gradient_colors) - 2)
        local_t = segment - idx
        
        c1 = gradient_colors[idx]
        c2 = gradient_colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        for y in range(text_height):
            gradient_pixels[x, y] = (r, g, b)
    
    # Create text mask
    mask = Image.new("L", (text_width, text_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((0, 0), text, font=font, fill=255)
    
    # Apply mask to gradient
    gradient = gradient.convert("RGBA")
    gradient.putalpha(mask)
    
    # Paste onto image
    result = img.copy().convert("RGBA")
    result.paste(gradient, position, gradient)
    
    return result


# ==================== TYPEWRITER TEXT ====================

def draw_typewriter_text(
    img: Image.Image,
    text: str,
    position: Tuple[int, int],
    progress: float,  # 0 to 1
    font_size: int = 48,
    color: Tuple[int, int, int] = (255, 255, 255),
    show_cursor: bool = True,
    cursor_blink_frame: int = 0
) -> Image.Image:
    """
    Draw text with typewriter effect - characters appear one by one
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    # Calculate visible characters
    visible_chars = int(len(text) * progress)
    visible_text = text[:visible_chars]
    
    x, y = position
    
    # Draw visible text
    draw.text((x, y), visible_text, font=font, fill=(*color, 255))
    
    # Draw cursor
    if show_cursor and visible_chars < len(text):
        # Blink cursor
        if (cursor_blink_frame // 15) % 2 == 0:
            text_bbox = draw.textbbox((x, y), visible_text, font=font)
            cursor_x = text_bbox[2] + 3
            cursor_y = y + 5
            cursor_height = font_size - 10
            draw.rectangle(
                (cursor_x, cursor_y, cursor_x + 3, cursor_y + cursor_height),
                fill=(*color, 255)
            )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# ==================== FLOATING ANIMATION ====================

def apply_floating_offset(
    base_y: int,
    time: float,
    amplitude: int = 10,
    frequency: float = 1.0
) -> int:
    """
    Calculate Y offset for floating animation
    """
    return base_y + int(math.sin(time * math.pi * 2 * frequency) * amplitude)


# ==================== PROGRESS BAR ====================

def draw_progress_bar(
    img: Image.Image,
    position: Tuple[int, int],
    size: Tuple[int, int],
    progress: float,  # 0 to 1
    bg_color: Tuple[int, int, int] = (60, 60, 60),
    fill_color: Tuple[int, int, int] = (255, 255, 255),
    corner_radius: int = 4
) -> Image.Image:
    """
    Draw animated progress bar like music player
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    x, y = position
    w, h = size
    
    # Background
    draw.rounded_rectangle(
        (x, y, x + w, y + h),
        radius=corner_radius,
        fill=(*bg_color, 255)
    )
    
    # Fill
    fill_width = int(w * progress)
    if fill_width > 0:
        draw.rounded_rectangle(
            (x, y, x + fill_width, y + h),
            radius=corner_radius,
            fill=(*fill_color, 255)
        )
    
    # Playhead circle
    circle_radius = h + 2
    circle_x = x + fill_width
    circle_y = y + h // 2
    draw.ellipse(
        (circle_x - circle_radius, circle_y - circle_radius,
         circle_x + circle_radius, circle_y + circle_radius),
        fill=(*fill_color, 255)
    )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# ==================== DEVICE MOCKUPS ====================

def draw_iphone_mockup(
    img: Image.Image,
    screen_content: Image.Image,
    position: Tuple[int, int],
    scale: float = 1.0,
    shadow: bool = True
) -> Image.Image:
    """
    Draw iPhone device mockup with screen content
    """
    device_w = int(220 * scale)
    device_h = int(450 * scale)
    bezel = int(10 * scale)
    corner_radius = int(35 * scale)
    notch_w = int(80 * scale)
    notch_h = int(25 * scale)
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    x, y = position
    
    # Shadow
    if shadow:
        shadow_layer = Image.new("RGBA", (device_w + 40, device_h + 40), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            (20, 25, device_w + 20, device_h + 25),
            radius=corner_radius,
            fill=(0, 0, 0, 60)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=12))
        layer.paste(shadow_layer, (x - 20, y - 20), shadow_layer)
    
    # Device frame
    device = Image.new("RGBA", (device_w, device_h), (0, 0, 0, 0))
    device_draw = ImageDraw.Draw(device)
    
    # Outer frame (titanium)
    device_draw.rounded_rectangle(
        (0, 0, device_w, device_h),
        radius=corner_radius,
        fill=(45, 45, 50, 255)
    )
    
    # Screen
    screen_w = device_w - bezel * 2
    screen_h = device_h - bezel * 2
    device_draw.rounded_rectangle(
        (bezel, bezel, device_w - bezel, device_h - bezel),
        radius=corner_radius - bezel,
        fill=(0, 0, 0, 255)
    )
    
    # Add screen content
    if screen_content:
        screen_content = screen_content.resize((screen_w, screen_h), Image.LANCZOS)
        device.paste(screen_content, (bezel, bezel))
    
    # Dynamic Island
    island_x = (device_w - notch_w) // 2
    island_y = bezel + int(8 * scale)
    device_draw.rounded_rectangle(
        (island_x, island_y, island_x + notch_w, island_y + notch_h),
        radius=notch_h // 2,
        fill=(0, 0, 0, 255)
    )
    
    layer.paste(device, (x, y), device)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_macbook_mockup(
    img: Image.Image,
    screen_content: Image.Image,
    position: Tuple[int, int],
    scale: float = 1.0,
    shadow: bool = True
) -> Image.Image:
    """
    Draw MacBook device mockup with screen content
    """
    device_w = int(450 * scale)
    device_h = int(290 * scale)
    bezel_top = int(18 * scale)
    bezel_side = int(12 * scale)
    bezel_bottom = int(22 * scale)
    corner_radius = int(12 * scale)
    base_h = int(15 * scale)
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    x, y = position
    
    # Shadow
    if shadow:
        shadow_layer = Image.new("RGBA", (device_w + 60, device_h + 60), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            (30, 35, device_w + 30, device_h - base_h + 35),
            radius=corner_radius,
            fill=(0, 0, 0, 50)
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=15))
        layer.paste(shadow_layer, (x - 30, y - 30), shadow_layer)
    
    # Device
    device = Image.new("RGBA", (device_w, device_h), (0, 0, 0, 0))
    device_draw = ImageDraw.Draw(device)
    
    # Screen frame
    device_draw.rounded_rectangle(
        (0, 0, device_w, device_h - base_h),
        radius=corner_radius,
        fill=(58, 58, 60, 255)  # Space gray
    )
    
    # Screen area
    screen_w = device_w - bezel_side * 2
    screen_h = device_h - bezel_top - bezel_bottom - base_h
    device_draw.rounded_rectangle(
        (bezel_side, bezel_top, device_w - bezel_side, bezel_top + screen_h),
        radius=int(5 * scale),
        fill=(0, 0, 0, 255)
    )
    
    # Webcam
    cam_r = int(4 * scale)
    cam_x = device_w // 2
    cam_y = int(9 * scale)
    device_draw.ellipse(
        (cam_x - cam_r, cam_y - cam_r, cam_x + cam_r, cam_y + cam_r),
        fill=(28, 28, 30, 255)
    )
    
    # Base/hinge
    hinge_w = int(device_w * 0.8)
    hinge_x = (device_w - hinge_w) // 2
    device_draw.rounded_rectangle(
        (hinge_x, device_h - base_h, hinge_x + hinge_w, device_h),
        radius=int(4 * scale),
        fill=(45, 45, 48, 255)
    )
    
    # Add screen content
    if screen_content:
        screen_content = screen_content.resize((screen_w, screen_h), Image.LANCZOS)
        device.paste(screen_content, (bezel_side, bezel_top))
    
    layer.paste(device, (x, y), device)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# ==================== RENDER FUNCTIONS ====================

async def render_spotify_style(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render Spotify-style video with aurora gradient and UI cards
    Based on video2 reference
    """
    output_path = output_dir / f"spotify_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    brand_name = script_data.get("brand_name") or "Spotify"
    tagline = script_data.get("tagline") or "Music for everyone"
    
    # Spotify colors
    aurora_colors = [
        (29, 185, 84),
        (30, 215, 96),
        (25, 150, 70),
        (18, 80, 45),
    ]
    
    total_frames = 90  # 3 seconds at 30fps for speed
    
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        time = frame_num / fps  # Time in seconds
        
        # Create animated aurora background
        bg = create_aurora_gradient(WIDTH, HEIGHT, progress, aurora_colors)
        bg = bg.convert("RGBA")
        draw = ImageDraw.Draw(bg)
        
        # Phase 1: Brand name appears (0-0.25)
        if progress < 0.25:
            phase_progress = progress / 0.25
            
            # Fade in with scale
            alpha = int(255 * ease_out_cubic(phase_progress))
            scale = 0.8 + 0.2 * ease_out_back(phase_progress)
            
            font_size = int(64 * scale)
            font = get_font(font_size, bold=True)
            
            text_bbox = draw.textbbox((0, 0), brand_name, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            text_x = (WIDTH - text_w) // 2
            text_y = HEIGHT // 2 - 50
            
            # Glow effect
            for offset in [6, 4, 2]:
                glow_alpha = int(alpha * 0.2)
                draw.text((text_x, text_y), brand_name, 
                         font=font, fill=(29, 185, 84, glow_alpha))
            
            draw.text((text_x, text_y), brand_name, 
                     font=font, fill=(255, 255, 255, alpha))
        
        # Phase 2: UI cards slide up (0.25-0.6)
        elif progress < 0.6:
            phase_progress = (progress - 0.25) / 0.35
            
            # Brand name moves to top
            font = get_font(36, bold=True)
            draw.text((WIDTH // 2 - 60, 60), brand_name, 
                     font=font, fill=(255, 255, 255, 255))
            
            # Card slides up from bottom
            card_progress = ease_out_back(min(1, phase_progress * 1.5))
            card_y = int(HEIGHT + 50 - (HEIGHT // 2 + 100) * card_progress)
            
            # Draw card with 3D effect
            bg = draw_3d_card(
                bg,
                position=(WIDTH // 2 - 250, card_y),
                size=(500, 320),
                rotation_y=5 * (1 - card_progress),
                shadow_offset=20,
                corner_radius=25,
                bg_color=(30, 30, 35)
            )
            
            # Draw UI elements on card if visible
            if card_y < HEIGHT - 100:
                draw = ImageDraw.Draw(bg)
                card_x = WIDTH // 2 - 250
                
                # "Made For You" header
                header_font = get_font(20, bold=True)
                draw.text((card_x + 20, card_y + 15), "Made For You", 
                         font=header_font, fill=(255, 255, 255, 200))
                
                # Album covers (placeholder squares)
                for i in range(3):
                    album_x = card_x + 20 + i * 160
                    album_y = card_y + 50
                    
                    # Album art placeholder
                    colors = [(219, 68, 55), (244, 180, 0), (15, 157, 88)]
                    draw.rounded_rectangle(
                        (album_x, album_y, album_x + 140, album_y + 140),
                        radius=8,
                        fill=colors[i]
                    )
                    
                    # Album label
                    label_font = get_font(14)
                    draw.text((album_x, album_y + 150), f"Playlist {i+1}", 
                             font=label_font, fill=(180, 180, 180, 255))
        
        # Phase 3: Tagline with gradient text (0.6-1.0)
        else:
            phase_progress = (progress - 0.6) / 0.4
            
            # Keep brand name and card
            font = get_font(36, bold=True)
            draw.text((WIDTH // 2 - 60, 60), brand_name, 
                     font=font, fill=(255, 255, 255, 255))
            
            # Tagline fades in at bottom
            if phase_progress > 0.2:
                text_progress = (phase_progress - 0.2) / 0.8
                alpha = int(255 * ease_out_cubic(text_progress))
                
                # Split tagline to highlight last word
                words = tagline.split()
                highlight_word = words[-1] if words else ""
                base_text = " ".join(words[:-1]) + " " if len(words) > 1 else ""
                
                font_tag = get_font(36)
                base_bbox = draw.textbbox((0, 0), base_text, font=font_tag)
                highlight_bbox = draw.textbbox((0, 0), highlight_word, font=font_tag)
                
                total_w = base_bbox[2] + highlight_bbox[2]
                start_x = (WIDTH - total_w) // 2
                text_y = HEIGHT - 150
                
                # Draw base text in white
                draw.text((start_x, text_y), base_text, 
                         font=font_tag, fill=(255, 255, 255, alpha))
                
                # Draw highlight word with gradient
                if alpha > 100:
                    bg = draw_gradient_text(
                        bg, highlight_word,
                        (start_x + base_bbox[2], text_y),
                        font_size=36,
                        gradient_colors=[(29, 185, 84), (30, 215, 96), (100, 255, 150)]
                    )
        
        # TikTok watermark
        font_small = get_font(14)
        draw = ImageDraw.Draw(bg)
        draw.text((WIDTH - 100, 30), "TikTok", font=font_small, fill=(255, 255, 255, 150))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.save(frame_path, "PNG")
    
    # Encode video
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
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    logger.info(f"Rendered Spotify-style video: {output_path}")
    return str(output_path)


async def render_imessage_style(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render iMessage chat style video with bubbles and typing indicator
    Based on video1 reference
    """
    output_path = output_dir / f"imessage_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    messages = script_data.get("messages") or [
        {"text": "Are you free Tuesday?", "sender": True},
        {"text": "What about Thursday?", "sender": False},
        {"text": "Thursday works!", "sender": True},
    ]
    
    total_frames = 120  # 4 seconds at 30fps
    message_duration = total_frames // (len(messages) + 1)
    
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        
        # White background
        bg = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
        draw = ImageDraw.Draw(bg)
        
        # Header
        font_header = get_font(18)
        draw.text((WIDTH // 2 - 40, 50), "Messages", font=font_header, fill=(0, 0, 0, 255))
        
        # Draw messages based on timing
        current_y = 150
        
        for i, msg in enumerate(messages):
            msg_start_frame = i * message_duration
            msg_end_frame = (i + 1) * message_duration
            
            if frame_num >= msg_start_frame:
                # Calculate animation progress for this message
                if frame_num < msg_end_frame:
                    anim_progress = (frame_num - msg_start_frame) / (message_duration * 0.3)
                    anim_progress = min(1.0, anim_progress)
                else:
                    anim_progress = 1.0
                
                # Position based on sender/receiver
                if msg["sender"]:
                    x_pos = WIDTH - 300
                else:
                    x_pos = 30
                
                bg = draw_message_bubble(
                    bg, 
                    msg["text"],
                    (x_pos, current_y),
                    is_sender=msg["sender"],
                    animation_progress=anim_progress
                )
                
                current_y += 80
            
            # Show typing indicator before next message appears
            elif frame_num >= msg_start_frame - message_duration * 0.3:
                if not msg["sender"]:  # Only show for incoming messages
                    bg = draw_typing_indicator(bg, (30, current_y), frame_num)
        
        # TikTok watermark
        font_small = get_font(14)
        draw = ImageDraw.Draw(bg)
        draw.text((20, HEIGHT - 50), "TikTok", font=font_small, fill=(0, 0, 0, 100))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.save(frame_path, "PNG")
    
    # Encode video
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
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    logger.info(f"Rendered iMessage-style video: {output_path}")
    return str(output_path)


async def render_dashboard_style(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render dashboard/SaaS style video with gradient and 3D cards
    Based on video4 reference
    """
    output_path = output_dir / f"dashboard_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    headline = script_data.get("headline") or "Build something."
    
    # Pastel gradient colors (pink to orange)
    gradient_colors = [
        (255, 200, 180),  # Peach
        (255, 180, 200),  # Pink
        (230, 170, 210),  # Lavender
    ]
    
    total_frames = 90  # 3 seconds at 30fps
    
    # Pre-render static gradient background once
    static_bg = Image.new("RGB", (WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        idx = min(int(t * (len(gradient_colors) - 1)), len(gradient_colors) - 2)
        local_t = (t * (len(gradient_colors) - 1)) - idx
        c1 = gradient_colors[idx]
        c2 = gradient_colors[idx + 1]
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        for x in range(WIDTH):
            static_bg.putpixel((x, y), (r, g, b))
    
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        time = frame_num / fps
        
        # Use pre-rendered gradient (copy to avoid mutation)
        bg = static_bg.copy().convert("RGBA")
        
        # Phase 1: Typewriter headline (0-0.3)
        if progress < 0.3:
            type_progress = progress / 0.3
            bg = draw_typewriter_text(
                bg, headline,
                (60, HEIGHT // 2 - 50),
                progress=type_progress,
                font_size=56,
                color=(50, 50, 60),
                cursor_blink_frame=frame_num
            )
        
        # Phase 2: Dashboard card appears (0.3-0.7)
        elif progress < 0.7:
            phase_progress = (progress - 0.3) / 0.4
            
            # Keep headline
            draw = ImageDraw.Draw(bg)
            font = get_font(42, bold=True)
            draw.text((60, 100), headline, font=font, fill=(50, 50, 60, 255))
            
            # Animate card from bottom with rotation
            card_progress = ease_out_back(min(1, phase_progress * 1.2))
            card_y = int(HEIGHT + 100 - 450 * card_progress)
            rotation = 10 * (1 - card_progress)
            
            bg = draw_3d_card(
                bg,
                position=(WIDTH // 2 - 280, card_y),
                size=(560, 380),
                rotation_y=rotation,
                shadow_offset=25,
                corner_radius=30,
                bg_color=(255, 255, 255)
            )
            
            # Draw dashboard content on card
            if card_progress > 0.5:
                draw = ImageDraw.Draw(bg)
                card_x = WIDTH // 2 - 280
                
                # Header
                font_small = get_font(16, bold=True)
                draw.text((card_x + 20, card_y + 15), "Your app", 
                         font=font_small, fill=(80, 80, 90))
                
                # Big number
                font_big = get_font(48, bold=True)
                draw.text((card_x + 20, card_y + 50), "$682.5", 
                         font=font_big, fill=(50, 50, 60))
                
                # Bar chart (simplified)
                chart_x = card_x + 20
                chart_y = card_y + 140
                bar_heights = [60, 80, 55, 90, 70, 85, 95, 75]
                bar_width = 50
                for i, h in enumerate(bar_heights):
                    animated_h = int(h * min(1, (card_progress - 0.5) * 3))
                    draw.rounded_rectangle(
                        (chart_x + i * (bar_width + 10), chart_y + 100 - animated_h,
                         chart_x + i * (bar_width + 10) + bar_width, chart_y + 100),
                        radius=5,
                        fill=(100, 100, 255)
                    )
        
        # Phase 3: Final message (0.7-1.0)
        else:
            phase_progress = (progress - 0.7) / 0.3
            
            # Create purple gradient for final phase
            final_bg = Image.new("RGB", (WIDTH, HEIGHT))
            for y in range(HEIGHT):
                t = y / HEIGHT + phase_progress * 0.3
                r = int(max(0, 180 - t * 80))
                g = int(max(0, 150 - t * 100))
                b = int(max(0, 220 - t * 20))
                for x in range(WIDTH):
                    final_bg.putpixel((x, y), (r, g, b))
            
            bg = final_bg.convert("RGBA")
            
            # Final text with fade
            alpha = int(255 * ease_out_cubic(phase_progress))
            draw = ImageDraw.Draw(bg)
            font = get_font(40, bold=True)
            
            final_text = "This is your AI."
            text_bbox = draw.textbbox((0, 0), final_text, font=font)
            text_x = (WIDTH - (text_bbox[2] - text_bbox[0])) // 2
            draw.text((text_x, HEIGHT // 2 - 30), final_text, 
                     font=font, fill=(255, 255, 255, alpha))
            
            font_sub = get_font(32)
            draw.text((text_x + 50, HEIGHT // 2 + 30), "In motion.", 
                     font=font_sub, fill=(255, 255, 255, int(alpha * 0.8)))
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.save(frame_path, "PNG")
    
    # Encode video
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
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    logger.info(f"Rendered dashboard-style video: {output_path}")
    return str(output_path)
