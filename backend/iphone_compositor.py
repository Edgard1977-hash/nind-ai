"""
iPhone 16 3D compositor v5
100% phone size, real-time 3D transforms for smooth dynamic animation
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from pathlib import Path
import math


def get_base_iphone() -> tuple:
    """Load base iPhone render and screen mask (angle 12 as base)."""
    renders_dir = Path("/app/backend/iphone_renders")
    path = renders_dir / "iphone_rot_12.png"
    
    if not path.exists():
        # Fallback to any available
        for f in renders_dir.glob("iphone_rot_*.png"):
            path = f
            break
    
    original = Image.open(path).convert("RGBA")
    
    # Get screen mask from original (pink area)
    arr = np.array(original)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    a = arr[:,:,3] if arr.shape[2] == 4 else np.ones_like(r) * 255
    pink_mask = (r > 150) & (g < 100) & (b > 150) & (a > 150)
    mask = Image.fromarray((pink_mask * 255).astype(np.uint8), mode='L')
    mask = mask.filter(ImageFilter.MinFilter(7))
    
    # Remove pink from render
    arr_copy = arr.copy()
    pink_pixels = (r > 100) & (b > 100) & (g < r) & (g < b)
    arr_copy[pink_pixels, 0] = 0
    arr_copy[pink_pixels, 1] = 0
    arr_copy[pink_pixels, 2] = 0
    cleaned = Image.fromarray(arr_copy, mode='RGBA')
    
    return cleaned, mask


def apply_3d_rotation(img: Image.Image, rotation_y: float, rotation_x: float = 0) -> Image.Image:
    """
    Apply 3D rotation effect using perspective transform.
    rotation_y: rotation around Y axis (left-right tilt) in degrees
    rotation_x: rotation around X axis (forward-back tilt) in degrees
    """
    if abs(rotation_y) < 0.5 and abs(rotation_x) < 0.5:
        return img
    
    width, height = img.size
    
    # Calculate perspective distortion
    # More rotation = more skew
    skew_y = math.tan(math.radians(rotation_y)) * 0.12
    skew_x = math.tan(math.radians(rotation_x)) * 0.08
    
    # Source corners
    src = [(0, 0), (width, 0), (width, height), (0, height)]
    
    # Calculate destination corners based on rotation
    if rotation_y >= 0:
        # Rotated right - left side appears closer
        left_shrink = abs(skew_y) * height * 0.3
        dst = [
            (width * abs(skew_y) * 0.2, left_shrink),           # top-left moves right and down
            (width, 0),                                          # top-right stays
            (width, height),                                     # bottom-right stays
            (width * abs(skew_y) * 0.2, height - left_shrink),  # bottom-left moves right and up
        ]
    else:
        # Rotated left - right side appears closer
        right_shrink = abs(skew_y) * height * 0.3
        dst = [
            (0, 0),                                               # top-left stays
            (width - width * abs(skew_y) * 0.2, right_shrink),   # top-right moves left and down
            (width - width * abs(skew_y) * 0.2, height - right_shrink),  # bottom-right moves
            (0, height),                                          # bottom-left stays
        ]
    
    # Calculate perspective coefficients
    coeffs = find_coeffs(src, dst)
    
    # Apply transform
    result = img.transform((width, height), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    
    return result


def find_coeffs(src, dst):
    """Calculate perspective transform coefficients."""
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    res = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(res.flatten())


def composite_video_on_screen(iphone: Image.Image, mask: Image.Image, video: Image.Image) -> Image.Image:
    """Put video on iPhone screen using mask."""
    mask_arr = np.array(mask)
    rows = np.any(mask_arr > 50, axis=1)
    cols = np.any(mask_arr > 50, axis=0)
    
    if not (rows.any() and cols.any()):
        return iphone
    
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    
    screen_w, screen_h = x2 - x1, y2 - y1
    if screen_w <= 10 or screen_h <= 10:
        return iphone
    
    video_resized = video.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    result = iphone.copy()
    result_arr = np.array(result)
    video_arr = np.array(video_resized.convert("RGBA"))
    
    mask_eroded = mask.filter(ImageFilter.MinFilter(5))
    mask_crop = np.array(mask_eroded)[y1:y2, x1:x2].astype(float) / 255.0
    mask_crop = mask_crop[:, :, np.newaxis]
    
    result_arr[y1:y2, x1:x2] = (
        result_arr[y1:y2, x1:x2] * (1 - mask_crop) + video_arr * mask_crop
    ).astype(np.uint8)
    
    return Image.fromarray(result_arr, mode='RGBA')


def create_dark_gradient(width: int, height: int, base_color: tuple = (25, 35, 30)) -> Image.Image:
    """Dark gradient background with subtle spotlight."""
    y, x = np.mgrid[0:height, 0:width]
    
    # Spotlight from bottom
    cx, cy = width // 2, height + 300
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = np.sqrt(width**2 + (height + 300)**2)
    t = np.clip(dist / max_dist, 0, 1)
    
    r = np.clip(base_color[0] + 30 * (1 - t), 0, 255).astype(np.uint8)
    g = np.clip(base_color[1] + 40 * (1 - t), 0, 255).astype(np.uint8)
    b = np.clip(base_color[2] + 30 * (1 - t), 0, 255).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')


def create_shadow(phone_bounds: tuple, output_size: tuple) -> Image.Image:
    """Create floor shadow under phone."""
    shadow = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    px, py, pw, ph = phone_bounds
    sw = int(pw * 0.5)
    sh = int(pw * 0.1)
    sx = px + (pw - sw) // 2
    sy = py + ph - sh // 2
    
    for i in range(25, 0, -1):
        alpha = int(35 * (i / 25))
        exp = (25 - i) * 4
        draw.ellipse([sx - exp, sy - exp//3, sx + sw + exp, sy + sh + exp//3], 
                     fill=(0, 0, 0, alpha))
    
    return shadow.filter(ImageFilter.GaussianBlur(15))


def render_dynamic_phone(
    video_frame: Image.Image,
    time_progress: float,  # 0.0 to 1.0
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (25, 35, 30),
    phone_scale: float = 0.92  # 92% of screen height for full look with margins
) -> Image.Image:
    """
    Render phone with REAL dynamic animation.
    Rotation and position change smoothly every frame.
    """
    # Get base iPhone
    iphone, mask = get_base_iphone()
    
    # Put video on screen FIRST (before rotation)
    composited = composite_video_on_screen(iphone, mask, video_frame)
    
    # DYNAMIC ANIMATION - these values change every frame!
    # Rotation oscillates: -15 to +15 degrees
    rotation = 15 * math.sin(time_progress * math.pi * 2)
    
    # Apply 3D rotation transform
    rotated = apply_3d_rotation(composited, rotation)
    
    # Scale to fit output
    target_h = int(output_size[1] * phone_scale)
    scale = target_h / rotated.height
    new_w = int(rotated.width * scale)
    new_h = int(rotated.height * scale)
    scaled = rotated.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Position with floating animation
    float_y = 30 * math.sin(time_progress * math.pi * 4)  # Float up/down
    float_x = 15 * math.sin(time_progress * math.pi * 3)  # Slight horizontal
    
    x = (output_size[0] - scaled.width) // 2 + int(float_x)
    y = (output_size[1] - scaled.height) // 2 + int(float_y)
    
    # Ensure visible
    y = max(10, min(y, output_size[1] - scaled.height - 10))
    
    # Create background
    bg = create_dark_gradient(output_size[0], output_size[1], bg_color).convert("RGBA")
    
    # Add shadow
    shadow = create_shadow((x, y, scaled.width, scaled.height), output_size)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(scaled, (x, y), scaled)
    
    return bg.convert("RGB")


def render_phone_with_text(
    video_frame: Image.Image,
    text_lines: list,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (25, 35, 30),
    phone_position: str = "left"
) -> Image.Image:
    """Phone on side with animated text."""
    iphone, mask = get_base_iphone()
    composited = composite_video_on_screen(iphone, mask, video_frame)
    
    # Animation
    rotation = 20 + 10 * math.sin(time_progress * math.pi * 2)
    rotated = apply_3d_rotation(composited, rotation)
    
    # Smaller phone to fit with text
    target_h = int(output_size[1] * 0.6)
    scale = target_h / rotated.height
    scaled = rotated.resize((int(rotated.width * scale), int(rotated.height * scale)), Image.Resampling.LANCZOS)
    
    float_y = 20 * math.sin(time_progress * math.pi * 3)
    
    if phone_position == "left":
        phone_x = output_size[0] // 5
        text_x = output_size[0] // 2 + 50
    else:
        phone_x = output_size[0] * 3 // 5
        text_x = 50
    
    phone_y = (output_size[1] - scaled.height) // 2 + int(float_y)
    
    bg = create_dark_gradient(output_size[0], output_size[1], bg_color).convert("RGBA")
    
    shadow = create_shadow((phone_x, phone_y, scaled.width, scaled.height), output_size)
    bg = Image.alpha_composite(bg, shadow)
    bg.paste(scaled, (phone_x, phone_y), scaled)
    
    # Draw text
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 72)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
    except:
        font_big = font_small = ImageFont.load_default()
    
    text_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    text_y = output_size[1] // 2 - len(text_lines) * 50
    
    for i, line in enumerate(text_lines):
        prog = max(0, min(1, (time_progress - i * 0.1) * 3))
        alpha = int(255 * prog)
        slide = int(40 * (1 - prog))
        
        font = font_big if i == 0 else font_small
        draw.text((text_x + slide, text_y + i * 90), line, font=font, fill=(255, 255, 255, alpha))
    
    bg = Image.alpha_composite(bg, text_layer)
    return bg.convert("RGB")


# Compatibility functions
def create_simple_float_frame(video_frame, time_seconds, output_size=(1080, 1920), 
                               bg_color=(25, 35, 30), use_gradient=True):
    progress = (time_seconds % 4.0) / 4.0
    return render_dynamic_phone(video_frame, progress, output_size, bg_color, 0.92)


def create_animated_iphone_frame(video_frame, time_progress, total_duration=6.0,
                                  output_size=(1080, 1920), bg_color=(25, 35, 30)):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, 0.92)


def create_smooth_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                               bg_color=(25, 35, 30), position="center"):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, 0.92)


def create_phone_with_text_frame(video_frame, text, time_progress, output_size=(1080, 1920),
                                  bg_color=(25, 35, 30), phone_position="left", font_size=72):
    lines = [text] if isinstance(text, str) else text
    return render_phone_with_text(video_frame, lines, time_progress, output_size, bg_color, phone_position)


def blend_iphone_renders(angle):
    img, mask = get_base_iphone()
    return img, mask

def composite_video_clean(iphone, video):
    _, mask = get_base_iphone()
    return composite_video_on_screen(iphone, mask, video)

def select_iphone_render(rotation):
    return "/app/backend/iphone_renders/iphone_rot_12.png", 12
