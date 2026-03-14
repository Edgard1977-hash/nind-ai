"""
iPhone 16 3D compositor v6
FULL SCREEN phone + DYNAMIC 3D animation matching reference video
Key improvements:
- Phone fills 100% of screen height
- Strong 3D perspective rotation (30-40 degrees)
- Smooth sine-wave animation
- No choppy transitions
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from pathlib import Path
import math


def load_iphone_render(angle: int = 12) -> tuple:
    """Load iPhone render at specific angle and extract screen mask."""
    renders_dir = Path("/app/backend/iphone_renders")
    
    # Find closest available angle
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
    
    # Pink detection: high R, low G, high B
    pink_mask = (r > 150) & (g < 100) & (b > 150) & (a > 150)
    mask = Image.fromarray((pink_mask * 255).astype(np.uint8), mode='L')
    mask = mask.filter(ImageFilter.MinFilter(5))  # Erode slightly
    
    # Remove pink pixels from render (replace with black)
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
    
    # Add small margin
    margin = 5
    y1 = max(0, y1 - margin)
    y2 = min(img.size[1], y2 + margin)
    x1 = max(0, x1 - margin)
    x2 = min(img.size[0], x2 + margin)
    
    cropped = img.crop((x1, y1, x2, y2))
    return cropped, (x1, y1, x2, y2)


def apply_strong_3d_transform(img: Image.Image, rotation_y: float) -> Image.Image:
    """
    Apply strong 3D perspective transform.
    rotation_y: rotation in degrees (-45 to +45 recommended)
    Positive = phone rotated to the right (left edge closer)
    """
    if abs(rotation_y) < 1:
        return img
    
    w, h = img.size
    
    # Stronger perspective effect
    # At 30 degrees, one edge should compress by ~15-20%
    angle_rad = math.radians(abs(rotation_y))
    compress_factor = math.sin(angle_rad) * 0.35  # How much the far edge compresses
    shift_factor = math.sin(angle_rad) * 0.08  # Horizontal shift
    
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    
    if rotation_y > 0:
        # Rotated right - right edge appears farther/smaller
        compress = int(h * compress_factor)
        shift = int(w * shift_factor)
        dst = [
            (0, 0),                      # top-left stays
            (w - shift, compress),       # top-right moves left and down
            (w - shift, h - compress),   # bottom-right moves left and up  
            (0, h),                       # bottom-left stays
        ]
    else:
        # Rotated left - left edge appears farther/smaller
        compress = int(h * compress_factor)
        shift = int(w * shift_factor)
        dst = [
            (shift, compress),           # top-left moves right and down
            (w, 0),                       # top-right stays
            (w, h),                       # bottom-right stays
            (shift, h - compress),       # bottom-left moves right and up
        ]
    
    # Calculate perspective transform coefficients
    coeffs = find_perspective_coeffs(src, dst)
    
    # Apply with high quality resampling
    result = img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    
    return result


def find_perspective_coeffs(src, dst):
    """Calculate 8-point perspective transform matrix."""
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    res = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(res.flatten())


def composite_video_on_screen(phone: Image.Image, mask: Image.Image, video: Image.Image) -> Image.Image:
    """Composite video frame onto phone screen using mask."""
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
    
    # Resize video to fit screen
    video_resized = video.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    # Create result with video composited
    result = phone.copy()
    result_arr = np.array(result)
    video_arr = np.array(video_resized.convert("RGBA"))
    
    # Use mask for blending
    mask_crop = np.array(mask)[y1:y2, x1:x2].astype(float) / 255.0
    mask_crop = mask_crop[:, :, np.newaxis]
    
    # Blend video with phone where mask is active
    result_arr[y1:y2, x1:x2] = (
        result_arr[y1:y2, x1:x2] * (1 - mask_crop) + video_arr * mask_crop
    ).astype(np.uint8)
    
    return Image.fromarray(result_arr, mode='RGBA')


def create_spotlight_background(width: int, height: int, base_color: tuple = (30, 35, 32)) -> Image.Image:
    """Create dark background with subtle spotlight from below."""
    y, x = np.mgrid[0:height, 0:width]
    
    # Spotlight from bottom center
    cx, cy = width // 2, height + 400
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = np.sqrt((width/2)**2 + (height + 400)**2)
    t = np.clip(dist / max_dist, 0, 1)
    
    # Subtle lighting effect
    brightness = (1 - t) * 0.3
    r = np.clip(base_color[0] + brightness * 40, 0, 255).astype(np.uint8)
    g = np.clip(base_color[1] + brightness * 50, 0, 255).astype(np.uint8)
    b = np.clip(base_color[2] + brightness * 40, 0, 255).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')


def create_phone_shadow(phone_bounds: tuple, output_size: tuple, rotation: float = 0) -> Image.Image:
    """Create realistic floor shadow under phone."""
    shadow = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    px, py, pw, ph = phone_bounds
    
    # Shadow is ellipse under phone
    shadow_w = int(pw * 0.6)
    shadow_h = int(pw * 0.15)
    shadow_x = px + (pw - shadow_w) // 2
    shadow_y = py + ph - shadow_h // 2
    
    # Offset shadow based on rotation
    shadow_x += int(rotation * 1.5)
    
    # Draw soft shadow with multiple layers
    for i in range(30, 0, -1):
        alpha = int(40 * (i / 30))
        expand = (30 - i) * 5
        draw.ellipse([
            shadow_x - expand, 
            shadow_y - expand//4, 
            shadow_x + shadow_w + expand, 
            shadow_y + shadow_h + expand//3
        ], fill=(0, 0, 0, alpha))
    
    return shadow.filter(ImageFilter.GaussianBlur(20))


def ease_in_out_sine(t: float) -> float:
    """Smooth sine-based easing for natural motion."""
    return -(math.cos(math.pi * t) - 1) / 2


def render_dynamic_phone(
    video_frame: Image.Image,
    time_progress: float,  # 0.0 to 1.0
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (30, 35, 32),
    phone_scale: float = 1.05  # >1.0 to fill screen fully
) -> Image.Image:
    """
    Render phone with smooth, dynamic 3D animation.
    Phone fills ~100% of screen height with continuous rotation.
    """
    # Load phone render
    phone, mask, base_angle = load_iphone_render(12)
    
    # Composite video onto screen BEFORE transforms
    composited = composite_video_on_screen(phone, mask, video_frame)
    
    # Crop to actual phone bounds (remove padding)
    cropped, bounds = crop_to_phone_bounds(composited)
    
    # DYNAMIC ANIMATION
    # Rotation: oscillates between -35 and +35 degrees
    # Using sine wave for smooth, continuous motion
    rotation = 35 * math.sin(time_progress * math.pi * 2)
    
    # Apply 3D perspective transform
    transformed = apply_strong_3d_transform(cropped, rotation)
    
    # Scale to fill output height
    target_h = int(output_size[1] * phone_scale)
    scale_ratio = target_h / transformed.height
    new_w = int(transformed.width * scale_ratio)
    new_h = int(transformed.height * scale_ratio)
    scaled = transformed.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Floating animation (subtle vertical bobbing)
    float_offset_y = int(25 * math.sin(time_progress * math.pi * 4))
    float_offset_x = int(15 * math.sin(time_progress * math.pi * 3))
    
    # Center phone in frame
    x = (output_size[0] - scaled.width) // 2 + float_offset_x
    y = (output_size[1] - scaled.height) // 2 + float_offset_y
    
    # Allow phone to extend beyond frame edges (for 100% fill)
    # Clamp to keep at least 80% visible
    min_visible = int(scaled.height * 0.1)
    y = max(-min_visible, min(y, output_size[1] - scaled.height + min_visible))
    
    # Create background
    bg = create_spotlight_background(output_size[0], output_size[1], bg_color).convert("RGBA")
    
    # Add shadow
    shadow = create_phone_shadow((x, y, scaled.width, scaled.height), output_size, rotation)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(scaled, (x, y), scaled)
    
    return bg.convert("RGB")


def render_phone_with_text(
    video_frame: Image.Image,
    text_lines: list,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (30, 35, 32),
    phone_position: str = "right"  # "left" or "right"
) -> Image.Image:
    """
    Render phone on one side with animated text on the other.
    Matches reference video layout.
    """
    # Load and composite phone
    phone, mask, _ = load_iphone_render(12)
    composited = composite_video_on_screen(phone, mask, video_frame)
    cropped, _ = crop_to_phone_bounds(composited)
    
    # Constant rotation angle (like reference)
    rotation = 30 if phone_position == "right" else -30
    transformed = apply_strong_3d_transform(cropped, rotation)
    
    # Scale phone to ~65% of screen height (leaves room for text)
    target_h = int(output_size[1] * 0.75)
    scale_ratio = target_h / transformed.height
    new_w = int(transformed.width * scale_ratio)
    new_h = int(transformed.height * scale_ratio)
    scaled = transformed.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Floating animation
    float_y = int(20 * math.sin(time_progress * math.pi * 3))
    
    # Position phone
    if phone_position == "right":
        phone_x = output_size[0] - scaled.width - 20
        text_x = 60
        text_align = "left"
    else:
        phone_x = 20
        text_x = output_size[0] - 60
        text_align = "right"
    
    phone_y = (output_size[1] - scaled.height) // 2 + float_y
    
    # Create background
    bg = create_spotlight_background(output_size[0], output_size[1], bg_color).convert("RGBA")
    
    # Add shadow
    shadow = create_phone_shadow((phone_x, phone_y, scaled.width, scaled.height), output_size, rotation)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(scaled, (phone_x, phone_y), scaled)
    
    # Draw animated text
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        font_big = ImageFont.truetype(font_path, 64)
        font_small = ImageFont.truetype(font_path, 36)
    except:
        font_big = font_small = ImageFont.load_default()
    
    text_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    # Center text vertically
    total_text_height = len(text_lines) * 80
    text_start_y = (output_size[1] - total_text_height) // 2
    
    for i, line in enumerate(text_lines):
        # Staggered fade-in animation
        line_progress = max(0, min(1, (time_progress - i * 0.1) * 2.5))
        alpha = int(255 * ease_in_out_sine(line_progress))
        slide_x = int(50 * (1 - ease_in_out_sine(line_progress)))
        
        font = font_big if i == 0 else font_small
        line_y = text_start_y + i * 80
        
        if text_align == "left":
            line_x = text_x + slide_x
        else:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            line_x = text_x - line_w - slide_x
        
        draw.text((line_x, line_y), line, font=font, fill=(255, 255, 255, alpha))
    
    bg = Image.alpha_composite(bg, text_layer)
    return bg.convert("RGB")


# ============================================
# COMPATIBILITY WRAPPER FUNCTIONS
# ============================================

def get_base_iphone() -> tuple:
    """Legacy compatibility - load base iPhone."""
    phone, mask, _ = load_iphone_render(12)
    return phone, mask


def create_simple_float_frame(video_frame, time_seconds, output_size=(1080, 1920), 
                               bg_color=(30, 35, 32), use_gradient=True):
    """Legacy wrapper - simple floating animation."""
    progress = (time_seconds % 4.0) / 4.0
    return render_dynamic_phone(video_frame, progress, output_size, bg_color, 1.05)


def create_animated_iphone_frame(video_frame, time_progress, total_duration=6.0,
                                  output_size=(1080, 1920), bg_color=(30, 35, 32)):
    """Legacy wrapper - animated iPhone frame."""
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, 1.05)


def create_smooth_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                               bg_color=(30, 35, 32), position="center"):
    """Legacy wrapper - smooth phone animation."""
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, 1.05)


def create_phone_with_text_frame(video_frame, text, time_progress, output_size=(1080, 1920),
                                  bg_color=(30, 35, 32), phone_position="right", font_size=64):
    """Legacy wrapper - phone with text layout."""
    lines = [text] if isinstance(text, str) else text
    return render_phone_with_text(video_frame, lines, time_progress, output_size, bg_color, phone_position)


def blend_iphone_renders(angle):
    """Legacy compatibility."""
    img, mask = get_base_iphone()
    return img, mask


def composite_video_clean(iphone, video):
    """Legacy compatibility."""
    _, mask = get_base_iphone()
    return composite_video_on_screen(iphone, mask, video)


def select_iphone_render(rotation):
    """Legacy compatibility."""
    return "/app/backend/iphone_renders/iphone_rot_12.png", 12
