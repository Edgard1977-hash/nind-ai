"""
iPhone 16 3D Compositor v2 - SMOOTH Animation
Uses single high-quality render + PIL perspective transform for smooth motion
NO frame jumping, stable screen content
"""

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
import math
import os

RENDER_DIR = "/app/backend/iphone_16_renders"

SCREEN_INSET_PERCENT = {
    'left': 0.047,
    'right': 0.047,
    'top': 0.042,
    'bottom': 0.015
}


def load_base_render():
    path = os.path.join(RENDER_DIR, "iphone16_angle_0.png")
    if os.path.exists(path):
        return Image.open(path).convert('RGBA')
    raise FileNotFoundError(f"Base render not found: {path}")


def get_phone_bounds(img):
    arr = np.array(img)
    alpha = arr[:,:,3]
    non_transparent = np.where(alpha > 10)
    
    if len(non_transparent[0]) > 0:
        y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
        x_min, x_max = non_transparent[1].min(), non_transparent[1].max()
        return (x_min, y_min, x_max, y_max)
    return (0, 0, img.width, img.height)


def get_screen_bounds(phone_bounds):
    px_min, py_min, px_max, py_max = phone_bounds
    pw = px_max - px_min
    ph = py_max - py_min
    
    sx_min = px_min + int(pw * SCREEN_INSET_PERCENT['left'])
    sx_max = px_max - int(pw * SCREEN_INSET_PERCENT['right'])
    sy_min = py_min + int(ph * SCREEN_INSET_PERCENT['top'])
    sy_max = py_max - int(ph * SCREEN_INSET_PERCENT['bottom'])
    
    return (sx_min, sy_min, sx_max, sy_max)


def _calc_perspective_coeffs(src, dst):
    matrix = []
    for s, d in zip(src, dst):
        matrix.append([s[0], s[1], 1, 0, 0, 0, -d[0]*s[0], -d[0]*s[1]])
        matrix.append([0, 0, 0, s[0], s[1], 1, -d[1]*s[0], -d[1]*s[1]])
    A = np.array(matrix, dtype=np.float64)
    B = np.array([p for pair in dst for p in pair], dtype=np.float64)
    return tuple(np.linalg.lstsq(A, B, rcond=None)[0])


def apply_perspective_transform(img, angle_y, angle_x=0):
    if abs(angle_y) < 0.5 and abs(angle_x) < 0.5:
        return img
    
    w, h = img.size
    padding = int(max(w, h) * 0.25)
    padded_w = w + 2 * padding
    padded_h = h + 2 * padding
    
    padded = Image.new('RGBA', (padded_w, padded_h), (0, 0, 0, 0))
    padded.paste(img, (padding, padding), img)
    
    pw, ph = padded_w, padded_h
    angle_rad = math.radians(angle_y)
    compress = abs(math.sin(angle_rad)) * 0.20
    shift = abs(math.sin(angle_rad)) * 0.08
    
    src = [(0, 0), (pw, 0), (pw, ph), (0, ph)]
    cy = int(ph * compress)
    sx = int(pw * shift)
    
    if angle_y >= 0:
        dst = [(0, 0), (pw - sx, cy), (pw - sx, ph - cy), (0, ph)]
    else:
        dst = [(sx, cy), (pw, 0), (pw, ph), (sx, ph - cy)]
    
    coeffs = _calc_perspective_coeffs(src, dst)
    result = padded.transform((pw, ph), Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
    return result


def composite_screen_content(phone_img, screen_content, phone_bounds, angle_y=0):
    result = phone_img.copy()
    screen_bounds = get_screen_bounds(phone_bounds)
    sx_min, sy_min, sx_max, sy_max = screen_bounds
    screen_w = sx_max - sx_min
    screen_h = sy_max - sy_min
    
    if screen_w <= 0 or screen_h <= 0:
        return result
    
    screen_resized = screen_content.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
    if screen_resized.mode != 'RGBA':
        screen_resized = screen_resized.convert('RGBA')
    
    phone_arr = np.array(phone_img)
    alpha = phone_arr[:,:,3]
    r, g, b = phone_arr[:,:,0], phone_arr[:,:,1], phone_arr[:,:,2]
    
    mask_arr = np.zeros((screen_h, screen_w), dtype=np.uint8)
    
    for y in range(screen_h):
        img_y = sy_min + y
        if img_y >= phone_img.height:
            continue
        for x in range(screen_w):
            img_x = sx_min + x
            if img_x >= phone_img.width:
                continue
            
            if alpha[img_y, img_x] > 10:
                pr, pg, pb = r[img_y, img_x], g[img_y, img_x], b[img_y, img_x]
                is_dynamic_island = pr < 12 and pg < 12 and pb < 15
                is_screen = (pr >= 8 and pr < 70 and pg >= 8 and pg < 70 and pb >= 8 and pb < 90)
                
                if is_screen and not is_dynamic_island:
                    mask_arr[y, x] = 255
    
    mask_img = Image.fromarray(mask_arr, mode='L')
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(1.5))
    result.paste(screen_resized, (sx_min, sy_min), mask_img)
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
    sy = pos_y + phone_h + 18
    sy = min(sy, output_size[1] - sh - 12)
    
    for i in range(25, 0, -1):
        a = int(22 * (i / 25))
        expand = (25 - i) * 4
        draw.ellipse([sx - expand, sy - expand//4, sx + sw + expand, sy + sh + expand//4], fill=(0, 0, 0, a))
    
    return shadow.filter(ImageFilter.GaussianBlur(12))


def ease_in_out(t):
    return -(math.cos(math.pi * t) - 1) / 2


def render_3d_phone_frame(video_frame, time_progress, output_size=(1080, 1920),
                          bg_color1=(90, 15, 15), bg_color2=(15, 5, 5), animation_style="camera"):
    out_w, out_h = output_size
    
    if animation_style == "camera":
        if time_progress < 0.35:
            t = time_progress / 0.35
            angle_y = 28 - 8 * ease_in_out(t)
        elif time_progress < 0.65:
            t = (time_progress - 0.35) / 0.30
            angle_y = 20 - 48 * ease_in_out(t)
        else:
            t = (time_progress - 0.65) / 0.35
            angle_y = -28 + 36 * ease_in_out(t)
    elif animation_style == "float":
        angle_y = 18 * math.sin(time_progress * math.pi * 2)
    else:
        angle_y = 12
    
    base_phone = load_base_render()
    phone_bounds = get_phone_bounds(base_phone)
    phone_with_content = composite_screen_content(base_phone, video_frame, phone_bounds, angle_y)
    transformed = apply_perspective_transform(phone_with_content, angle_y)
    
    trans_arr = np.array(transformed)
    alpha = trans_arr[:,:,3]
    non_transparent = np.where(alpha > 10)
    
    if len(non_transparent[0]) > 0:
        y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
        x_min, x_max = non_transparent[1].min(), non_transparent[1].max()
        pad = 3
        y_min = max(0, y_min - pad)
        y_max = min(transformed.height, y_max + pad)
        x_min = max(0, x_min - pad)
        x_max = min(transformed.width, x_max + pad)
        cropped = transformed.crop((x_min, y_min, x_max, y_max))
    else:
        cropped = transformed
    
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
    
    float_y = int(8 * math.sin(time_progress * math.pi * 2.5))
    float_x = int(5 * math.sin(time_progress * math.pi * 2))
    
    pos_x = (out_w - final_w) // 2 + float_x
    pos_y = (out_h - final_h) // 2 + float_y
    
    pos_x = max(margin, min(pos_x, out_w - final_w - margin))
    pos_y = max(margin, min(pos_y, out_h - final_h - margin))
    
    bg = create_gradient_bg(out_w, out_h, bg_color1, bg_color2).convert('RGBA')
    shadow = create_shadow(final_w, final_h, pos_x, pos_y, output_size, angle_y)
    bg = Image.alpha_composite(bg, shadow)
    bg.paste(phone_scaled, (pos_x, pos_y), phone_scaled)
    
    return bg.convert('RGB')


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
    img = load_base_render()
    mask = Image.new('L', img.size, 255)
    return img, mask


def create_3d_iphone_mockup(screen_content, rotation_y=25, frame_width=400, frame_height=820):
    base = load_base_render()
    bounds = get_phone_bounds(base)
    with_content = composite_screen_content(base, screen_content, bounds, rotation_y)
    return apply_perspective_transform(with_content, rotation_y)


def load_render(angle):
    return load_base_render()


def interpolate_renders(angle):
    return load_base_render()


def find_screen_region(phone_img):
    bounds = get_phone_bounds(phone_img)
    return get_screen_bounds(bounds)
