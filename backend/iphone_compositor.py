"""
iPhone Mockup Generator v9
Creates FULL PHONE mockup that is ALWAYS COMPLETELY VISIBLE
Based on reference video analysis - phone fills ~60-65% of screen height
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math


def create_iphone_frame(width: int = 400, height: int = 820, corner_radius: int = 55) -> tuple:
    """
    Create realistic iPhone frame with 3D depth effect.
    Returns: (frame_image, screen_mask, screen_bounds)
    """
    # Frame with rounded corners
    frame = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    
    # Outer bezel - dark titanium color
    bezel_color = (28, 28, 32, 255)
    
    # Draw frame shadow/depth on right side for 3D effect
    shadow_offset = 4
    draw.rounded_rectangle(
        [shadow_offset, shadow_offset, width-1+shadow_offset, height-1+shadow_offset], 
        radius=corner_radius, 
        fill=(15, 15, 18, 200)
    )
    
    # Main frame body
    draw.rounded_rectangle([0, 0, width-1, height-1], radius=corner_radius, fill=bezel_color)
    
    # Subtle highlight on top-left for 3D
    highlight = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(highlight)
    h_draw.rounded_rectangle([0, 0, width//3, height//4], radius=corner_radius, fill=(255, 255, 255, 15))
    frame = Image.alpha_composite(frame, highlight.filter(ImageFilter.GaussianBlur(20)))
    draw = ImageDraw.Draw(frame)
    
    # Screen area (inset from frame)
    bezel_thickness = 12
    screen_x1 = bezel_thickness
    screen_y1 = bezel_thickness
    screen_x2 = width - bezel_thickness
    screen_y2 = height - bezel_thickness
    screen_radius = corner_radius - bezel_thickness + 2
    
    # Draw screen background (will be replaced with video)
    screen_color = (255, 0, 255, 255)  # Magenta for masking
    draw.rounded_rectangle(
        [screen_x1, screen_y1, screen_x2, screen_y2], 
        radius=screen_radius, 
        fill=screen_color
    )
    
    # Create screen mask
    mask = Image.new('L', (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [screen_x1, screen_y1, screen_x2, screen_y2],
        radius=screen_radius,
        fill=255
    )
    
    # Dynamic Island (notch)
    island_width = 110
    island_height = 32
    island_x = (width - island_width) // 2
    island_y = screen_y1 + 12
    
    # Draw Dynamic Island on frame
    draw.rounded_rectangle(
        [island_x, island_y, island_x + island_width, island_y + island_height],
        radius=16,
        fill=(5, 5, 8, 255)
    )
    
    # Side buttons with 3D effect
    button_color = (45, 45, 50, 255)
    button_highlight = (60, 60, 65, 255)
    
    # Power button - right side
    draw.rectangle([width-3, 180, width, 255], fill=button_color)
    draw.rectangle([width-2, 182, width-1, 253], fill=button_highlight)
    
    # Volume buttons - left side
    draw.rectangle([0, 160, 3, 205], fill=button_color)
    draw.rectangle([1, 162, 2, 203], fill=button_highlight)
    draw.rectangle([0, 215, 3, 260], fill=button_color)
    draw.rectangle([1, 217, 2, 258], fill=button_highlight)
    
    # Silent switch
    draw.rectangle([0, 115, 3, 145], fill=button_color)
    
    # Camera bump (subtle)
    cam_y = screen_y1 + 8
    cam_x = width // 2 - 20
    draw.ellipse([cam_x, cam_y, cam_x + 8, cam_y + 8], fill=(20, 20, 25, 255))
    draw.ellipse([cam_x + 14, cam_y, cam_x + 22, cam_y + 8], fill=(20, 20, 25, 255))
    
    # Screen bounds for video placement
    screen_bounds = (screen_x1, screen_y1, screen_x2, screen_y2)
    
    return frame, mask, screen_bounds


def composite_video_on_phone(phone_frame: Image.Image, screen_mask: Image.Image, 
                              screen_bounds: tuple, video_frame: Image.Image) -> Image.Image:
    """Place video content inside phone screen."""
    x1, y1, x2, y2 = screen_bounds
    screen_w = x2 - x1
    screen_h = y2 - y1
    
    # Resize video to fit screen
    video_resized = video_frame.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    
    # Create composite
    result = phone_frame.copy()
    result_arr = np.array(result)
    video_arr = np.array(video_resized.convert("RGBA"))
    
    # Use mask for blending
    mask_crop = np.array(screen_mask)[y1:y2, x1:x2].astype(float) / 255.0
    mask_crop = mask_crop[:, :, np.newaxis]
    
    # Blend video where mask is active
    result_arr[y1:y2, x1:x2] = (
        result_arr[y1:y2, x1:x2] * (1 - mask_crop) + video_arr * mask_crop
    ).astype(np.uint8)
    
    return Image.fromarray(result_arr, mode='RGBA')


def apply_3d_transform(img: Image.Image, rotation_y: float, rotation_x: float = 0) -> Image.Image:
    """
    Apply 3D perspective transform to phone.
    rotation_y: horizontal rotation (-60 to +60 degrees)
    rotation_x: forward/back tilt (-20 to +20 degrees)
    """
    if abs(rotation_y) < 0.5 and abs(rotation_x) < 0.5:
        return img
    
    w, h = img.size
    
    # Calculate perspective distortion
    angle_y = math.radians(abs(rotation_y))
    compress_y = math.sin(angle_y) * 0.22
    shift_y = math.sin(angle_y) * 0.05
    
    angle_x = math.radians(abs(rotation_x))
    compress_x = math.sin(angle_x) * 0.12
    
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    
    if rotation_y >= 0:
        # Rotated right
        cy = int(h * compress_y)
        sx = int(w * shift_y)
        dst = [(0, 0), (w - sx, cy), (w - sx, h - cy), (0, h)]
    else:
        # Rotated left
        cy = int(h * compress_y)
        sx = int(w * shift_y)
        dst = [(sx, cy), (w, 0), (w, h), (sx, h - cy)]
    
    # Apply X rotation
    if abs(rotation_x) > 0.5:
        cx = int(w * compress_x)
        if rotation_x > 0:
            dst[0] = (dst[0][0] + cx, dst[0][1])
            dst[1] = (dst[1][0] - cx, dst[1][1])
        else:
            dst[2] = (dst[2][0] - cx, dst[2][1])
            dst[3] = (dst[3][0] + cx, dst[3][1])
    
    coeffs = _perspective_coeffs(src, dst)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def _perspective_coeffs(src, dst):
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    res = np.linalg.lstsq(A, B, rcond=None)[0]
    return tuple(res.flatten())


def create_gradient_bg(width: int, height: int, 
                       color1: tuple = (100, 20, 20),  # Bright red
                       color2: tuple = (20, 5, 5)) -> Image.Image:  # Dark red
    """Create radial gradient background like reference."""
    y, x = np.mgrid[0:height, 0:width]
    
    # Radial gradient from center
    cx, cy = width // 2, height // 2
    max_dist = math.sqrt((width/2)**2 + (height/2)**2)
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    t = np.clip(dist / max_dist, 0, 1)
    t = t ** 0.5  # Softer falloff
    
    r = (color1[0] * (1 - t) + color2[0] * t).astype(np.uint8)
    g = (color1[1] * (1 - t) + color2[1] * t).astype(np.uint8)
    b = (color1[2] * (1 - t) + color2[2] * t).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')


def create_shadow(phone_size: tuple, position: tuple, output_size: tuple, 
                  rotation: float = 0, intensity: float = 0.5) -> Image.Image:
    """Create soft shadow under phone."""
    shadow = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    pw, ph = phone_size
    px, py = position
    
    # Elliptical shadow
    shadow_w = int(pw * 0.5)
    shadow_h = int(pw * 0.08)
    shadow_x = px + (pw - shadow_w) // 2 + int(rotation * 0.5)
    shadow_y = py + ph + 10
    
    # Clamp to screen
    shadow_y = min(shadow_y, output_size[1] - shadow_h - 5)
    
    max_alpha = int(50 * intensity)
    for i in range(25, 0, -1):
        alpha = int(max_alpha * (i / 25))
        expand = (25 - i) * 4
        draw.ellipse([
            shadow_x - expand,
            shadow_y - expand // 4,
            shadow_x + shadow_w + expand,
            shadow_y + shadow_h + expand // 4
        ], fill=(0, 0, 0, alpha))
    
    return shadow.filter(ImageFilter.GaussianBlur(12))


def ease_in_out_sine(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)


def render_full_phone_animation(
    video_frame: Image.Image,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color1: tuple = (100, 20, 20),
    bg_color2: tuple = (20, 5, 5),
    position: str = "center",
    phone_scale: float = 0.60  # Phone takes 60% of screen height - FULLY VISIBLE
) -> Image.Image:
    """
    Render FULL PHONE that is ALWAYS COMPLETELY VISIBLE.
    No cropping, no cutting - entire phone visible at all times.
    """
    out_w, out_h = output_size
    
    # Create phone mockup
    phone_w = 400
    phone_h = 820
    phone_frame, screen_mask, screen_bounds = create_iphone_frame(phone_w, phone_h)
    
    # Composite video on screen
    composited = composite_video_on_phone(phone_frame, screen_mask, screen_bounds, video_frame)
    
    # ANIMATION: Camera movement like reference
    # Phase 1 (0.0-0.4): Phone appears with rotation, gentle float
    # Phase 2 (0.4-0.7): Phone rotates other direction
    # Phase 3 (0.7-1.0): Phone returns to slight rotation
    
    if time_progress < 0.4:
        t = time_progress / 0.4
        rotation_y = 25 - 15 * ease_in_out_sine(t)  # 25 -> 10
        rotation_x = 3
    elif time_progress < 0.7:
        t = (time_progress - 0.4) / 0.3
        rotation_y = 10 - 35 * ease_in_out_sine(t)  # 10 -> -25
        rotation_x = 3 + 5 * t
    else:
        t = (time_progress - 0.7) / 0.3
        rotation_y = -25 + 35 * ease_in_out_sine(t)  # -25 -> 10
        rotation_x = 8 - 5 * t
    
    # Apply 3D transform
    transformed = apply_3d_transform(composited, rotation_y, rotation_x)
    
    # Scale phone to fit FULLY in screen with margins
    margin_y = int(out_h * 0.12)  # 12% margin top and bottom
    margin_x = int(out_w * 0.15)  # 15% margin sides
    
    available_h = out_h - 2 * margin_y
    target_h = int(available_h * phone_scale)
    scale_ratio = target_h / phone_h
    final_w = int(phone_w * scale_ratio)
    final_h = target_h
    
    # Ensure fits width
    if final_w > (out_w - 2 * margin_x):
        final_w = out_w - 2 * margin_x
        final_h = int(final_w * phone_h / phone_w)
    
    scaled = transformed.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    # Floating animation
    float_y = int(15 * math.sin(time_progress * math.pi * 2.5))
    float_x = int(10 * math.sin(time_progress * math.pi * 2))
    
    # Position
    if position == "center":
        pos_x = (out_w - final_w) // 2 + float_x
    elif position == "left":
        pos_x = margin_x + float_x
    else:  # right
        pos_x = out_w - final_w - margin_x + float_x
    
    pos_y = (out_h - final_h) // 2 + float_y
    
    # STRICTLY keep phone FULLY within bounds
    pos_x = max(margin_x, min(pos_x, out_w - final_w - margin_x))
    pos_y = max(margin_y, min(pos_y, out_h - final_h - margin_y))
    
    # Create background
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert("RGBA")
    
    # Add shadow
    shadow = create_shadow((final_w, final_h), (pos_x, pos_y), output_size, rotation_y, 0.6)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(scaled, (pos_x, pos_y), scaled)
    
    return bg.convert("RGB")


# Wrapper functions for compatibility
def render_dynamic_phone(video_frame, time_progress, output_size=(1080, 1920),
                         bg_color=(100, 20, 20), bg_color2=None, phone_scale=0.60,
                         animation_style="camera", position="center"):
    """Main render function - phone ALWAYS FULLY VISIBLE."""
    if bg_color2 is None:
        bg_color2 = tuple(max(0, c - 70) for c in bg_color)
    
    return render_full_phone_animation(
        video_frame=video_frame,
        time_progress=time_progress,
        output_size=output_size,
        bg_color1=bg_color,
        bg_color2=bg_color2,
        position=position,
        phone_scale=phone_scale
    )


def render_camera_animation(video_frame, time_progress, output_size=(1080, 1920),
                            bg_color1=(100, 20, 20), bg_color2=(20, 5, 5),
                            position="center", phone_scale_start=0.55, phone_scale_end=0.65):
    """Camera animation - same as render_full_phone_animation."""
    return render_full_phone_animation(
        video_frame=video_frame,
        time_progress=time_progress,
        output_size=output_size,
        bg_color1=bg_color1,
        bg_color2=bg_color2,
        position=position,
        phone_scale=0.60
    )


def render_simple_float(video_frame, time_progress, output_size=(1080, 1920),
                        bg_color1=(100, 20, 20), bg_color2=(20, 5, 5),
                        position="center", phone_scale=0.60):
    """Simple float animation."""
    return render_full_phone_animation(
        video_frame=video_frame,
        time_progress=time_progress,
        output_size=output_size,
        bg_color1=bg_color1,
        bg_color2=bg_color2,
        position=position,
        phone_scale=phone_scale
    )


def render_phone_with_text(video_frame, text_lines, time_progress, output_size=(1920, 1080),
                           bg_color1=(100, 20, 20), bg_color2=(20, 5, 5),
                           phone_position="right"):
    """Phone with text layout."""
    from PIL import ImageFont
    
    out_w, out_h = output_size
    
    phone_frame, screen_mask, screen_bounds = create_iphone_frame(400, 820)
    composited = composite_video_on_phone(phone_frame, screen_mask, screen_bounds, video_frame)
    
    rotation_y = 25 if phone_position == "right" else -25
    transformed = apply_3d_transform(composited, rotation_y, 3)
    
    # Scale phone
    margin = int(min(out_w, out_h) * 0.08)
    target_h = int((out_h - 2 * margin) * 0.6)
    scale_ratio = target_h / 820
    final_w = int(400 * scale_ratio)
    final_h = target_h
    
    scaled = transformed.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    float_y = int(12 * math.sin(time_progress * math.pi * 2))
    
    if phone_position == "right":
        phone_x = out_w - final_w - margin
        text_x = margin
        text_align = "left"
    else:
        phone_x = margin
        text_x = out_w - margin
        text_align = "right"
    
    phone_y = (out_h - final_h) // 2 + float_y
    phone_y = max(margin, min(phone_y, out_h - final_h - margin))
    
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert("RGBA")
    shadow = create_shadow((final_w, final_h), (phone_x, phone_y), output_size, rotation_y)
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


# Legacy compatibility
def get_base_iphone():
    phone, mask, _ = create_iphone_frame()
    return phone, mask

def create_simple_float_frame(video_frame, time_seconds, output_size=(1080, 1920),
                               bg_color=(100, 20, 20), use_gradient=True):
    progress = (time_seconds % 4.0) / 4.0
    return render_dynamic_phone(video_frame, progress, output_size, bg_color)

def create_animated_iphone_frame(video_frame, time_progress, total_duration=6.0,
                                  output_size=(1080, 1920), bg_color=(100, 20, 20)):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color)

def create_smooth_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                               bg_color=(100, 20, 20), position="center"):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, position=position)

def create_phone_with_text_frame(video_frame, text, time_progress, output_size=(1920, 1080),
                                  bg_color=(100, 20, 20), phone_position="right", font_size=64):
    lines = [text] if isinstance(text, str) else text
    bg_color2 = tuple(max(0, c - 70) for c in bg_color)
    return render_phone_with_text(video_frame, lines, time_progress, output_size, bg_color, bg_color2, phone_position)

def load_iphone_render(angle=12):
    phone, mask, bounds = create_iphone_frame()
    return phone, mask, angle

def composite_video_on_screen(phone, mask, video):
    _, _, bounds = create_iphone_frame()
    return composite_video_on_phone(phone, mask, bounds, video)

def blend_iphone_renders(angle):
    return get_base_iphone()

def composite_video_clean(iphone, video):
    phone, mask, bounds = create_iphone_frame()
    return composite_video_on_phone(phone, mask, bounds, video)

def select_iphone_render(rotation):
    return "/app/backend/iphone_renders/iphone_rot_12.png", 12
