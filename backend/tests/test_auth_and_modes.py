"""Auth sessions and the Basic/Enhanced generation switch.

Providers are mocked. MongoDB is an in-memory fake, so the suite does not
need API keys or a database.
"""

import os

os.environ.setdefault("JWT_SECRET", "test-secret-not-for-production-32b")
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
os.environ.setdefault("DB_NAME", "nind_test")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")
os.environ["NIND_SYNC_GENERATION"] = "1"
os.environ["GENERATION_CREDIT_COST"] = "10"
os.environ["SIGNUP_CREDITS"] = "100"

import copy
import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server
from ai.base import ProviderNotConfigured
from ai.factory import clear_provider_overrides, set_provider_overrides


class FakeCursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, key, direction=1):
        self.docs.sort(key=lambda doc: doc.get(key) or "", reverse=direction < 0)
        return self

    async def to_list(self, limit):
        return copy.deepcopy(self.docs[:limit])


class FakeCollection:
    def __init__(self):
        self.docs = []

    def _match(self, doc, query):
        for key, expected in query.items():
            if isinstance(expected, dict):
                if "$ne" in expected and doc.get(key) == expected["$ne"]:
                    return False
                if "$gte" in expected and not (doc.get(key, 0) >= expected["$gte"]):
                    return False
            elif doc.get(key) != expected:
                return False
        return True

    def _project(self, doc, projection):
        cloned = copy.deepcopy(doc)
        if not projection:
            return cloned
        if all(value == 0 for value in projection.values()):
            for key in projection:
                cloned.pop(key, None)
            return cloned
        included = {key for key, value in projection.items() if value == 1}
        return {key: cloned[key] for key in included if key in cloned}

    def _apply_update(self, doc, update):
        for key, value in (update.get("$set") or {}).items():
            doc[key] = copy.deepcopy(value)
        for key, value in (update.get("$inc") or {}).items():
            doc[key] = doc.get(key, 0) + value

    async def find_one(self, query, projection=None):
        for doc in self.docs:
            if self._match(doc, query):
                return self._project(doc, projection)
        return None

    async def insert_one(self, doc):
        self.docs.append(copy.deepcopy(doc))
        return type("InsertResult", (), {"inserted_id": "fake"})()

    async def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if self._match(doc, query):
                self._apply_update(doc, update)
                return type("Result", (), {"matched_count": 1, "modified_count": 1})()
        return type("Result", (), {"matched_count": 0, "modified_count": 0})()

    async def update_many(self, query, update):
        count = 0
        for doc in self.docs:
            if self._match(doc, query):
                self._apply_update(doc, update)
                count += 1
        return type("Result", (), {"modified_count": count})()

    async def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if self._match(doc, query):
                self.docs.pop(index)
                return type("Result", (), {"deleted_count": 1})()
        return type("Result", (), {"deleted_count": 0})()

    async def delete_many(self, query):
        before = len(self.docs)
        self.docs = [doc for doc in self.docs if not self._match(doc, query)]
        return type("Result", (), {"deleted_count": before - len(self.docs)})()

    async def find_one_and_update(self, query, update, projection=None, return_document=None):
        for doc in self.docs:
            if self._match(doc, query):
                self._apply_update(doc, update)
                return self._project(doc, projection)
        return None

    def find(self, query, projection=None):
        matched = [self._project(doc, projection) for doc in self.docs if self._match(doc, query)]
        return FakeCursor(matched)

    async def count_documents(self, query):
        return sum(1 for doc in self.docs if self._match(doc, query))


class FakeDB:
    def __init__(self):
        self.users = FakeCollection()
        self.video_projects = FakeCollection()
        self.notifications = FakeCollection()
        self.team_members = FakeCollection()
        self.team_invites = FakeCollection()
        self.upload_sessions = FakeCollection()
        self.montage_projects = FakeCollection()
        self.payment_transactions = FakeCollection()

    def __getitem__(self, name):
        return getattr(self, name)


class FakeText:
    name = "fake-text"

    def __init__(self):
        self.calls = []

    async def complete(self, *, system, user, model=None):
        self.calls.append({"system": system, "user": user, "model": model})
        return (
            '{"title":"Night market","narration":"A quiet night market.",'
            '"scenes":[{"image_prompt":"lanterns over a wet street","animation":"zoom_in","duration":3}]}'
        )


class FakeImage:
    name = "fake-image"

    def __init__(self):
        self.prompts = []

    async def generate(self, prompt, *, aspect_ratio="9:16"):
        self.prompts.append((prompt, aspect_ratio))
        # 1x1 transparent PNG
        return bytes.fromhex(
            "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
            "890000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
        )


class FakeVideo:
    name = "unconfigured"
    configured = False

    async def generate(self, *, prompt, image_urls=None, duration_seconds=None):
        raise ProviderNotConfigured(
            "Enhanced mode is coming soon: no video generation provider is configured."
        )


@pytest.fixture()
def client(monkeypatch, tmp_path):
    fake = FakeDB()
    monkeypatch.setattr(server, "db", fake)
    monkeypatch.setattr(server, "UPLOADS_DIR", tmp_path)
    monkeypatch.setattr(server, "WORK_DIR", tmp_path / "work")
    text = FakeText()
    image = FakeImage()

    class SilentTTS:
        name = "unconfigured"

        async def synthesize(self, text, *, voice=None):
            raise ProviderNotConfigured("TTS provider is not configured")

        async def synthesize_detailed(self, text, *, voice=None):
            raise ProviderNotConfigured("TTS provider is not configured")

    set_provider_overrides(text=text, image=image, video=FakeVideo(), tts=SilentTTS())

    async def fake_clip(image_url, output_path, duration=4.0, animation="zoom_in", **kwargs):
        del image_url, duration, animation, kwargs
        output_path.mkdir(parents=True, exist_ok=True)
        clip = output_path / "clip.mp4"
        clip.write_bytes(b"fake-mp4")
        return clip

    async def fake_concat(paths, output_path):
        del output_path
        return paths[0]

    monkeypatch.setattr("generation.create_image_video", fake_clip)
    monkeypatch.setattr("generation.concatenate_videos", fake_concat)

    with TestClient(server.app) as test_client:
        yield test_client, fake, text, image
    clear_provider_overrides()


def test_register_login_and_me(client):
    http, _db, _text, _image = client
    registered = http.post("/api/auth/register", json={"email": "ada@example.com", "password": "correct-horse"})
    assert registered.status_code == 200, registered.text
    body = registered.json()
    assert body["email"] == "ada@example.com"
    assert body["credits"] == 100
    assert body["token"]
    assert "password_hash" not in body

    logged_out = http.get("/api/auth/me")
    # Cookie from the register response is stored by TestClient.
    assert logged_out.status_code == 200

    fresh = TestClient(server.app)
    denied = fresh.get("/api/auth/me")
    assert denied.status_code == 401
    allowed = fresh.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert allowed.status_code == 200
    assert allowed.json()["user_id"] == body["user_id"]

    again = http.post("/api/auth/login", json={"email": "ada@example.com", "password": "correct-horse"})
    assert again.status_code == 200
    assert again.json()["user_id"] == body["user_id"]
    wrong = http.post("/api/auth/login", json={"email": "ada@example.com", "password": "nope-nope"})
    assert wrong.status_code == 401


def test_legacy_sha256_password_is_upgraded(client):
    http, db, _text, _image = client
    legacy = hashlib.sha256(b"correct-horse").hexdigest()
    db.users.docs.append(
        {
            "user_id": "user_legacy",
            "email": "legacy@example.com",
            "name": "legacy",
            "username": "legacy",
            "password_hash": legacy,
            "plan": "free",
            "credits": 40,
        }
    )
    response = http.post("/api/auth/login", json={"email": "legacy@example.com", "password": "correct-horse"})
    assert response.status_code == 200, response.text
    stored = db.users.docs[0]["password_hash"]
    assert stored.startswith("$2")
    assert stored != legacy


def test_protected_generate_rejects_missing_token(client):
    http, _db, _text, _image = client
    response = http.post("/api/video/generate", json={"prompt": "a cat", "mode": "basic"})
    assert response.status_code == 401
    listing = http.get("/api/videos")
    assert listing.status_code == 401


def test_basic_generation_uses_providers_and_debits_credits(client):
    http, db, text, image = client
    registered = http.post("/api/auth/register", json={"email": "ada@example.com", "password": "correct-horse"})
    token = registered.json()["token"]
    response = http.post(
        "/api/video/generate",
        json={"prompt": "night market in the rain", "format_id": "auto", "mode": "basic", "user_id": "someone-else"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["mode"] == "basic"
    assert response.json()["credits"] == 90
    assert text.calls, "text provider was not called"
    assert image.prompts, "image provider was not called"
    assert "night market" in text.calls[0]["user"]
    project = db.video_projects.docs[0]
    assert project["user_id"] == registered.json()["user_id"]
    assert project["user_id"] != "someone-else"
    assert project["status"] == "completed"
    assert project["mode"] == "basic"
    assert project["video_url"].endswith(".mp4")
    video_file = Path(server.UPLOADS_DIR) / project["video_url"].rsplit("/", 1)[-1]
    assert video_file.exists()


def test_enhanced_mode_is_not_configured(client):
    http, db, _text, _image = client
    registered = http.post("/api/auth/register", json={"email": "ada@example.com", "password": "correct-horse"})
    token = registered.json()["token"]
    response = http.post(
        "/api/video/generate",
        json={"prompt": "a generated clip", "mode": "enhanced"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 501
    assert "coming soon" in response.json()["detail"].lower() or "not configured" in response.json()["detail"].lower()
    assert db.users.docs[0]["credits"] == 100
    assert db.video_projects.docs == []


def test_formats_route_exists(client):
    http, _db, _text, _image = client
    response = http.get("/api/formats")
    assert response.status_code == 200
    assert response.json()["formats"]


def test_voices_include_female_and_male_options(client):
    http, _db, _text, _image = client
    response = http.get("/api/voices")
    assert response.status_code == 200
    voices = response.json()["voices"]
    genders = {item["gender"] for item in voices}
    assert "female" in genders
    assert "male" in genders
    assert response.json()["default"] == "marin"


def test_basic_generation_times_scenes_to_the_voiceover(client, monkeypatch):
    http, db, _text, _image = client
    from ai.base import SpeechSynthesis

    seen = {}

    class Speaking:
        name = "fake-tts"

        async def synthesize(self, text, *, voice=None):
            return b"audio"

        async def synthesize_detailed(self, narration, *, voice=None):
            seen["voice"] = voice
            seen["narration"] = narration
            return SpeechSynthesis(audio=b"RIFFxxxx", transcript=narration, audio_format="wav", voice=voice or "")

    set_provider_overrides(tts=Speaking())
    durations = []

    async def fake_clip(image_url, output_path, duration=4.0, animation="zoom_in", **kwargs):
        del image_url, animation, kwargs
        durations.append(duration)
        output_path.mkdir(parents=True, exist_ok=True)
        clip = output_path / "clip.mp4"
        clip.write_bytes(b"fake-mp4")
        return clip

    async def fake_compose(video_path, work_dir, voice_path=None, captions=None, ambient_bed=None):
        del work_dir, ambient_bed
        seen["captions"] = captions
        seen["voice_path"] = voice_path
        return video_path

    monkeypatch.setattr("generation.create_image_video", fake_clip)
    monkeypatch.setattr("generation.compose_basic_master", fake_compose)
    monkeypatch.setattr("generation.wav_duration", lambda _audio: 6.0)

    registered = http.post("/api/auth/register", json={"email": "ada@example.com", "password": "correct-horse"})
    token = registered.json()["token"]
    response = http.post(
        "/api/video/generate",
        json={"prompt": "night market in the rain", "mode": "basic", "voice": "echo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    project = db.video_projects.docs[0]
    assert project["status"] == "completed", project.get("error")
    assert project["voice"] == "echo"
    assert seen["voice"] == "echo"
    assert "night market" in seen["narration"].lower()
    assert durations == [6.0]
    assert seen["captions"] and len(seen["captions"]) >= 2
    assert seen["captions"][0]["timestamp_start"] == 0
    assert seen["captions"][-1]["timestamp_end"] == 6.0
    assert project["audio_url"].endswith(".wav")
