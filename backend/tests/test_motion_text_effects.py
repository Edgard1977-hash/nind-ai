"""Sanity test for motion text effects — render single frames at progress=0.7 to verify no crashes."""
import sys
sys.path.insert(0, "/app/backend")

from PIL import Image
from motion_text_effects import (
    draw_text_blur_in,
    draw_text_char_fade_slide,
    draw_text_apple_scale_slide,
    draw_text_word_slide_left,
    draw_text_fade_scale_up_underline,
)

WIDTH, HEIGHT = 1080, 1920


def bg(color):
    return Image.new("RGBA", (WIDTH, HEIGHT), (*color, 255))


def main():
    out_dir = "/tmp/motion_test"
    import os
    os.makedirs(out_dir, exist_ok=True)

    cases = [
        ("01_blur_in",
         draw_text_blur_in(bg((255, 255, 255)), "Quer esse texto?", 0.7, (0, 0, 0))),
        ("02_char_fade_emphasis",
         draw_text_char_fade_slide(bg((0, 0, 0)), "could mean 150 devices to manage.", 0.85,
                                   (255, 255, 255), font_size=110, emphasis_word="manage")),
        ("03_apple_scale",
         draw_text_apple_scale_slide(bg((255, 255, 255)), "Made Really Easy", 0.8, (0, 0, 0))),
        ("04_word_slide",
         draw_text_word_slide_left(bg((255, 255, 255)), "This one word slide in", 0.7, (0, 0, 0))),
        ("05_fade_underline",
         draw_text_fade_scale_up_underline(bg((255, 255, 255)), "Can animate like them.", 0.95,
                                           (0, 0, 0), emphasis_words=["animate", "them"])),
    ]

    for name, img in cases:
        path = f"{out_dir}/{name}.png"
        img.convert("RGB").save(path)
        print(f"OK {path}")

    print("All 5 motion effects rendered without errors.")


if __name__ == "__main__":
    main()
