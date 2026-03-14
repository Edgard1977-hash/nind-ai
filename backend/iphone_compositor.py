"""
iPhone 16 3D model compositor v3
Fixes: purple artifacts, smooth interpolation, phone+text layout
"""

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from pathlib import Path
import math

# Available pre-rendered angles
AVAILABLE_ANGLES = [5, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40]

def get_screen_mask_clean(iphone_img: Image.Image) -> Image.Image:
    """
    Extract screen mask with aggressive cleanup to remove ALL pink/purple artifacts.
    """
    arr = np.array(iphone_img)
    
    # Detect magenta/pink screen area with multiple thresholds
    # Pink/magenta has: high R, low G, high B
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    a = arr[:,:,3] if arr.shape[2] == 4 else np.ones_like(r) * 255
    
    # Primary mask: strict magenta detection
    pink_mask = (r > 150) & (g < 100) & (b > 150) & (a > 150)
    
    # Secondary: catch edge bleeding (where R and B are similar and high, G is low)
    edge_mask = (r > 120) & (b > 120) & (g < 120) & (abs(r.astype(int) - b.astype(int)) < 60)
    
    # Tertiary: catch any purplish colors
    purple_mask = (r > 100) & (b > 100) & (g < r - 30) & (g < b - 30)
    
    # Combine masks
    combined_mask = pink_mask | edge_mask | purple_mask
    
    mask = Image.fromarray((combined_mask * 255).astype(np.uint8), mode='L')
    
    # Aggressive erosion to shrink mask and remove ALL edge artifacts
    mask = mask.filter(ImageFilter.MinFilter(11))
    
    # Then slight dilation to smooth
    mask = mask.filter(ImageFilter.MaxFilter(3))
    
    return mask


def get_raw_screen_mask(iphone_img: Image.Image) -> Image.Image:
    """
    Get screen mask from ORIGINAL render (before pink removal).
    Used to find screen bounds only.
    """
    arr = np.array(iphone_img)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    a = arr[:,:,3] if arr.shape[2] == 4 else np.ones_like(r) * 255
    
    # Detect pink/magenta screen
    pink_mask = (r > 150) & (g < 100) & (b > 150) & (a > 150)
    
    mask = Image.fromarray((pink_mask * 255).astype(np.uint8), mode='L')
    mask = mask.filter(ImageFilter.MinFilter(7))
    
    return mask


def remove_pink_from_render(iphone_img: Image.Image) -> Image.Image:
    """
    Pre-process iPhone render to replace ALL pink/purple pixels with black.
    This runs before compositing to ensure no artifacts remain.
    """
    arr = np.array(iphone_img).copy()
    
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    
    # Find all pinkish/purplish pixels
    pink_pixels = (r > 100) & (b > 100) & (g < r) & (g < b)
    
    # Replace with black
    arr[pink_pixels, 0] = 0  # R
    arr[pink_pixels, 1] = 0  # G
    arr[pink_pixels, 2] = 0  # B
    
    return Image.fromarray(arr, mode=iphone_img.mode)


def blend_iphone_renders(angle: float) -> tuple:
    """
    Smoothly interpolate between two pre-rendered iPhone angles.
    Returns: (blended_image_with_black_screen, screen_mask)
    """
    renders_dir = Path("/app/backend/iphone_renders")
    
    # Find the two nearest angles
    lower_angle = max([a for a in AVAILABLE_ANGLES if a <= angle], default=AVAILABLE_ANGLES[0])
    upper_angle = min([a for a in AVAILABLE_ANGLES if a >= angle], default=AVAILABLE_ANGLES[-1])
    
    # Load both renders
    lower_path = renders_dir / f"iphone_rot_{lower_angle}.png"
    upper_path = renders_dir / f"iphone_rot_{upper_angle}.png"
    
    if not lower_path.exists():
        lower_path = renders_dir / "iphone_rot_12.png"
    if not upper_path.exists():
        upper_path = renders_dir / "iphone_rot_12.png"
    
    lower_img = Image.open(lower_path).convert("RGBA")
    
    # Get mask from original (before pink removal)
    lower_mask = get_raw_screen_mask(lower_img)
    
    # Clean pink
    lower_img = remove_pink_from_render(lower_img)
    
    if lower_angle == upper_angle:
        return lower_img, lower_mask
    
    upper_img = Image.open(upper_path).convert("RGBA")
    upper_mask = get_raw_screen_mask(upper_img)
    upper_img = remove_pink_from_render(upper_img)
    
    # Calculate blend factor (0 = lower, 1 = upper)
    blend = (angle - lower_angle) / (upper_angle - lower_angle)
    
    # Blend both images and masks
    blended = Image.blend(lower_img, upper_img, blend)
    blended_mask = Image.blend(lower_mask.convert("L"), upper_mask.convert("L"), blend)
    
    return blended, blended_mask


def composite_video_on_screen(
    iphone_img: Image.Image,
    screen_mask: Image.Image,
    video_frame: Image.Image
) -> Image.Image:
    """
    Composite video onto iPhone screen using the provided mask.
    iPhone image should already have black screen (pink removed).
    """
    # Find screen bounds from mask
    mask_arr = np.array(screen_mask)
    rows = np.any(mask_arr > 50, axis=1)
    cols = np.any(mask_arr > 50, axis=0)
    
    if not (rows.any() and cols.any()):
        return iphone_img
    
    y1, y2 = np.where(rows)[0][[0, -1]]
    x1, x2 = np.where(cols)[0][[0, -1]]
    
    screen_w = x2 - x1
    screen_h = y2 - y1
    
    if screen_w <= 10 or screen_h <= 10:
        return iphone_img
    
    # Resize video to fit screen
    video_resized = video_frame.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    # Create result
    result = iphone_img.copy()
    result_arr = np.array(result)
    
    # Create video layer
    video_rgba = video_resized.convert("RGBA")
    video_arr = np.array(video_rgba)
    
    # Get mask for the screen area (eroded to avoid edge artifacts)
    mask_eroded = screen_mask.filter(ImageFilter.MinFilter(5))
    mask_crop = np.array(mask_eroded)[y1:y2, x1:x2].astype(float) / 255.0
    mask_crop = mask_crop[:, :, np.newaxis]
    
    # Blend: where mask is white, use video; where black, keep original
    result_arr[y1:y2, x1:x2] = (
        result_arr[y1:y2, x1:x2] * (1 - mask_crop) + 
        video_arr * mask_crop
    ).astype(np.uint8)
    
    return Image.fromarray(result_arr, mode='RGBA')


def composite_video_clean(
    iphone_img: Image.Image,
    video_frame: Image.Image
) -> Image.Image:
    """
    Legacy function - get mask from original then composite.
    """
    # Need to reload original to get mask
    renders_dir = Path("/app/backend/iphone_renders")
    original = Image.open(renders_dir / "iphone_rot_12.png").convert("RGBA")
    mask = get_raw_screen_mask(original)
    
    return composite_video_on_screen(iphone_img, mask, video_frame)


def create_spotlight_gradient(width: int, height: int, color: tuple = (60, 80, 60)) -> Image.Image:
    """
    Create gradient background with spotlight effect from below (like reference).
    """
    # Create with numpy for speed
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    
    # Spotlight center at bottom-center
    cx = width // 2
    cy = height + height // 4  # Below the frame
    
    # Distance from spotlight
    dist = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
    max_dist = np.sqrt(width**2 + height**2)
    
    # Normalize and invert (bright near source)
    t = np.clip(dist / max_dist, 0, 1)
    
    # Create color with falloff
    r = (color[0] * (1 - t * 0.7)).astype(np.uint8)
    g = (color[1] * (1 - t * 0.7)).astype(np.uint8)
    b = (color[2] * (1 - t * 0.7)).astype(np.uint8)
    
    rgb = np.stack([r, g, b], axis=-1)
    return Image.fromarray(rgb, mode='RGB')


def create_phone_shadow(phone_img: Image.Image, offset_y: int = 50) -> Image.Image:
    """
    Create realistic floor shadow for phone.
    """
    # Get alpha channel to create shadow shape
    if phone_img.mode != 'RGBA':
        phone_img = phone_img.convert('RGBA')
    
    # Create shadow from alpha
    alpha = np.array(phone_img.split()[3])
    
    # Squeeze shadow vertically and blur
    shadow_h = phone_img.height // 8
    shadow_w = int(phone_img.width * 0.8)
    
    shadow = Image.new('L', (shadow_w, shadow_h), 0)
    shadow_draw = ImageDraw.Draw(shadow)
    
    # Elliptical shadow
    shadow_draw.ellipse([0, 0, shadow_w, shadow_h], fill=80)
    
    # Blur
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=20))
    
    return shadow


def ease_in_out_cubic(t: float) -> float:
    """Smooth cubic easing function."""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2


def create_smooth_phone_frame(
    video_frame: Image.Image,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (60, 80, 60),  # Greenish like reference
    position: str = "center"  # "center", "left", "right"
) -> Image.Image:
    """
    Create a single frame with smooth iPhone animation.
    Uses interpolation between renders for smooth motion.
    """
    # Smooth easing
    t = ease_in_out_cubic(time_progress)
    
    # Animation: rotation goes from 8 to 35 degrees
    rotation = 8 + 27 * t
    
    # Floating offset
    float_offset = math.sin(time_progress * math.pi * 4) * 20
    
    # Scale decreases slightly as rotation increases
    scale = 1.0 - 0.15 * t
    
    # Get smoothly interpolated iPhone render and mask
    iphone, screen_mask = blend_iphone_renders(rotation)
    
    # Composite video onto screen
    composited = composite_video_on_screen(iphone, screen_mask, video_frame)
    
    # Scale
    new_w = int(composited.width * scale)
    new_h = int(composited.height * scale)
    composited = composited.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Create background with spotlight
    bg = create_spotlight_gradient(output_size[0], output_size[1], bg_color)
    bg = bg.convert("RGBA")
    
    # Calculate position
    if position == "left":
        x = output_size[0] // 6 - composited.width // 2
    elif position == "right":
        x = output_size[0] * 5 // 6 - composited.width // 2
    else:  # center
        x = (output_size[0] - composited.width) // 2
    
    y = (output_size[1] - composited.height) // 2 + int(float_offset) - int(50 * t)
    
    # Add shadow
    shadow = create_phone_shadow(composited)
    shadow_x = x + (composited.width - shadow.width) // 2
    shadow_y = y + composited.height - 30
    
    # Paste shadow first
    shadow_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    shadow_rgba = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
    shadow_rgba.putalpha(shadow)
    shadow_layer.paste(shadow_rgba, (shadow_x, shadow_y), shadow_rgba)
    bg = Image.alpha_composite(bg, shadow_layer)
    
    # Paste phone
    bg.paste(composited, (x, y), composited)
    
    return bg.convert("RGB")


def create_phone_with_text_frame(
    video_frame: Image.Image,
    text: str,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (60, 80, 60),
    phone_position: str = "left",  # "left" or "right"
    font_size: int = 72
) -> Image.Image:
    """
    Create frame with phone on one side and animated text on other side.
    Like the Spotify reference video.
    """
    # Smooth easing
    t = ease_in_out_cubic(time_progress)
    
    # Phone animation
    rotation = 10 + 20 * t
    float_offset = math.sin(time_progress * math.pi * 3) * 15
    scale = 0.75 - 0.1 * t  # Smaller to fit with text
    
    # Get smoothly interpolated iPhone and mask
    iphone, screen_mask = blend_iphone_renders(rotation)
    composited = composite_video_on_screen(iphone, screen_mask, video_frame)
    
    # Scale phone
    new_w = int(composited.width * scale)
    new_h = int(composited.height * scale)
    composited = composited.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Create background
    bg = create_spotlight_gradient(output_size[0], output_size[1], bg_color)
    bg = bg.convert("RGBA")
    
    # Phone position
    if phone_position == "left":
        phone_x = output_size[0] // 5 - composited.width // 2
        text_x = output_size[0] * 3 // 5
    else:
        phone_x = output_size[0] * 4 // 5 - composited.width // 2
        text_x = output_size[0] // 5
    
    phone_y = (output_size[1] - composited.height) // 2 + int(float_offset)
    
    # Add shadow
    shadow = create_phone_shadow(composited)
    shadow_x = phone_x + (composited.width - shadow.width) // 2
    shadow_y = phone_y + composited.height - 30
    
    shadow_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    shadow_rgba = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
    shadow_rgba.putalpha(shadow)
    shadow_layer.paste(shadow_rgba, (shadow_x, shadow_y), shadow_rgba)
    bg = Image.alpha_composite(bg, shadow_layer)
    
    # Paste phone
    bg.paste(composited, (phone_x, phone_y), composited)
    
    # Draw text with fade-in animation
    draw = ImageDraw.Draw(bg)
    
    # Text fade-in (starts at 20% progress)
    text_progress = max(0, (time_progress - 0.2) / 0.3)
    text_progress = min(1, text_progress)
    text_alpha = int(255 * ease_in_out_cubic(text_progress))
    
    # Text slide-in from right
    text_slide = int(100 * (1 - text_progress))
    
    # Try to load font
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position
    text_y = output_size[1] // 2
    
    # Draw text with alpha (using a separate layer)
    text_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    
    # Draw text
    text_draw.text(
        (text_x + text_slide, text_y),
        text,
        font=font,
        fill=(255, 255, 255, text_alpha)
    )
    
    # Composite text
    bg = Image.alpha_composite(bg, text_layer)
    
    return bg.convert("RGB")


# Keep old functions for compatibility
def select_iphone_render(rotation: float) -> tuple:
    """Select closest pre-rendered iPhone and return path + actual angle"""
    renders_dir = Path("/app/backend/iphone_renders")
    
    available = []
    for f in renders_dir.glob("iphone_rot_*.png"):
        try:
            angle = int(f.stem.split("_")[-1])
            available.append(angle)
        except:
            pass
    
    if not available:
        available = [12]
    
    closest = min(available, key=lambda x: abs(x - rotation))
    return str(renders_dir / f"iphone_rot_{closest}.png"), closest


def create_simple_float_frame(
    video_frame: Image.Image,
    time_seconds: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (60, 80, 60),
    use_gradient: bool = True
) -> Image.Image:
    """Simple floating animation with smooth interpolation."""
    # Animation parameters
    float_period = 3.5
    rotation_period = 4.0
    
    # Calculate smooth values
    float_offset = math.sin(time_seconds * 2 * math.pi / float_period) * 25
    rotation = 12 + 8 * math.sin(time_seconds * 2 * math.pi / rotation_period)
    
    # Get interpolated iPhone and mask
    iphone, screen_mask = blend_iphone_renders(rotation)
    
    # Composite video
    composited = composite_video_on_screen(iphone, screen_mask, video_frame)
    
    # Create background
    if use_gradient:
        bg = create_spotlight_gradient(output_size[0], output_size[1], bg_color)
    else:
        bg = Image.new("RGB", output_size, bg_color)
    bg = bg.convert("RGBA")
    
    # Center position with float
    x = (output_size[0] - composited.width) // 2
    y = (output_size[1] - composited.height) // 2 + int(float_offset)
    
    # Add shadow
    shadow = create_phone_shadow(composited)
    shadow_x = x + (composited.width - shadow.width) // 2
    shadow_y = y + composited.height - 30
    
    shadow_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    shadow_rgba = Image.new('RGBA', shadow.size, (0, 0, 0, 0))
    shadow_rgba.putalpha(shadow)
    shadow_layer.paste(shadow_rgba, (shadow_x, shadow_y), shadow_rgba)
    bg = Image.alpha_composite(bg, shadow_layer)
    
    # Paste phone
    bg.paste(composited, (x, y), composited)
    
    return bg.convert("RGB")


def create_animated_iphone_frame(
    video_frame: Image.Image,
    time_progress: float,
    total_duration: float = 6.0,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (60, 80, 60)
) -> Image.Image:
    """
    Create cinematic animation frame with smooth interpolation.
    """
    return create_smooth_phone_frame(
        video_frame=video_frame,
        time_progress=time_progress,
        output_size=output_size,
        bg_color=bg_color,
        position="center"
    )
