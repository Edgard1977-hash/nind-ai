"""Basic-mode voice routing, caption timing, and ffmpeg montage."""

import asyncio
import os
import subprocess
import wave
from pathlib import Path

import pytest
from PIL import Image

from ai.factory import clear_provider_overrides, get_tts_provider
from ai.tts import AudioStreamAssembler
from ai.voices import resolve_voice
from captions import allocate_durations, cues_for_narration, normalize_plan, wav_info, words_evenly
from video_service import compose_basic_master, create_image_video


def _mean_abs_diff(left: Image.Image, right: Image.Image) -> float:
    left_bytes = left.convert("RGB").tobytes()
    right_bytes = right.convert("RGB").tobytes()
    count = min(len(left_bytes), len(right_bytes))
    if count == 0:
        return 0.0
    return sum(abs(left_bytes[index] - right_bytes[index]) for index in range(count)) / count


def _wav(duration: float, rate: int = 24000) -> bytes:
    frames = int(duration * rate)
    buffer = bytearray(frames * 2)
    path = Path(os.environ.get("TMPDIR", "/tmp")) / "nind-voice-test.wav"
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(buffer)
    return path.read_bytes()


def test_openrouter_key_alone_selects_gpt_audio_mini(monkeypatch):
    monkeypatch.delenv("TTS_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("TTS_PROVIDER", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("TTS_MODEL", "tts-1")
    monkeypatch.setenv("TTS_BASE_URL", "https://api.openai.com/v1")
    clear_provider_overrides()
    provider = get_tts_provider()
    assert provider.name == "openrouter-chat-audio"
    assert provider.model == "openai/gpt-audio-mini"
    assert "openrouter.ai" in provider.base_url


def test_speech_provider_stays_available_when_asked(monkeypatch):
    monkeypatch.setenv("TTS_PROVIDER", "speech")
    monkeypatch.setenv("TTS_API_KEY", "sk-test")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")
    monkeypatch.setenv("TTS_MODEL", "tts-1")
    clear_provider_overrides()
    provider = get_tts_provider()
    assert provider.name == "openai-tts"
    assert provider.model == "tts-1"


def test_unknown_voice_falls_back_to_marin(monkeypatch):
    monkeypatch.delenv("TTS_VOICE", raising=False)
    assert resolve_voice("echo") == "echo"
    assert resolve_voice("not-a-voice") == "marin"
    assert resolve_voice(None) == "marin"


def test_scene_durations_follow_speech_and_sum_to_it():
    durations = allocate_durations([2, 4, 2, 8], total=20, minimum=1.5)
    assert len(durations) == 4
    assert durations == pytest.approx([20 * 2 / 16, 20 * 4 / 16, 20 * 2 / 16, 20 * 8 / 16])
    assert sum(durations) == pytest.approx(20)


def test_short_total_is_split_evenly_when_minimum_cannot_fit():
    durations = allocate_durations([1, 1, 1], total=3, minimum=1.5)
    assert durations == pytest.approx([1, 1, 1])


def test_phrase_cues_track_words_instead_of_one_line():
    words = words_evenly("alpha bravo charlie delta echo foxtrot", 6)
    cues = cues_for_narration(
        audio=b"",
        snapshots=[],
        transcript="alpha bravo charlie delta echo foxtrot",
        script="",
        duration=6,
    )
    assert len(cues) >= 2
    assert cues[0]["timestamp_start"] == 0
    assert cues[-1]["timestamp_end"] == pytest.approx(6)
    assert all(len(cue["text"].split()) <= 3 for cue in cues)
    assert " ".join(cue["text"] for cue in cues) == "alpha bravo charlie delta echo foxtrot"
    del words


def test_aligned_audio_snapshots_move_captions_with_the_transcript():
    audio = _wav(4.0)
    info = wav_info(audio)
    assert info is not None
    words = "one two three four five six seven eight".split()
    transcript = ""
    snapshots = []
    for index, word in enumerate(words):
        transcript = f"{transcript} {word}".strip()
        position = info["data_offset"] + int((index + 1) / len(words) * info["duration"] * info["bytes_per_second"])
        snapshots.append((position, transcript))
    cues = cues_for_narration(
        audio=audio,
        snapshots=snapshots,
        transcript=transcript,
        script=transcript,
        duration=4.0,
    )
    assert cues[0]["timestamp_start"] < 0.6
    assert cues[-1]["timestamp_end"] == pytest.approx(4.0)
    assert cues[0]["text"].split()[0] == "one"


def test_late_transcript_still_spreads_phrases_across_the_file():
    audio = _wav(4.0)
    cues = cues_for_narration(
        audio=audio,
        snapshots=[(len(audio), "one two three four five six")],
        transcript="one two three four five six",
        script="one two three four five six",
        duration=4.0,
    )
    assert len(cues) >= 2
    assert cues[0]["timestamp_start"] == 0
    midpoint = cues[len(cues) // 2]["timestamp_start"]
    assert 0.5 < midpoint < 3.5


def test_normalize_plan_splits_narration_across_scenes():
    plan = normalize_plan(
        {
            "title": "Market",
            "narration": "Rain on the awning lights the fruit and the street",
            "scenes": [
                {"image_prompt": "awnings", "animation": "zoom_in"},
                {"image_prompt": "fruit", "animation": "zoom_in"},
                {"image_prompt": "street", "animation": "pan_left"},
            ],
        },
        "night market",
    )
    spoken = " ".join(scene["spoken"] for scene in plan["scenes"])
    assert spoken == plan["narration"]
    assert plan["scenes"][1]["animation"] != "zoom_in"


def test_audio_stream_assembler_joins_split_base64_and_transcript():
    raw = b"hello world, this is a voiceover"
    encoded = __import__("base64").b64encode(raw).decode()
    split = 5
    assembler = AudioStreamAssembler()
    problem = assembler.feed(
        {"choices": [{"delta": {"audio": {"data": encoded[:split], "transcript": "hello "}}}]}
    )
    assert problem is None
    problem = assembler.feed(
        {"choices": [{"delta": {"audio": {"data": encoded[split:], "transcript": "world"}}}]}
    )
    assert problem is None
    audio, transcript, snapshots = assembler.finish()
    assert audio == raw
    assert transcript == "hello world"
    assert len(snapshots) == 2


def test_ffmpeg_ken_burns_captions_and_bed(tmp_path):
    if subprocess.call(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        pytest.skip("ffmpeg is not installed")
    still = tmp_path / "still.png"
    subprocess.check_call(
        [
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=720x1280:rate=1",
            "-frames:v", "1", str(still),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    clip = asyncio.run(
        create_image_video(str(still), tmp_path, duration=1.0, animation="zoom_in", width=1080, height=1920, fps=30)
    )
    assert clip and clip.exists()
    voice = tmp_path / "voice.wav"
    voice.write_bytes(_wav(1.0, rate=44100))
    master = asyncio.run(
        compose_basic_master(
            clip,
            tmp_path,
            voice_path=voice,
            captions=[{"text": "Slow zoom", "timestamp_start": 0.1, "timestamp_end": 0.85}],
            ambient_bed=True,
        )
    )
    assert master and master.exists()
    probe = subprocess.check_output(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height:format=duration",
            "-of", "default=nw=1",
            str(master),
        ],
        text=True,
    )
    assert "codec_type=video" in probe
    assert "codec_type=audio" in probe
    assert "width=1080" in probe
    assert "height=1920" in probe
    duration_line = next(line for line in probe.splitlines() if line.startswith("duration="))
    assert abs(float(duration_line.split("=", 1)[1]) - 1.0) < 0.15
    frame = tmp_path / "frame.png"
    early = tmp_path / "early.png"
    subprocess.check_call(
        ["ffmpeg", "-y", "-ss", "0.05", "-i", str(master), "-frames:v", "1", str(early)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.check_call(
        ["ffmpeg", "-y", "-ss", "0.40", "-i", str(master), "-frames:v", "1", str(frame)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    image = Image.open(frame).convert("RGB")
    band = image.crop((image.width // 5, int(image.height * 0.68), image.width * 4 // 5, int(image.height * 0.86)))
    raw = band.tobytes()
    bright = sum(
        1
        for index in range(0, len(raw), 3)
        if raw[index] > 220 and raw[index + 1] > 220 and raw[index + 2] > 220
    )
    assert bright > 200
    early_image = Image.open(early).convert("RGB")
    top = (40, 80, image.width - 40, 420)
    assert _mean_abs_diff(early_image.crop(top), image.crop(top)) > 4
