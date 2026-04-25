"""Verify legacy scene types redirect to motion_*."""
import asyncio, sys, subprocess
from pathlib import Path
sys.path.insert(0, "/app/backend")

from universal_effects import render_universal_video


async def main():
    work_dir = Path("/tmp/motion_legacy")
    work_dir.mkdir(parents=True, exist_ok=True)

    # Use OLD scene types — should auto-redirect to motion_*
    script = {
        "scenes": [
            {"type": "apple_text", "text": "Old apple_text type",
             "bg": "white", "color": [0, 0, 0], "duration": 1.5},
            {"type": "calcom_text", "text": "Old calcom with emphasis word",
             "emphasis_word": "emphasis", "bg": "black", "color": [255, 255, 255],
             "duration": 1.5},
            {"type": "text", "text": "Plain text type",
             "bg": "white", "color": [0, 0, 0], "duration": 1.5},
        ],
        "user_prompt": "test"
    }

    out = await render_universal_video(script, work_dir)
    print("OUTPUT:", out)
    if out and Path(out).exists():
        print("OK file_size=", Path(out).stat().st_size)
        # extract a frame from the second scene at ~1.5s + 0.7s = 2.2s — should show gradient
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", "2.2", "-i", out,
            "-frames:v", "1", str(work_dir / "frame_calcom_redirected.png")
        ], check=True)
        print("Frame extracted: frame_calcom_redirected.png")


asyncio.run(main())
