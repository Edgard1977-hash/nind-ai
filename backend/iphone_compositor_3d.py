"""
iPhone 16 3D Compositor v1
Uses pre-rendered 3D iPhone 16 models for realistic animation
Key features:
- Real 3D renders from Blender
- Screen content replacement
- Smooth angle interpolation
- FULL phone visibility guaranteed
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
import os

# Paths
RENDER_DIR = "/app/backend/iphone_16_renders"

# Pre-analyzed screen coordinates for 0-degree render (1080x2160)
# These are relative to the phone bounds
PHONE_BOUNDS_0 = {
    'x_min': 96, 'x_max': 684,
    'y_min': 478, 'y_max': 1681
}
SCREEN_BOUNDS_0 = {
    'x_min': 124, 'x_max': 655,
    'y_min': 503, 'y_max': 1656
}

# Available render angles
RENDER_ANGLES = [-40, -30, -20, -10, 0, 10, 20, 30, 40]


def load_render(angle: int) -> Image.Image:
    """Load pre-rendered iPhone at specified angle"""
    # Clamp to available angles
    angle = max(-40, min(40, angle))
    # Round to nearest available angle
    nearest = min(RENDER_ANGLES, key=lambda x: abs(x - angle))
    
    path = os.path.join(RENDER_DIR, f"iphone16_angle_{nearest}.png")
    if os.path.exists(path):
        return Image.open(path).convert('RGBA')
    else:
        # Fallback to 0-degree
        return Image.open(os.path.join(RENDER_DIR, "iphone16_angle_0.png")).convert('RGBA')


def interpolate_renders(angle: float) -> Image.Image:
    """Interpolate between two pre-rendered angles for smooth animation"""
    if angle <= -40:
        return load_render(-40)
    if angle >= 40:
        return load_render(40)
    
    # Find surrounding angles
    lower_angle = max(a for a in RENDER_ANGLES if a <= angle)
    upper_angle = min(a for a in RENDER_ANGLES if a >= angle)
    
    if lower_angle == upper_angle:
        return load_render(lower_angle)
    
    # Load both renders
    lower_img = load_render(lower_angle)
    upper_img = load_render(upper_angle)
    
    # Calculate blend factor
    t = (angle - lower_angle) / (upper_angle - lower_angle)
    
    # Blend images
    return Image.blend(lower_img, upper_img, t)


def find_screen_region(phone_img: Image.Image) -> tuple:
    """Find the screen region in the phone render by color analysis"""
    arr = np.array(phone_img)
    alpha = arr[:,:,3]
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]
    
    # First find phone bounds
    phone_alpha = np.where(alpha > 10)
    if len(phone_alpha[0]) == 0:
        return None
        
    py_min, py_max = phone_alpha[0].min(), phone_alpha[0].max()
    px_min, px_max = phone_alpha[1].min(), phone_alpha[1].max()
    
    pw = px_max - px_min
    ph = py_max - py_min
    
    # Screen is inset from phone edges
    # Leave room at top for Dynamic Island (about 5% of height)
    sx_min = px_min + int(pw * 0.05)
    sx_max = px_max - int(pw * 0.05)
    sy_min = py_min + int(ph * 0.05)  # Extra room at top for Dynamic Island
    sy_max = py_max - int(ph * 0.02)
    
    return (sx_min, sy_min, sx_max, sy_max)


def composite_screen_content(phone_img: Image.Image, screen_content: Image.Image, angle: float = 0) -> Image.Image:
    """
    Replace the screen area with custom content.
    Returns a new image with the screen content composited.
    Preserves Dynamic Island and bezel visibility.
    """
    result = phone_img.copy()
    phone_arr = np.array(phone_img)
    
    # Find screen region
    screen_bounds = find_screen_region(phone_img)
    if not screen_bounds:
        return result
    
    sx_min, sy_min, sx_max, sy_max = screen_bounds
    screen_w = sx_max - sx_min
    screen_h = sy_max - sy_min
    
    # Apply perspective distortion to screen content based on angle
    if abs(angle) > 5:
        screen_content = apply_screen_perspective(screen_content, angle)
    
    # Resize screen content to fit
    screen_resized = screen_content.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    if screen_resized.mode != 'RGBA':
        screen_resized = screen_resized.convert('RGBA')
    
    # Create mask based on original screen darkness
    # Screen pixels are dark (r,g,b all low) and opaque
    alpha = phone_arr[:,:,3]
    r, g, b = phone_arr[:,:,0], phone_arr[:,:,1], phone_arr[:,:,2]
    
    # Build mask only where original pixels are dark (screen area)
    # This preserves Dynamic Island (which is very dark/black)
    screen_mask = np.zeros((screen_h, screen_w), dtype=np.uint8)
    
    for y in range(screen_h):
        img_y = sy_min + y
        if img_y >= phone_img.height:
            continue
        for x in range(screen_w):
            img_x = sx_min + x
            if img_x >= phone_img.width:
                continue
            
            if alpha[img_y, img_x] > 10:
                # Screen is dark blue/gray, Dynamic Island is very dark black
                pixel_r, pixel_g, pixel_b = r[img_y, img_x], g[img_y, img_x], b[img_y, img_x]
                
                # Dynamic Island pixels are nearly black (< 15)
                is_dynamic_island = pixel_r < 15 and pixel_g < 15 and pixel_b < 20
                
                # Screen pixels are dark but have slight color (15-80 range)
                is_screen = (pixel_r >= 10 and pixel_r < 80 and 
                            pixel_g >= 10 and pixel_g < 80 and 
                            pixel_b >= 10 and pixel_b < 100)
                
                if is_screen and not is_dynamic_island:
                    screen_mask[y, x] = 255
    
    # Create PIL mask
    mask_img = Image.fromarray(screen_mask, mode='L')
    
    # Blur mask slightly for smoother edges
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(2))
    
    # Composite screen content onto phone
    result.paste(screen_resized, (sx_min, sy_min), mask_img)
    
    return result


def apply_screen_perspective(img: Image.Image, angle: float) -> Image.Image:
    """Apply subtle perspective distortion to screen content"""
    if abs(angle) < 3:
        return img
    
    w, h = img.size
    
    # Calculate compression based on angle
    compress = abs(math.sin(math.radians(angle))) * 0.15
    
    if angle > 0:
        # Right side compressed
        src = [(0, 0), (w, 0), (w, h), (0, h)]
        dst = [(0, 0), (w, int(h * compress)), (w, h - int(h * compress)), (0, h)]
    else:
        # Left side compressed
        src = [(0, 0), (w, 0), (w, h), (0, h)]
        dst = [(0, int(h * compress)), (w, 0), (w, h), (0, h - int(h * compress))]
    
    # Calculate transform coefficients
    coeffs = _calc_perspective_coeffs(src, dst)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def _calc_perspective_coeffs(src, dst):
    """Calculate perspective transform coefficients"""
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    return tuple(np.linalg.lstsq(A, B, rcond=None)[0])


def create_gradient_bg(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    """Create radial gradient background"""
    y, x = np.mgrid[0:h, 0:w]
    cx, cy = w // 2, h // 2
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = math.sqrt((w/2)**2 + (h/2)**2)
    t = np.clip(dist / max_dist, 0, 1) ** 0.6
    
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')


def create_shadow(phone_w: int, phone_h: int, pos_x: int, pos_y: int, 
                  output_size: tuple, angle: float) -> Image.Image:
    """Create realistic shadow under phone"""
    shadow = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    # Shadow parameters
    sw = int(phone_w * 0.5)
    sh = int(phone_w * 0.06)
    sx = pos_x + (phone_w - sw) // 2 + int(angle * 0.5)  # Shadow shifts with angle
    sy = pos_y + phone_h + 20
    sy = min(sy, output_size[1] - sh - 15)
    
    # Draw soft shadow ellipse
    for i in range(30, 0, -1):
        alpha = int(25 * (i / 30))
        expand = (30 - i) * 5
        draw.ellipse([sx - expand, sy - expand//4, sx + sw + expand, sy + sh + expand//4],
                     fill=(0, 0, 0, alpha))
    
    return shadow.filter(ImageFilter.GaussianBlur(15))


def ease_in_out(t: float) -> float:
    """Smooth easing function"""
    return -(math.cos(math.pi * t) - 1) / 2


def render_3d_phone_frame(
    video_frame: Image.Image,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color1: tuple = (90, 15, 15),
    bg_color2: tuple = (15, 5, 5),
    animation_style: str = "camera"
) -> Image.Image:
    """
    Render 3D iPhone with video content.
    Uses pre-rendered 3D models for realistic appearance.
    Phone is ALWAYS FULLY VISIBLE.
    """
    out_w, out_h = output_size
    
    # Calculate animation parameters
    if animation_style == "camera":
        # Multi-stage camera animation
        if time_progress < 0.35:
            t = time_progress / 0.35
            angle = 30 - 10 * ease_in_out(t)  # 30° -> 20°
        elif time_progress < 0.65:
            t = (time_progress - 0.35) / 0.30
            angle = 20 - 50 * ease_in_out(t)  # 20° -> -30°
        else:
            t = (time_progress - 0.65) / 0.35
            angle = -30 + 40 * ease_in_out(t)  # -30° -> 10°
    elif animation_style == "float":
        angle = 20 * math.sin(time_progress * math.pi * 2)
    else:
        angle = 15
    
    # Get interpolated phone render
    phone_render = interpolate_renders(angle)
    
    # Composite video content onto screen
    phone_with_content = composite_screen_content(phone_render, video_frame, angle)
    
    # Get phone bounds
    phone_arr = np.array(phone_with_content)
    alpha = phone_arr[:,:,3]
    non_transparent = np.where(alpha > 10)
    
    if len(non_transparent[0]) > 0:
        y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
        x_min, x_max = non_transparent[1].min(), non_transparent[1].max()
        # Crop to phone bounds
        phone_cropped = phone_with_content.crop((x_min, y_min, x_max + 1, y_max + 1))
    else:
        phone_cropped = phone_with_content
    
    # Scale phone to fit output
    # Phone should take 65% of screen height
    target_h = int(out_h * 0.65)
    scale = target_h / phone_cropped.height
    final_w = int(phone_cropped.width * scale)
    final_h = int(phone_cropped.height * scale)
    
    # Ensure it fits width with margins
    margin = int(out_w * 0.08)
    if final_w > (out_w - 2 * margin):
        scale = (out_w - 2 * margin) / phone_cropped.width
        final_w = int(phone_cropped.width * scale)
        final_h = int(phone_cropped.height * scale)
    
    phone_scaled = phone_cropped.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    # Add floating animation
    float_y = int(10 * math.sin(time_progress * math.pi * 2.5))
    float_x = int(6 * math.sin(time_progress * math.pi * 2))
    
    # Center position
    pos_x = (out_w - final_w) // 2 + float_x
    pos_y = (out_h - final_h) // 2 + float_y
    
    # Ensure within bounds with margins
    pos_x = max(margin, min(pos_x, out_w - final_w - margin))
    pos_y = max(margin, min(pos_y, out_h - final_h - margin))
    
    # Create background
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert('RGBA')
    
    # Add shadow
    shadow = create_shadow(final_w, final_h, pos_x, pos_y, output_size, angle)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(phone_scaled, (pos_x, pos_y), phone_scaled)
    
    return bg.convert('RGB')


# Compatibility wrappers for existing code
def render_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                       bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                       position="center", animation_style="camera"):
    return render_3d_phone_frame(video_frame, time_progress, output_size, 
                                  bg_color1, bg_color2, animation_style)


def render_dynamic_phone(video_frame, time_progress, output_size=(1080, 1920),
                         bg_color=(90, 15, 15), bg_color2=None, phone_scale=0.55,
                         animation_style="camera", position="center"):
    if bg_color2 is None:
        bg_color2 = tuple(max(0, c - 70) for c in bg_color)
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color, bg_color2, animation_style)


def render_camera_animation(video_frame, time_progress, output_size=(1080, 1920),
                            bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                            position="center", **kwargs):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, "camera")


def render_simple_float(video_frame, time_progress, output_size=(1080, 1920),
                        bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                        position="center", **kwargs):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, "float")


def render_full_phone_animation(video_frame, time_progress, output_size=(1080, 1920),
                                bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                                position="center", **kwargs):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, "camera")


# Legacy compatibility
def get_base_iphone():
    img = load_render(0)
    mask = Image.new('L', img.size, 255)
    return img, mask

def create_3d_iphone_mockup(screen_content, rotation_y=25, frame_width=400, frame_height=820):
    """Create phone mockup using 3D renders"""
    phone = interpolate_renders(rotation_y)
    return composite_screen_content(phone, screen_content, rotation_y)
