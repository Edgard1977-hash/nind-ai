"""
iPhone 16 3D Compositor v5 - FIXED SCREEN CONTENT
- 91 pre-rendered angles (step 1°) for maximum smoothness  
- Content LOCKED to screen - no floating
- No status bar - just black bars for non-matching videos
- Full screen for matching aspect ratio
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
import os

RENDER_DIR = "/app/backend/iphone_16_renders_final"
FALLBACK_DIR = "/app/backend/iphone_16_renders_ultra"

AVAILABLE_ANGLES = list(range(-45, 46, 1))

# Fixed screen position as percentage of phone bounds
# These are carefully calibrated for the iPhone 16 model
SCREEN_MARGIN = {
    'left': 0.048,
    'right': 0.048, 
    'top': 0.022,
    'bottom': 0.018
}

IPHONE_SCREEN_RATIO = 19.5 / 9


def get_render_path(angle):
    nearest = min(AVAILABLE_ANGLES, key=lambda x: abs(x - angle))
    sign = '+' if nearest >= 0 else ''
    
    # Try final renders first
    path = os.path.join(RENDER_DIR, f"iphone_{sign}{nearest:03d}.png")
    if os.path.exists(path):
        return path
    
    # Fallback to ultra renders (step 2)
    nearest_2 = min(list(range(-45, 46, 2)), key=lambda x: abs(x - angle))
    sign_2 = '+' if nearest_2 >= 0 else ''
    path_2 = os.path.join(FALLBACK_DIR, f"iphone_{sign_2}{nearest_2:03d}.png")
    if os.path.exists(path_2):
        return path_2
    
    return None


def load_render_at_angle(angle):
    path = get_render_path(angle)
    if path and os.path.exists(path):
        return Image.open(path).convert('RGBA')
    # Last fallback
    for d in [RENDER_DIR, FALLBACK_DIR]:
        p = os.path.join(d, "iphone_+000.png")
        if os.path.exists(p):
            return Image.open(p).convert('RGBA')
    raise FileNotFoundError("No renders found")


def interpolate_renders(angle):
    """Smooth interpolation between adjacent angles"""
    angle = max(-45, min(45, angle))
    
    # Find surrounding angles
    lower = max(a for a in AVAILABLE_ANGLES if a <= angle)
    upper = min(a for a in AVAILABLE_ANGLES if a >= angle)
    
    if lower == upper:
        return load_render_at_angle(lower)
    
    lower_img = load_render_at_angle(lower)
    upper_img = load_render_at_angle(upper)
    
    t = (angle - lower) / (upper - lower)
    return Image.blend(lower_img, upper_img, t)


def get_phone_bounds(img):
    """Get tight bounding box of phone"""
    arr = np.array(img)
    alpha = arr[:,:,3]
    mask = alpha > 10
    
    if not mask.any():
        return (0, 0, img.width, img.height)
    
    rows = mask.any(axis=1)
    cols = mask.any(axis=0)
    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]
    
    return (int(x_min), int(y_min), int(x_max), int(y_max))


def get_screen_rect(phone_bounds):
    """Get fixed screen rectangle within phone bounds"""
    px_min, py_min, px_max, py_max = phone_bounds
    pw = px_max - px_min
    ph = py_max - py_min
    
    # Calculate screen bounds with fixed margins
    sx = px_min + int(pw * SCREEN_MARGIN['left'])
    sy = py_min + int(ph * SCREEN_MARGIN['top'])
    sw = pw - int(pw * (SCREEN_MARGIN['left'] + SCREEN_MARGIN['right']))
    sh = ph - int(ph * (SCREEN_MARGIN['top'] + SCREEN_MARGIN['bottom']))
    
    return (sx, sy, sw, sh)


def create_screen_mask(phone_img, screen_rect):
    """Create precise mask for screen area only"""
    sx, sy, sw, sh = screen_rect
    
    phone_arr = np.array(phone_img)
    alpha = phone_arr[:,:,3]
    r, g, b = phone_arr[:,:,0], phone_arr[:,:,1], phone_arr[:,:,2]
    
    # Create mask only within screen rect
    mask = np.zeros((phone_img.height, phone_img.width), dtype=np.uint8)
    
    for y in range(sy, min(sy + sh, phone_img.height)):
        for x in range(sx, min(sx + sw, phone_img.width)):
            if alpha[y, x] > 10:
                pr, pg, pb = r[y, x], g[y, x], b[y, x]
                
                # Dynamic Island is very dark black
                is_dynamic_island = pr < 15 and pg < 15 and pb < 18
                
                # Screen area is dark but not pure black
                is_screen = pr < 90 and pg < 90 and pb < 110
                
                if is_screen and not is_dynamic_island:
                    mask[y, x] = 255
    
    return Image.fromarray(mask, mode='L')


def prepare_video_content(video_frame, screen_w, screen_h):
    """
    Prepare video for screen display.
    - If aspect matches iPhone: fill entire screen
    - If not: center with black bars (no status bar)
    """
    video_w, video_h = video_frame.size
    video_ratio = video_h / video_w
    screen_ratio = screen_h / screen_w
    
    # Create black screen canvas
    screen = Image.new('RGB', (screen_w, screen_h), (0, 0, 0))
    
    # Check if video matches iPhone aspect (within 15% tolerance)
    ratio_diff = abs(video_ratio - IPHONE_SCREEN_RATIO) / IPHONE_SCREEN_RATIO
    
    if ratio_diff <= 0.15:
        # Matching ratio - fill entire screen
        video_resized = video_frame.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
        screen.paste(video_resized, (0, 0))
    else:
        # Non-matching - center with black bars (NO status bar)
        scale = min(screen_w / video_w, screen_h / video_h)
        new_w = int(video_w * scale)
        new_h = int(video_h * scale)
        
        video_resized = video_frame.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Center
        x = (screen_w - new_w) // 2
        y = (screen_h - new_h) // 2
        screen.paste(video_resized, (x, y))
    
    return screen


def composite_screen_locked(phone_img, video_frame):
    """
    Composite video onto phone with LOCKED positioning.
    Content stays fixed within screen bounds.
    """
    result = phone_img.copy()
    
    # Get phone and screen bounds
    phone_bounds = get_phone_bounds(phone_img)
    screen_rect = get_screen_rect(phone_bounds)
    sx, sy, sw, sh = screen_rect
    
    if sw <= 0 or sh <= 0:
        return result
    
    # Prepare video content for this screen size
    screen_content = prepare_video_content(video_frame, sw, sh)
    screen_rgba = screen_content.convert('RGBA')
    
    # Create precise screen mask
    mask = create_screen_mask(phone_img, screen_rect)
    
    # Crop mask to screen area
    mask_cropped = mask.crop((sx, sy, sx + sw, sy + sh))
    
    # Slight blur for smooth edges
    mask_cropped = mask_cropped.filter(ImageFilter.GaussianBlur(1))
    
    # Paste content at exact screen position
    result.paste(screen_rgba, (sx, sy), mask_cropped)
    
    return result


def create_gradient_bg(w, h, c1, c2):
    y, x = np.mgrid[0:h, 0:w]
    cx, cy = w // 2, h // 2
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = math.sqrt((w/2)**2 + (h/2)**2)
    t = np.clip(dist / max_dist, 0, 1) ** 0.6
    
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')


def create_shadow(phone_w, phone_h, pos_x, pos_y, output_size, angle):
    shadow = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    sw = int(phone_w * 0.45)
    sh = int(phone_w * 0.05)
    sx = pos_x + (phone_w - sw) // 2 + int(angle * 0.4)
    sy = pos_y + phone_h + 15
    sy = min(sy, output_size[1] - sh - 10)
    
    for i in range(25, 0, -1):
        a = int(20 * (i / 25))
        exp = (25 - i) * 4
        draw.ellipse([sx - exp, sy - exp//4, sx + sw + exp, sy + sh + exp//4], fill=(0, 0, 0, a))
    
    return shadow.filter(ImageFilter.GaussianBlur(12))


def ease_smooth(t):
    """Extra smooth easing"""
    return t * t * t * (t * (t * 6 - 15) + 10)


def render_3d_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                          bg_color1=(90, 15, 15), bg_color2=(15, 5, 5), animation_style="camera"):
    """
    Render 3D iPhone with ultra-smooth animation.
    Screen content is LOCKED in place.
    """
    out_w, out_h = output_size
    
    # VERY SLOW and SMOOTH animation with small angle range
    if animation_style == "camera":
        # Slower motion: ±15° range (smaller than before)
        if time_progress < 0.45:
            t = ease_smooth(time_progress / 0.45)
            angle_y = 14 - 4 * t  # 14 -> 10
        elif time_progress < 0.75:
            t = ease_smooth((time_progress - 0.45) / 0.30)
            angle_y = 10 - 24 * t  # 10 -> -14
        else:
            t = ease_smooth((time_progress - 0.75) / 0.25)
            angle_y = -14 + 20 * t  # -14 -> 6
    elif animation_style == "float":
        # Very gentle: ±10°
        angle_y = 10 * math.sin(time_progress * math.pi * 1.2)
    else:
        angle_y = 8
    
    # Get phone render at current angle
    phone_render = interpolate_renders(angle_y)
    
    # Composite with LOCKED screen content
    phone_with_content = composite_screen_locked(phone_render, video_frame)
    
    # Crop to phone bounds
    phone_arr = np.array(phone_with_content)
    alpha = phone_arr[:,:,3]
    mask = alpha > 10
    
    if mask.any():
        rows = mask.any(axis=1)
        cols = mask.any(axis=0)
        y_min, y_max = np.where(rows)[0][[0, -1]]
        x_min, x_max = np.where(cols)[0][[0, -1]]
        pad = 2
        y_min = max(0, y_min - pad)
        y_max = min(phone_with_content.height, y_max + pad)
        x_min = max(0, x_min - pad)
        x_max = min(phone_with_content.width, x_max + pad)
        cropped = phone_with_content.crop((x_min, y_min, x_max, y_max))
    else:
        cropped = phone_with_content
    
    # Scale to fit output
    target_h = int(out_h * 0.65)
    scale = target_h / cropped.height
    final_w = int(cropped.width * scale)
    final_h = int(cropped.height * scale)
    
    margin = int(out_w * 0.08)
    if final_w > (out_w - 2 * margin):
        scale = (out_w - 2 * margin) / cropped.width
        final_w = int(cropped.width * scale)
        final_h = int(cropped.height * scale)
    
    phone_scaled = cropped.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    # Very gentle float
    float_y = int(5 * math.sin(time_progress * math.pi * 1.8))
    float_x = int(3 * math.sin(time_progress * math.pi * 1.2))
    
    pos_x = (out_w - final_w) // 2 + float_x
    pos_y = (out_h - final_h) // 2 + float_y
    
    pos_x = max(margin, min(pos_x, out_w - final_w - margin))
    pos_y = max(margin, min(pos_y, out_h - final_h - margin))
    
    # Background
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert('RGBA')
    
    # Shadow
    shadow = create_shadow(final_w, final_h, pos_x, pos_y, output_size, angle_y)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(phone_scaled, (pos_x, pos_y), phone_scaled)
    
    return bg.convert('RGB')


# Compatibility wrappers
def render_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                       bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                       position="center", animation_style="camera"):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, animation_style)


def render_dynamic_phone(video_frame, time_progress, output_size=(1080, 1920),
                         bg_color=(90, 15, 15), bg_color2=None, phone_scale=0.55,
                         animation_style="camera", position="center"):
    if bg_color2 is None:
        bg_color2 = tuple(max(0, c - 70) for c in bg_color)
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color, bg_color2, animation_style)


def render_camera_animation(video_frame, time_progress, output_size=(1080, 1920),
                            bg_color1=(90, 15, 15), bg_color2=(15, 5, 5), position="center", **kwargs):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, "camera")


def render_simple_float(video_frame, time_progress, output_size=(1080, 1920),
                        bg_color1=(90, 15, 15), bg_color2=(15, 5, 5), position="center", **kwargs):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, "float")


def render_full_phone_animation(video_frame, time_progress, output_size=(1080, 1920),
                                bg_color1=(90, 15, 15), bg_color2=(15, 5, 5), position="center", **kwargs):
    return render_3d_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, "camera")


def get_base_iphone():
    img = load_render_at_angle(0)
    mask = Image.new('L', img.size, 255)
    return img, mask


def create_3d_iphone_mockup(screen_content, rotation_y=25, frame_width=400, frame_height=820):
    phone = load_render_at_angle(rotation_y)
    return composite_screen_locked(phone, screen_content)


def load_render(angle):
    return load_render_at_angle(angle)


def load_base_render():
    return load_render_at_angle(0)


def apply_perspective_transform(img, angle_y, angle_x=0):
    return img


def find_screen_region(phone_img):
    bounds = get_phone_bounds(phone_img)
    return get_screen_rect(bounds)
