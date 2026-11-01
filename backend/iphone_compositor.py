"""
iPhone Mockup v13 - Smooth 3D Animation
Uses single 3D render + perspective transform for fluid motion
"""

from iphone_compositor_3d import (
    render_3d_phone_frame,
    render_phone_frame,
    render_dynamic_phone,
    render_camera_animation,
    render_simple_float,
    render_full_phone_animation,
    load_render,
    interpolate_renders,
    find_screen_region,
    composite_screen_content,
    create_gradient_bg,
    create_shadow,
    ease_in_out,
    get_base_iphone,
    create_3d_iphone_mockup,
    load_base_render,
    get_phone_bounds,
    apply_perspective_transform,
)

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import math
import numpy as np

RENDER_DIR = "/app/backend/iphone_16_renders"
RENDER_ANGLES = [-40, -30, -20, -10, 0, 10, 20, 30, 40]


def render_phone_with_text(video_frame, text_lines, time_progress, output_size=(1920, 1080),
                           bg_color1=(90, 15, 15), bg_color2=(15, 5, 5),
                           phone_position="right"):
    out_w, out_h = output_size
    rotation_y = 25 if phone_position == "right" else -25
    
    base_phone = load_base_render()
    phone_bounds = get_phone_bounds(base_phone)
    phone_with_content = composite_screen_content(base_phone, video_frame, phone_bounds, rotation_y)
    transformed = apply_perspective_transform(phone_with_content, rotation_y)
    
    trans_arr = np.array(transformed)
    alpha = trans_arr[:,:,3]
    non_transparent = np.where(alpha > 10)
    
    if len(non_transparent[0]) > 0:
        y_min, y_max = non_transparent[0].min(), non_transparent[0].max()
        x_min, x_max = non_transparent[1].min(), non_transparent[1].max()
        phone_cropped = transformed.crop((x_min, y_min, x_max + 1, y_max + 1))
    else:
        phone_cropped = transformed
    
    margin = int(min(out_w, out_h) * 0.06)
    max_phone_w = int(out_w * 0.35)
    max_phone_h = int(out_h - 2 * margin)
    
    scale_w = max_phone_w / phone_cropped.width
    scale_h = max_phone_h / phone_cropped.height
    scale = min(scale_w, scale_h)
    
    final_w = int(phone_cropped.width * scale)
    final_h = int(phone_cropped.height * scale)
    
    phone_scaled = phone_cropped.resize((final_w, final_h), Image.Resampling.LANCZOS)
    
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
    bg.paste(phone_scaled, (phone_x, phone_y), phone_scaled)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                  int(min(out_w, out_h) * 0.04))
    except:
        font = ImageFont.load_default()
    
    text_layer = Image.new('RGBA', output_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)
    
    line_height = int(out_h * 0.06)
    start_y = (out_h - len(text_lines) * line_height) // 2
    
    for i, line in enumerate(text_lines):
        prog = max(0, min(1, (time_progress - i * 0.1) * 2.5))
        alpha_val = int(255 * (1 - (1 - prog) ** 3))
        slide = int(25 * (1 - prog))
        
        y = start_y + i * line_height
        if text_align == "left":
            x = text_x + slide
        else:
            bbox = draw.textbbox((0, 0), line, font=font)
            x = text_x - (bbox[2] - bbox[0]) - slide
        
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, alpha_val // 3))
        draw.text((x, y), line, font=font, fill=(255, 255, 255, alpha_val))
    
    bg = Image.alpha_composite(bg, text_layer)
    return bg.convert('RGB')


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
