"""
PROFESSIONAL VIDEO EFFECTS v5
На основе анализа реальных промо-видео (Cal.com, Notion, Linear)

КЛЮЧЕВЫЕ ПРИНЦИПЫ:
1. ВСЁ КРУПНОЕ - элементы занимают 60-80% экрана
2. ОДИН ЭЛЕМЕНТ - ОДИН ЭКРАН
3. PARALLAX - элементы на разных слоях
4. 3D КАРТОЧКИ - перспектива, тени
"""

import math
import uuid
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess
import shutil
import logging
import asyncio

logger = logging.getLogger(__name__)

WIDTH = 1080
HEIGHT = 1920


def get_font(size: int, bold: bool = True, thin: bool = False) -> ImageFont.FreeTypeFont:
    """Get Inter font (Apple-style) with fallbacks"""
    if thin:
        paths = [
            "/usr/share/fonts/opentype/inter/Inter-Light.otf",
            "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    elif bold:
        paths = [
            "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
            "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
    else:
        paths = [
            "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            pass
    return ImageFont.load_default()


# =============================================================
# EASING
# =============================================================

def ease_out_cubic(t): return 1 - pow(1 - t, 3)
def ease_out_quart(t): return 1 - pow(1 - t, 4)
def ease_out_back(t):
    c = 1.70158
    return 1 + (c + 1) * pow(t - 1, 3) + c * pow(t - 1, 2)
def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


# =============================================================
# BACKGROUNDS
# =============================================================

def create_light_bg(w: int, h: int, time: float = 0) -> Image.Image:
    """Светлый градиент как в Cal.com"""
    img = Image.new("RGB", (w, h), (250, 248, 245))
    draw = ImageDraw.Draw(img)
    
    # Мягкий градиент сверху вниз
    for y in range(h):
        t = y / h
        wave = math.sin(t * math.pi + time * math.pi) * 0.02
        t = max(0, min(1, t + wave))
        
        r = int(255 - t * 15)
        g = int(252 - t * 20)
        b = int(248 - t * 25)
        
        draw.line((0, y, w, y), fill=(r, g, b))
    
    return img


def create_dark_bg(w: int, h: int) -> Image.Image:
    """Тёмный фон"""
    return Image.new("RGB", (w, h), (10, 10, 15))


def create_gradient_bg(w: int, h: int, colors: List[Tuple[int,int,int]], time: float = 0) -> Image.Image:
    """Градиентный фон с анимацией"""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    
    if len(colors) < 2:
        colors = [(100, 80, 200), (80, 120, 220)]
    
    for y in range(h):
        t = y / h
        wave = math.sin(t * 2 + time * math.pi * 2) * 0.05
        t = max(0, min(1, t + wave))
        
        idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
        local_t = (t * (len(colors) - 1)) - idx
        
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        draw.line((0, y, w, y), fill=(r, g, b))
    
    return img


# =============================================================
# TEXT - ОГРОМНЫЙ, ПО ЦЕНТРУ
# =============================================================

def draw_huge_text(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int,int,int] = (255, 255, 255),
    y_offset: int = 0
) -> Image.Image:
    """Большой текст по центру - Apple-стиль (Inter font, 60-70% ширины)"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Начальный размер - подбираем чтобы было 60-70% ширины
    font_size = 160
    font = get_font(font_size, bold=True)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    
    # Целевая ширина - 65% экрана
    target_width = int(WIDTH * 0.65)
    
    # Подгоняем размер
    while text_w > target_width and font_size > 80:
        font_size -= 10
        font = get_font(font_size, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
    
    # Если слишком маленький текст - увеличиваем
    while text_w < target_width * 0.7 and font_size < 180:
        font_size += 10
        font = get_font(font_size, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
    
    text_h = bbox[3] - bbox[1]
    
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 + y_offset
    
    # Анимация
    alpha = int(255 * ease_out_cubic(progress))
    scale = 0.92 + 0.08 * ease_out_back(min(1, progress * 1.5))
    
    actual_size = int(font_size * scale)
    font = get_font(actual_size, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 + y_offset
    
    # Тень
    draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, alpha // 4))
    
    # Текст
    draw.text((x, y), text, font=font, fill=(*color, alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


def draw_gradient_huge_text(
    img: Image.Image,
    text: str,
    progress: float,
    colors: List[Tuple[int,int,int]],
    shimmer_offset: float = 0,
    y_offset: int = 0
) -> Image.Image:
    """Большой текст с градиентом - Apple-стиль"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    
    font_size = 160
    font = get_font(font_size, bold=True)
    
    temp_draw = ImageDraw.Draw(layer)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    
    # Целевая ширина - 65% экрана
    target_width = int(WIDTH * 0.65)
    
    while text_w > target_width and font_size > 80:
        font_size -= 10
        font = get_font(font_size, bold=True)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
    
    while text_w < target_width * 0.7 and font_size < 180:
        font_size += 10
        font = get_font(font_size, bold=True)
        bbox = temp_draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
    
    text_h = bbox[3] - bbox[1]
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2 + y_offset
    
    # Создаём градиент
    grad = Image.new("RGBA", (text_w + 20, text_h + 20), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(grad)
    
    if len(colors) < 2:
        colors = [(100, 180, 255), (200, 100, 255)]
    
    for px in range(text_w + 20):
        t = ((px / (text_w + 20)) + shimmer_offset) % 1.0
        
        idx = min(int(t * (len(colors) - 1)), len(colors) - 2)
        local_t = (t * (len(colors) - 1)) - idx
        
        c1, c2 = colors[idx], colors[idx + 1]
        r = int(c1[0] * (1 - local_t) + c2[0] * local_t)
        g = int(c1[1] * (1 - local_t) + c2[1] * local_t)
        b = int(c1[2] * (1 - local_t) + c2[2] * local_t)
        
        grad_draw.line((px, 0, px, text_h + 20), fill=(r, g, b, 255))
    
    # Маска
    mask = Image.new("L", (text_w + 20, text_h + 20), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.text((10, 10), text, font=font, fill=255)
    
    grad.putalpha(mask)
    
    # Анимация
    alpha = ease_out_cubic(progress)
    if alpha < 1:
        r, g, b, a = grad.split()
        a = a.point(lambda p: int(p * alpha))
        grad = Image.merge("RGBA", (r, g, b, a))
    
    layer.paste(grad, (x - 10, y - 10), grad)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# CHAT BUBBLE - ОГРОМНЫЙ, ОДИН НА ЭКРАН (как в Cal.com)
# =============================================================

def draw_huge_chat_bubble(
    img: Image.Image,
    text: str,
    is_sender: bool,
    progress: float
) -> Image.Image:
    """ОГРОМНЫЙ чат-пузырь как в Cal.com примере"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Цвета
    if is_sender:
        bubble_color = (0, 132, 255)  # iMessage blue
        text_color = (255, 255, 255)
    else:
        bubble_color = (235, 235, 240)
        text_color = (0, 0, 0)
    
    # ОГРОМНЫЙ шрифт
    font_size = 72
    font = get_font(font_size, bold=True)
    
    # Измеряем текст
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # Padding
    pad_x = 60
    pad_y = 40
    
    bubble_w = text_w + pad_x * 2
    bubble_h = text_h + pad_y * 2
    
    # Центрируем
    bubble_x = (WIDTH - bubble_w) // 2
    bubble_y = (HEIGHT - bubble_h) // 2
    
    # Анимация
    alpha = int(255 * ease_out_cubic(progress))
    scale = 0.7 + 0.3 * ease_out_back(min(1, progress * 1.3))
    
    # Масштабируем
    actual_w = int(bubble_w * scale)
    actual_h = int(bubble_h * scale)
    actual_x = (WIDTH - actual_w) // 2
    actual_y = (HEIGHT - actual_h) // 2
    
    radius = min(45, actual_h // 2)
    
    # Тень
    shadow = 12
    draw.rounded_rectangle(
        (actual_x + shadow, actual_y + shadow, actual_x + actual_w + shadow, actual_y + actual_h + shadow),
        radius=radius, fill=(0, 0, 0, alpha // 5)
    )
    
    # Пузырь
    draw.rounded_rectangle(
        (actual_x, actual_y, actual_x + actual_w, actual_y + actual_h),
        radius=radius, fill=(*bubble_color, alpha)
    )
    
    # Хвостик
    if progress > 0.5:
        tail_alpha = int(alpha * min(1, (progress - 0.5) * 2))
        tail_size = 25
        if is_sender:
            tail = [
                (actual_x + actual_w - 30, actual_y + actual_h - 20),
                (actual_x + actual_w + tail_size, actual_y + actual_h + 15),
                (actual_x + actual_w - 10, actual_y + actual_h)
            ]
        else:
            tail = [
                (actual_x + 30, actual_y + actual_h - 20),
                (actual_x - tail_size, actual_y + actual_h + 15),
                (actual_x + 10, actual_y + actual_h)
            ]
        draw.polygon(tail, fill=(*bubble_color, tail_alpha))
    
    # Текст
    text_alpha = int(alpha * min(1, progress * 2))
    actual_font_size = int(font_size * scale)
    font = get_font(actual_font_size, bold=True)
    
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    tx = actual_x + (actual_w - tw) // 2
    ty = actual_y + (actual_h - th) // 2
    
    draw.text((tx, ty), text, font=font, fill=(*text_color, text_alpha))
    
    # "Delivered" под пузырём
    if is_sender and progress > 0.7:
        del_alpha = int(200 * (progress - 0.7) / 0.3)
        del_font = get_font(28, bold=False)
        draw.text((actual_x + actual_w - 150, actual_y + actual_h + 25), "Delivered", 
                  font=del_font, fill=(150, 150, 155, del_alpha))
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# UI FORM - КРУПНАЯ ФОРМА
# =============================================================

def draw_huge_form(
    img: Image.Image,
    fields: List[str],
    button_text: str,
    button_color: Tuple[int,int,int],
    progress: float
) -> Image.Image:
    """Крупная форма - по центру экрана"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    field_w = 800
    field_h = 85
    spacing = 25
    
    total_h = len(fields) * (field_h + spacing) + 100  # +100 для кнопки
    start_y = (HEIGHT - total_h) // 2
    x = (WIDTH - field_w) // 2
    
    current_y = start_y
    
    for i, placeholder in enumerate(fields):
        field_progress = max(0, min(1, (progress * (len(fields) + 1) - i) / 1.0))
        
        if field_progress > 0:
            alpha = int(255 * ease_out_cubic(field_progress))
            offset_x = int((1 - ease_out_quart(field_progress)) * 150)
            
            # Поле
            radius = field_h // 2
            draw.rounded_rectangle(
                (x + offset_x, current_y, x + field_w + offset_x, current_y + field_h),
                radius=radius, fill=(55, 55, 65, alpha)
            )
            
            # Placeholder
            font = get_font(36, bold=False)
            draw.text((x + offset_x + 35, current_y + 22), placeholder, 
                      font=font, fill=(160, 160, 170, alpha))
        
        current_y += field_h + spacing
    
    # Кнопка
    btn_progress = max(0, min(1, (progress * (len(fields) + 1) - len(fields)) / 1.0))
    
    if btn_progress > 0:
        btn_alpha = int(255 * ease_out_cubic(btn_progress))
        btn_scale = ease_out_back(btn_progress)
        
        btn_w = int(field_w * btn_scale)
        btn_h = int(90 * btn_scale)
        btn_x = (WIDTH - btn_w) // 2
        
        # Тень
        draw.rounded_rectangle(
            (btn_x + 5, current_y + 25, btn_x + btn_w + 5, current_y + btn_h + 25),
            radius=btn_h // 2, fill=(0, 0, 0, btn_alpha // 4)
        )
        
        # Кнопка
        draw.rounded_rectangle(
            (btn_x, current_y + 20, btn_x + btn_w, current_y + btn_h + 20),
            radius=btn_h // 2, fill=(*button_color, btn_alpha)
        )
        
        # Текст кнопки
        btn_font = get_font(int(40 * btn_scale), bold=True)
        bbox = draw.textbbox((0, 0), button_text, font=btn_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        
        draw.text(
            (btn_x + (btn_w - tw) // 2, current_y + 20 + (btn_h - th) // 2 - 3),
            button_text, font=btn_font, fill=(255, 255, 255, btn_alpha)
        )
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# 3D UI CARDS (как в примере 4 - карточки вокруг)
# =============================================================

def draw_floating_cards(
    img: Image.Image,
    progress: float,
    time: float
) -> Image.Image:
    """Плавающие 3D карточки вокруг центра"""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    
    # Карточки на разных позициях
    cards = [
        {"x": 50, "y": 200, "w": 280, "h": 160, "blur": 8, "alpha": 120},
        {"x": 750, "y": 150, "w": 300, "h": 180, "blur": 6, "alpha": 150},
        {"x": -30, "y": 1400, "w": 320, "h": 200, "blur": 10, "alpha": 100},
        {"x": 800, "y": 1500, "w": 260, "h": 150, "blur": 5, "alpha": 140},
        {"x": 100, "y": 900, "w": 200, "h": 120, "blur": 12, "alpha": 80},
        {"x": 850, "y": 850, "w": 220, "h": 140, "blur": 8, "alpha": 110},
    ]
    
    alpha_mult = ease_out_cubic(progress)
    
    for i, card in enumerate(cards):
        # Parallax движение
        offset_y = math.sin(time * math.pi * 2 + i) * 15
        offset_x = math.cos(time * math.pi * 1.5 + i * 0.5) * 10
        
        x = card["x"] + int(offset_x)
        y = card["y"] + int(offset_y)
        w = card["w"]
        h = card["h"]
        
        alpha = int(card["alpha"] * alpha_mult)
        
        # Рисуем карточку
        card_img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
        card_draw = ImageDraw.Draw(card_img)
        
        # Тень
        card_draw.rounded_rectangle((10, 10, w + 10, h + 10), radius=20, fill=(0, 0, 0, 40))
        
        # Карточка
        card_draw.rounded_rectangle((0, 0, w, h), radius=20, fill=(255, 255, 255, alpha))
        
        # Добавляем линии внутри (имитация контента)
        for j in range(3):
            line_y = 30 + j * 35
            line_w = w - 60 - j * 40
            card_draw.rounded_rectangle(
                (25, line_y, 25 + line_w, line_y + 15),
                radius=7, fill=(230, 230, 235, alpha)
            )
        
        # Размываем
        if card["blur"] > 0:
            card_img = card_img.filter(ImageFilter.GaussianBlur(radius=card["blur"]))
        
        layer.paste(card_img, (x, y), card_img)
    
    return Image.alpha_composite(img.convert("RGBA"), layer)


# =============================================================
# MAIN RENDER
# =============================================================

async def render_professional_video(
    scenes: List[Dict],
    output_dir: Path,
    fps: int = 30
) -> str:
    """Рендер видео с профессиональными эффектами"""
    output_path = output_dir / f"video_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    # Расчёт таймингов
    timings = []
    current = 0.0
    
    for scene in scenes:
        dur = scene.get("duration", 2.5)
        timings.append({"start": current, "end": current + dur, "scene": scene})
        current += dur
    
    total_dur = current
    total_frames = int(fps * total_dur)
    
    logger.info(f"Rendering {total_frames} frames, {len(scenes)} scenes, {total_dur}s")
    logger.info(f"Scenes: {scenes}")
    
    for frame_num in range(total_frames):
        time_sec = frame_num / fps
        global_progress = frame_num / total_frames
        
        # Находим активную сцену
        active = None
        scene_progress = 0
        local_time = 0
        
        for t in timings:
            if t["start"] <= time_sec < t["end"]:
                active = t["scene"]
                local_time = time_sec - t["start"]
                scene_progress = local_time / (t["end"] - t["start"])
                break
        
        if not active:
            continue
        
        # Фон
        bg_type = active.get("background", "light")
        if bg_type == "dark":
            bg = create_dark_bg(WIDTH, HEIGHT)
        elif bg_type == "gradient":
            colors = [tuple(c) for c in active.get("bg_colors", [[100, 80, 200], [80, 120, 220]])]
            bg = create_gradient_bg(WIDTH, HEIGHT, colors, global_progress)
        else:
            bg = create_light_bg(WIDTH, HEIGHT, global_progress)
        
        bg = bg.convert("RGBA")
        
        # Переходы
        trans_in = active.get("trans_in", 0.3)
        trans_out = active.get("trans_out", 0.2)
        dur = active.get("duration", 2.5)
        
        if local_time < trans_in:
            vis = local_time / trans_in
        elif local_time > dur - trans_out:
            vis = (dur - local_time) / trans_out
        else:
            vis = 1.0
        
        vis = ease_out_cubic(max(0, min(1, vis)))
        
        scene_type = active.get("type", "text")
        content = active.get("content", {})
        
        # === TEXT ===
        if scene_type == "text":
            text = content.get("text", "Hello")
            color = tuple(content.get("color", [255, 255, 255]))
            bg = draw_huge_text(bg, text, vis, color)
        
        # === GRADIENT TEXT ===
        elif scene_type == "gradient_text":
            text = content.get("text", "Hello")
            colors = [tuple(c) for c in content.get("colors", [[100, 180, 255], [200, 100, 255]])]
            shimmer = global_progress * 2 if content.get("shimmer", True) else 0
            bg = draw_gradient_huge_text(bg, text, vis, colors, shimmer)
        
        # === CHAT ===
        elif scene_type == "chat":
            text = content.get("text", "Hello")
            is_sender = content.get("sender", True)
            bg = draw_huge_chat_bubble(bg, text, is_sender, vis)
        
        # === UI FORM ===
        elif scene_type == "ui_form":
            fields = content.get("fields", ["Email"])
            btn_text = content.get("button", "Submit")
            btn_color = tuple(content.get("btn_color", [0, 122, 255]))
            bg = draw_huge_form(bg, fields, btn_text, btn_color, vis)
        
        # === FLOATING CARDS ===
        elif scene_type == "cards":
            bg = draw_floating_cards(bg, vis, global_progress)
            # Текст поверх
            if "text" in content:
                bg = draw_huge_text(bg, content["text"], vis, (255, 255, 255))
        
        # Сохраняем фрейм
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
        
        if frame_num % 30 == 0:
            logger.info(f"Frame {frame_num}/{total_frames}")
    
    # Кодируем
    logger.info("Encoding...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-shortest",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        await asyncio.wait_for(proc.communicate(), timeout=120)
    except:
        proc.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Done: {output_path}")
        return str(output_path)
    return ""


# Backward compatible
async def render_universal_video(script_data: Dict, output_dir: Path, fps: int = 30) -> str:
    elements = script_data.get("elements", [])
    scenes = []
    
    for elem in elements:
        t = elem.get("type", "text")
        dur = elem.get("duration", 2.5)
        
        scene = {
            "type": t,
            "duration": dur,
            "trans_in": 0.3,
            "trans_out": 0.2,
            "background": "dark" if t in ["text", "gradient_text"] else "light",
            "content": {}
        }
        
        if t == "text":
            scene["content"] = {
                "text": elem.get("content", ""),
                "color": elem.get("color", [255, 255, 255])
            }
        elif t == "gradient_text":
            scene["content"] = {
                "text": elem.get("content", ""),
                "colors": elem.get("gradient_colors", [[100, 180, 255], [200, 100, 255]]),
                "shimmer": elem.get("shimmer", True)
            }
        elif t == "chat":
            # Обрабатываем сообщения как отдельные сцены
            msgs = elem.get("messages", [])
            for msg in msgs:
                scenes.append({
                    "type": "chat",
                    "duration": 2.0,
                    "trans_in": 0.3,
                    "trans_out": 0.2,
                    "background": "light",
                    "content": {
                        "text": msg.get("text", ""),
                        "sender": msg.get("sender", True)
                    }
                })
            continue
        elif t == "ui_form":
            scene["content"] = {
                "fields": elem.get("fields", ["Field"]),
                "button": elem.get("button_text", "Submit"),
                "btn_color": elem.get("button_color", [0, 122, 255])
            }
            scene["background"] = "light"
        
        scenes.append(scene)
    
    if not scenes:
        scenes = [{"type": "text", "duration": 2.5, "background": "dark", "content": {"text": "Hello"}}]
    
    return await render_professional_video(scenes, output_dir, fps)



# =============================================================
# LOGO ANIMATION
# =============================================================

async def render_logo_animation(
    logo_path: str,
    text: str,
    bg_color: Tuple[int,int,int],
    output_dir: Path,
    fps: int = 30,
    duration: float = 4.0
) -> str:
    """
    Анимация логотипа - логотип появляется с эффектом + текст бренда
    """
    output_path = output_dir / f"logo_{uuid.uuid4().hex[:8]}.mp4"
    frames_dir = output_dir / f"frames_{uuid.uuid4().hex[:8]}"
    frames_dir.mkdir(exist_ok=True)
    
    total_frames = int(fps * duration)
    
    # Загружаем логотип
    try:
        logo = Image.open(logo_path).convert("RGBA")
        # Масштабируем до 400px по большей стороне
        max_size = 400
        ratio = min(max_size / logo.width, max_size / logo.height)
        new_size = (int(logo.width * ratio), int(logo.height * ratio))
        logo = logo.resize(new_size, Image.Resampling.LANCZOS)
    except Exception as e:
        logger.error(f"Failed to load logo: {e}")
        # Создаём placeholder
        logo = Image.new("RGBA", (400, 400), (*bg_color, 255))
    
    for frame_num in range(total_frames):
        progress = frame_num / total_frames
        
        # Фон с цветом
        bg = Image.new("RGB", (WIDTH, HEIGHT), bg_color)
        bg = bg.convert("RGBA")
        
        # Анимация логотипа
        logo_progress = min(1.0, progress * 2)  # Первая половина - появление логотипа
        
        # Scale + fade для логотипа
        logo_scale = 0.5 + 0.5 * ease_out_back(logo_progress)
        logo_alpha = int(255 * ease_out_cubic(logo_progress))
        
        scaled_w = int(logo.width * logo_scale)
        scaled_h = int(logo.height * logo_scale)
        
        if scaled_w > 0 and scaled_h > 0:
            scaled_logo = logo.resize((scaled_w, scaled_h), Image.Resampling.LANCZOS)
            
            # Применяем alpha
            r, g, b, a = scaled_logo.split()
            a = a.point(lambda p: int(p * logo_alpha / 255))
            scaled_logo = Image.merge("RGBA", (r, g, b, a))
            
            # Позиция - центр, но чуть выше
            logo_x = (WIDTH - scaled_w) // 2
            logo_y = (HEIGHT - scaled_h) // 2 - 150
            
            bg.paste(scaled_logo, (logo_x, logo_y), scaled_logo)
        
        # Текст бренда - появляется во второй половине
        if progress > 0.4 and text:
            text_progress = (progress - 0.4) / 0.4
            text_progress = min(1.0, text_progress)
            
            layer = Image.new("RGBA", bg.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(layer)
            
            font_size = 80
            font = get_font(font_size, bold=True)
            
            bbox = draw.textbbox((0, 0), text, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            
            text_x = (WIDTH - text_w) // 2
            text_y = (HEIGHT + logo.height) // 2 - 50
            
            # Slide up + fade
            offset_y = int((1 - ease_out_quart(text_progress)) * 50)
            alpha = int(255 * ease_out_cubic(text_progress))
            
            # Определяем цвет текста (контрастный к фону)
            brightness = (bg_color[0] * 299 + bg_color[1] * 587 + bg_color[2] * 114) / 1000
            text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)
            
            draw.text((text_x, text_y + offset_y), text, font=font, fill=(*text_color, alpha))
            
            bg = Image.alpha_composite(bg, layer)
        
        # Сохраняем фрейм
        frame_path = frames_dir / f"frame_{frame_num:05d}.png"
        bg.convert("RGB").save(frame_path, "PNG", optimize=True)
    
    # Кодируем
    logger.info("Encoding logo animation...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(fps),
        "-i", str(frames_dir / "frame_%05d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-shortest",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        str(output_path)
    ]
    
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        await asyncio.wait_for(proc.communicate(), timeout=60)
    except:
        proc.kill()
    
    shutil.rmtree(frames_dir, ignore_errors=True)
    
    if output_path.exists():
        logger.info(f"Logo animation done: {output_path}")
        return str(output_path)
    return ""
