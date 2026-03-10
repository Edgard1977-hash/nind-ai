"""
APPLE-STYLE VIDEO EFFECTS SYSTEM v3
Последовательные сцены, UI элементы, минимализм
"""

import math
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import logging
import asyncio

logger = logging.getLogger(__name__)

# Video dimensions (9:16 vertical)
WIDTH = 1080
HEIGHT = 1920


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get system font"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


# =============================================================
# EASING FUNCTIONS
# =============================================================

def ease_out_cubic(t: float) -> float:
    return 1 - pow(1 - t, 3)

def ease_out_quart(t: float) -> float:
    return 1 - pow(1 - t, 4)

def ease_in_out_cubic(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2

def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)


# =============================================================
# BACKGROUND RENDERERS
# =============================================================

def create_solid_black(width: int, height: int) -> Image.Image:
    """Apple-style solid black background"""
    return Image.new("RGB", (width, height), (0, 0, 0))


def create_gradient_bg(
    width: int, 
    height: int, 
    colors: List[Tuple[int, int, int]],
    time: float = 0
) -> Image.Image:
    """Animated gradient background"""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(0, 0, 0), (30, 30, 50)]
    
    # Animated wave effect
    for y in range(height):
        ny = y / height
        wave = math.sin(ny * 3 + time * math.pi * 2) * 0.1
        t = max(0, min(1, ny + wave))
        
        num_colors = len(colors)
        segment = t * (num_colors - 1)
        idx = min(int(segment), num_colors - 2)
        local_t = segment - idx
        
        c1 = colors[idx]
        c2 = colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        draw.line((0, y, width, y), fill=(r, g, b))
    
    return img


# =============================================================
# TEXT RENDERERS - Apple Style
# =============================================================

def draw_text_centered(
    img: Image.Image,
    text: str,
    y_position: int,
    font_size: int = 90,
    color: Tuple[int, int, int] = (255, 255, 255),
    alpha: int = 255
) -> Image.Image:
    """Draw centered text"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    
    x = (img.size[0] - text_w) // 2
    
    # Shadow for depth
    draw.text((x + 3, y_position + 3), text, font=font, fill=(0, 0, 0, alpha // 3))
    draw.text((x, y_position), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_gradient_text(
    img: Image.Image,
    text: str,
    y_position: int,
    font_size: int = 90,
    gradient_colors: List[Tuple[int, int, int]] = None,
    alpha: int = 255,
    shimmer_offset: float = 0
) -> Image.Image:
    """Text with gradient fill"""
    if not gradient_colors:
        gradient_colors = [(0, 150, 255), (100, 200, 255)]
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    font = get_font(font_size, bold=True)
    
    # Measure text
    temp_draw = ImageDraw.Draw(layer)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = (img.size[0] - text_w) // 2
    
    # Create gradient strip
    gradient_img = Image.new("RGBA", (text_w + 20, text_h + 20))
    
    for px in range(text_w + 20):
        t = ((px / (text_w + 20)) + shimmer_offset) % 1.0
        
        num_colors = len(gradient_colors)
        segment = t * (num_colors - 1)
        idx = min(int(segment), num_colors - 2)
        local_t = segment - idx
        
        c1 = gradient_colors[idx]
        c2 = gradient_colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        for py in range(text_h + 20):
            gradient_img.putpixel((px, py), (r, g, b, alpha))
    
    # Create text mask
    mask = Image.new("L", (text_w + 20, text_h + 20), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10, 10), text, font=font, fill=255)
    
    gradient_img.putalpha(mask)
    
    # Paste to layer
    layer.paste(gradient_img, (x - 10, y_position - 10), gradient_img)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_fade_in(
    img: Image.Image,
    text: str,
    y_position: int,
    font_size: int,
    color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Text fades in smoothly"""
    alpha = int(255 * ease_out_cubic(progress))
    return draw_text_centered(img, text, y_position, font_size, color, alpha)


def draw_text_scale_in(
    img: Image.Image,
    text: str,
    y_position: int,
    font_size: int,
    color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Text scales up with bounce"""
    scale = ease_out_back(min(1, progress * 1.2))
    alpha = int(255 * ease_out_cubic(progress))
    actual_size = max(10, int(font_size * scale))
    return draw_text_centered(img, text, y_position, actual_size, color, alpha)


# =============================================================
# UI ELEMENT RENDERERS
# =============================================================

def draw_input_field(
    img: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    placeholder: str = "",
    alpha: int = 255
) -> Image.Image:
    """Draw iOS-style input field"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Background
    bg_color = (45, 45, 50, alpha)
    radius = height // 2
    
    # Rounded rectangle
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=radius,
        fill=bg_color
    )
    
    # Placeholder text
    if placeholder:
        font = get_font(height // 2)
        draw.text(
            (x + 20, y + height // 4),
            placeholder,
            font=font,
            fill=(150, 150, 155, alpha)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_button(
    img: Image.Image,
    x: int,
    y: int,
    width: int,
    height: int,
    text: str,
    bg_color: Tuple[int, int, int] = (0, 122, 255),
    text_color: Tuple[int, int, int] = (255, 255, 255),
    alpha: int = 255
) -> Image.Image:
    """Draw iOS-style button"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    radius = height // 2
    
    # Button background
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=radius,
        fill=(*bg_color, alpha)
    )
    
    # Button text
    font = get_font(height // 2, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    text_x = x + (width - text_w) // 2
    text_y = y + (height - text_h) // 2 - 5
    
    draw.text((text_x, text_y), text, font=font, fill=(*text_color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_ui_form(
    img: Image.Image,
    y_start: int,
    fields: List[str],
    button_text: str,
    button_color: Tuple[int, int, int] = (0, 122, 255),
    progress: float = 1.0
) -> Image.Image:
    """Draw complete form with input fields and button"""
    result = img.copy()
    
    field_width = 700
    field_height = 70
    spacing = 25
    x = (WIDTH - field_width) // 2
    
    current_y = y_start
    
    # Animate fields appearing one by one
    for i, placeholder in enumerate(fields):
        field_start = i * 0.15  # Stagger start time
        field_progress = max(0, min(1, (progress - field_start) / 0.3))
        
        if field_progress > 0:
            alpha = int(255 * ease_out_cubic(field_progress))
            # Slide in from right
            offset_x = int((1 - ease_out_quart(field_progress)) * 100)
            
            result = draw_input_field(
                result, x + offset_x, current_y, field_width, field_height,
                placeholder, alpha
            )
        
        current_y += field_height + spacing
    
    # Button appears last
    button_start = len(fields) * 0.15 + 0.1
    button_progress = max(0, min(1, (progress - button_start) / 0.4))
    
    if button_progress > 0:
        alpha = int(255 * ease_out_cubic(button_progress))
        scale = ease_out_back(button_progress)
        
        btn_width = int(field_width * scale)
        btn_x = (WIDTH - btn_width) // 2
        
        result = draw_button(
            result, btn_x, current_y + 20, btn_width, 75,
            button_text, button_color, (255, 255, 255), alpha
        )
    
    return result


# =============================================================
# CHAT BUBBLE RENDERER (IMPROVED)
# =============================================================

def draw_chat_bubble(
    img: Image.Image,
    text: str,
    y_position: int,
    is_sender: bool,
    alpha: int = 255
) -> Tuple[Image.Image, int]:
    """Draw single chat bubble"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # iMessage colors
    if is_sender:
        bubble_color = (0, 122, 255)
        text_color = (255, 255, 255)
    else:
        bubble_color = (58, 58, 62)
        text_color = (255, 255, 255)
    
    # Font
    font_size = 48
    font = get_font(font_size)
    
    # Wrap text
    max_width = int(WIDTH * 0.65)
    padding_x = 30
    padding_y = 22
    
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    line_height = font_size + 10
    text_height = len(lines) * line_height
    text_width = max((draw.textbbox((0, 0), line, font=font)[2] for line in lines), default=100)
    
    bubble_w = text_width + padding_x * 2
    bubble_h = text_height + padding_y * 2
    
    margin = 50
    if is_sender:
        bubble_x = WIDTH - bubble_w - margin
    else:
        bubble_x = margin
    
    radius = 25
    
    # Shadow
    draw.rounded_rectangle(
        (bubble_x + 4, y_position + 4, bubble_x + bubble_w + 4, y_position + bubble_h + 4),
        radius=radius,
        fill=(0, 0, 0, alpha // 5)
    )
    
    # Bubble
    draw.rounded_rectangle(
        (bubble_x, y_position, bubble_x + bubble_w, y_position + bubble_h),
        radius=radius,
        fill=(*bubble_color, alpha)
    )
    
    # Tail
    tail_size = 12
    if is_sender:
        tail_points = [
            (bubble_x + bubble_w - 12, y_position + bubble_h - 10),
            (bubble_x + bubble_w + tail_size, y_position + bubble_h + 6),
            (bubble_x + bubble_w - 4, y_position + bubble_h)
        ]
    else:
        tail_points = [
            (bubble_x + 12, y_position + bubble_h - 10),
            (bubble_x - tail_size, y_position + bubble_h + 6),
            (bubble_x + 4, y_position + bubble_h)
        ]
    draw.polygon(tail_points, fill=(*bubble_color, alpha))
    
    # Text
    text_y = y_position + padding_y
    for line in lines:
        text_x = bubble_x + padding_x
        draw.text((text_x, text_y), line, font=font, fill=(*text_color, alpha))
        text_y += line_height
    
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result, bubble_h + 20


def draw_typing_indicator(
    img: Image.Image,
    y_position: int,
    frame: int,
    is_sender: bool = False
) -> Image.Image:
    """Draw animated typing indicator"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    bubble_color = (58, 58, 62)
    bubble_w = 90
    bubble_h = 50
    
    margin = 50
    if is_sender:
        bubble_x = WIDTH - bubble_w - margin
    else:
        bubble_x = margin
    
    # Bubble
    draw.rounded_rectangle(
        (bubble_x, y_position, bubble_x + bubble_w, y_position + bubble_h),
        radius=25,
        fill=(*bubble_color, 255)
    )
    
    # Dots
    dot_radius = 6
    dot_spacing = 20
    base_x = bubble_x + bubble_w // 2 - dot_spacing
    base_y = y_position + bubble_h // 2
    
    for i in range(3):
        phase = (frame * 0.15 + i * 0.5) % (math.pi * 2)
        bounce = math.sin(phase) * 5
        
        dot_x = base_x + i * dot_spacing
        dot_y = int(base_y + bounce)
        
        draw.ellipse(
            (dot_x - dot_radius, dot_y - dot_radius,
             dot_x + dot_radius, dot_y + dot_radius),
            fill=(130, 130, 135, 255)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# SCENE-BASED RENDERING
# =============================================================

async def render_apple_style_video(
    scenes: List[Dict],
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Render video with sequential scenes (Apple-style).
    
    Each scene:
    {
        "type": "text" | "gradient_text" | "ui_form" | "chat",
        "duration": 3.0,
        "transition_in": 0.5,
        "transition_out": 0.3,
        "content": {...}
    }
    """
    output_path = output_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Calculate total duration and scene timings
    scene_timings = []
    current_time = 0.0
    
    for scene in scenes:
        duration = scene.get("duration", 3.0)
        scene_timings.append({
            "start": current_time,
            "end": current_time + duration,
            "scene": scene
        })
        current_time += duration
    
    total_duration = current_time
    total_frames = int(fps * total_duration)
    
    logger.info(f"Rendering {total_frames} frames, {len(scenes)} scenes, duration: {total_duration}s")
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        
        # Black background (Apple style)
        bg = create_solid_black(WIDTH, HEIGHT)
        bg = bg.convert("RGBA")
        
        # Find active scene
        for timing in scene_timings:
            if timing["start"] <= time_sec < timing["end"]:
                scene = timing["scene"]
                scene_progress = (time_sec - timing["start"]) / (timing["end"] - timing["start"])
                
                # Transition in/out
                trans_in = scene.get("transition_in", 0.4)
                trans_out = scene.get("transition_out", 0.3)
                duration = timing["end"] - timing["start"]
                
                local_time = time_sec - timing["start"]
                
                # Calculate visibility
                if local_time < trans_in:
                    visibility = local_time / trans_in
                elif local_time > duration - trans_out:
                    visibility = (duration - local_time) / trans_out
                else:
                    visibility = 1.0
                
                visibility = ease_out_cubic(min(1, max(0, visibility)))
                
                scene_type = scene.get("type", "text")
                content = scene.get("content", {})
                
                # ===== TEXT SCENE =====
                if scene_type == "text":
                    text = content.get("text", "")
                    color = tuple(content.get("color", [255, 255, 255]))
                    font_size = content.get("font_size", 90)
                    y_pos = content.get("y_position", HEIGHT // 2 - 50)
                    effect = content.get("effect", "fade")
                    
                    if effect == "scale":
                        bg = draw_text_scale_in(bg, text, y_pos, font_size, color, visibility)
                    else:
                        bg = draw_text_fade_in(bg, text, y_pos, font_size, color, visibility)
                
                # ===== GRADIENT TEXT SCENE =====
                elif scene_type == "gradient_text":
                    text = content.get("text", "")
                    font_size = content.get("font_size", 90)
                    y_pos = content.get("y_position", HEIGHT // 2 - 50)
                    colors = [tuple(c) for c in content.get("gradient_colors", [[0, 150, 255], [100, 200, 255]])]
                    shimmer = content.get("shimmer", True)
                    
                    shimmer_offset = (time_sec * 0.5) if shimmer else 0
                    alpha = int(255 * visibility)
                    
                    bg = draw_gradient_text(bg, text, y_pos, font_size, colors, alpha, shimmer_offset)
                
                # ===== UI FORM SCENE =====
                elif scene_type == "ui_form":
                    fields = content.get("fields", ["Field 1", "Field 2"])
                    button_text = content.get("button_text", "Submit")
                    button_color = tuple(content.get("button_color", [0, 122, 255]))
                    y_start = content.get("y_start", 500)
                    
                    # Stagger element appearance
                    form_progress = visibility
                    bg = draw_ui_form(bg, y_start, fields, button_text, button_color, form_progress)
                
                # ===== CHAT SCENE =====
                elif scene_type == "chat":
                    messages = content.get("messages", [])
                    
                    # Center chat vertically
                    total_msgs = len(messages)
                    estimated_height = total_msgs * 100
                    start_y = max(200, (HEIGHT - estimated_height) // 2)
                    
                    current_y = start_y
                    
                    for i, msg in enumerate(messages):
                        # Stagger message appearance
                        msg_start = i * 0.2
                        msg_visibility = max(0, min(1, (visibility * len(messages) - i) / 1.0))
                        
                        if msg_visibility > 0:
                            alpha = int(255 * ease_out_cubic(msg_visibility))
                            
                            # Show typing indicator before message appears
                            if msg_visibility < 0.5 and not msg.get("sender", False):
                                bg = draw_typing_indicator(bg, current_y, frame_num, False)
                            else:
                                bg, height = draw_chat_bubble(
                                    bg,
                                    msg.get("text", ""),
                                    current_y,
                                    msg.get("sender", False),
                                    alpha
                                )
                                current_y += height
                
                break  # Only render one scene at a time
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
        
        if frame_num % 30 == 0:
            logger.info(f"Rendered frame {frame_num}/{total_frames}")
    
    # Encode video
    logger.info("Encoding video with ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-shortest",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        str(output_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        await asyncio.wait_for(process.communicate(), timeout=180)
    except asyncio.TimeoutError:
        process.kill()
        logger.error("Video encoding timed out")
    
    # Cleanup
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Video rendered: {output_path}")
        return str(output_path)
    
    return ""


# =============================================================
# UNIVERSAL RENDER FUNCTION (backward compatible)
# =============================================================

async def render_universal_video(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Universal render function - converts script_data to scenes.
    """
    elements = script_data.get("elements", [])
    scenes = []
    
    for elem in elements:
        elem_type = elem.get("type", "text")
        duration = elem.get("duration", 3.0)
        
        if elem_type == "text":
            scenes.append({
                "type": "text",
                "duration": duration,
                "transition_in": 0.4,
                "transition_out": 0.3,
                "content": {
                    "text": elem.get("content", ""),
                    "color": elem.get("color", [255, 255, 255]),
                    "font_size": elem.get("font_size", 90),
                    "y_position": HEIGHT // 2 - 50,
                    "effect": elem.get("effect", "scale")
                }
            })
        
        elif elem_type == "gradient_text":
            scenes.append({
                "type": "gradient_text",
                "duration": duration,
                "transition_in": 0.4,
                "transition_out": 0.3,
                "content": {
                    "text": elem.get("content", ""),
                    "font_size": elem.get("font_size", 90),
                    "y_position": HEIGHT // 2 - 50,
                    "gradient_colors": elem.get("gradient_colors", [[0, 150, 255], [100, 200, 255]]),
                    "shimmer": elem.get("shimmer", True)
                }
            })
        
        elif elem_type == "ui_form":
            scenes.append({
                "type": "ui_form",
                "duration": duration,
                "transition_in": 0.5,
                "transition_out": 0.3,
                "content": {
                    "fields": elem.get("fields", ["Field 1"]),
                    "button_text": elem.get("button_text", "Submit"),
                    "button_color": elem.get("button_color", [0, 122, 255]),
                    "y_start": 550
                }
            })
        
        elif elem_type == "chat":
            scenes.append({
                "type": "chat",
                "duration": duration,
                "transition_in": 0.3,
                "transition_out": 0.3,
                "content": {
                    "messages": elem.get("messages", [])
                }
            })
    
    if not scenes:
        # Default scene
        scenes = [{
            "type": "text",
            "duration": 3.0,
            "content": {"text": "Hello World", "color": [255, 255, 255]}
        }]
    
    return await render_apple_style_video(scenes, output_dir, fps)
