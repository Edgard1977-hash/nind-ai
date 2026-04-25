"""
Motion text effects — 5 styles distilled from the user's reference videos:

1. blur_in           (Motion1) — character blur 20px → 0, staggered
2. char_fade_slide   (Motion2) — char-by-char fade + 14px slide-up, optional gradient on emphasis word
3. apple_scale_slide (Motion3) — word-by-word scale 0.9→1.0 + slide-left + fade
4. word_slide_left   (Motion4) — full phrase / per-word slide-in from left, soft shadow
5. fade_scale_up_underline (Motion5) — char-by-char fade + scale 0.9→1.0 + slide up + draw-underline on emphasis

All functions accept (img, text, progress, ...) and return composed PIL Image.
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
    """Orange → Purple gradient interpolation (Motion2 style)."""
    a = (255, 154, 0)   # warm orange
    b = (138, 43, 226)  # purple
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        int(a[2] + (b[2] - a[2]) * t),
    )


def _draw_char(draw, x, y, ch, font, color, alpha):
    draw.text((x, y), ch, font=font, fill=(*color, alpha))


# ---------- 1. BLUR-IN (Motion1) ---------- #

def draw_text_blur_in(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_size: int = 160,
    weight: str = "bold",
    by_char: bool = True,
    max_blur: float = 22.0,
) -> Image.Image:
    """Each character fades in from heavy gaussian blur to crisp."""
    base = img.convert("RGBA")
    font, _ = fit_text_to_width(text, MAX_TEXT_WIDTH, font_size, weight)

    if not by_char:
        # whole-phrase variant
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

    # Per-character blur with stagger
    chars = list(text)
    fonts_widths = []
    total_w = 0
    for ch in chars:
        w, h = _measure(ch if ch.strip() else "·", font)
        if not ch.strip():
            w = font.size // 3
        fonts_widths.append(w)
        total_w += w

    text_h = _measure("Mg", font)[1]
    start_x = (WIDTH - total_w) // 2
    y = (HEIGHT - text_h) // 2

    cur_x = start_x
    for i, ch in enumerate(chars):
        cw = fonts_widths[i]
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


# ---------- 2. CHAR FADE + SLIDE (Motion2) ---------- #

def draw_text_char_fade_slide(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 130,
    weight: str = "bold",
    emphasis_word: Optional[str] = None,
    use_gradient: bool = True,
) -> Image.Image:
    """Character-by-character left-to-right fade + 16px slide-up. emphasis_word gets gradient."""
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

    # Map characters to their word index for emphasis lookup
    def char_in_emphasis(idx: int) -> bool:
        if not emphasis_word:
            return False
        # build word boundaries
        word_start = 0
        for word in text.split(" "):
            wlen = len(word)
            if word_start <= idx < word_start + wlen:
                clean = "".join(c for c in word if c.isalnum())
                return clean.lower() == emphasis_word.lower()
            word_start += wlen + 1  # space
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
            slide = int(16 * (1 - eased))
            if char_in_emphasis(i) and use_gradient:
                # Position-based gradient across full text width
                t = (cur_x - start_x) / max(1, total_w)
                col = _gradient_color(t)
            else:
                col = color
            d.text((cur_x, y - slide), ch, font=font, fill=(*col, alpha))
        cur_x += cw

    return Image.alpha_composite(base, layer)


# ---------- 3. APPLE SCALE + SLIDE-LEFT (Motion3) ---------- #

def draw_text_apple_scale_slide(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 150,
    weight: str = "bold",
) -> Image.Image:
    """Word-by-word: scale 0.9 → 1.0, slide-from-left 22px → 0, fade. Apple-style."""
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

    cur_x = start_x
    for i, w in enumerate(words):
        ww = word_widths[i]
        wp = _stagger_progress(progress, len(words), i, item_dur=0.55)
        eased = ease_out_cubic(wp)
        alpha = int(255 * eased)
        slide = int(22 * (1 - eased))
        scale = 0.9 + 0.1 * eased

        scaled_size = int(fitted_size * scale)
        scaled_font = get_font(scaled_size, weight)
        scaled_w, scaled_h = _measure(w, scaled_font)
        # center on the slot
        wx = cur_x - slide + (ww - scaled_w) // 2
        wy = y + (text_h - scaled_h) // 2
        d.text((wx, wy), w, font=scaled_font, fill=(*color, alpha))
        cur_x += ww + space_w

    return Image.alpha_composite(base, layer)


# ---------- 4. WORD SLIDE-LEFT WITH SHADOW (Motion4) ---------- #

def draw_text_word_slide_left(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 130,
    weight: str = "bold",
    shadow: bool = True,
) -> Image.Image:
    """Word-by-word slide-in from left with smooth ease-out and subtle drop shadow."""
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
        slide = int(48 * (1 - eased))
        wx = cur_x - slide
        if shadow and alpha > 0:
            d.text((wx + 3, y + 4), w, font=font, fill=(0, 0, 0, int(alpha * 0.55)))
        d.text((wx, y), w, font=font, fill=(*color, alpha))
        cur_x += ww + space_w

    if shadow:
        # Soften shadow
        shadow_layer = layer.filter(ImageFilter.GaussianBlur(0.6))
        layer = shadow_layer
    return Image.alpha_composite(base, layer)


# ---------- 5. FADE + SCALE-UP + DRAW-UNDERLINE (Motion5) ---------- #

def draw_text_fade_scale_up_underline(
    img: Image.Image,
    text: str,
    progress: float,
    color: Tuple[int, int, int] = (0, 0, 0),
    font_size: int = 150,
    weight: str = "bold",
    emphasis_words: Optional[List[str]] = None,
) -> Image.Image:
    """Char-by-char: fade + scale 0.9→1.0 + slide-up 18px. Draws animated underline under emphasis_words."""
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

    # Per-word ranges for underline placement
    word_ranges = []  # list of (clean_word, start_idx, end_idx_exclusive)
    cursor = 0
    for word in text.split(" "):
        clean = "".join(c for c in word if c.isalnum()).lower()
        word_ranges.append((clean, cursor, cursor + len(word)))
        cursor += len(word) + 1

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    # Draw chars
    cur_x = start_x
    char_x_start = []  # store left x for each char
    for i, ch in enumerate(chars):
        char_x_start.append(cur_x)
        cw = widths[i]
        if ch.strip():
            cp = _stagger_progress(progress, len(chars), i, item_dur=0.5)
            eased = ease_out_cubic(cp)
            alpha = int(255 * eased)
            slide = int(18 * (1 - eased))
            scale = 0.9 + 0.1 * eased
            scaled_size = max(8, int(fitted_size * scale))
            scaled_font = get_font(scaled_size, weight)
            sw, sh = _measure(ch, scaled_font)
            wx = cur_x + (cw - sw) // 2
            wy = y + (text_h - sh) // 2 + slide
            d.text((wx, wy), ch, font=scaled_font, fill=(*color, alpha))
        cur_x += cw

    # Underlines for emphasis
    if emphasis_words:
        em_set = {w.lower() for w in emphasis_words}
        for clean, s, e in word_ranges:
            if clean in em_set and s < len(chars):
                # Underline appears after character animation has progressed
                start_progress = (s / max(1, len(chars))) * 0.7
                u_progress = max(0.0, min(1.0, (progress - start_progress) / 0.4))
                if u_progress <= 0:
                    continue
                u_eased = ease_out_quad(u_progress)
                xs = char_x_start[s]
                xe = char_x_start[e - 1] + widths[e - 1] if e - 1 < len(widths) else char_x_start[s]
                line_y = y + text_h + 12
                line_w = int((xe - xs) * u_eased)
                line_thickness = max(4, fitted_size // 28)
                d.rectangle(
                    (xs, line_y, xs + line_w, line_y + line_thickness),
                    fill=(*color, 255),
                )

    return Image.alpha_composite(base, layer)
