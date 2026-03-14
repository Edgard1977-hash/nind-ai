"""
iPhone 16 3D model compositor v2
Smooth animation with dark gradient background like reference video
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from pathlib import Path
import math

# Available pre-rendered angles
AVAILABLE_ANGLES = [5, 8, 10, 12, 15, 16, 20, 25, 30, 35, 40]

def get_screen_mask(iphone_img: Image.Image) -> Image.Image:
    """Extract screen mask from iPhone render by detecting pink/magenta color"""
    arr = np.array(iphone_img)
    
    # Screen is magenta: high R, low G, high B
    # Strict threshold to avoid edge bleeding
    pink_mask = (arr[:,:,0] > 180) & (arr[:,:,1] < 80) & (arr[:,:,2] > 180) & (arr[:,:,3] > 200)
    
    mask = Image.fromarray((pink_mask * 255).astype(np.uint8), mode='L')
    
    # Erode to remove edge artifacts
    mask = mask.filter(ImageFilter.MinFilter(7))
    
    # Smooth edges
    mask = mask.filter(ImageFilter.GaussianBlur(radius=1))
    
    return mask


def create_dark_gradient_bg(width: int, height: int, color: tuple = (80, 20, 20)) -> Image.Image:
    """Create dark radial gradient background like reference video"""
    bg = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(bg)
    
    # Center point for radial gradient
    cx, cy = width // 2, height // 2
    max_radius = math.sqrt(cx**2 + cy**2)
    
    # Create radial gradient
    for y in range(height):
        for x in range(width):
            # Distance from center
            dist = math.sqrt((x - cx)**2 + (y - cy)**2)
            # Normalize (0 at center, 1 at edges)
            t = min(dist / max_radius, 1.0)
            
            # Interpolate from color to black
            r = int(color[0] * (1 - t * 0.8))
            g = int(color[1] * (1 - t * 0.9))
            b = int(color[2] * (1 - t * 0.9))
            
            bg.putpixel((x, y), (r, g, b))
    
    return bg


def create_gradient_bg_fast(width: int, height: int, color: tuple = (100, 25, 25)) -> Image.Image:
    """Fast version of gradient background using numpy"""
    # Create coordinate grids
    y_coords, x_coords = np.mgrid[0:height, 0:width]
    
    # Center
    cx, cy = width // 2, height // 2
    
    # Distance from center (normalized)
    dist = np.sqrt((x_coords - cx)**2 + (y_coords - cy)**2)
    max_dist = np.sqrt(cx**2 + cy**2)
    t = np.clip(dist / max_dist, 0, 1)
    
    # Create RGB channels with radial falloff
    r = (color[0] * (1 - t * 0.85)).astype(np.uint8)
    g = (color[1] * (1 - t * 0.9)).astype(np.uint8)
    b = (color[2] * (1 - t * 0.9)).astype(np.uint8)
    
    # Stack to RGB
    rgb = np.stack([r, g, b], axis=-1)
    
    return Image.fromarray(rgb, mode='RGB')


def apply_perspective_transform(img: Image.Image, rotation_y: float) -> Image.Image:
    """Apply 3D perspective transform for rotation effect"""
    if abs(rotation_y) < 1:
        return img
    
    width, height = img.size
    
    # Calculate perspective distortion based on rotation
    skew = math.tan(math.radians(rotation_y)) * 0.15
    
    # Source corners
    src = [(0, 0), (width, 0), (width, height), (0, height)]
    
    # Destination corners with perspective
    if rotation_y > 0:
        # Rotated right
        shrink_top = int(height * 0.03 * (rotation_y / 15))
        shrink_bot = int(height * 0.03 * (rotation_y / 15))
        shift = int(width * skew * 0.5)
        dst = [
            (shift, shrink_top),
            (width, 0),
            (width, height),
            (shift, height - shrink_bot)
        ]
    else:
        # Rotated left
        shrink_top = int(height * 0.03 * (abs(rotation_y) / 15))
        shrink_bot = int(height * 0.03 * (abs(rotation_y) / 15))
        shift = int(width * abs(skew) * 0.5)
        dst = [
            (0, 0),
            (width - shift, shrink_top),
            (width - shift, height - shrink_bot),
            (0, height)
        ]
    
    # Calculate perspective transform coefficients
    coeffs = find_perspective_coeffs(src, dst)
    
    # Apply transform
    result = img.transform((width, height), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    
    return result


def find_perspective_coeffs(src, dst):
    """Calculate perspective transform coefficients"""
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    res = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(res.flatten())


def composite_video_on_iphone(
    iphone_img: Image.Image,
    video_frame: Image.Image
) -> Image.Image:
    """Composite video frame onto iPhone screen"""
    # Get screen mask
    screen_mask = get_screen_mask(iphone_img)
    
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
    
    if screen_w <= 0 or screen_h <= 0:
        return iphone_img
    
    # Resize video frame to fit screen
    video_resized = video_frame.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    # Create result
    result = iphone_img.copy()
    arr = np.array(result)
    
    # Create video layer
    video_arr = np.array(video_resized.convert("RGBA"))
    
    # Get mask for blending (crop to screen area)
    mask_crop = mask_arr[y1:y2, x1:x2]
    
    # Expand mask to 4 channels
    alpha = mask_crop[:, :, np.newaxis] / 255.0
    
    # Blend video onto result in screen area
    arr[y1:y2, x1:x2] = (arr[y1:y2, x1:x2] * (1 - alpha) + video_arr * alpha).astype(np.uint8)
    
    return Image.fromarray(arr, mode='RGBA')


def select_iphone_render(rotation: float) -> tuple:
    """Select closest pre-rendered iPhone and return path + actual angle"""
    renders_dir = Path("/app/backend/iphone_renders")
    
    # Check what files actually exist
    available = []
    for f in renders_dir.glob("iphone_rot_*.png"):
        try:
            angle = int(f.stem.split("_")[-1])
            available.append(angle)
        except:
            pass
    
    if not available:
        available = [12]  # Default
    
    # Find closest
    closest = min(available, key=lambda x: abs(x - rotation))
    
    return str(renders_dir / f"iphone_rot_{closest}.png"), closest


def create_animated_iphone_frame(
    video_frame: Image.Image,
    time_progress: float,  # 0.0 to 1.0 through animation
    total_duration: float = 6.0,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (100, 25, 25)  # Dark red like reference
) -> Image.Image:
    """
    Create a single frame with iPhone animation matching reference video.
    
    Animation phases (based on reference):
    - 0.0-0.25: iPhone enters, slight rotation 10-15°
    - 0.25-0.5: Rotation increases 15-25°, moves up
    - 0.5-0.75: Strong rotation 25-35°, continues up  
    - 0.75-1.0: Maximum rotation 35-40°, slight settle
    
    Args:
        video_frame: Video frame to show on screen
        time_progress: Progress through animation (0.0 to 1.0)
        total_duration: Total animation duration in seconds
        output_size: Output image size
        bg_color: Background gradient color
    
    Returns:
        Final composited frame
    """
    # Smooth easing function
    def ease_in_out(t):
        return t * t * (3 - 2 * t)
    
    # Animation keyframes based on reference video
    if time_progress < 0.25:
        # Phase 1: Enter with slight rotation
        t = ease_in_out(time_progress / 0.25)
        base_rotation = 8 + 7 * t  # 8 to 15
        float_y = 30 * (1 - t)  # Start below, move to center
        scale = 0.95 + 0.05 * t  # Grow slightly
        
    elif time_progress < 0.5:
        # Phase 2: Increase rotation, move up
        t = ease_in_out((time_progress - 0.25) / 0.25)
        base_rotation = 15 + 10 * t  # 15 to 25
        float_y = -40 * t  # Move up
        scale = 1.0 - 0.02 * t
        
    elif time_progress < 0.75:
        # Phase 3: Strong rotation
        t = ease_in_out((time_progress - 0.5) / 0.25)
        base_rotation = 25 + 10 * t  # 25 to 35
        float_y = -40 - 30 * t  # Continue up
        scale = 0.98 - 0.05 * t
        
    else:
        # Phase 4: Maximum rotation with settle
        t = ease_in_out((time_progress - 0.75) / 0.25)
        base_rotation = 35 + 5 * t  # 35 to 40
        float_y = -70 - 10 * t  # Final position
        scale = 0.93 - 0.03 * t
    
    # Add subtle continuous wobble for organic feel
    wobble = 1.5 * math.sin(time_progress * math.pi * 8)
    rotation = base_rotation + wobble
    
    # Clamp rotation to available renders
    rotation = max(5, min(40, rotation))
    
    # Get closest pre-rendered iPhone
    iphone_path, actual_angle = select_iphone_render(rotation)
    
    # Load iPhone render
    try:
        iphone = Image.open(iphone_path).convert("RGBA")
    except:
        iphone_path = "/app/backend/iphone_renders/iphone_rot_12.png"
        iphone = Image.open(iphone_path).convert("RGBA")
    
    # Composite video onto screen
    composited = composite_video_on_iphone(iphone, video_frame)
    
    # Apply additional perspective for angles between pre-rendered
    extra_rotation = rotation - actual_angle
    if abs(extra_rotation) > 1.5:
        composited = apply_perspective_transform(composited, extra_rotation * 0.7)
    
    # Scale
    if scale != 1.0:
        new_w = int(composited.width * scale)
        new_h = int(composited.height * scale)
        composited = composited.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    # Create gradient background
    bg = create_gradient_bg_fast(output_size[0], output_size[1], bg_color)
    bg = bg.convert("RGBA")
    
    # Center iPhone with animation offset
    x = (output_size[0] - composited.width) // 2
    y = (output_size[1] - composited.height) // 2 + int(float_y)
    
    # Paste with transparency
    bg.paste(composited, (x, y), composited)
    
    return bg.convert("RGB")


def create_simple_float_frame(
    video_frame: Image.Image,
    time_seconds: float,
    output_size: tuple = (1080, 1920),
    bg_color: tuple = (255, 255, 255),
    use_gradient: bool = False
) -> Image.Image:
    """
    Simple floating animation - smooth sine wave movement.
    
    Args:
        video_frame: Video frame to show on screen
        time_seconds: Current time in seconds
        output_size: Output image size
        bg_color: Background color (or gradient base if use_gradient=True)
        use_gradient: Use dark gradient background
    """
    # Animation parameters
    float_amplitude = 25
    float_period = 3.5
    rotation_amplitude = 4
    base_rotation = 12
    
    # Calculate animation values
    float_offset = math.sin(time_seconds * 2 * math.pi / float_period) * float_amplitude
    rotation_offset = math.sin(time_seconds * 2 * math.pi / (float_period * 1.2)) * rotation_amplitude
    rotation = base_rotation + rotation_offset
    
    # Get iPhone render
    iphone_path, actual_angle = select_iphone_render(rotation)
    
    try:
        iphone = Image.open(iphone_path).convert("RGBA")
    except:
        iphone_path = "/app/backend/iphone_renders/iphone_rot_12.png"
        iphone = Image.open(iphone_path).convert("RGBA")
    
    # Composite video
    composited = composite_video_on_iphone(iphone, video_frame)
    
    # Apply extra perspective if needed
    extra_rotation = rotation - actual_angle
    if abs(extra_rotation) > 1:
        composited = apply_perspective_transform(composited, extra_rotation * 0.5)
    
    # Create background
    if use_gradient:
        bg = create_gradient_bg_fast(output_size[0], output_size[1], bg_color)
    else:
        bg = Image.new("RGB", output_size, bg_color)
    bg = bg.convert("RGBA")
    
    # Position
    x = (output_size[0] - composited.width) // 2
    y = (output_size[1] - composited.height) // 2 + int(float_offset)
    
    bg.paste(composited, (x, y), composited)
    
    return bg.convert("RGB")
