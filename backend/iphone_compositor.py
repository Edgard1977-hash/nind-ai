"""
iPhone Mockup v11 - With 3D Side Edge
Creates realistic 3D iPhone with visible side edge/thickness
NO artifacts, FULL phone visibility
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math


def create_3d_iphone_mockup(
    screen_content: Image.Image,
    rotation_y: float = 25,
    frame_width: int = 400,
    frame_height: int = 820
) -> Image.Image:
    """
    Create a 3D iPhone mockup with visible side edge.
    rotation_y: horizontal rotation in degrees
    Returns: Phone image with alpha channel
    """
    # Colors
    bezel_front = (30, 30, 35)  # Front bezel
    bezel_side = (50, 50, 58)   # Side edge (lighter - metallic)
    bezel_dark = (20, 20, 25)   # Shadow side
    
    corner_radius = 55
    bezel_thickness = 14
    side_thickness = int(abs(rotation_y) * 0.4) + 8  # Visible side based on rotation
    
    # Calculate total size (phone + side edge)
    total_width = frame_width + side_thickness
    total_height = frame_height
    
    # Create canvas
    canvas = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    
    # Screen dimensions
    screen_x = bezel_thickness
    screen_y = bezel_thickness
    screen_w = frame_width - 2 * bezel_thickness
    screen_h = frame_height - 2 * bezel_thickness
    screen_corner = corner_radius - bezel_thickness
    
    if rotation_y >= 0:
        # Rotated right - side edge visible on LEFT
        side_x = 0
        phone_x = side_thickness
        side_color = bezel_side
        
        # Draw side edge (left)
        draw.rounded_rectangle(
            [side_x, 15, side_x + side_thickness + 10, total_height - 15],
            radius=10,
            fill=(*side_color, 255)
        )
        
        # Add gradient to side edge
        for i in range(side_thickness):
            alpha = int(255 * (1 - i / side_thickness * 0.3))
            brightness = int(50 + 30 * (i / side_thickness))
            draw.line(
                [(side_x + i, 20), (side_x + i, total_height - 20)],
                fill=(brightness, brightness, brightness + 8, alpha)
            )
        
        # Side buttons on left edge
        button_color = (65, 65, 75, 255)
        # Volume up
        draw.rounded_rectangle([side_x, 150, side_x + 4, 200], radius=2, fill=button_color)
        # Volume down
        draw.rounded_rectangle([side_x, 220, side_x + 4, 270], radius=2, fill=button_color)
        # Silent switch
        draw.rounded_rectangle([side_x, 110, side_x + 4, 135], radius=2, fill=button_color)
        
    else:
        # Rotated left - side edge visible on RIGHT
        phone_x = 0
        side_x = frame_width
        side_color = bezel_side
        
        # Draw side edge (right)
        draw.rounded_rectangle(
            [side_x - 10, 15, side_x + side_thickness, total_height - 15],
            radius=10,
            fill=(*side_color, 255)
        )
        
        # Add gradient to side edge
        for i in range(side_thickness):
            alpha = int(255 * (1 - i / side_thickness * 0.3))
            brightness = int(60 - 20 * (i / side_thickness))
            draw.line(
                [(side_x + i, 20), (side_x + i, total_height - 20)],
                fill=(brightness, brightness, brightness + 5, alpha)
            )
        
        # Power button on right edge
        button_color = (60, 60, 70, 255)
        draw.rounded_rectangle(
            [side_x + side_thickness - 4, 180, side_x + side_thickness, 250],
            radius=2, fill=button_color
        )
    
    # Draw front face of phone
    draw.rounded_rectangle(
        [phone_x, 0, phone_x + frame_width - 1, frame_height - 1],
        radius=corner_radius,
        fill=(*bezel_front, 255)
    )
    
    # Add subtle highlights to front bezel
    # Top highlight
    highlight = Image.new('RGBA', (total_width, total_height), (0, 0, 0, 0))
    h_draw = ImageDraw.Draw(highlight)
    h_draw.rounded_rectangle(
        [phone_x, 0, phone_x + frame_width - 1, 8],
        radius=corner_radius,
        fill=(70, 70, 80, 60)
    )
    # Left highlight
    h_draw.rounded_rectangle(
        [phone_x, 0, phone_x + 8, frame_height - 1],
        radius=corner_radius,
        fill=(70, 70, 80, 40)
    )
    canvas = Image.alpha_composite(canvas, highlight)
    draw = ImageDraw.Draw(canvas)
    
    # Resize and place screen content
    screen_resized = screen_content.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    if screen_resized.mode != 'RGBA':
        screen_resized = screen_resized.convert('RGBA')
    
    # Create rounded mask for screen
    screen_mask = Image.new('L', (screen_w, screen_h), 0)
    mask_draw = ImageDraw.Draw(screen_mask)
    mask_draw.rounded_rectangle(
        [0, 0, screen_w - 1, screen_h - 1],
        radius=screen_corner,
        fill=255
    )
    
    # Apply mask to screen content
    screen_masked = Image.new('RGBA', (screen_w, screen_h), (0, 0, 0, 0))
    screen_masked.paste(screen_resized, (0, 0), screen_mask)
    
    # Paste screen onto canvas
    canvas.paste(screen_masked, (phone_x + screen_x, screen_y), screen_masked)
    
    # Draw Dynamic Island
    island_w = 100
    island_h = 30
    island_x = phone_x + (frame_width - island_w) // 2
    island_y = screen_y + 12
    
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(
        [island_x, island_y, island_x + island_w, island_y + island_h],
        radius=15,
        fill=(8, 8, 12, 255)
    )
    
    return canvas


def apply_perspective(img: Image.Image, rotation_y: float, rotation_x: float = 0) -> Image.Image:
    """Apply perspective distortion for 3D effect."""
    if abs(rotation_y) < 1 and abs(rotation_x) < 1:
        return img
    
    w, h = img.size
    
    # Calculate distortion
    angle_y = math.radians(rotation_y)
    compress = abs(math.sin(angle_y)) * 0.25
    shift = abs(math.sin(angle_y)) * 0.05
    
    cy = int(h * compress)
    sx = int(w * shift)
    
    src = [(0, 0), (w, 0), (w, h), (0, h)]
    
    if rotation_y >= 0:
        dst = [(0, 0), (w - sx, cy), (w - sx, h - cy), (0, h)]
    else:
        dst = [(sx, cy), (w, 0), (w, h), (sx, h - cy)]
    
    # Apply X rotation
    if abs(rotation_x) > 1:
        cx = int(w * abs(math.sin(math.radians(rotation_x))) * 0.12)
        if rotation_x > 0:
            dst[0] = (dst[0][0] + cx, dst[0][1])
            dst[1] = (dst[1][0] - cx, dst[1][1])
        else:
            dst[2] = (dst[2][0] - cx, dst[2][1])
            dst[3] = (dst[3][0] + cx, dst[3][1])
    
    coeffs = _calc_coeffs(src, dst)
    return img.transform((w, h), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)


def _calc_coeffs(src, dst):
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    return tuple(np.linalg.lstsq(A, B, rcond=None)[0])


def create_gradient_bg(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    """Create radial gradient background."""
    y, x = np.mgrid[0:h, 0:w]
    cx, cy = w // 2, h // 2
    dist = np.sqrt((x - cx)**2 + (y - cy)**2)
    max_dist = math.sqrt((w/2)**2 + (h/2)**2)
    t = np.clip(dist / max_dist, 0, 1) ** 0.6
    
    r = (c1[0] * (1 - t) + c2[0] * t).astype(np.uint8)
    g = (c1[1] * (1 - t) + c2[1] * t).astype(np.uint8)
    b = (c1[2] * (1 - t) + c2[2] * t).astype(np.uint8)
    
    return Image.fromarray(np.stack([r, g, b], axis=-1), mode='RGB')


def create_shadow(pw: int, ph: int, px: int, py: int, out_size: tuple, rot: float) -> Image.Image:
    """Create shadow under phone."""
    shadow = Image.new('RGBA', out_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    
    sw = int(pw * 0.5)
    sh = int(pw * 0.08)
    sx = px + (pw - sw) // 2 + int(rot * 0.3)
    sy = py + ph + 15
    sy = min(sy, out_size[1] - sh - 10)
    
    for i in range(25, 0, -1):
        alpha = int(30 * (i / 25))
        expand = (25 - i) * 4
        draw.ellipse([sx - expand, sy - expand//4, sx + sw + expand, sy + sh + expand//4],
                     fill=(0, 0, 0, alpha))
    
    return shadow.filter(ImageFilter.GaussianBlur(12))


def ease(t: float) -> float:
    return -(math.cos(math.pi * t) - 1) / 2


def render_phone_frame(
    video_frame: Image.Image,
    time_progress: float,
    output_size: tuple = (1080, 1920),
    bg_color1: tuple = (90, 15, 15),
    bg_color2: tuple = (15, 5, 5),
    position: str = "center",
    animation_style: str = "camera"
) -> Image.Image:
    """
    Render 3D phone with video content.
    Phone is ALWAYS FULLY VISIBLE.
    """
    out_w, out_h = output_size
    
    # Animation
    if animation_style == "camera":
        if time_progress < 0.35:
            t = time_progress / 0.35
            rotation_y = 30 - 5 * ease(t)
            rotation_x = 4
        elif time_progress < 0.65:
            t = (time_progress - 0.35) / 0.30
            rotation_y = 25 - 55 * ease(t)
            rotation_x = 4 + 6 * t
        else:
            t = (time_progress - 0.65) / 0.35
            rotation_y = -30 + 40 * ease(t)
            rotation_x = 10 - 6 * t
    elif animation_style == "float":
        rotation_y = 20 * math.sin(time_progress * math.pi * 2)
        rotation_x = 5 * math.sin(time_progress * math.pi * 1.5)
    else:
        rotation_y = 25
        rotation_x = 4
    
    # Create phone mockup with side edge
    phone = create_3d_iphone_mockup(video_frame, rotation_y, 400, 820)
    
    # Apply perspective
    transformed = apply_perspective(phone, rotation_y, rotation_x)
    
    # Scale to fit with margins
    margin_y = int(out_h * 0.18)
    margin_x = int(out_w * 0.18)
    
    available_h = out_h - 2 * margin_y
    max_h = int(available_h * 0.58)
    
    scale = max_h / 820
    final_w = int(transformed.width * scale)
    final_h = int(820 * scale)
    
    # Check width fit
    if final_w > (out_w - 2 * margin_x):
        scale = (out_w - 2 * margin_x) / transformed.width
        final_w = int(transformed.width * scale)
        final_h = int(820 * scale)
    
    scaled = transformed.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    # Float animation
    float_y = int(12 * math.sin(time_progress * math.pi * 2.5))
    float_x = int(8 * math.sin(time_progress * math.pi * 2))
    
    # Position
    if position == "center":
        pos_x = (out_w - final_w) // 2 + float_x
    elif position == "left":
        pos_x = margin_x + float_x
    else:
        pos_x = out_w - final_w - margin_x + float_x
    
    pos_y = (out_h - final_h) // 2 + float_y
    
    # Bounds check
    pos_x = max(margin_x, min(pos_x, out_w - final_w - margin_x))
    pos_y = max(margin_y, min(pos_y, out_h - final_h - margin_y))
    
    # Background
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert('RGBA')
    
    # Shadow
    shadow = create_shadow(final_w, final_h, pos_x, pos_y, output_size, rotation_y)
    bg = Image.alpha_composite(bg, shadow)
    
    # Paste phone
    bg.paste(scaled, (pos_x, pos_y), scaled)
    
    return bg.convert('RGB')


# Compatibility wrappers
def render_dynamic_phone(video_frame, time_progress, output_size=(1080, 1920),
                         bg_color=(90, 15, 15), bg_color2=None, phone_scale=0.55,
                         animation_style="camera", position="center"):
    if bg_color2 is None:
        bg_color2 = tuple(max(0, c - 70) for c in bg_color)
    return render_phone_frame(video_frame, time_progress, output_size, bg_color, bg_color2, position, animation_style)


def render_camera_animation(video_frame, time_progress, output_size=(1080, 1920),
                            bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                            position="center", **kwargs):
    return render_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, position, "camera")


def render_simple_float(video_frame, time_progress, output_size=(1080, 1920),
                        bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                        position="center", **kwargs):
    return render_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, position, "float")


def render_full_phone_animation(video_frame, time_progress, output_size=(1080, 1920),
                                bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                                position="center", **kwargs):
    return render_phone_frame(video_frame, time_progress, output_size, bg_color1, bg_color2, position, "camera")


def render_phone_with_text(video_frame, text_lines, time_progress, output_size=(1920, 1080),
                           bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                           phone_position="right"):
    from PIL import ImageFont
    
    out_w, out_h = output_size
    rotation_y = 25 if phone_position == "right" else -25
    
    phone = create_3d_iphone_mockup(video_frame, rotation_y, 400, 820)
    transformed = apply_perspective(phone, rotation_y, 4)
    
    margin = int(min(out_w, out_h) * 0.08)
    max_h = int((out_h - 2 * margin) * 0.55)
    scale = max_h / 820
    final_w = int(transformed.width * scale)
    final_h = int(820 * scale)
    
    scaled = transformed.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
    float_y = int(10 * math.sin(time_progress * math.pi * 2))
    
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
    
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert('RGBA')
    shadow = create_shadow(final_w, final_h, phone_x, phone_y, output_size, rotation_y)
    bg = Image.alpha_composite(bg, shadow)
    bg.paste(scaled, (phone_x, phone_y), scaled)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                  int(min(out_w, out_h) * 0.045))
    except:
        font = ImageFont.load_default()
    
    text_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    line_height = int(out_h * 0.065)
    start_y = (out_h - len(text_lines) * line_height) // 2
    
    for i, line in enumerate(text_lines):
        prog = max(0, min(1, (time_progress - i * 0.1) * 2.5))
        alpha = int(255 * (1 - (1 - prog) ** 3))
        slide = int(25 * (1 - prog))
        
        y = start_y + i * line_height
        if text_align == "left":
            x = text_x + slide
        else:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = text_x - (bbox[2] - bbox[0]) - slide
        
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, alpha // 3))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, alpha))
    
    bg = Image.alpha_composite(bg, text_layer)
    return bg.convert('RGB')


# Legacy
def get_base_iphone():
    return Image.new('RGBA', (400, 820), (0,0,0,0)), Image.new('L', (400, 820), 255)

def create_simple_float_frame(video_frame, time_seconds, output_size=(1080, 1920),
                               bg_color=(90, 15, 15), use_gradient=True):
    return render_dynamic_phone(video_frame, (time_seconds % 4) / 4, output_size, bg_color, animation_style="float")

def create_animated_iphone_frame(video_frame, time_progress, total_duration=6.0,
                                  output_size=(1080, 1920), bg_color=(90, 15, 15)):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, animation_style="camera")

def create_smooth_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                               bg_color=(90, 15, 15), position="center"):
    return render_dynamic_phone(video_frame, time_progress, output_size, bg_color, position=position, animation_style="float")

def create_phone_with_text_frame(video_frame, text, time_progress, output_size=(1920, 1080),
                                  bg_color=(90, 15, 15), phone_position="right", font_size=64):
    lines = [text] if isinstance(text, str) else text
    return render_phone_with_text(video_frame, lines, time_progress, output_size, bg_color, 
                                  tuple(max(0, c-70) for c in bg_color), phone_position)

def load_iphone_render(angle=12):
    return get_base_iphone()[0], get_base_iphone()[1], angle

def composite_video_on_screen(phone, mask, video):
    return create_3d_iphone_mockup(video, 25)

def blend_iphone_renders(angle):
    return get_base_iphone()

def composite_video_clean(iphone, video):
    return create_3d_iphone_mockup(video, 25)

def select_iphone_render(rotation):
    return "", 12
