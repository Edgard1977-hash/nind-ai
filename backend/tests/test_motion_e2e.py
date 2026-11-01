"""End-to-end render test: feed a hand-crafted script with all 5 motion types
through render_universal_video and inspect the produced video frames.
"""
import asyncio
import sys
import os
sys.path.insert(0, "/app/backend")

from universal_effects import render_universal_video


async def main():
    from pathlib import Path
    work_dir = Path("/tmp/motion_e2e")
    work_dir.mkdir(parents=True, exist_ok=True)

    script = {
        "scenes": [
            {"type": "motion_blur_in", "text": "Test One",
             "bg": "white", "color": [0, 0, 0], "by_char": True, "duration": 1.5},
            {"type": "motion_char_fade", "text": "Two with emphasis",
             "emphasis_word": "emphasis",
             "bg": "black", "color": [255, 255, 255],
             "use_gradient": True, "duration": 1.5},
            {"type": "motion_apple_scale", "text": "Three Apple Style",
             "bg": "white", "color": [0, 0, 0], "duration": 1.5},
            {"type": "motion_word_slide", "text": "Four words slide in",
             "bg": "white", "color": [0, 0, 0], "shadow": True, "duration": 1.5},
            {"type": "motion_fade_underline", "text": "Five with underline now",
             "emphasis_words": ["underline", "now"],
             "bg": "white", "color": [0, 0, 0], "duration": 1.5},
        ],
        "user_prompt": "test"
    }

    out = await render_universal_video(script, work_dir)
    print("OUTPUT:", out)
    if out and os.path.exists(out):
        size = os.path.getsize(out)
        print(f"OK file_size={size}")
        # extract frames at 0.7s into each scene
        import subprocess
        for i in range(5):
            t = 1.5 * i + 0.9
            frame_path = f"{work_dir}/frame_motion_{i+1}.png"
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error",
                "-ss", str(t), "-i", out,
                "-frames:v", "1", frame_path
            ], check=True)
            print(f"  extracted: {frame_path}")
    else:
        print("FAILED")


if __name__ == "__main__":
    asyncio.run(main())
