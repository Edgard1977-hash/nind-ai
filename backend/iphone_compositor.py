"""
iPhone 16 3D model compositor
Composites video frames onto pre-rendered iPhone 3D model
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from pathlib import Path
import math

# Screen bounds from pre-rendered iPhone at rotation 12
SCREEN_BOUNDS = {
    8: {"x1": 143, "x2": 944, "y1": 365, "y2": 1919},   # Rotation 8 degrees
    12: {"x1": 140, "x2": 944, "y1": 350, "y2": 1919},  # Rotation 12 degrees
    16: {"x1": 134, "x2": 944, "y1": 330, "y2": 1919},  # Rotation 16 degrees
}

def get_screen_mask(iphone_img: Image.Image) -> Image.Image:
    """Extract screen mask from iPhone render by detecting pink/magenta color"""
    arr = np.array(iphone_img)
    
    # Screen is magenta: high R, low G, high B
    # Use strict threshold to avoid edge bleeding
    pink_mask = (arr[:,:,0] > 180) & (arr[:,:,1] < 80) & (arr[:,:,2] > 180) & (arr[:,:,3] > 220)
    
    # Convert to image
    mask = Image.fromarray((pink_mask * 255).astype(np.uint8), mode='L')
    
    # Erode slightly to remove edge artifacts
    from PIL import ImageFilter
    mask = mask.filter(ImageFilter.MinFilter(3))
    
    # Slight blur for anti-aliasing
    mask = mask.filter(ImageFilter.GaussianBlur(radius=0.5))
    
    return mask

def composite_video_on_iphone(
    iphone_img: Image.Image,
    video_frame: Image.Image,
    rotation: int = 12
) -> Image.Image:
    """
    Composite video frame onto iPhone screen.
    
    Args:
        iphone_img: Pre-rendered iPhone image with pink screen
        video_frame: Video frame to display on screen
        rotation: Rotation angle (8, 12, or 16 degrees)
    
    Returns:
        Composited image
    """
    # Get screen mask
    screen_mask = get_screen_mask(iphone_img)
    
    # Find screen bounds from mask
    mask_arr = np.array(screen_mask)
    rows = np.any(mask_arr > 100, axis=1)
    cols = np.any(mask_arr > 100, axis=0)
    
    if rows.any() and cols.any():
        y1, y2 = np.where(rows)[0][[0, -1]]
        x1, x2 = np.where(cols)[0][[0, -1]]
    else:
        # Use default bounds
        bounds = SCREEN_BOUNDS.get(rotation, SCREEN_BOUNDS[12])
        x1, y1, x2, y2 = bounds["x1"], bounds["y1"], bounds["x2"], bounds["y2"]
    
    screen_w = x2 - x1
    screen_h = y2 - y1
    
    # Resize video frame to fit screen
    video_resized = video_frame.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    # Create result image
    result = iphone_img.copy()
    
    # Create screen layer
    screen_layer = Image.new("RGBA", iphone_img.size, (0, 0, 0, 0))
    screen_layer.paste(video_resized.convert("RGBA"), (x1, y1))
    
    # Apply mask
    screen_layer.putalpha(screen_mask)
    
    # Composite: replace pink screen with video
    # First, remove pink from original
    arr = np.array(result)
    mask_arr = np.array(screen_mask)
    
    # Where mask is white, replace with video
    screen_arr = np.array(screen_layer)
    
    # Blend based on mask
    alpha = mask_arr[:, :, np.newaxis] / 255.0
    result_arr = arr * (1 - alpha) + screen_arr * alpha
    
    result = Image.fromarray(result_arr.astype(np.uint8), mode='RGBA')
    
    return result


def create_floating_iphone_frame(
    iphone_path: str,
    video_frame: Image.Image,
    float_offset: float,
    rotation: int,
    bg_color: tuple = (255, 255, 255),
    output_size: tuple = (1080, 1920)
) -> Image.Image:
    """
    Create a single frame with iPhone + video + floating animation.
    
    Args:
        iphone_path: Path to pre-rendered iPhone PNG
        video_frame: Video frame to show on screen
        float_offset: Vertical offset for floating animation
        rotation: Rotation angle (8, 12, 16)
        bg_color: Background color
        output_size: Output image size
    
    Returns:
        Final composited frame
    """
    # Load iPhone render
    iphone = Image.open(iphone_path).convert("RGBA")
    
    # Composite video onto screen
    composited = composite_video_on_iphone(iphone, video_frame, rotation)
    
    # Create background
    bg = Image.new("RGB", output_size, bg_color)
    bg = bg.convert("RGBA")
    
    # Center iPhone with float offset
    x = (output_size[0] - composited.width) // 2
    y = (output_size[1] - composited.height) // 2 + int(float_offset)
    
    # Paste with transparency
    bg.paste(composited, (x, y), composited)
    
    return bg.convert("RGB")


def select_iphone_render(rotation: float) -> str:
    """Select closest pre-rendered iPhone based on rotation"""
    renders_dir = Path("/app/backend/iphone_renders")
    
    # Available rotations
    available = [8, 12, 16]
    
    # Find closest
    closest = min(available, key=lambda x: abs(x - rotation))
    
    return str(renders_dir / f"iphone_rot_{closest}.png")
