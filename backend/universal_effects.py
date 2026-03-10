"""
UNIVERSAL EFFECTS SYSTEM v2
Профессиональные анимации для AI видео-генерации
- Крупные сообщения с плавной трансформацией
- Apple-стиль анимации текста
- Переливающиеся градиенты
"""

import math
import random
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import logging
import asyncio

logger = logging.getLogger(__name__)

# Video dimensions (9:16 vertical) - Full HD
WIDTH = 1080
HEIGHT = 1920


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get system font with fallback"""
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
# EASING FUNCTIONS - Профессиональные кривые анимации
# =============================================================

def ease_out_cubic(t: float) -> float:
    """Плавное замедление"""
    return 1 - pow(1 - t, 3)

def ease_out_quart(t: float) -> float:
    """Более плавное замедление"""
    return 1 - pow(1 - t, 4)

def ease_out_back(t: float) -> float:
    """С небольшим перескоком назад"""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

def ease_in_out_cubic(t: float) -> float:
    """Плавное начало и конец"""
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def ease_out_elastic(t: float) -> float:
    """Упругий эффект"""
    if t == 0 or t == 1:
        return t
    return pow(2, -10 * t) * math.sin((t * 10 - 0.75) * (2 * math.pi) / 3) + 1

def spring_animation(t: float, damping: float = 0.5) -> float:
    """Пружинная анимация"""
    if t >= 1:
        return 1
    return 1 - math.exp(-6 * t) * math.cos(12 * t * (1 - damping))


# =============================================================
# GRADIENT BACKGROUNDS
# =============================================================

def create_aurora_gradient(
    width: int, 
    height: int, 
    colors: List[Tuple[int, int, int]],
    time: float
) -> Image.Image:
    """Переливающийся aurora градиент"""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(40, 20, 80), (80, 40, 140), (40, 80, 160)]
    
    num_bands = 80
    band_height = height // num_bands
    
    for band_idx in range(num_bands):
        y_start = band_idx * band_height
        y_end = (band_idx + 1) * band_height
        
        ny = band_idx / num_bands
        
        # Многослойные волны для плавности
        wave1 = math.sin(ny * 3 + time * math.pi * 2) * 0.15
        wave2 = math.cos(ny * 2.5 + time * math.pi * 1.7) * 0.12
        wave3 = math.sin(ny * 4 + time * math.pi * 2.3) * 0.08
        
        t = ny + wave1 + wave2 + wave3
        t = max(0, min(1, t))
        
        # Интерполяция между цветами
        num_colors = len(colors)
        segment = t * (num_colors - 1)
        idx = int(segment)
        local_t = segment - idx
        
        if idx >= num_colors - 1:
            idx = num_colors - 2
            local_t = 1.0
        
        c1 = colors[idx]
        c2 = colors[idx + 1]
        
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        draw.rectangle((0, y_start, width, y_end), fill=(r, g, b))
    
    # Мягкое размытие для плавности
    img = img.filter(ImageFilter.GaussianBlur(radius=20))
    
    return img


def create_solid_gradient(
    width: int, 
    height: int, 
    colors: List[Tuple[int, int, int]]
) -> Image.Image:
    """Простой вертикальный градиент"""
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(30, 30, 40), (50, 50, 70)]
    
    for y in range(height):
        t = y / height
        r = int(colors[0][0] * (1 - t) + colors[-1][0] * t)
        g = int(colors[0][1] * (1 - t) + colors[-1][1] * t)
        b = int(colors[0][2] * (1 - t) + colors[-1][2] * t)
        draw.line((0, y, width, y), fill=(r, g, b))
    
    return img


# =============================================================
# TEXT ANIMATIONS - Apple Style
# =============================================================

def draw_text_scale_up(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int,
    color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Текст увеличивается из центра с bounce"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Анимация масштаба с overshoot
    scale = ease_out_back(progress) if progress < 1 else 1.0
    alpha = int(255 * min(1, progress * 2))
    
    actual_size = max(10, int(font_size * scale))
    font = get_font(actual_size, bold=True)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = center[0] - text_w // 2
    y = center[1] - text_h // 2
    
    # Тень
    draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, alpha // 3))
    # Основной текст
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_wave_down(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int,
    color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Apple-стиль: буквы падают волной сверху"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    # Измеряем полную ширину
    total_bbox = draw.textbbox((0, 0), text, font=font)
    total_w = total_bbox[2] - total_bbox[0]
    
    start_x = center[0] - total_w // 2
    
    # Рисуем каждую букву с задержкой
    current_x = start_x
    for i, char in enumerate(text):
        if char == ' ':
            char_bbox = draw.textbbox((0, 0), ' ', font=font)
            current_x += char_bbox[2] - char_bbox[0]
            continue
        
        # Задержка для каждой буквы
        char_delay = i * 0.05
        char_progress = max(0, min(1, (progress - char_delay) / 0.3))
        
        if char_progress > 0:
            # Падение сверху
            offset_y = int((1 - ease_out_quart(char_progress)) * -100)
            alpha = int(255 * ease_out_cubic(char_progress))
            
            char_bbox = draw.textbbox((0, 0), char, font=font)
            char_h = char_bbox[3] - char_bbox[1]
            
            y = center[1] - char_h // 2 + offset_y
            
            draw.text((current_x, y), char, font=font, fill=(*color, alpha))
        
        char_bbox = draw.textbbox((0, 0), char, font=font)
        current_x += char_bbox[2] - char_bbox[0]
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_wave_up(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int,
    color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Apple-стиль: буквы поднимаются волной снизу"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    total_bbox = draw.textbbox((0, 0), text, font=font)
    total_w = total_bbox[2] - total_bbox[0]
    
    start_x = center[0] - total_w // 2
    current_x = start_x
    
    for i, char in enumerate(text):
        if char == ' ':
            char_bbox = draw.textbbox((0, 0), ' ', font=font)
            current_x += char_bbox[2] - char_bbox[0]
            continue
        
        char_delay = i * 0.04
        char_progress = max(0, min(1, (progress - char_delay) / 0.25))
        
        if char_progress > 0:
            # Подъём снизу
            offset_y = int((1 - ease_out_quart(char_progress)) * 80)
            alpha = int(255 * ease_out_cubic(char_progress))
            
            char_bbox = draw.textbbox((0, 0), char, font=font)
            char_h = char_bbox[3] - char_bbox[1]
            
            y = center[1] - char_h // 2 + offset_y
            
            draw.text((current_x, y), char, font=font, fill=(*color, alpha))
        
        char_bbox = draw.textbbox((0, 0), char, font=font)
        current_x += char_bbox[2] - char_bbox[0]
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_text_fade_blur(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int,
    color: Tuple[int, int, int],
    progress: float
) -> Image.Image:
    """Плавное появление из размытия"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    font = get_font(font_size, bold=True)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = center[0] - text_w // 2
    y = center[1] - text_h // 2
    
    alpha = int(255 * ease_out_cubic(progress))
    
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    # Размытие уменьшается по мере появления
    if progress < 0.7:
        blur_amount = int((1 - progress / 0.7) * 10)
        if blur_amount > 0:
            layer = layer.filter(ImageFilter.GaussianBlur(radius=blur_amount))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_gradient_text(
    img: Image.Image,
    text: str,
    center: Tuple[int, int],
    font_size: int,
    gradient_colors: List[Tuple[int, int, int]],
    progress: float,
    shimmer_offset: float = 0
) -> Image.Image:
    """Текст с градиентом и shimmer эффектом"""
    if not gradient_colors:
        gradient_colors = [(0, 150, 255), (150, 50, 255)]
    
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    font = get_font(font_size, bold=True)
    
    # Создаём временное изображение для текста
    temp = Image.new("RGBA", img.size, (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp)
    
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    x = center[0] - text_w // 2
    y = center[1] - text_h // 2
    
    # Рисуем градиент горизонтально
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
        
        for py in range(text_h + 10):
            temp.putpixel((x + px, y + py), (r, g, b, 255))
    
    # Создаём маску из текста
    mask = Image.new("L", img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((x, y), text, font=font, fill=255)
    
    # Применяем маску
    temp.putalpha(mask)
    
    # Анимация появления
    alpha_mult = ease_out_cubic(progress)
    if alpha_mult < 1:
        r, g, b, a = temp.split()
        a = a.point(lambda p: int(p * alpha_mult))
        temp = Image.merge("RGBA", (r, g, b, a))
    
    return Image.alpha_composite(img.convert("RGBA"), temp)


# =============================================================
# CHAT BUBBLES - Профессиональные сообщения
# =============================================================

def draw_rounded_rect(
    draw: ImageDraw.Draw,
    bounds: Tuple[int, int, int, int],
    radius: int,
    fill: Tuple[int, int, int, int]
):
    """Рисует прямоугольник со скруглёнными углами"""
    x1, y1, x2, y2 = bounds
    
    # Основной прямоугольник
    draw.rectangle((x1 + radius, y1, x2 - radius, y2), fill=fill)
    draw.rectangle((x1, y1 + radius, x2, y2 - radius), fill=fill)
    
    # Углы
    draw.ellipse((x1, y1, x1 + radius * 2, y1 + radius * 2), fill=fill)
    draw.ellipse((x2 - radius * 2, y1, x2, y1 + radius * 2), fill=fill)
    draw.ellipse((x1, y2 - radius * 2, x1 + radius * 2, y2), fill=fill)
    draw.ellipse((x2 - radius * 2, y2 - radius * 2, x2, y2), fill=fill)


def draw_chat_bubble_morphing(
    img: Image.Image,
    text: str,
    y_position: int,
    is_sender: bool,
    morph_progress: float,  # 0 = typing indicator, 1 = full message
    typing_phase: int = 0
) -> Tuple[Image.Image, int]:
    """
    Профессиональный чат-пузырь с морфингом из typing indicator.
    
    morph_progress:
    - 0.0-0.3: typing indicator (три точки)
    - 0.3-1.0: трансформация в сообщение
    """
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Цвета в стиле iOS
    if is_sender:
        bubble_color = (0, 122, 255)  # iMessage blue
        text_color = (255, 255, 255)
    else:
        bubble_color = (235, 235, 240)  # Light gray
        text_color = (0, 0, 0)
    
    # КРУПНЫЙ шрифт
    font_size = 52
    font = get_font(font_size)
    
    # Максимальная ширина пузыря - 70% экрана
    max_bubble_width = int(WIDTH * 0.7)
    padding_x = 36
    padding_y = 28
    
    # Измеряем и переносим текст
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        test_line = current_line + " " + word if current_line else word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_bubble_width - padding_x * 2:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    line_height = font_size + 12
    text_height = len(lines) * line_height
    text_width = max((draw.textbbox((0, 0), line, font=font)[2] for line in lines), default=100)
    
    final_bubble_w = text_width + padding_x * 2
    final_bubble_h = text_height + padding_y * 2
    
    # Размеры typing indicator
    typing_w = 90
    typing_h = 55
    
    # Морфинг размеров
    if morph_progress < 0.3:
        # Показываем typing indicator
        bubble_w = typing_w
        bubble_h = typing_h
        show_typing = True
        show_text = False
        alpha = 255
    else:
        # Трансформация в сообщение
        t = (morph_progress - 0.3) / 0.7
        eased_t = ease_out_quart(t)
        
        bubble_w = int(typing_w + (final_bubble_w - typing_w) * eased_t)
        bubble_h = int(typing_h + (final_bubble_h - typing_h) * eased_t)
        show_typing = t < 0.3
        show_text = t > 0.2
        alpha = 255
    
    # Позиционирование
    margin = 50
    if is_sender:
        bubble_x = WIDTH - bubble_w - margin
    else:
        bubble_x = margin
    
    bubble_y = y_position
    radius = min(28, bubble_h // 2)
    
    # Тень
    shadow_offset = 6
    draw_rounded_rect(
        draw,
        (bubble_x + shadow_offset, bubble_y + shadow_offset,
         bubble_x + bubble_w + shadow_offset, bubble_y + bubble_h + shadow_offset),
        radius,
        (0, 0, 0, 40)
    )
    
    # Основной пузырь
    draw_rounded_rect(
        draw,
        (bubble_x, bubble_y, bubble_x + bubble_w, bubble_y + bubble_h),
        radius,
        (*bubble_color, alpha)
    )
    
    # Хвостик пузыря (только когда полностью раскрыт)
    if morph_progress > 0.8:
        tail_alpha = int(255 * ((morph_progress - 0.8) / 0.2))
        tail_size = 14
        if is_sender:
            # Хвостик справа внизу
            tail_points = [
                (bubble_x + bubble_w - 15, bubble_y + bubble_h - 12),
                (bubble_x + bubble_w + tail_size, bubble_y + bubble_h + 8),
                (bubble_x + bubble_w - 5, bubble_y + bubble_h)
            ]
        else:
            # Хвостик слева внизу
            tail_points = [
                (bubble_x + 15, bubble_y + bubble_h - 12),
                (bubble_x - tail_size, bubble_y + bubble_h + 8),
                (bubble_x + 5, bubble_y + bubble_h)
            ]
        draw.polygon(tail_points, fill=(*bubble_color, tail_alpha))
    
    # Typing indicator (три точки)
    if show_typing:
        typing_alpha = int(255 * (1 - max(0, (morph_progress - 0.15) / 0.15)))
        dot_radius = 7
        dot_spacing = 22
        base_x = bubble_x + bubble_w // 2 - dot_spacing
        base_y = bubble_y + bubble_h // 2
        
        for i in range(3):
            # Анимация прыгающих точек
            phase = (typing_phase * 0.15 + i * 0.5) % (math.pi * 2)
            bounce = math.sin(phase) * 6
            
            dot_x = base_x + i * dot_spacing
            dot_y = int(base_y + bounce)
            
            dot_color = (150, 150, 155) if not is_sender else (200, 200, 210)
            draw.ellipse(
                (dot_x - dot_radius, dot_y - dot_radius,
                 dot_x + dot_radius, dot_y + dot_radius),
                fill=(*dot_color, typing_alpha)
            )
    
    # Текст сообщения
    if show_text:
        text_alpha = int(255 * min(1, (morph_progress - 0.5) / 0.3))
        text_y = bubble_y + padding_y
        for line in lines:
            text_x = bubble_x + padding_x
            draw.text((text_x, text_y), line, font=font, fill=(*text_color, text_alpha))
            text_y += line_height
    
    result = Image.alpha_composite(img.convert("RGBA"), layer)
    return result, final_bubble_h + 25


# =============================================================
# MAIN RENDER FUNCTION
# =============================================================

async def render_universal_video(
    script_data: Dict,
    output_dir: Path,
    fps: int = 30
) -> str:
    """
    Универсальный рендерер видео с профессиональными эффектами.
    
    script_data format:
    {
        "background": {"type": "aurora"|"solid", "colors": [[r,g,b], ...]},
        "elements": [
            {
                "type": "text"|"chat"|"gradient_text",
                "content": "...",
                "start_time": 0.0,
                "duration": 3.0,
                "effect": "scale_up"|"wave_down"|"wave_up"|"fade_blur",
                ...
            }
        ],
        "duration": 10.0
    }
    """
    output_path = output_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Parse script
    bg_config = script_data.get("background", {})
    bg_type = bg_config.get("type", "aurora")
    bg_colors = bg_config.get("colors", [[40, 30, 70], [70, 50, 120], [50, 80, 130]])
    bg_colors = [tuple(c) for c in bg_colors]
    
    elements = script_data.get("elements", [])
    total_duration = script_data.get("duration", 10.0)
    total_frames = int(fps * total_duration)
    
    logger.info(f"Rendering {total_frames} frames, duration: {total_duration}s")
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        progress = frame_num / total_frames
        
        # Background
        if bg_type == "aurora":
            bg = create_aurora_gradient(WIDTH, HEIGHT, bg_colors, progress)
        else:
            bg = create_solid_gradient(WIDTH, HEIGHT, bg_colors)
        
        bg = bg.convert("RGBA")
        
        # Render elements
        for elem in elements:
            elem_type = elem.get("type", "text")
            start_time = elem.get("start_time", 0)
            duration = elem.get("duration", 3.0)
            
            if time_sec < start_time:
                continue
            
            elem_progress = min(1.0, (time_sec - start_time) / duration)
            
            # Fade out в конце
            end_time = start_time + duration
            if time_sec > end_time - 0.5:
                fade_out = max(0, (end_time - time_sec) / 0.5)
                elem_progress = min(elem_progress, fade_out + 0.5)
            
            # ===== TEXT ELEMENT =====
            if elem_type == "text":
                content = elem.get("content", "")
                effect = elem.get("effect", "scale_up")
                font_size = elem.get("font_size", 80)
                color = tuple(elem.get("color", [255, 255, 255]))
                
                # Позиция
                pos = elem.get("position", "center")
                if pos == "center":
                    center = (WIDTH // 2, HEIGHT // 2)
                elif pos == "top":
                    center = (WIDTH // 2, 300)
                elif pos == "bottom":
                    center = (WIDTH // 2, HEIGHT - 400)
                else:
                    center = (WIDTH // 2, HEIGHT // 2)
                
                anim_progress = min(1.0, elem_progress * 2)  # Анимация за первую половину
                
                if effect == "wave_down":
                    bg = draw_text_wave_down(bg, content, center, font_size, color, anim_progress)
                elif effect == "wave_up":
                    bg = draw_text_wave_up(bg, content, center, font_size, color, anim_progress)
                elif effect == "fade_blur":
                    bg = draw_text_fade_blur(bg, content, center, font_size, color, anim_progress)
                else:  # scale_up
                    bg = draw_text_scale_up(bg, content, center, font_size, color, anim_progress)
            
            # ===== GRADIENT TEXT =====
            elif elem_type == "gradient_text":
                content = elem.get("content", "")
                font_size = elem.get("font_size", 80)
                gradient_colors = [tuple(c) for c in elem.get("gradient_colors", [[0, 150, 255], [150, 50, 255]])]
                shimmer = elem.get("shimmer", True)
                
                center = (WIDTH // 2, HEIGHT // 2)
                shimmer_offset = progress * 2 if shimmer else 0
                
                bg = draw_gradient_text(bg, content, center, font_size, gradient_colors, elem_progress, shimmer_offset)
            
            # ===== CHAT ELEMENT =====
            elif elem_type == "chat":
                messages = elem.get("messages", [])
                
                # Центрируем диалог вертикально
                total_msgs = len(messages)
                estimated_height = total_msgs * 120
                start_y = max(200, (HEIGHT - estimated_height) // 2)
                
                current_y = start_y
                
                for i, msg in enumerate(messages):
                    msg_text = msg.get("text", "")
                    is_sender = msg.get("sender", False)
                    
                    # Время появления каждого сообщения
                    msg_start = start_time + i * 1.5  # 1.5 сек на сообщение
                    msg_duration = 1.2  # Длительность анимации
                    
                    if time_sec < msg_start:
                        # Не показываем ещё
                        continue
                    
                    msg_elapsed = time_sec - msg_start
                    morph_progress = min(1.0, msg_elapsed / msg_duration)
                    
                    bg, bubble_height = draw_chat_bubble_morphing(
                        bg,
                        msg_text,
                        current_y,
                        is_sender,
                        morph_progress,
                        typing_phase=frame_num
                    )
                    
                    # Следующее сообщение ниже (только когда это появилось)
                    if morph_progress > 0.3:
                        current_y += bubble_height
        
        # Save frame
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
        
        if frame_num % 30 == 0:
            logger.info(f"Rendered frame {frame_num}/{total_frames}")
    
    # Encode video with AUDIO (silent) for browser compatibility
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
        size = output_path.stat().st_size
        logger.info(f"Video rendered: {output_path} ({size} bytes)")
        return str(output_path)
    else:
        logger.error("Video encoding failed")
        return ""
