"""
iPhone 16 3D compositor v8
CAMERA MOVEMENT animation matching reference video
Key features:
- Phone is ALWAYS FULLY VISIBLE (no cropping)
- Camera movement: zoom + pan + rotation
- Support for custom gradient backgrounds
- Multiple positions: center, left, right
- Formats: 16:9 landscape, 9:16 portrait
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from pathlib import Path
import math


def load_iphone_render(angle: int = 12) -> tuple:
    """Load iPhone render at specific angle and extract screen mask."""
    renders_dir = Path("/app/backend/iphone_renders")
    
    available = [5, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40]
    closest = min(available, key=lambda x: abs(x - angle))
    
    path = renders_dir / f"iphone_rot_{closest}.png"
    if not path.exists():
        path = renders_dir / "iphone_rot_12.png"
    
    original = Image.open(path).convert("RGBA")
    
    # Extract screen mask (pink/magenta area)
    arr = np.array(original)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    a = arr[:,:,3] if arr.shape[2] == 4 else np.ones_like(r) * 255
    
    pink_mask = (r > 150) & (g < 100) & (b > 150) & (a > 150)
    mask = Image.fromarray((pink_mask * 255).astype(np.uint8), mode='L')
    mask = mask.filter(ImageFilter.MinFilter(5))
    
    # Remove pink pixels from render
    arr_clean = arr.copy()
    pink_pixels = (r > 100) & (b > 100) & (g < r) & (g < b)
    arr_clean[pink_pixels, 0] = 0
    arr_clean[pink_pixels, 1] = 0
    arr_clean[pink_pixels, 2] = 0
    cleaned = Image.fromarray(arr_clean, mode='RGBA')
    
    return cleaned, mask, closest


def crop_to_phone_bounds(img: Image.Image) -> tuple:
    """Crop image to actual phone bounds (remove padding)."""
    arr = np.array(img)
    if arr.shape[2] < 4:
        return img, (0, 0, img.size[0], img.size[1])
    
    alpha = arr[:,:,3]
    rows = np.any(alpha > 30, axis=1)
    cols = np.any(alpha > 30, axis=0)
    
    if not (rows.any() and cols.any()):
        return img, (0, 0, img.size[0], img.size[1])
    
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    
    # Small margin
    margin = 2
    y1 = max(0, y1 - margin)
    y2 = min(img.size[1], y2 + margin + 1)
    x1 = max(0, x1 - margin)
    x2 = min(img.size[0], x2 + margin + 1)
    
    return img.crop((x1, y1, x2, y2)), (x1, y1, x2, y2)


def apply_3d_perspective(img: Image.Image, rotation_y: float, rotation_x: float = 0) -> Image.Image:
    """
    Apply 3D perspective transform.
    rotation_y: left-right rotation (-60 to +60 degrees)
    rotation_x: forward-back tilt (-30 to +30 degrees)
    """
    if abs(rotation_y) < 0.5 and abs(rotation_x) < 0.5:
        return img
    
    w, h = img.size
    
    # Calculate perspective distortion
    angle_rad_y = math.radians(abs(rotation_y))
    compress_y = math.sin(angle_rad_y) * 0.28
    shift_y = math.sin(angle_rad_y) * 0.07
    
    angle_rad_x = math.radians(abs(rotation_x))
    compress_x = math.sin(angle_rad_x) * 0.18
    
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    
    if rotation_y >= 0:
        # Rotated right - right edge farther
        cy = int(h * compress_y)
        sx = int(w * shift_y)
        dst = [
            (0, 0),
            (w - sx, cy),
            (w - sx, h - cy),
            (0, h)
        ]
    else:
        # Rotated left - left edge farther
        cy = int(h * compress_y)
        sx = int(w * shift_y)
        dst = [
            (sx, cy),
            (w, 0),
            (w, h),
            (sx, h - cy)
        ]
    
    # Apply X rotation if present
    if abs(rotation_x) > 0.5:
        cx = int(w * compress_x)
        if rotation_x > 0:
            dst[0] = (dst[0][0] + cx, dst[0][1])
            dst[1] = (dst[1][0] - cx, dst[1][1])
        else:
            dst[2] = (dst[2][0] - cx, dst[2][1])
            dst[3] = (dst[3][0] + cx, dst[3][1])
    
    coeffs = find_perspective_coeffs(src, dst)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def find_perspective_coeffs(src, dst):
    """Calculate perspective transform coefficients."""
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    res = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(res.flatten())


def composite_video_on_screen(phone: Image.Image, mask: Image.Image, video: Image.Image) -> Image.Image:
    """Composite video frame onto phone screen."""
    mask_arr = np.array(mask)
    rows = np.any(mask_arr > 50, axis=1)
    cols = np.any(mask_arr > 50, axis=0)
    
    if not (rows.any() and cols.any()):
        return phone
    
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    
    screen_w = x2 - x1
    screen_h = y2 - y1
    
    if screen_w < 20 or screen_h < 20:
        return phone
    
    video_resized = video.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    result = phone.copy()
    result_arr = np.array(result)
    video_arr = np.array(video_resized.convert("RGBA"))
    
    mask_crop = np.array(mask)[y1:y2, x1:x2].astype(float) / 255.0
    mask_crop = mask_crop[:, :, np.newaxis]
    
    result_arr[y1:y2, x1:x2] = (
        result_arr[y1:y2, x1:x2] * (1 - mask_crop) + video_arr * mask_crop
    ).astype(np.uint8)
    
    return Image.fromarray(result_arr, mode='RGBA')


def create_gradient_background(
    width: int, 
    height: int, 
    color1: tuple = (80, 20, 20),  # Dark red
    color2: tuple = (30, 10, 10),  # Very dark red
    spotlight: bool = True,
    spotlight_color: tuple = None
) -> Image.Image:
    """
    Create gradient background with optional spotlight.
    color1: Top/center color
    color2: Edge/bottom color
    """
    y, x = np.mgrid[0:height, 0:width]
    
    if spotlight:
        # Radial gradient from center
        cx, cy = width // 2, height // 2
        max_dist = math.sqrt((width/2)**2 + (height/2)**2)
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)
        t = np.clip(dist / max_dist, 0, 1)
        t = t ** 0.6  # Softer falloff
    else:
        # Vertical gradient
        t = y / height
    
    r = (color1[0] * (1 - t) + color2[0] * t).astype(np.uint8)
    g = (color1[1] * (1 - t) + color2[1] * t).astype(np.uint8)
    b = (color1[2] * (1 - t) + color2[2] * t).astype(np.uint8)
    
    bg = Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')
    
    # Add subtle spotlight glow if specified
    if spotlight and spotlight_color:
        glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(glow)
        for i in range(50, 0, -1):
            alpha = int(15 * (i / 50))
            r = int(width * 0.3 * (50 - i) / 50)
            draw.ellipse([
                width//2 - r, height//2 - r,
                width//2 + r, height//2 + r
            ], fill=(*spotlight_color[:3], alpha))
        bg = Image.alpha_composite(bg.convert('RGBA'), glow).convert('RGB')
    
    return bg


def create_phone_shadow(
    phone_size: tuple, 
    position: tuple, 
    output_size: tuple, 
    rotation: float = 0,
    intensity: float = 0.5
) -> Image.Image:
    """Create realistic shadow under phone."""
    shadow = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    pw, ph = phone_size
    px, py = position
    
    # Shadow ellipse under phone
    shadow_w = int(pw * 0.6)
    shadow_h = int(pw * 0.1)
    shadow_x = px + (pw - shadow_w) // 2 + int(rotation * 0.5)
    shadow_y = py + ph + int(ph * 0.02)
    
    # Clamp to screen
    shadow_y = min(shadow_y, output_size[1] - shadow_h - 5)
    
    max_alpha = int(45 * intensity)
    for i in range(30, 0, -1):
        alpha = int(max_alpha * (i / 30))
        expand = (30 - i) * 3
        draw.ellipse([
            shadow_x - expand,
            shadow_y - expand // 4,
            shadow_x + shadow_w + expand,
            shadow_y + shadow_h + expand // 3
        ], fill=(0, 0, 0, alpha))
    
    return shadow.filter(ImageFilter.GaussianBlur(15))


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)


def ease_in_out_quad(t: float) -> float:
    return 2 * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 2) / 2


def render_camera_animation(
    video_frame: Image.Image,
    time_progress: float,  # 0.0 to 1.0
    output_size: tuple = (1080, 1920),  # Default 9:16 portrait
    bg_color1: tuple = (80, 20, 20),  # Gradient start (bright)
    bg_color2: tuple = (25, 8, 8),    # Gradient end (dark)
    position: str = "center",  # "center", "left", "right"
    phone_scale_start: float = 0.50,  # Phone takes 50% of screen height at start
    phone_scale_end: float = 0.75,    # Phone takes 75% at end (zoom in but still FULLY visible)
) -> Image.Image:
    """
    Render phone with CAMERA MOVEMENT animation.
    Phone is ALWAYS FULLY VISIBLE - no cropping ever.
    
    Animation:
    - Camera starts far (phone smaller, centered)
    - Camera moves closer (phone larger)
    - Camera rotates around phone (changing 3D angle)
    - Subtle floating effect
    """
    phone, mask, _ = load_iphone_render(12)
    composited = composite_video_on_screen(phone, mask, video_frame)
    cropped, _ = crop_to_phone_bounds(composited)
    
    out_w, out_h = output_size
    crop_w, crop_h = cropped.size
    
    # CAMERA ANIMATION - phone always stays FULLY visible
    # Phase 1 (0.0-0.3): Start position, slight rotation right
    # Phase 2 (0.3-0.6): Move camera, rotation changes to left
    # Phase 3 (0.6-1.0): Camera closer, stronger rotation but still FULLY visible
    
    if time_progress < 0.3:
        t = time_progress / 0.3
        scale = phone_scale_start + (phone_scale_start * 0.15) * ease_out_cubic(t)
        rotation_y = 25 - 10 * ease_in_out_sine(t)  # 25 -> 15 degrees right
        rotation_x = 3
        
    elif time_progress < 0.6:
        t = (time_progress - 0.3) / 0.3
        scale = phone_scale_start * 1.15 + (phone_scale_end - phone_scale_start * 1.15) * 0.5 * ease_in_out_quad(t)
        rotation_y = 15 - 45 * ease_in_out_sine(t)  # 15 -> -30 degrees (rotating left)
        rotation_x = 3 + 5 * t
        
    else:
        t = (time_progress - 0.6) / 0.4
        scale = phone_scale_start * 1.15 + (phone_scale_end - phone_scale_start * 1.15) * (0.5 + 0.5 * ease_in_out_quad(t))
        rotation_y = -30 - 15 * ease_in_out_sine(t)  # -30 -> -45 degrees
        rotation_x = 8 + 4 * t
    
    # CRITICAL: Calculate maximum safe size that keeps phone FULLY visible
    # Account for perspective distortion which makes phone appear wider
    margin_x = int(out_w * 0.10)  # 10% margin on each side
    margin_y = int(out_h * 0.08)  # 8% margin top/bottom
    
    available_w = out_w - 2 * margin_x
    available_h = out_h - 2 * margin_y
    
    # Perspective makes phone wider when rotated
    # At 45 degrees, phone appears ~15% wider
    perspective_factor = 1.0 + abs(rotation_y) * 0.003
    
    # Calculate size that fits within available space
    target_h = int(available_h * scale)
    scale_ratio = target_h / crop_h
    phone_w = int(crop_w * scale_ratio)
    phone_h = target_h
    
    # Adjust if perspective-expanded width exceeds available
    effective_w = int(phone_w * perspective_factor)
    if effective_w > available_w:
        reduction = available_w / effective_w
        phone_w = int(phone_w * reduction)
        phone_h = int(phone_h * reduction)
    
    # Apply perspective transform
    transformed = apply_3d_perspective(cropped, rotation_y, rotation_x)
    scaled = transformed.resize((phone_w, phone_h), Image.Resampling.LANCZOS)
    
    # Subtle floating animation
    float_y = int(8 * math.sin(time_progress * math.pi * 3))
    float_x = int(5 * math.sin(time_progress * math.pi * 2.5))
    
    # Calculate position ensuring FULL visibility
    if position == "center":
        pos_x = (out_w - phone_w) // 2 + float_x
    elif position == "left":
        pos_x = margin_x + float_x
    else:  # right
        pos_x = out_w - phone_w - margin_x + float_x
    
    pos_y = (out_h - phone_h) // 2 + float_y
    
    # STRICTLY ensure phone is FULLY within bounds
    pos_x = max(margin_x, min(pos_x, out_w - phone_w - margin_x))
    pos_y = max(margin_y, min(pos_y, out_h - phone_h - margin_y))
    
    # Create gradient background
    bg = create_gradient_background(out_w, out_h, bg_color1, bg_color2, spotlight=True)
    bg = bg.convert("RGBA")
    
    # Add shadow
    shadow = create_phone_shadow((phone_w, phone_h), (pos_x, pos_y), output_size, rotation_y, 0.6)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(scaled, (pos_x, pos_y), scaled)
    
    return bg.convert("RGB")


def render_simple_float(
    video_frame: Image.Image,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color1: tuple = (40, 45, 40),
    bg_color2: tuple = (20, 25, 20),
    position: str = "center",
    phone_scale: float = 0.65
) -> Image.Image:
    """
    Simple floating animation - phone stays in place with gentle movement.
    Phone is ALWAYS FULLY VISIBLE.
    """
    phone, mask, _ = load_iphone_render(12)
    composited = composite_video_on_screen(phone, mask, video_frame)
    cropped, _ = crop_to_phone_bounds(composited)
    
    out_w, out_h = output_size
    
    # Fixed margins
    margin_x = int(out_w * 0.1)
    margin_y = int(out_h * 0.08)
    
    available_h = out_h - 2 * margin_y
    target_h = int(available_h * phone_scale)
    scale_ratio = target_h / cropped.height
    phone_w = int(cropped.width * scale_ratio)
    phone_h = target_h
    
    # Gentle rotation oscillation
    rotation_y = 15 * math.sin(time_progress * math.pi * 2)
    rotation_x = 3 * math.sin(time_progress * math.pi * 1.5)
    
    transformed = apply_3d_perspective(cropped, rotation_y, rotation_x)
    scaled = transformed.resize((phone_w, phone_h), Image.Resampling.LANCZOS)
    
    # Floating movement
    float_y = int(15 * math.sin(time_progress * math.pi * 2))
    float_x = int(10 * math.sin(time_progress * math.pi * 2.5))
    
    if position == "center":
        pos_x = (out_w - phone_w) // 2 + float_x
    elif position == "left":
        pos_x = margin_x + float_x
    else:
        pos_x = out_w - phone_w - margin_x + float_x
    
    pos_y = (out_h - phone_h) // 2 + float_y
    
    # Ensure fully visible
    pos_x = max(margin_x // 2, min(pos_x, out_w - phone_w - margin_x // 2))
    pos_y = max(margin_y // 2, min(pos_y, out_h - phone_h - margin_y // 2))
    
    bg = create_gradient_background(out_w, out_h, bg_color1, bg_color2, spotlight=True)
    bg = bg.convert("RGBA")
    
    shadow = create_phone_shadow((phone_w, phone_h), (pos_x, pos_y), output_size, rotation_y)
    bg = Image.alpha_composite(bg, shadow)
    bg.paste(scaled, (pos_x, pos_y), scaled)
    
    return bg.convert("RGB")


def render_phone_with_text(
    video_frame: Image.Image,
    text_lines: list,
    time_progress: float,
    output_size: tuple = (1920, 1080),
    bg_color1: tuple = (40, 45, 40),
    bg_color2: tuple = (20, 25, 20),
    phone_position: str = "right"
) -> Image.Image:
    """Render phone on one side with animated text. Phone is FULLY VISIBLE."""
    phone, mask, _ = load_iphone_render(12)
    composited = composite_video_on_screen(phone, mask, video_frame)
    cropped, _ = crop_to_phone_bounds(composited)
    
    out_w, out_h = output_size
    
    # Phone takes 60% of height with margins
    margin = int(min(out_w, out_h) * 0.05)
    available_h = out_h - 2 * margin
    target_h = int(available_h * 0.65)
    scale_ratio = target_h / cropped.height
    phone_w = int(cropped.width * scale_ratio)
    phone_h = target_h
    
    rotation_y = 25 if phone_position == "right" else -25
    
    transformed = apply_3d_perspective(cropped, rotation_y, 3)
    scaled = transformed.resize((phone_w, phone_h), Image.Resampling.LANCZOS)
    
    float_y = int(12 * math.sin(time_progress * math.pi * 2))
    
    if phone_position == "right":
        phone_x = out_w - phone_w - margin
        text_x = margin
        text_align = "left"
    else:
        phone_x = margin
        text_x = out_w - margin
        text_align = "right"
    
    phone_y = (out_h - phone_h) // 2 + float_y
    phone_y = max(margin, min(phone_y, out_h - phone_h - margin))
    
    bg = create_gradient_background(out_w, out_h, bg_color1, bg_color2, spotlight=True)
    bg = bg.convert("RGBA")
    
    shadow = create_phone_shadow((phone_w, phone_h), (phone_x, phone_y), output_size, rotation_y)
    bg = Image.alpha_composite(bg, shadow)
    bg.paste(scaled, (phone_x, phone_y), scaled)
    
    # Draw text
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        base_size = int(min(out_w, out_h) * 0.05)
        font_big = ImageFont.truetype(font_path, base_size)
        font_small = ImageFont.truetype(font_path, int(base_size * 0.6))
    except:
        font_big = font_small = ImageFont.load_default()
    
    text_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    line_height = int(out_h * 0.07)
    total_h = len(text_lines) * line_height
    text_start_y = (out_h - total_h) // 2
    
    for i, line in enumerate(text_lines):
        line_progress = max(0, min(1, (time_progress - i * 0.1) * 2.5))
        alpha = int(255 * ease_out_cubic(line_progress))
        slide = int(30 * (1 - ease_out_cubic(line_progress)))
        
        font = font_big if i == 0 else font_small
        y = text_start_y + i * line_height
        
        if text_align == "left":
            x = text_x + slide
        else:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = text_x - (bbox[2] - bbox[0]) - slide
        
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, alpha // 3))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, alpha))
    
    bg = Image.alpha_composite(bg, text_layer)
    return bg.convert("RGB")


# ============================================
# MAIN RENDER FUNCTION
# ============================================

def render_dynamic_phone(
    video_frame: Image.Image,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (80, 20, 20),  # Single color or gradient start
    bg_color2: tuple = None,  # Gradient end (optional)
    phone_scale: float = 0.65,
    animation_style: str = "camera",  # "camera", "float", "static"
    position: str = "center"  # "center", "left", "right"
) -> Image.Image:
    """
    Main render function with multiple animation styles.
    Phone is ALWAYS FULLY VISIBLE.
    
    animation_style:
    - "camera": Camera movement animation (zoom + rotate) like reference
    - "float": Simple floating animation
    - "static": No animation, just positioned phone
    """
    # Set gradient colors
    if bg_color2 is None:
        # Create darker version for gradient end
        bg_color2 = tuple(max(0, c - 50) for c in bg_color)
    
    if animation_style == "camera":
        return render_camera_animation(
            video_frame=video_frame,
            time_progress=time_progress,
            output_size=output_size,
            bg_color1=bg_color,
            bg_color2=bg_color2,
            position=position,
            phone_scale_start=0.55,
            phone_scale_end=0.85
        )
    elif animation_style == "float":
        return render_simple_float(
            video_frame=video_frame,
            time_progress=time_progress,
            output_size=output_size,
            bg_color1=bg_color,
            bg_color2=bg_color2,
            position=position,
            phone_scale=phone_scale
        )
    else:  # static
        return render_simple_float(
            video_frame=video_frame,
            time_progress=0.0,  # No animation
            output_size=output_size,
            bg_color1=bg_color,
            bg_color2=bg_color2,
            position=position,
            phone_scale=phone_scale
        )


# ============================================
# COMPATIBILITY WRAPPER FUNCTIONS
# ============================================

def get_base_iphone() -> tuple:
    phone, mask, _ = load_iphone_render(12)
    return phone, mask


def create_simple_float_frame(video_frame, time_seconds, output_size=(1080, 1920),
                               bg_color=(40, 45, 40), use_gradient=True):
    progress = (time_seconds % 4.0) / 4.0
    return render_dynamic_phone(video_frame, progress, output_size, bg_color,
                                animation_style="float", phone_scale=0.65)


def create_animated_iphone_frame(video_frame, time_progress, total_duration=6.0,
                                  output_size=(1080, 1920), bg_color=(80, 20, 20)):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color,
                                animation_style="camera")


def create_smooth_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                               bg_color=(40, 45, 40), position="center"):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color,
                                animation_style="float", position=position)


def create_phone_with_text_frame(video_frame, text, time_progress, output_size=(1920, 1080),
                                  bg_color=(40, 45, 40), phone_position="right", font_size=64):
    lines = [text] if isinstance(text, str) else text
    bg_color2 = tuple(max(0, c - 30) for c in bg_color)
    return render_phone_with_text(video_frame, lines, time_progress, output_size,
                                  bg_color, bg_color2, phone_position)


def blend_iphone_renders(angle):
    img, mask = get_base_iphone()
    return img, mask


def composite_video_clean(iphone, video):
    _, mask = get_base_iphone()
    return composite_video_on_screen(iphone, mask, video)


def select_iphone_render(rotation):
    return "/app/backend/iphone_renders/iphone_rot_12.png", 12
