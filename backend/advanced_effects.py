"""
Advanced Video Effects and Transitions
Based on analysis of professional TikTok/Reels videos
"""

import math
import random
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

# Easing functions for smooth animations
def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2

def ease_out_back(t: float) -> float:
    """Overshoot then settle - great for bouncy UI elements"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_out_elastic(t: float) -> float:
    """Elastic bounce - for playful elements"""
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

def ease_out_bounce(t: float) -> float:
    """Bounce effect"""
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


# ==================== GRADIENT BACKGROUNDS ====================

def create_gradient_background(
    width: int,
    height: int,
    colors: List[str],
    direction: str = "vertical",
    noise: float = 0.02
) -> Image.Image:
    """Create gradient background with optional noise"""
    img = Image.new("RGB", (width, height))
    pixels = img.load()
    
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    rgb_colors = [hex_to_rgb(c) for c in colors]
    
    for y in range(height):
        for x in range(width):
            if direction == "vertical":
                t = y / height
            elif direction == "horizontal":
                t = x / width
            elif direction == "diagonal":
                t = (x + y) / (width + height)
            elif direction == "radial":
                cx, cy = width / 2, height / 2
                dist = math.sqrt((x - cx)**2 + (y - cy)**2)
                max_dist = math.sqrt(cx**2 + cy**2)
                t = dist / max_dist
            else:
                t = y / height
            
            # Interpolate between colors
            if len(rgb_colors) == 2:
                r = int(rgb_colors[0][0] * (1-t) + rgb_colors[1][0] * t)
                g = int(rgb_colors[0][1] * (1-t) + rgb_colors[1][1] * t)
                b = int(rgb_colors[0][2] * (1-t) + rgb_colors[1][2] * t)
            else:
                # Multi-color gradient
                segment = t * (len(rgb_colors) - 1)
                idx = min(int(segment), len(rgb_colors) - 2)
                local_t = segment - idx
                r = int(rgb_colors[idx][0] * (1-local_t) + rgb_colors[idx+1][0] * local_t)
                g = int(rgb_colors[idx][1] * (1-local_t) + rgb_colors[idx+1][1] * local_t)
                b = int(rgb_colors[idx][2] * (1-local_t) + rgb_colors[idx+1][2] * local_t)
            
            # Add noise
            if noise > 0:
                noise_val = int((random.random() - 0.5) * noise * 255)
                r = max(0, min(255, r + noise_val))
                g = max(0, min(255, g + noise_val))
                b = max(0, min(255, b + noise_val))
            
            pixels[x, y] = (r, g, b)
    
    return img


# ==================== GRADIENT PRESETS ====================

GRADIENT_PRESETS = {
    "spotify": ["#1DB954", "#121212"],
    "tiktok": ["#000000", "#25F4EE", "#FE2C55"],
    "instagram": ["#833AB4", "#FD1D1D", "#F77737"],
    "notion": ["#E3F2FD", "#BBDEFB", "#90CAF9"],
    "apple_dark": ["#000000", "#1C1C1E"],
    "sunset": ["#FF6B6B", "#FFA07A", "#FFD93D"],
    "ocean": ["#0077B6", "#00B4D8", "#90E0EF"],
    "purple_haze": ["#7B2CBF", "#9D4EDD", "#C77DFF"],
    "mint": ["#2D6A4F", "#40916C", "#74C69D"],
    "coral": ["#FF6B6B", "#FFE66D", "#4ECDC4"],
}


# ==================== TEXT EFFECTS ====================

def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: str,
    outline_color: str = "#000000",
    outline_width: int = 2
):
    """Draw text with outline/stroke"""
    x, y = position
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    # Draw main text
    draw.text(position, text, font=font, fill=fill)


def draw_gradient_text(
    img: Image.Image,
    position: Tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    colors: List[str]
) -> Image.Image:
    """Draw text with gradient fill"""
    # Create text mask
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Create gradient
    gradient = create_gradient_background(
        text_width, text_height, colors, "horizontal"
    )
    
    # Create text mask
    mask = Image.new("L", (text_width, text_height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((0, 0), text, font=font, fill=255)
    
    # Apply mask to gradient
    gradient.putalpha(mask)
    
    # Paste onto image
    img.paste(gradient, position, gradient)
    return img


def typewriter_text(
    text: str,
    progress: float
) -> str:
    """Return text up to progress point (typewriter effect)"""
    char_count = int(len(text) * progress)
    return text[:char_count]


# ==================== CARD / UI ELEMENTS ====================

def draw_floating_card(
    img: Image.Image,
    position: Tuple[int, int],
    size: Tuple[int, int],
    content_img: Optional[Image.Image] = None,
    corner_radius: int = 20,
    shadow_blur: int = 15,
    shadow_offset: Tuple[int, int] = (0, 8),
    bg_color: str = "#FFFFFF",
    rotation: float = 0
) -> Image.Image:
    """Draw a floating card with shadow and optional 3D effect"""
    x, y = position
    w, h = size
    
    # Create card with shadow
    card_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    # Shadow
    shadow = Image.new("RGBA", (w + 40, h + 40), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (20, 20, w + 20, h + 20),
        radius=corner_radius,
        fill=(0, 0, 0, 80)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))
    card_layer.paste(shadow, (x - 20 + shadow_offset[0], y - 20 + shadow_offset[1]), shadow)
    
    # Main card
    card = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    card_draw = ImageDraw.Draw(card)
    
    def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    rgb = hex_to_rgb(bg_color)
    card_draw.rounded_rectangle(
        (0, 0, w, h),
        radius=corner_radius,
        fill=(*rgb, 255)
    )
    
    # Add content if provided
    if content_img:
        content_img = content_img.resize((w - 20, h - 20))
        card.paste(content_img, (10, 10))
    
    # Apply rotation if needed
    if rotation != 0:
        card = card.rotate(rotation, expand=True, resample=Image.BICUBIC)
    
    card_layer.paste(card, (x, y), card)
    
    # Composite onto main image
    return Image.alpha_composite(img.convert("RGBA"), card_layer)


# ==================== TRANSITIONS ====================

def apply_zoom_transition(
    img: Image.Image,
    progress: float,
    zoom_in: bool = True,
    center: Optional[Tuple[int, int]] = None
) -> Image.Image:
    """Apply zoom in/out transition"""
    if center is None:
        center = (img.width // 2, img.height // 2)
    
    if zoom_in:
        scale = 1 + progress * 0.3  # Zoom from 1x to 1.3x
    else:
        scale = 1.3 - progress * 0.3  # Zoom from 1.3x to 1x
    
    new_size = (int(img.width * scale), int(img.height * scale))
    scaled = img.resize(new_size, Image.LANCZOS)
    
    # Crop to original size centered
    left = (scaled.width - img.width) // 2
    top = (scaled.height - img.height) // 2
    cropped = scaled.crop((left, top, left + img.width, top + img.height))
    
    return cropped


def apply_glitch_effect(
    img: Image.Image,
    intensity: float = 0.5
) -> Image.Image:
    """Apply digital glitch effect"""
    img = img.copy()
    pixels = img.load()
    
    # RGB shift
    r_shift = int(intensity * 10)
    for y in range(img.height):
        if random.random() < intensity * 0.1:
            for x in range(img.width):
                if x + r_shift < img.width:
                    r, g, b = pixels[x + r_shift, y][:3] if len(pixels[x + r_shift, y]) >= 3 else (pixels[x + r_shift, y], pixels[x + r_shift, y], pixels[x + r_shift, y])
                    orig = pixels[x, y]
                    if len(orig) >= 3:
                        pixels[x, y] = (r, orig[1], orig[2])
    
    # Random horizontal displacement
    num_glitches = int(intensity * 5)
    for _ in range(num_glitches):
        y = random.randint(0, img.height - 20)
        height = random.randint(2, 20)
        offset = random.randint(-30, 30)
        
        strip = img.crop((0, y, img.width, y + height))
        img.paste(strip, (offset, y))
    
    return img


def apply_scan_lines(
    img: Image.Image,
    opacity: float = 0.1,
    line_spacing: int = 4
) -> Image.Image:
    """Apply CRT scan line effect"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    for y in range(0, img.height, line_spacing):
        draw.line([(0, y), (img.width, y)], fill=(0, 0, 0, int(255 * opacity)))
    
    return Image.alpha_composite(img.convert("RGBA"), overlay)


# ==================== PARTICLE EFFECTS ====================

class Particle:
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 size: float, color: str, life: float = 1.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.life = life
        self.max_life = life
    
    def update(self, dt: float = 0.033):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.life -= dt
        self.vy += 0.5  # Gravity
    
    @property
    def alpha(self) -> float:
        return max(0, self.life / self.max_life)


def create_confetti_particles(
    center: Tuple[int, int],
    count: int = 50,
    spread: float = 200
) -> List[Particle]:
    """Create confetti particle burst"""
    particles = []
    colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#95E1D3", "#F38181", "#AA96DA"]
    
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(5, 15)
        particles.append(Particle(
            x=center[0],
            y=center[1],
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed - 10,  # Initial upward burst
            size=random.uniform(5, 12),
            color=random.choice(colors),
            life=random.uniform(1.0, 2.0)
        ))
    
    return particles


def draw_particles(
    img: Image.Image,
    particles: List[Particle]
) -> Image.Image:
    """Draw particles onto image"""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    def hex_to_rgba(hex_color: str, alpha: int) -> Tuple[int, int, int, int]:
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return (*rgb, alpha)
    
    for p in particles:
        if p.life > 0:
            alpha = int(255 * p.alpha)
            color = hex_to_rgba(p.color, alpha)
            size = int(p.size * p.alpha)
            x, y = int(p.x), int(p.y)
            draw.ellipse(
                (x - size, y - size, x + size, y + size),
                fill=color
            )
    
    return Image.alpha_composite(img.convert("RGBA"), overlay)


# ==================== MOTION BLUR ====================

def apply_motion_blur(
    img: Image.Image,
    angle: float = 0,
    distance: int = 20
) -> Image.Image:
    """Apply directional motion blur"""
    # Create kernel
    kernel_size = distance * 2 + 1
    kernel = Image.new("L", (kernel_size, kernel_size), 0)
    kernel_draw = ImageDraw.Draw(kernel)
    
    # Draw line in direction of motion
    cx, cy = kernel_size // 2, kernel_size // 2
    dx = int(math.cos(math.radians(angle)) * distance)
    dy = int(math.sin(math.radians(angle)) * distance)
    kernel_draw.line([(cx - dx, cy - dy), (cx + dx, cy + dy)], fill=255, width=1)
    
    # Apply as filter
    return img.filter(ImageFilter.Kernel(
        size=(kernel_size, kernel_size),
        kernel=[1] * (kernel_size * kernel_size),
        scale=kernel_size * kernel_size
    ))


# ==================== UI MOCKUPS ====================

def draw_iphone_frame(
    img: Image.Image,
    screen_content: Image.Image,
    position: Tuple[int, int],
    scale: float = 1.0
) -> Image.Image:
    """Draw iPhone-like device frame with content"""
    # iPhone 15 Pro proportions
    device_width = int(250 * scale)
    device_height = int(530 * scale)
    bezel = int(12 * scale)
    corner_radius = int(40 * scale)
    notch_width = int(100 * scale)
    notch_height = int(25 * scale)
    
    device = Image.new("RGBA", (device_width, device_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(device)
    
    # Device frame (titanium gray)
    draw.rounded_rectangle(
        (0, 0, device_width, device_height),
        radius=corner_radius,
        fill="#2C2C2E"
    )
    
    # Screen area
    screen_w = device_width - bezel * 2
    screen_h = device_height - bezel * 2
    draw.rounded_rectangle(
        (bezel, bezel, device_width - bezel, device_height - bezel),
        radius=corner_radius - bezel,
        fill="#000000"
    )
    
    # Resize and paste screen content
    screen_content = screen_content.resize((screen_w, screen_h), Image.LANCZOS)
    device.paste(screen_content, (bezel, bezel))
    
    # Dynamic Island
    island_x = (device_width - notch_width) // 2
    island_y = bezel + int(8 * scale)
    draw.rounded_rectangle(
        (island_x, island_y, island_x + notch_width, island_y + notch_height),
        radius=notch_height // 2,
        fill="#000000"
    )
    
    # Paste device onto image
    x, y = position
    result = img.copy().convert("RGBA")
    result.paste(device, (x, y), device)
    
    return result


def draw_macbook_frame(
    img: Image.Image,
    screen_content: Image.Image,
    position: Tuple[int, int],
    scale: float = 1.0
) -> Image.Image:
    """Draw MacBook-like device frame with content"""
    # MacBook proportions
    device_width = int(500 * scale)
    device_height = int(320 * scale)
    bezel_top = int(20 * scale)
    bezel_side = int(12 * scale)
    bezel_bottom = int(25 * scale)
    corner_radius = int(15 * scale)
    
    device = Image.new("RGBA", (device_width, device_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(device)
    
    # Screen frame (space gray)
    draw.rounded_rectangle(
        (0, 0, device_width, device_height - int(20 * scale)),
        radius=corner_radius,
        fill="#3A3A3C"
    )
    
    # Screen bezel
    screen_w = device_width - bezel_side * 2
    screen_h = device_height - bezel_top - bezel_bottom - int(20 * scale)
    draw.rounded_rectangle(
        (bezel_side, bezel_top, device_width - bezel_side, bezel_top + screen_h),
        radius=int(5 * scale),
        fill="#000000"
    )
    
    # Webcam
    cam_size = int(6 * scale)
    draw.ellipse(
        (device_width // 2 - cam_size, int(8 * scale), 
         device_width // 2 + cam_size, int(8 * scale) + cam_size * 2),
        fill="#1C1C1E"
    )
    
    # Base/keyboard
    base_height = int(20 * scale)
    draw.rounded_rectangle(
        (int(30 * scale), device_height - base_height, 
         device_width - int(30 * scale), device_height),
        radius=int(5 * scale),
        fill="#2C2C2E"
    )
    
    # Trackpad indication
    draw.rounded_rectangle(
        (device_width // 2 - int(50 * scale), device_height - base_height + int(5 * scale),
         device_width // 2 + int(50 * scale), device_height - int(5 * scale)),
        radius=int(3 * scale),
        fill="#3A3A3C"
    )
    
    # Resize and paste screen content
    screen_content = screen_content.resize((screen_w, screen_h), Image.LANCZOS)
    device.paste(screen_content, (bezel_side, bezel_top))
    
    # Paste device onto image
    x, y = position
    result = img.copy().convert("RGBA")
    result.paste(device, (x, y), device)
    
    return result
