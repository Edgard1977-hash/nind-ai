"""
Motion text effects — 5 distinct kinetic typography styles.
Each effect is intentionally exaggerated so the difference is unmistakable.

1. blur_in           — heavy gaussian blur 38px → 0, stagger by char
2. char_fade_slide   — char slide-up 28px + fade + gradient (orange→purple) on emphasis word
3. apple_scale_slide — word scale 0.78 → 1.0 + slide-left 56px + fade  (Apple keynote)
4. word_slide_left   — word slide-from-left 110px + soft drop shadow
5. fade_scale_up_underline — char scale 0.6 → 1.0 + slide-up 38px + draw underline
"""

from typing import Tuple, Optional, List
from PIL import Image, ImageDraw, ImageFilter

from universal_effects import (
    WIDTH,
    HEIGHT,
    get_font,
    fit_text_to_width,
    ease_out_cubic,
    ease_out_quad,
    ease_out_back,
    MAX_TEXT_WIDTH,
)


# ---------- helpers ---------- #

def _measure(text: str, font) -> Tuple[int, int]:
    tmp = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(tmp)
    bbox = d.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _stagger_progress(progress: float, count: int, item_index: int, item_dur: float = 0.45) -> float:
    """Per-item progress where each item has duration `item_dur` (in [0..1]) and a stagger gap."""
    if count <= 1:
        return max(0.0, min(1.0, progress))
    gap = (1.0 - item_dur) / max(1, count - 1)
    start = item_index * gap
    end = start + item_dur
    if progress <= start:
        return 0.0
    if progress >= end:
        return 1.0
    return (progress - start) / (end - start)


def _gradient_color(t: float) -> Tuple[int, int, int]:
    """Orange → Purple gradient (Motion2 style)."""
    a = (255, 140, 0)
    b = (160, 50, 230)
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


# ---------- 1. BLUR-IN ---------- #

def draw_text_blur_in(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_size: int = 170,
    weight: str = "bold",
    by_char: bool = True,
    max_blur: float = 38.0,
) -> Image.Image:
    base = img.convert("RGBA")
    font, _ = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)

    if not by_char:
        text_w, text_h = _measure(text, font)
        x = (WIDTH - text_w) // 2
        y = (HEIGHT - text_h) // 2
        layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        eased = ease_out_cubic(min(1.0, progress * 1.4))
        alpha = int(255 * eased)
        d.text((x, y), text, font=font, fill=(*color, alpha))
        blur_radius = max_blur * (1.0 - eased)
        if blur_radius > 0.5:
            layer = layer.filter(ImageFilter.GaussianBlur(blur_radius))
        return Image.alpha_composite(base, layer)

    chars = list(text)
    widths = []
    total_w = 0
    for ch in chars:
        w = _measure(ch, font)[0] if ch.strip() else font.size // 3
        widths.append(w)
        total_w += w

    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    cur_x = start_x
    for i, ch in enumerate(chars):
        cw = widths[i]
        if ch.strip():
            cp = _stagger_progress(progress, len(chars), i, item_dur=0.55)
            eased = ease_out_cubic(cp)
            alpha = int(255 * eased)
            blur_radius = max_blur * (1.0 - eased)
            char_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(char_layer)
            d.text((cur_x, y), ch, font=font, fill=(*color, alpha))
            if blur_radius > 0.5:
                char_layer = char_layer.filter(ImageFilter.GaussianBlur(blur_radius))
            base = Image.alpha_composite(base, char_layer)
        cur_x += cw

    return base


# ---------- 2. CHAR FADE + SLIDE ---------- #

def draw_text_char_fade_slide(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    weight: str = "bold",
    emphasis_word: Optional[str] = None,
    use_gradient: bool = True,
) -> Image.Image:
    base = img.convert("RGBA")
    font, _ = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    text_h = _measure("Mg", font)[1]

    chars = list(text)
    widths = []
    total_w = 0
    for ch in chars:
        w = _measure(ch, font)[0] if ch.strip() else font.size // 3
        widths.append(w)
        total_w += w

    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    def char_in_emphasis(idx: int) -> bool:
        if not emphasis_word:
            return False
        word_start = 0
        for word in text.split(" "):
            wlen = len(word)
            if word_start <= idx < word_start + wlen:
                clean = "".join(c for c in word if c.isalnum())
                return clean.lower() == emphasis_word.lower()
            word_start += wlen + 1
        return False

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    cur_x = start_x
    for i, ch in enumerate(chars):
        cw = widths[i]
        if ch.strip():
            cp = _stagger_progress(progress, len(chars), i, item_dur=0.45)
            eased = ease_out_cubic(cp)
            alpha = int(255 * eased)
            slide = int(28 * (1 - eased))  # bigger slide for visibility
            if char_in_emphasis(i) and use_gradient:
                t = (cur_x - start_x) / max(1, total_w)
                col = _gradient_color(t)
            else:
                col = color
            d.text((cur_x, y - slide), ch, font=font, fill=(*col, alpha))
        cur_x += cw

    return Image.alpha_composite(base, layer)


# ---------- 3. APPLE SCALE + SLIDE-LEFT ---------- #

def draw_text_apple_scale_slide(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 160,
    weight: str = "bold",
) -> Image.Image:
    base = img.convert("RGBA")
    font, fitted_size = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    space_w = fitted_size // 3

    words = text.split()
    if not words:
        return base

    word_widths = [_measure(w, font)[0] for w in words]
    total_w = sum(word_widths) + space_w * (len(words) - 1)
    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    eps = 0.99
    cur_x = start_x
    for i, w in enumerate(words):
        ww = word_widths[i]
        wp = _stagger_progress(progress, len(words), i, item_dur=0.55)
        eased = ease_out_cubic(wp)
        alpha = int(255 * eased)
        slide = int(56 * (1 - eased))
        if eased >= eps:
            # Snap: pixel-perfect alignment on final frame
            d.text((cur_x, y), w, font=font, fill=(*color, alpha))
        else:
            scale = 0.78 + 0.22 * eased
            scaled_size = max(8, int(fitted_size * scale))
            scaled_font = get_font(scaled_size, weight)
            scaled_w, scaled_h = _measure(w, scaled_font)
            wx = cur_x - slide + (ww - scaled_w) // 2
            wy = y + (text_h - scaled_h) // 2
            d.text((wx, wy), w, font=scaled_font, fill=(*color, alpha))
        cur_x += ww + space_w

    return Image.alpha_composite(base, layer)


# ---------- 4. WORD SLIDE-LEFT WITH SHADOW ---------- #

def draw_text_word_slide_left(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    weight: str = "bold",
    shadow: bool = True,
) -> Image.Image:
    base = img.convert("RGBA")
    font, fitted_size = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    space_w = fitted_size // 3

    words = text.split()
    if not words:
        return base
    widths = [_measure(w, font)[0] for w in words]
    total_w = sum(widths) + space_w * (len(words) - 1)
    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    # Pronounced shadow: render in its own layer, blur, then composite
    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    text_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d_shadow = ImageDraw.Draw(shadow_layer)
    d_text = ImageDraw.Draw(text_layer)

    cur_x = start_x
    for i, w in enumerate(words):
        ww = widths[i]
        wp = _stagger_progress(progress, len(words), i, item_dur=0.5)
        eased = ease_out_cubic(wp)
        alpha = int(255 * eased)
        slide = int(110 * (1 - eased))           # very pronounced slide
        wx = cur_x - slide
        if shadow and alpha > 0:
            d_shadow.text((wx + 6, y + 9), w, font=font, fill=(0, 0, 0, int(alpha * 0.65)))
        d_text.text((wx, y), w, font=font, fill=(*color, alpha))
        cur_x += ww + space_w

    if shadow:
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(7))
        base = Image.alpha_composite(base, shadow_layer)
    return Image.alpha_composite(base, text_layer)


# ---------- 5. FADE + SCALE-UP + DRAW-UNDERLINE ---------- #
def draw_text_fade_scale_up_underline(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_size: int = 160,
    weight: str = "bold",
    emphasis_words: Optional[List[str]] = None,
) -> Image.Image:
    base = img.convert("RGBA")
    font, fitted_size = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    chars = list(text)
    widths = []
    total_w = 0
    for ch in chars:
        w = _measure(ch, font)[0] if ch.strip() else fitted_size // 3
        widths.append(w)
        total_w += w
    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    word_ranges = []
    cursor = 0
    for word in text.split(" "):
        clean = "".join(c for c in word if c.isalnum()).lower()
        word_ranges.append((clean, cursor, cursor + len(word)))
        cursor += len(word) + 1

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Snap to original font on final frames to avoid sub-pixel baseline drift
    eps = 0.99
    full_text_h = _measure("Mg", font)[1]
    cur_x = start_x
    char_x_start = []
    for i, ch in enumerate(chars):
        char_x_start.append(cur_x)
        cw = widths[i]
        if ch.strip():
            cp = _stagger_progress(progress, len(chars), i, item_dur=0.5)
            eased = ease_out_cubic(cp)
            alpha = int(255 * eased)
            slide = int(38 * (1 - eased))
            if eased >= eps:
                # Snap: use original font + zero slide so final frame is pixel-perfect aligned
                d.text((cur_x, y), ch, font=font, fill=(*color, alpha))
            else:
                scale = 0.6 + 0.4 * eased
                scaled_size = max(8, int(fitted_size * scale))
                scaled_font = get_font(scaled_size, weight)
                sw, _sh = _measure(ch, scaled_font)
                wx = cur_x + (cw - sw) // 2
                # All chars share the SAME y baseline (use full_text_h as height reference)
                wy = y + (full_text_h - _measure(ch, font)[1]) // 2 + slide
                d.text((wx, wy), ch, font=scaled_font, fill=(*color, alpha))
        cur_x += cw

    if emphasis_words:
        em_set = {w.lower() for w in emphasis_words}
        for clean, s, e in word_ranges:
            if clean in em_set and s < len(chars):
                start_progress = (s / max(1, len(chars))) * 0.6
                u_progress = max(0.0, min(1.0, (progress - start_progress) / 0.4))
                if u_progress <= 0:
                    continue
                u_eased = ease_out_quad(u_progress)
                xs = char_x_start[s]
                xe = char_x_start[e - 1] + widths[e - 1] if e - 1 < len(widths) else char_x_start[s]
                line_y = y + text_h + 14
                line_w = int((xe - xs) * u_eased)
                line_thickness = max(6, fitted_size // 22)  # thicker underline
                d.rectangle(
                    (xs, line_y, xs + line_w, line_y + line_thickness),
                    fill=(*color, 255),
                )

    return Image.alpha_composite(base, layer)


# ---------- 6. WORD SLIDE-FROM-RIGHT ---------- #

def draw_text_word_slide_right(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    weight: str = "bold",
) -> Image.Image:
    """Word-by-word slide-from-right with stagger + fade. TikTok-style."""
    base = img.convert("RGBA")
    font, fitted_size = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    space_w = fitted_size // 3

    words = text.split()
    if not words:
        return base
    widths = [_measure(w, font)[0] for w in words]
    total_w = sum(widths) + space_w * (len(words) - 1)
    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    cur_x = start_x
    for i, w in enumerate(words):
        ww = widths[i]
        wp = _stagger_progress(progress, len(words), i, item_dur=0.5)
        eased = ease_out_cubic(wp)
        alpha = int(255 * eased)
        slide = int(110 * (1 - eased))  # slide from RIGHT (+offset)
        wx = cur_x + slide
        d.text((wx, y), w, font=font, fill=(*color, alpha))
        cur_x += ww + space_w

    return Image.alpha_composite(base, layer)


# ---------- 7. WORD SLIDE-UP (from below) ---------- #

def draw_text_word_slide_up(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    weight: str = "bold",
) -> Image.Image:
    """Word-by-word slide-from-below + fade. Each word floats up with stagger."""
    base = img.convert("RGBA")
    font, fitted_size = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    space_w = fitted_size // 3

    words = text.split()
    if not words:
        return base
    widths = [_measure(w, font)[0] for w in words]
    total_w = sum(widths) + space_w * (len(words) - 1)
    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    cur_x = start_x
    for i, w in enumerate(words):
        ww = widths[i]
        wp = _stagger_progress(progress, len(words), i, item_dur=0.5)
        eased = ease_out_cubic(wp)
        alpha = int(255 * eased)
        rise = int(90 * (1 - eased))  # slide UP from below (positive y-offset)
        d.text((cur_x, y + rise), w, font=font, fill=(*color, alpha))
        cur_x += ww + space_w

    return Image.alpha_composite(base, layer)


# ---------- 8. WORD SLIDE-DOWN (from above) ---------- #

def draw_text_word_slide_down(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 140,
    weight: str = "bold",
) -> Image.Image:
    """Word-by-word fall-from-above + fade."""
    base = img.convert("RGBA")
    font, fitted_size = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    space_w = fitted_size // 3

    words = text.split()
    if not words:
        return base
    widths = [_measure(w, font)[0] for w in words]
    total_w = sum(widths) + space_w * (len(words) - 1)
    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    cur_x = start_x
    for i, w in enumerate(words):
        ww = widths[i]
        wp = _stagger_progress(progress, len(words), i, item_dur=0.5)
        eased = ease_out_cubic(wp)
        alpha = int(255 * eased)
        fall = int(90 * (1 - eased))  # fall from ABOVE (negative y-offset)
        d.text((cur_x, y - fall), w, font=font, fill=(*color, alpha))
        cur_x += ww + space_w

    return Image.alpha_composite(base, layer)


# ---------- 9. WHOLE-LINE SLIDE-UP-FADE ---------- #

def draw_text_line_slide_up(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 150,
    weight: str = "bold",
) -> Image.Image:
    """Whole-line slide-up-fade as a single block. CTA / payoff style."""
    base = img.convert("RGBA")
    font, _ = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)
    text_w, text_h = _measure(text, font)
    x = (WIDTH - text_w) // 2
    y = (HEIGHT - text_h) // 2

    eased = ease_out_cubic(min(1.0, progress * 1.4))
    alpha = int(255 * eased)
    rise = int(70 * (1 - eased))

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((x, y + rise), text, font=font, fill=(*color, alpha))
    return Image.alpha_composite(base, layer)
