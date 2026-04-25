from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile, File, Request, Depends
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone, timedelta
import asyncio
import base64
import json
import httpx
import subprocess
import shutil

# AUTO-INSTALL DEPENDENCIES (ffmpeg, fonts)
def ensure_dependencies():
    """Install ffmpeg and fonts if missing"""
    # Check ffmpeg
    if not shutil.which("ffmpeg"):
        print("Installing ffmpeg...")
        subprocess.run(["apt-get", "update"], capture_output=True)
        subprocess.run(["apt-get", "install", "-y", "ffmpeg"], capture_output=True)
    
    # Check fonts
    font_path = Path("/usr/share/fonts/opentype/inter")
    if not font_path.exists():
        print("Installing fonts...")
        subprocess.run(["apt-get", "install", "-y", "fonts-inter", "fonts-dejavu"], capture_output=True)
        subprocess.run(["fc-cache", "-f"], capture_output=True)
    
    print(f"Dependencies OK: ffmpeg={shutil.which('ffmpeg')}, fonts={font_path.exists()}")

ensure_dependencies()

# Stripe integration
from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, 
    CheckoutSessionResponse, 
    CheckoutStatusResponse, 
    CheckoutSessionRequest
)

# Import video service
from video_service import (
    create_gameplay_clip, create_split_screen_video, download_youtube_clip,
    create_image_video, concatenate_videos, add_audio_to_video, 
    add_subtitles_to_video, cleanup_work_dir, create_chat_animation_video,
    create_apple_text_animation, create_kinetic_typography, create_logo_animation,
    WORK_DIR
)

# Import professional animation renderer
from animation_renderer import (
    render_chat_animation,
    render_apple_text_animation,
    render_kinetic_typography,
    render_logo_animation,
    render_product_advertisement,
    render_spotify_demo,
    render_saas_demo
)
from pro_effects import (
    render_spotify_style,
    render_imessage_style,
    render_dashboard_style
)
from exact_effects import (
    render_spotify_exact,
    render_imessage_exact
)
from universal_effects import render_universal_video, render_apple_text_sequence, render_video_on_device

# Import montage service
from montage_service import (
    analyze_video_for_montage,
    create_montage,
    add_text_overlay,
    MONTAGE_STYLES
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create uploads directory
UPLOADS_DIR = ROOT_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== MODELS ====================

class VideoFormat(BaseModel):
    id: str
    name: str
    name_ru: str
    description: str
    description_ru: str
    icon: str
    category: str
    image_url: str

class VideoGenerateRequest(BaseModel):
    prompt: str
    format_id: str = "auto"  # Auto-detect by default
    language: str = "auto"
    youtube_url: Optional[str] = None
    character_type: Optional[str] = None
    gameplay_type: Optional[str] = None
    # Product advertisement fields
    product_images: Optional[List[str]] = None  # URLs to uploaded product images
    logo_url: Optional[str] = None  # URL to uploaded logo
    brand_name: Optional[str] = None  # Brand name for logo animation
    user_id: Optional[str] = None  # User ID from frontend


class MontageRequest(BaseModel):
    video_url: str  # URL to uploaded video
    prompt: Optional[str] = None  # User's instruction for montage
    style: str = "auto"  # auto, tiktok, youtube, meme, cinematic
    music_url: Optional[str] = None  # URL to uploaded music
    text_overlays: Optional[List[Dict]] = None  # Optional text overlays


class MontageProject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_video_url: str
    prompt: Optional[str] = None
    style: str
    music_url: Optional[str] = None
    status: str = "pending"
    progress: int = 0
    progress_message: str = "Инициализация..."
    analysis: Optional[Dict] = None
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VideoScene(BaseModel):
    text: str
    image_url: Optional[str] = None
    animation: str = "zoom_in"
    duration: float = 3.0

class VideoProject(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    format_id: str
    language: str
    user_id: Optional[str] = None  # User ID for filtering user's videos
    youtube_url: Optional[str] = None
    character_type: Optional[str] = None
    gameplay_type: Optional[str] = None
    # Product advertisement fields
    product_images: Optional[List[str]] = None
    logo_url: Optional[str] = None
    brand_name: Optional[str] = None
    status: str = "pending"
    progress: int = 0
    progress_message: str = "Инициализация..."
    scenes: List[dict] = []
    audio_url: Optional[str] = None
    video_url: Optional[str] = None  # Final video URL
    poster_url: Optional[str] = None  # Poster image for preview
    script: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== AUTH MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    username: Optional[str] = None
    plan: str = "free"
    credits: int = 100
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionRequest(BaseModel):
    session_id: str


# ==================== VIDEO FORMATS ====================

VIDEO_FORMATS = [
    VideoFormat(
        id="news",
        name="News Report",
        name_ru="Новостной",
        description="Breaking news style with dynamic images",
        description_ru="Новостной стиль с динамичными изображениями",
        icon="Newspaper",
        category="informational",
        image_url="https://images.unsplash.com/photo-1742805382153-bb4be26d6031?w=400"
    ),
    VideoFormat(
        id="story",
        name="Story",
        name_ru="История",
        description="Cinematic storytelling format",
        description_ru="Кинематографический формат истории",
        icon="BookOpen",
        category="entertainment",
        image_url="https://images.unsplash.com/photo-1770893876530-68601a346202?w=400"
    ),
    VideoFormat(
        id="quiz",
        name="Quiz",
        name_ru="Викторина",
        description="Interactive quiz style content",
        description_ru="Интерактивный контент в стиле викторины",
        icon="HelpCircle",
        category="entertainment",
        image_url="https://images.unsplash.com/photo-1765213186469-727cd0f08c23?w=400"
    ),
    VideoFormat(
        id="meme",
        name="Meme",
        name_ru="Мемы",
        description="Viral meme compilation style",
        description_ru="Вирусные мемы и подборки",
        icon="Smile",
        category="entertainment",
        image_url="https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=400"
    ),
    VideoFormat(
        id="educational",
        name="Educational",
        name_ru="Образовательный",
        description="Learn something new",
        description_ru="Узнайте что-то новое",
        icon="GraduationCap",
        category="informational",
        image_url="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400"
    ),
    VideoFormat(
        id="product",
        name="Product Review",
        name_ru="Обзор продукта",
        description="Product showcase and review",
        description_ru="Обзор и демонстрация продуктов",
        icon="ShoppingBag",
        category="commercial",
        image_url="https://images.unsplash.com/photo-1613488329064-aafbeb1e4db1?w=400"
    ),
    VideoFormat(
        id="gameplay_clip",
        name="Gameplay + Clip",
        name_ru="Геймплей + Клип",
        description="YouTube clip on top, gameplay at bottom with subtitles",
        description_ru="Интересный момент из YouTube сверху, геймплей снизу + субтитры",
        icon="Gamepad2",
        category="entertainment",
        image_url="https://images.unsplash.com/photo-1542751371-adc38448a05e?w=400"
    ),
    VideoFormat(
        id="ai_story",
        name="AI Story",
        name_ru="AI История",
        description="AI-generated visual story with animations and narration",
        description_ru="AI генерирует историю с картинками, анимациями и озвучкой",
        icon="Sparkles",
        category="entertainment",
        image_url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=400"
    ),
    VideoFormat(
        id="character_explainer",
        name="Character Explainer",
        name_ru="Персонаж-объяснитель",
        description="Cute character explains topics with animated scenes",
        description_ru="Милый персонаж объясняет темы с анимированными сценами",
        icon="Cat",
        category="educational",
        image_url="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?w=400"
    ),
    VideoFormat(
        id="chat_animation",
        name="Chat Animation",
        name_ru="Анимация диалога",
        description="Animated chat/message conversation video",
        description_ru="Видео с анимированным диалогом сообщений в стиле iMessage",
        icon="MessageSquare",
        category="entertainment",
        image_url="https://images.unsplash.com/photo-1611746872915-64382b5c76da?w=400"
    ),
    VideoFormat(
        id="apple_text",
        name="Apple Text Style",
        name_ru="Текст в стиле Apple",
        description="Minimalist text animation like Apple presentations",
        description_ru="Минималистичная анимация текста как в презентациях Apple",
        icon="Type",
        category="presentation",
        image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400"
    ),
    VideoFormat(
        id="kinetic_typography",
        name="Kinetic Typography",
        name_ru="Кинетическая типографика",
        description="Word-by-word animated text reveal",
        description_ru="Слово за словом - динамичная анимация текста",
        icon="AlignLeft",
        category="presentation",
        image_url="https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?w=400"
    ),
    VideoFormat(
        id="logo_animation",
        name="Logo Animation",
        name_ru="Анимация логотипа",
        description="Simple brand logo reveal animation",
        description_ru="Простая анимация появления логотипа бренда",
        icon="Star",
        category="branding",
        image_url="https://images.unsplash.com/photo-1560179707-f14e90ef3623?w=400"
    ),
    VideoFormat(
        id="product_advertisement",
        name="Product Advertisement",
        name_ru="Реклама продукта",
        description="Professional product showcase like Apple ads - with hands, multiple angles, and brand reveal",
        description_ru="Профессиональная реклама продукта как у Apple - руки, ракурсы, бренд",
        icon="ShoppingBag",
        category="commercial",
        image_url="https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"
    ),
    VideoFormat(
        id="spotify_demo",
        name="Spotify/Brand Demo",
        name_ru="Spotify/Бренд демо",
        description="Brand-style demo with gradient background, logo animation, and UI mockup",
        description_ru="Демо в стиле бренда с градиентным фоном, анимацией лого и UI",
        icon="Music",
        category="commercial",
        image_url="https://images.unsplash.com/photo-1614680376593-902f74cf0d41?w=400"
    ),
    VideoFormat(
        id="saas_demo",
        name="SaaS/Dashboard Demo",
        name_ru="SaaS/Дашборд демо",
        description="Dashboard demo with typewriter text, animated charts, and cursor",
        description_ru="Демо дашборда с печатающимся текстом, графиками и курсором",
        icon="BarChart",
        category="commercial",
        image_url="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=400"
    ),
]

# Character types for character_explainer format
CHARACTER_TYPES = [
    {"id": "kitten", "name": "Котёнок", "name_en": "Kitten", "emoji": "🐱"},
    {"id": "puppy", "name": "Щенок", "name_en": "Puppy", "emoji": "🐶"},
    {"id": "skeleton", "name": "X-Ray Скелет", "name_en": "X-Ray Skeleton", "emoji": "💀"},
    {"id": "robot", "name": "Робот", "name_en": "Robot", "emoji": "🤖"},
    {"id": "alien", "name": "Инопланетянин", "name_en": "Alien", "emoji": "👽"},
    {"id": "bear", "name": "Медвежонок", "name_en": "Bear Cub", "emoji": "🐻"},
]

# Gameplay types for gameplay_clip format
GAMEPLAY_TYPES = [
    {"id": "minecraft_parkour", "name": "Minecraft Паркур", "name_en": "Minecraft Parkour"},
    {"id": "soap_cutting", "name": "Нарезка мыла ASMR", "name_en": "Soap Cutting ASMR"},
    {"id": "subway_surfers", "name": "Subway Surfers", "name_en": "Subway Surfers"},
    {"id": "satisfying", "name": "Satisfying видео", "name_en": "Satisfying Videos"},
    {"id": "slime_asmr", "name": "Слайм ASMR", "name_en": "Slime ASMR"},
    {"id": "cooking", "name": "Готовка", "name_en": "Cooking"},
]

FORMAT_CATEGORIES = {
    "all": {"name": "Все", "name_en": "All"},
    "informational": {"name": "Информационные", "name_en": "Informational"},
    "entertainment": {"name": "Развлекательные", "name_en": "Entertainment"},
    "commercial": {"name": "Коммерческие", "name_en": "Commercial"},
}

# ==================== AI SERVICES ====================

async def detect_video_type(prompt: str) -> dict:
    """DEPRECATED - Always return universal format. AI decides what to render."""
    lang = "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"
    return {"format_id": "universal", "confidence": 1.0, "detected_language": lang}


async def generate_universal_script(prompt: str, language: str, logo_path: str = None, brand_name: str = None) -> dict:
    """
    UNIVERSAL AI SCRIPT GENERATOR
    Analyzes any prompt and generates appropriate scene sequence.
    Cal.com style animations with emphasis words.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import re

    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))

    # ===== Intent detection =====
    # Topic intent: user describes what the video should be ABOUT — LLM must invent text.
    # Literal intent: user provides exact text in quotes / after colon — text must be used verbatim.
    prompt_lower = prompt.lower()
    topic_markers = (
        " про ", " о ", "про то", "на тему", "тему ", "тематик",
        " about ", " on the topic", " regarding ", " concerning ",
    )
    is_topic_intent = any(m in f" {prompt_lower} " for m in topic_markers)

    # Look for explicit literal markers
    literal_markers_re = re.compile(
        r'(?:сделай\s+(?:такой\s+)?текст|анимац\w*\s+текст\w*|текст(?:а)?\s*[:\-]|'
        r'make\s+text|animate\s+text|text\s*[:\-])\s*'
        r'(?:["“„«‟](?P<q1>[^"”»“„‟]+)["”»‟“]'
        r"|'(?P<q2>[^']+)'"
        r'|(?P<plain>.+))$',
        re.IGNORECASE,
    )
    quoted_match = re.search(
        r'["“„«‟]([^"”»“„‟]+)["”»‟“]'
        r"|'([^']+)'"
        r"|‘([^’]+)’",
        prompt,
    )

    literal_text = ""
    explicit_literal = literal_markers_re.search(prompt.strip())
    if explicit_literal and not is_topic_intent:
        literal_text = (
            explicit_literal.group("q1")
            or explicit_literal.group("q2")
            or (explicit_literal.group("plain") or "").strip(' "\'«»“”„‟‘’')
        ).strip()
    elif quoted_match and not is_topic_intent:
        literal_text = next((g for g in quoted_match.groups() if g), "").strip()
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"universal-{uuid.uuid4()}",
            system_message="You create video animation scripts. Return ONLY valid JSON."
        )
        chat.with_model("openai", "gpt-5.2")
        
        system_prompt = f"""Create a video animation script. Return ONLY valid JSON.

USER REQUEST (verbatim, in their exact words):
\"\"\"{prompt}\"\"\"

INTENT DETECTION (choose exactly one mode):

MODE A — LITERAL TEXT MODE (active when user provides exact wording for the screen):
{"  → ACTIVE. The user wants this exact text on screen: «" + literal_text + "». Every text scene MUST contain ONLY characters from this exact string. You MAY split it across 3–6 scenes for cinematic pacing, but DO NOT invent any new words." if literal_text else "  → INACTIVE. (No literal text was provided.)"}

MODE B — TOPIC MODE (active when user describes what the video should be ABOUT):
{"  → ACTIVE. The user wants a video ABOUT a topic, NOT the topic word itself. WRITE 3–6 short, punchy phrases (in " + ("Russian" if is_russian else "the user's language") + ") that tell a mini-story about the topic. Each scene = one phrase. Be creative, persuasive, cinematic." if is_topic_intent else "  → INACTIVE. (User did not describe a topic.)"}

If NEITHER mode is active above, treat the request as Topic Mode and write 3–6 short narrative phrases inspired by the prompt.

{"BRAND NAME: " + brand_name if brand_name else ""}
{"HAS LOGO: yes" if logo_path else ""}

UNIVERSAL RULES:
- Output language MUST match the user's language ({"Russian" if is_russian else "English"} detected).
- Every scene MUST have a non-empty "text" field if it is a text-type scene.
- DO NOT use placeholders like "Hello", "Hello World", "Sample", "Welcome", "Lorem ipsum", "Text", "Title".
- DO NOT translate the user's text in Literal Mode.

PRIMARY TEXT SCENE TYPES — USE A DIFFERENT TYPE FOR EACH SCENE so the video feels varied:

A. "motion_blur_in" — heavy gaussian blur (38px) → 0, char-by-char. CINEMATIC OPENING.
   {{"type": "motion_blur_in", "text": "...", "bg": "white", "color": [0,0,0], "by_char": true, "duration": 1.7}}

B. "motion_char_fade" — char fade + 28px slide-up + optional gradient (orange→purple) on emphasis_word.
   USE FOR narrative lines with one strong word.
   {{"type": "motion_char_fade", "text": "...", "emphasis_word": "<one_word>", "bg": "black", "color": [255,255,255], "use_gradient": true, "duration": 1.8}}

C. "motion_apple_scale" — word scale 0.78→1.0 + slide-from-left 56px. Apple keynote feel.
   USE FOR short punchy phrases (2–4 words).
   {{"type": "motion_apple_scale", "text": "...", "bg": "white", "color": [0,0,0], "duration": 1.4}}

D. "motion_word_slide" — word slide-from-left 110px with thick blurred drop shadow.
   USE FOR storytelling on white bg.
   {{"type": "motion_word_slide", "text": "...", "bg": "white", "color": [0,0,0], "shadow": true, "duration": 1.6}}

E. "motion_fade_underline" — char fade + scale 0.6→1.0 + slide-up 38px + animated thick underline on emphasis_words.
   USE FOR final call-to-action / payoff line. Pick 1–2 emphasis_words.
   {{"type": "motion_fade_underline", "text": "...", "emphasis_words": ["<word1>", "<word2>"], "bg": "white", "color": [0,0,0], "duration": 1.7}}

F. "motion_word_slide_right" — word-by-word slide-from-RIGHT + fade. TikTok / Adobe-tutorial style.
   USE FOR opening titles or transitional phrases.
   {{"type": "motion_word_slide_right", "text": "...", "bg": "black", "color": [255,255,255], "duration": 1.5}}

G. "motion_word_slide_up" — word-by-word slide-from-BELOW + fade. Each word floats up.
   USE FOR emotional / reflective lines, lyrics, value statements.
   {{"type": "motion_word_slide_up", "text": "...", "bg": "white", "color": [0,0,0], "duration": 1.5}}

H. "motion_word_slide_down" — word-by-word slide-from-ABOVE + fade. Each word falls in.
   USE FOR list items, headlines, dramatic announcements.
   {{"type": "motion_word_slide_down", "text": "...", "bg": "black", "color": [255,255,255], "duration": 1.5}}

I. "motion_line_slide_up" — whole phrase slides up as a single block + fade. Bold and clean.
   USE FOR final CTA / one-line statement / closing phrase.
   {{"type": "motion_line_slide_up", "text": "...", "bg": "black", "color": [255,255,255], "duration": 1.5}}

NON-TEXT SUPPORTING TYPES (use only when needed):
- "calcom_chat" — only for messaging/chat-style content
- "device_mockup" — only when user mentions a phone/device
- "logo_reveal" — only when a logo is provided

CINEMATIC RULES:
- Use 4–6 scenes total. Each scene MUST use a DIFFERENT motion_* type (pick from A–I above).
- Mix entry directions for variety: from-left, from-right, from-above, from-below.
- Always include "motion_blur_in" as the first/hero scene.
- Alternate background between "white" and "black" between scenes.
- Default text color: white on black bg, black on white bg.
- For motion_char_fade with use_gradient=true, pick the most meaningful word as emphasis_word.
- Scene duration: 1.2–2.0 s. Total video: 6–10 s.

OUTPUT JSON SHAPE:
{{
    "scenes": [
        {{"type": "motion_blur_in", "text": "...", "bg": "white", "color": [0,0,0], "by_char": true, "duration": 1.7}},
        {{"type": "motion_char_fade", "text": "...", "emphasis_word": "...", "bg": "black", "color": [255,255,255], "use_gradient": true, "duration": 1.8}},
        {{"type": "motion_apple_scale", "text": "...", "bg": "white", "color": [0,0,0], "duration": 1.4}},
        {{"type": "motion_word_slide", "text": "...", "bg": "white", "color": [0,0,0], "shadow": true, "duration": 1.6}},
        {{"type": "motion_fade_underline", "text": "...", "emphasis_words": ["..."], "bg": "white", "color": [0,0,0], "duration": 1.7}}
    ]
}}

Return ONLY valid JSON, no markdown, no commentary."""

        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)

        logger.info(f"Universal AI response: {response[:500]}")

        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])

            # === Post-processing: strip placeholder/empty text scenes ===
            BANNED_TEXTS = {"hello", "hello world", "hello world!", "sample", "lorem ipsum",
                            "welcome", "your text", "your text here", "text", "title", "subtitle"}
            cleaned = []
            for sc in result.get("scenes", []) or []:
                txt = (sc.get("text") or "").strip()
                if sc.get("type", "").startswith(("motion_", "calcom_", "apple_", "zoom_",
                                                  "gradient_", "text", "chat")):
                    if not txt:
                        logger.warning(f"Dropping scene with empty text: {sc.get('type')}")
                        continue
                    if txt.lower() in BANNED_TEXTS:
                        logger.warning(f"Dropping scene with placeholder text '{txt}'")
                        continue
                cleaned.append(sc)
            result["scenes"] = cleaned

            # If LLM completely ignored quoted text, force a hero motion_blur_in scene with it
            if literal_text and result["scenes"]:
                has_literal = any(
                    literal_text.lower() in (s.get("text") or "").lower()
                    for s in result["scenes"]
                )
                if not has_literal:
                    logger.warning("LLM ignored literal user text; injecting hero scene")
                    result["scenes"].insert(0, {
                        "type": "motion_blur_in",
                        "text": literal_text,
                        "bg": "white",
                        "color": [0, 0, 0],
                        "by_char": True,
                        "duration": 1.7,
                    })

            if not result["scenes"]:
                logger.warning("All scenes dropped; using literal/user fallback")
                fallback_text = literal_text or prompt[:80].strip()
                if fallback_text:
                    result["scenes"] = [{
                        "type": "motion_blur_in",
                        "text": fallback_text,
                        "bg": "white",
                        "color": [0, 0, 0],
                        "by_char": True,
                        "duration": 1.8,
                    }]

            if logo_path:
                result["logo_path"] = logo_path
            if brand_name:
                result["brand_name"] = brand_name
            result["user_prompt"] = prompt
            logger.info(f"Parsed universal script: {result}")
            return result
    except Exception as e:
        logger.warning(f"Universal script generation failed: {e}")

    # Fallback — use literal quoted text if present, else first 80 chars of prompt
    fallback_text = literal_text or prompt[:80].strip() or ("Привет" if is_russian else "Welcome")
    return {
        "scenes": [
            {"type": "motion_blur_in", "text": fallback_text, "bg": "white",
             "color": [0, 0, 0], "by_char": True, "duration": 1.8}
        ],
        "user_prompt": prompt,
        "total_duration": 1.8,
    }


async def generate_logo_animation_script(prompt: str, brand_name: str, language: str) -> dict:
    """
    AI generates logo animation script with custom effects based on user prompt.
    Supports: wink, bounce, pulse, shake, rotate, zoom, and more.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"logo-anim-{uuid.uuid4()}",
            system_message="You create logo animation scripts. Analyze user requests for special effects."
        )
        chat.with_model("openai", "gpt-5.2")
        
        system_prompt = f"""Create logo animation script. Return ONLY valid JSON.

Brand name: {brand_name}
User request: {prompt}

ANIMATION STRUCTURE:
The animation has 3 phases:
1. "intro" - Logo appears (0-1s)
2. "main" - Logo moves left, text appears right (1-2s)  
3. "outro" - Special effects at the end (2-3s)

AVAILABLE EFFECTS for "outro" phase:
- "wink" - Logo winks (one eye closes briefly) - good for logos with eyes/faces
- "bounce" - Logo bounces up and down
- "pulse" - Logo pulses (scales up/down)
- "shake" - Logo shakes horizontally
- "rotate" - Logo rotates 360 degrees
- "zoom" - Logo zooms in slightly
- "none" - No special effect, just static

RETURN JSON:
{{
    "brand_name": "{brand_name}",
    "bg_color": "#5865F2",
    "effects": {{
        "intro": "scale_fade",
        "outro": "wink"
    }},
    "outro_repeat": 2
}}

RULES:
- Analyze user prompt for effect hints (подмигнул=wink, прыгает=bounce, пульсирует=pulse)
- Choose appropriate bg_color based on brand (Discord=#5865F2, etc.)
- Default outro is "none" unless user asks for something specific
- outro_repeat = how many times to repeat the outro effect (1-3)

User prompt: {prompt}

Return ONLY JSON."""

        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            return result
    except Exception as e:
        logger.warning(f"Logo animation script generation failed: {e}")
    
    # Default script
    return {
        "brand_name": brand_name,
        "bg_color": "#5865F2",
        "effects": {"intro": "scale_fade", "outro": "none"},
        "outro_repeat": 1
    }





async def generate_chat_animation_script(prompt: str, language: str) -> dict:
    """Generate script for Chat Animation format - animated message dialogs"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"chat-anim-{uuid.uuid4()}",
            system_message="You are a creative content writer who creates engaging chat/message animations for viral videos."
        )
        chat.with_model("openai", "gpt-5.2")
        
        lang_instruction = "Respond in Russian." if is_russian else "Respond in English."
        
        system_prompt = f"""Create an animated chat/message conversation video script based on this prompt.
{lang_instruction}

The video will show an animated phone screen with messages appearing one by one in iMessage style.
Style: Modern messenger app (like iMessage) - black background, blue bubbles for received, gray for sent.

Requirements:
- Extract or create the conversation from the user's prompt
- Each message should have a sender (0 = received/left/blue, 1 = sent/right/gray)
- Add emojis where appropriate for engagement
- Messages should build tension or humor
- Total duration: 30-60 seconds
- Keep messages SHORT (max 50 characters each)

Return a JSON object:
{{
    "title": "Catchy title for the video",
    "theme": "dramatic/funny/romantic/business/mystery",
    "participants": [
        {{"name": "Contact Name", "side": "left", "avatar_color": "#007AFF"}},
        {{"name": "Me", "side": "right", "avatar_color": "#292929"}}
    ],
    "messages": [
        {{
            "sender": 0,
            "text": "Short message text",
            "delay": 1.2,
            "typing_duration": 0.6
        }}
    ],
    "full_script": "All messages combined for TTS narration"
}}

User prompt: {prompt}"""
        
        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"Chat animation script generation failed: {e}")
    
    # Fallback: create simple dialog
    if is_russian:
        return {
            "title": "Интересный диалог",
            "theme": "dramatic",
            "participants": [
                {"name": "Клиент", "side": "left", "avatar_color": "#007AFF"},
                {"name": "Я", "side": "right", "avatar_color": "#292929"}
            ],
            "messages": [
                {"sender": 0, "text": "Привет! 👋", "delay": 1.2, "typing_duration": 0.6},
                {"sender": 1, "text": "Здравствуйте!", "delay": 1.0, "typing_duration": 0.5},
                {"sender": 0, "text": "Как дела?", "delay": 1.2, "typing_duration": 0.5},
                {"sender": 1, "text": "Отлично! 😊", "delay": 1.0, "typing_duration": 0.4},
            ],
            "full_script": "Привет! Здравствуйте! Как дела? Отлично!"
        }
    else:
        return {
            "title": "Interesting Dialog",
            "theme": "dramatic",
            "participants": [
                {"name": "Client", "side": "left", "avatar_color": "#007AFF"},
                {"name": "Me", "side": "right", "avatar_color": "#292929"}
            ],
            "messages": [
                {"sender": 0, "text": "Hey! 👋", "delay": 1.2, "typing_duration": 0.6},
                {"sender": 1, "text": "Hello!", "delay": 1.0, "typing_duration": 0.5},
                {"sender": 0, "text": "How are you?", "delay": 1.2, "typing_duration": 0.5},
                {"sender": 1, "text": "Great! 😊", "delay": 1.0, "typing_duration": 0.4},
            ],
            "full_script": "Hey! Hello! How are you? Great!"
        }


async def generate_apple_text_script(prompt: str, language: str) -> dict:
    """Generate script for Apple-style text animation"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"apple-text-{uuid.uuid4()}",
            system_message="You follow user instructions EXACTLY. Never translate, never add extra content. Always return valid JSON."
        )
        chat.with_model("openai", "gpt-5.2")
        
        system_prompt = f"""Create Apple-style minimalist text animation.

CRITICAL RULES:
1. Use EXACTLY the text the user provides - DO NOT translate it
2. DO NOT add text that user didn't ask for  
3. If user specifies colors (like "blue gradient", "голубой", "голубо-синий"), add "gradient_colors" to that phrase
4. Keep the EXACT language user wrote in

GRADIENT COLORS (when user asks for gradient):
- "голубо-синий" / "голубой" / "blue" / "синий" = ["#00D4FF", "#0066FF"]
- "зелёный" / "green" = ["#00FF87", "#00D4AA"]  
- "фиолетовый" / "purple" = ["#9D4EDD", "#7B2CBF"]
- "оранжевый" / "orange" = ["#FF6B35", "#FF8C42"]
- "красный" / "red" = ["#FF416C", "#FF4B2B"]

IMPORTANT: When user says "переливнуть градиентом" or "gradient" for a specific text, you MUST add "gradient_colors" array to that phrase!

Return ONLY valid JSON (no markdown, no explanation):
{{
    "title": "Title",
    "phrases": [
        {{"text": "First phrase", "bg": "white"}},
        {{"text": "Second phrase with gradient", "bg": "black", "gradient_colors": ["#00D4FF", "#0066FF"]}}
    ],
    "full_script": "All text for TTS"
}}

User prompt: {prompt}"""
        
        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        logger.info(f"Apple text AI response: {response[:500]}")
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            logger.info(f"Parsed Apple text script: {result}")
            return result
    except Exception as e:
        logger.warning(f"Apple text script generation failed: {e}")
    
    # Fallback - try to parse user prompt for gradient request
    has_gradient = any(word in prompt.lower() for word in ['градиент', 'переливн', 'gradient', 'голубо', 'синий', 'blue'])
    
    if is_russian:
        fallback = {
            "title": "Презентация",
            "phrases": [
                {"text": "Давайте создадим", "bg": "white"},
                {"text": "Что-то невероятное", "bg": "white"},
                {"text": "Просто. Чисто.", "bg": "black"},
            ],
            "full_script": "Давайте создадим что-то невероятное. Просто. Чисто."
        }
        if has_gradient:
            fallback["phrases"].append({"text": "Бренд", "bg": "black", "gradient_colors": ["#00D4FF", "#0066FF"]})
        else:
            fallback["phrases"].append({"text": "Как Apple.", "bg": "white", "underline": "Apple"})
        return fallback
    else:
        fallback = {
            "title": "Presentation",
            "phrases": [
                {"text": "Let's create", "bg": "white"},
                {"text": "Something amazing", "bg": "white"},
                {"text": "Simple. Clean.", "bg": "black"},
            ],
            "full_script": "Let's create something amazing. Simple. Clean."
        }
        if has_gradient:
            fallback["phrases"].append({"text": "Brand", "bg": "black", "gradient_colors": ["#00D4FF", "#0066FF"]})
        else:
            fallback["phrases"].append({"text": "Like Apple.", "bg": "white", "underline": "Apple"})
        return fallback


async def generate_kinetic_typography_script(prompt: str, language: str) -> dict:
    """Generate script for kinetic typography animation"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"kinetic-{uuid.uuid4()}",
            system_message="You create impactful quotes and text for kinetic typography animations."
        )
        chat.with_model("openai", "gpt-5.2")
        
        lang_instruction = "Respond in Russian." if is_russian else "Respond in English."
        
        system_prompt = f"""Create text content for kinetic typography animation.
{lang_instruction}

The words will appear one by one on screen.
- Create a powerful quote or message (10-20 words)
- Each word appears sequentially with slight delay
- Content should be impactful and memorable

Return JSON:
{{
    "title": "Title",
    "full_script": "The complete text that will be animated word by word",
    "bg_color": "#000000",
    "text_color": "#ffffff"
}}

User prompt: {prompt}"""
        
        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"Kinetic typography script generation failed: {e}")
    
    # Fallback
    if is_russian:
        return {
            "title": "Мотивация",
            "full_script": "Каждое большое достижение начинается с решения попробовать",
            "bg_color": "#000000",
            "text_color": "#ffffff"
        }
    else:
        return {
            "title": "Motivation",
            "full_script": "Every great achievement begins with the decision to try",
            "bg_color": "#000000",
            "text_color": "#ffffff"
        }


# Old logo script function removed - using new AI-driven one at line 393


async def generate_product_advertisement_script(
    prompt: str, 
    language: str,
    product_images: Optional[List[str]] = None,
    logo_url: Optional[str] = None,
    brand_name: Optional[str] = None
) -> dict:
    """
    Generate script for Product Advertisement format.
    Like Apple MacBook Neo ads - professional product showcase with hands, angles, brand reveal.
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"product-ad-{uuid.uuid4()}",
            system_message="You create professional product advertisement scripts like Apple commercials."
        )
        chat.with_model("openai", "gpt-5.2")
        
        lang_instruction = "Respond in Russian." if is_russian else "Respond in English."
        has_images = product_images and len(product_images) > 0
        has_logo = logo_url is not None
        
        system_prompt = f"""Create a professional product advertisement video script like Apple MacBook Neo commercials.
{lang_instruction}

User prompt: {prompt}
Has product images uploaded: {has_images}
Has logo uploaded: {has_logo}
Brand name provided: {brand_name or 'Not specified'}

Video structure (like MacBook Neo ad):
1. Scene 1: Product introduction - closed/static view (hand holding from below if applicable)
2. Scene 2: Product reveal - open/dynamic view showing key feature
3. Scene 3: Brand reveal - Logo + Product name with gradient text effect
4. Scene 4 (optional): Tagline/disclaimer at bottom

For each scene, determine:
- Whether to use uploaded image OR generate new AI image
- Whether to include hands holding the product
- Camera movement (static, subtle pan, zoom)
- Text overlays and animations

Return JSON:
{{
    "title": "Product Ad Title",
    "product_name": "Product Name",
    "brand_name": "{brand_name or 'Brand'}",
    "tagline": "Optional tagline",
    "scenes": [
        {{
            "scene_number": 1,
            "description": "Product closed, held by hand from below",
            "use_uploaded_image": false,
            "image_prompt": "Professional product photo of [product] on pure white background, minimalist, high quality, hand holding from below, premium lighting, 9:16 vertical format",
            "needs_hands": true,
            "camera_movement": "static",
            "duration": 1.5,
            "text_overlay": null
        }},
        {{
            "scene_number": 2,
            "description": "Product open/revealed, side angle",
            "use_uploaded_image": false,
            "image_prompt": "Professional product photo of [product] from side angle showing key feature, pure white background, minimalist, premium lighting",
            "needs_hands": false,
            "camera_movement": "subtle_zoom_in",
            "duration": 1.5,
            "text_overlay": null
        }},
        {{
            "scene_number": 3,
            "description": "Brand reveal",
            "use_uploaded_image": false,
            "image_prompt": null,
            "needs_hands": false,
            "camera_movement": "static",
            "duration": 2.0,
            "text_overlay": {{
                "brand_name": "Brand",
                "product_name": "Product Name",
                "use_gradient": true,
                "gradient_colors": ["#00ff00", "#ffffff"]
            }}
        }}
    ],
    "bg_color": "#ffffff",
    "include_logo": {str(has_logo).lower()},
    "full_script": "Brand name. Product name."
}}

Important:
- If user uploaded product images, set use_uploaded_image=true for appropriate scenes
- If prompt mentions logo/brand at start or end, include logo scene
- Generate detailed image prompts for AI to create professional product shots
- Keep it minimal and premium like Apple ads
"""
        
        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"Product advertisement script generation failed: {e}")
    
    # Fallback script
    product_name_fallback = brand_name or "Product"
    if is_russian:
        return {
            "title": f"Реклама {product_name_fallback}",
            "product_name": product_name_fallback,
            "brand_name": brand_name or "Brand",
            "tagline": "",
            "scenes": [
                {
                    "scene_number": 1,
                    "description": "Продукт крупным планом",
                    "use_uploaded_image": bool(product_images),
                    "image_prompt": f"Professional product photography of {product_name_fallback}, pure white background, minimalist Apple style, hand holding from below, premium lighting, vertical 9:16",
                    "needs_hands": True,
                    "camera_movement": "static",
                    "duration": 1.5,
                    "text_overlay": None
                },
                {
                    "scene_number": 2,
                    "description": "Продукт с другого ракурса",
                    "use_uploaded_image": False,
                    "image_prompt": f"Professional product photography of {product_name_fallback} from side angle, pure white background, showing details, premium lighting",
                    "needs_hands": False,
                    "camera_movement": "subtle_zoom_in",
                    "duration": 1.5,
                    "text_overlay": None
                },
                {
                    "scene_number": 3,
                    "description": "Название бренда",
                    "use_uploaded_image": False,
                    "image_prompt": None,
                    "needs_hands": False,
                    "camera_movement": "static",
                    "duration": 2.0,
                    "text_overlay": {
                        "brand_name": brand_name or "Brand",
                        "product_name": product_name_fallback,
                        "use_gradient": True,
                        "gradient_colors": ["#00ff00", "#ffffff"]
                    }
                }
            ],
            "bg_color": "#ffffff",
            "include_logo": bool(logo_url),
            "full_script": f"{brand_name or 'Brand'}. {product_name_fallback}."
        }
    else:
        return {
            "title": f"{product_name_fallback} Advertisement",
            "product_name": product_name_fallback,
            "brand_name": brand_name or "Brand",
            "tagline": "",
            "scenes": [
                {
                    "scene_number": 1,
                    "description": "Product close-up",
                    "use_uploaded_image": bool(product_images),
                    "image_prompt": f"Professional product photography of {product_name_fallback}, pure white background, minimalist Apple style, hand holding from below, premium lighting, vertical 9:16",
                    "needs_hands": True,
                    "camera_movement": "static",
                    "duration": 1.5,
                    "text_overlay": None
                },
                {
                    "scene_number": 2,
                    "description": "Product from different angle",
                    "use_uploaded_image": False,
                    "image_prompt": f"Professional product photography of {product_name_fallback} from side angle, pure white background, showing details, premium lighting",
                    "needs_hands": False,
                    "camera_movement": "subtle_zoom_in",
                    "duration": 1.5,
                    "text_overlay": None
                },
                {
                    "scene_number": 3,
                    "description": "Brand name reveal",
                    "use_uploaded_image": False,
                    "image_prompt": None,
                    "needs_hands": False,
                    "camera_movement": "static",
                    "duration": 2.0,
                    "text_overlay": {
                        "brand_name": brand_name or "Brand",
                        "product_name": product_name_fallback,
                        "use_gradient": True,
                        "gradient_colors": ["#00ff00", "#ffffff"]
                    }
                }
            ],
            "bg_color": "#ffffff",
            "include_logo": bool(logo_url),
            "full_script": f"{brand_name or 'Brand'}. {product_name_fallback}."
        }


async def generate_poster_image(video_path: Path, output_path: Path) -> Optional[str]:
    """Extract first frame from video as poster image"""
    poster_path = output_path / f"poster_{video_path.stem}.jpg"
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-vframes", "1",
        "-q:v", "2",
        str(poster_path)
    ]
    
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await asyncio.wait_for(process.communicate(), timeout=30)
    
    if poster_path.exists():
        # Move to uploads
        final_poster = UPLOADS_DIR / poster_path.name
        poster_path.rename(final_poster)
        return f"/api/uploads/{final_poster.name}"
    return None

async def analyze_prompt_and_generate_script(prompt: str, format_id: str, language: str) -> dict:
    """Use LLM to analyze prompt and generate video script"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"script-{uuid.uuid4()}",
        system_message="You are a professional video scriptwriter for short-form vertical video content."
    )
    chat.with_model("openai", "gpt-5.2")
    
    format_info = next((f for f in VIDEO_FORMATS if f.id == format_id), VIDEO_FORMATS[0])
    
    lang_instruction = ""
    if language == "auto":
        lang_instruction = "Detect the language of the prompt and respond in the same language."
    elif language == "ru":
        lang_instruction = "Respond in Russian."
    else:
        lang_instruction = "Respond in English."
    
    system_prompt = f"""Create a video script for a {format_info.name} format video.
{lang_instruction}

The video should be:
- 30-60 seconds long
- Optimized for vertical 9:16 format (TikTok/Reels/Shorts)
- Engaging and attention-grabbing

Return a JSON object with this exact structure:
{{
    "title": "Video title",
    "detected_language": "ru" or "en",
    "scenes": [
        {{
            "text": "Narrator text for this scene",
            "image_prompt": "Detailed prompt for AI image generation",
            "animation": "zoom_in" or "zoom_out" or "pan_left" or "pan_right",
            "duration": 3.0
        }}
    ],
    "full_script": "Complete narration text for TTS"
}}

Create 4-6 scenes. Each scene's image_prompt should be vivid and detailed for AI image generation.
Topic: {prompt}"""

    msg = UserMessage(text=system_prompt)
    response = await chat.send_message(msg)
    
    # Parse JSON from response
    try:
        # Try to extract JSON from the response
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            json_str = response[json_start:json_end]
            return json.loads(json_str)
    except:
        pass
    
    # Fallback response
    return {
        "title": prompt[:50],
        "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en",
        "scenes": [
            {
                "text": prompt,
                "image_prompt": f"Professional photo related to: {prompt}",
                "animation": "zoom_in",
                "duration": 4.0
            }
        ],
        "full_script": prompt
    }

async def generate_ai_story_script(prompt: str, language: str) -> dict:
    """Generate script for AI Story format"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"story-{uuid.uuid4()}",
        system_message="You are a creative storyteller who creates engaging visual stories for short-form video."
    )
    chat.with_model("openai", "gpt-5.2")
    
    lang_instruction = "Respond in Russian." if language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя')) else "Respond in English."
    
    system_prompt = f"""Create a captivating visual story based on this prompt.
{lang_instruction}

Story requirements:
- The story should be 45-60 seconds when narrated
- Create vivid, cinematic scenes that can be illustrated
- Include emotional moments and a clear narrative arc
- Each scene should have a distinct visual that can be AI-generated

Return a JSON object:
{{
    "title": "Story title",
    "genre": "horror/comedy/drama/mystery/adventure",
    "scenes": [
        {{
            "text": "Narration text for this scene",
            "image_prompt": "Detailed cinematic description for AI image generation. Include mood, lighting, style.",
            "animation": "zoom_in" or "zoom_out" or "pan_left" or "pan_right",
            "duration": 4.0,
            "mood": "tense/happy/sad/mysterious/exciting"
        }}
    ],
    "full_script": "Complete story narration"
}}

Create 5-8 scenes for a compelling story.
User prompt: {prompt}"""

    msg = UserMessage(text=system_prompt)
    response = await chat.send_message(msg)
    
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except:
        pass
    
    return {
        "title": prompt[:50],
        "genre": "adventure",
        "scenes": [{"text": prompt, "image_prompt": prompt, "animation": "zoom_in", "duration": 4.0}],
        "full_script": prompt
    }

async def generate_character_explainer_script(prompt: str, character_type: str, language: str) -> dict:
    """Generate script for Character Explainer format"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    character_info = next((c for c in CHARACTER_TYPES if c["id"] == character_type), CHARACTER_TYPES[0])
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    chat = LlmChat(
        api_key=api_key,
        session_id=f"char-{uuid.uuid4()}",
        system_message=f"You are a creative content writer who creates educational content featuring cute {character_info['name_en']} characters."
    )
    chat.with_model("openai", "gpt-5.2")
    
    lang_instruction = "Respond in Russian." if language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя')) else "Respond in English."
    
    system_prompt = f"""Create an educational/entertaining video script where a cute {character_info['name_en']} character explains the topic.
{lang_instruction}

Style: Fun, engaging, with the {character_info['name_en']} character in different situations related to the topic.
Example: "How to earn money? Let {character_info['name_en']}s explain!" - then show the character trying different ways.

Return a JSON object:
{{
    "title": "Video title featuring the character",
    "character": "{character_info['name_en']}",
    "scenes": [
        {{
            "text": "Narration text",
            "image_prompt": "Cute {character_info['name_en']} in a specific situation. Cartoon/anime style, vibrant colors, expressive character.",
            "animation": "zoom_in" or "zoom_out" or "pan_left" or "pan_right",
            "duration": 3.5,
            "action": "What the character is doing in this scene"
        }}
    ],
    "full_script": "Complete narration"
}}

Create 5-7 scenes with the {character_info['name_en']} in different situations related to the topic.
Topic: {prompt}"""

    msg = UserMessage(text=system_prompt)
    response = await chat.send_message(msg)
    
    try:
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except:
        pass
    
    return {
        "title": f"{character_info['name']} объясняют: {prompt[:30]}",
        "character": character_info['name_en'],
        "scenes": [{"text": prompt, "image_prompt": f"Cute {character_info['name_en']} explaining {prompt}", "animation": "zoom_in", "duration": 4.0}],
        "full_script": prompt
    }

async def generate_gameplay_clip_script(prompt: str, youtube_url: str, gameplay_type: str, language: str) -> dict:
    """Generate script for Gameplay + Clip format"""
    
    # Detect language
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    # Try to use LLM, but have a good fallback
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        gameplay_info = next((g for g in GAMEPLAY_TYPES if g["id"] == gameplay_type), GAMEPLAY_TYPES[0])
        
        api_key = os.getenv("EMERGENT_LLM_KEY")
        chat = LlmChat(
            api_key=api_key,
            session_id=f"gameplay-{uuid.uuid4()}",
            system_message="You are a video editor who creates engaging split-screen content with gameplay at the bottom."
        )
        chat.with_model("openai", "gpt-5.2")
        
        lang_instruction = "Respond in Russian." if is_russian else "Respond in English."
        
        system_prompt = f"""Create subtitles and scene breakdown for a split-screen video.
{lang_instruction}

Video format:
- TOP (60%): Interesting clip from YouTube video
- BOTTOM (40%): {gameplay_info['name_en']} gameplay
- SUBTITLES: Engaging text overlay

YouTube URL: {youtube_url}
Additional context: {prompt}

Return a JSON object:
{{
    "title": "Video title",
    "youtube_url": "{youtube_url}",
    "gameplay_type": "{gameplay_type}",
    "scenes": [
        {{
            "text": "Subtitle text for this moment",
            "timestamp_start": 0.0,
            "timestamp_end": 3.0,
            "highlight": true/false (is this a key moment?)
        }}
    ],
    "suggested_clip_moments": ["0:15-0:45 interesting part", "1:20-1:50 funny moment"],
    "full_script": "All subtitle text combined"
}}

Create 8-12 subtitle segments for a 30-60 second clip.
Note: The actual YouTube clip extraction will be handled separately."""

        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"LLM generation failed for gameplay_clip, using fallback: {e}")
    
    # Fallback: Generate basic subtitles without LLM
    if is_russian:
        title = f"Лучшие моменты: {prompt[:30]}"
        scenes = [
            {"text": "Смотрите что будет дальше! 👀", "timestamp_start": 0, "timestamp_end": 3, "highlight": True},
            {"text": prompt[:50] if prompt else "Интересный момент", "timestamp_start": 3, "timestamp_end": 6, "highlight": False},
            {"text": "Вы такого не ожидали! 😱", "timestamp_start": 6, "timestamp_end": 9, "highlight": True},
            {"text": "Подписывайтесь!", "timestamp_start": 9, "timestamp_end": 12, "highlight": False},
        ]
        full_script = " ".join([s["text"] for s in scenes])
    else:
        title = f"Best moments: {prompt[:30]}"
        scenes = [
            {"text": "Watch what happens next! 👀", "timestamp_start": 0, "timestamp_end": 3, "highlight": True},
            {"text": prompt[:50] if prompt else "Interesting moment", "timestamp_start": 3, "timestamp_end": 6, "highlight": False},
            {"text": "You won't believe this! 😱", "timestamp_start": 6, "timestamp_end": 9, "highlight": True},
            {"text": "Subscribe for more!", "timestamp_start": 9, "timestamp_end": 12, "highlight": False},
        ]
        full_script = " ".join([s["text"] for s in scenes])
    
    return {
        "title": title,
        "youtube_url": youtube_url,
        "gameplay_type": gameplay_type,
        "scenes": scenes,
        "suggested_clip_moments": ["0:00-0:30 intro", "0:30-1:00 main content"],
        "full_script": full_script
    }

async def generate_image(prompt: str) -> Optional[str]:
    """Generate image using Gemini Nano Banana"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import base64
    
    try:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        chat = LlmChat(
            api_key=api_key,
            session_id=f"img-{uuid.uuid4()}",
            system_message="You are a helpful AI assistant"
        )
        chat.with_model("gemini", "gemini-3.1-flash-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=f"Generate a professional, high-quality vertical image (9:16 aspect ratio) for video content: {prompt}")
        
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Save image to file
            img_id = str(uuid.uuid4())
            img_path = UPLOADS_DIR / f"{img_id}.png"
            image_bytes = base64.b64decode(images[0]['data'])
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            logger.info(f"Generated AI image: {img_id}.png")
            return f"/api/uploads/{img_id}.png"
    except Exception as e:
        logger.error(f"Image generation error: {e}")
    
    return None

async def generate_tts(text: str) -> Optional[str]:
    """Generate TTS audio using OpenAI TTS"""
    from emergentintegrations.llm.openai import OpenAITextToSpeech
    
    try:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        tts = OpenAITextToSpeech(api_key=api_key)
        
        audio_bytes = await tts.generate_speech(
            text=text,
            model="tts-1",
            voice="nova",
            speed=1.0
        )
        
        audio_id = str(uuid.uuid4())
        audio_path = UPLOADS_DIR / f"{audio_id}.mp3"
        with open(audio_path, "wb") as f:
            f.write(audio_bytes)
        
        return f"/api/uploads/{audio_id}.mp3"
    except Exception as e:
        logger.error(f"TTS error: {e}")
    
    return None

async def process_video_generation(project_id: str):
    """Background task to process video generation with real video assembly"""
    work_dir = WORK_DIR / project_id
    work_dir.mkdir(exist_ok=True)
    
    try:
        # Get project from DB
        project = await db.video_projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            return
        
        format_id = project["format_id"]
        
        # Update status
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "processing", "progress": 5, "progress_message": "Анализируем промт..."}}
        )
        
        # ============ AUTO-DETECT FORMAT ============
        if format_id == "auto":
            detection_result = await detect_video_type(project["prompt"])
            format_id = detection_result.get("format_id", "ai_story")
            logger.info(f"Auto-detected format: {format_id} (confidence: {detection_result.get('confidence', 0)})")
            
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {
                    "format_id": format_id,
                    "progress": 8,
                    "progress_message": f"Определён тип: {format_id}"
                }}
            )
        
        # Step 1: Generate script based on format
        # NOTE: All text-only formats (ai_story / apple_text / kinetic_typography) are
        # routed through the unified motion_* engine for consistent cinematic typography.
        TEXT_FORMATS_VIA_MOTION = {"ai_story", "apple_text", "kinetic_typography"}
        if format_id in TEXT_FORMATS_VIA_MOTION:
            script_data = await generate_universal_script(
                project["prompt"],
                project["language"],
            )
            # Force motion-engine render path
            format_id = "_motion_engine"

        elif format_id == "chat_animation":
            script_data = await generate_chat_animation_script(
                project["prompt"],
                project["language"]
            )
        elif format_id == "apple_text":
            script_data = await generate_apple_text_script(
                project["prompt"],
                project["language"]
            )
        elif format_id == "kinetic_typography":
            script_data = await generate_kinetic_typography_script(
                project["prompt"],
                project["language"]
            )
        elif format_id == "logo_animation":
            script_data = await generate_logo_animation_script(
                project["prompt"],
                project.get("brand_name", "Brand"),
                project["language"]
            )
        elif format_id == "ai_story":
            script_data = await generate_ai_story_script(
                project["prompt"],
                project["language"]
            )
        elif format_id == "character_explainer":
            script_data = await generate_character_explainer_script(
                project["prompt"],
                project.get("character_type", "kitten"),
                project["language"]
            )
        elif format_id == "gameplay_clip":
            script_data = await generate_gameplay_clip_script(
                project["prompt"],
                project.get("youtube_url", ""),
                project.get("gameplay_type", "minecraft_parkour"),
                project["language"]
            )
        elif format_id == "product_advertisement":
            script_data = await generate_product_advertisement_script(
                project["prompt"],
                project["language"],
                project.get("product_images"),
                project.get("logo_url"),
                project.get("brand_name")
            )
        else:
            script_data = await analyze_prompt_and_generate_script(
                project["prompt"], 
                format_id,
                project["language"]
            )
        
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "progress": 15, 
                "progress_message": "Скрипт готов. Создаём видео...",
                "script": script_data.get("full_script", ""),
                "title": script_data.get("title", project["prompt"][:50])
            }}
        )
        
        scenes = script_data.get("scenes", [])
        video_url = None
        audio_url = None
        poster_url = None
        
        # ============ MOTION ENGINE (universal text/cinematic typography) ============
        if format_id == "_motion_engine":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 35, "progress_message": "Рендерим кинетическую типографию..."}}
            )

            final_video_str = await render_universal_video(script_data, work_dir)
            final_video = Path(final_video_str) if final_video_str else None

            if final_video and final_video.exists():
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 85, "progress_message": "Финализируем видео..."}}
                )
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"

        # ============ CHAT_ANIMATION FORMAT (Universal) ============
        elif format_id == "chat_animation":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Создаём анимацию сообщений..."}}
            )
            
            # Build universal script for chat
            messages = []
            if "messages" in script_data:
                for msg in script_data["messages"][:8]:
                    messages.append({
                        "text": msg.get("text", ""),
                        "sender": msg.get("sender", 0) == 1 or msg.get("sender") == True
                    })
            
            if not messages:
                messages = [
                    {"text": "Привет! 👋", "sender": True},
                    {"text": "Привет, как дела?", "sender": False},
                    {"text": "Отлично! Что нового?", "sender": True},
                    {"text": "Много всего интересного! 😊", "sender": False},
                ]
            
            # Universal script format
            universal_script = {
                "background": {
                    "type": "linear",
                    "colors": [[20, 20, 25], [40, 40, 50]]
                },
                "elements": [
                    {
                        "type": "chat",
                        "start_time": 0.3,
                        "duration": 10.0,
                        "style": "imessage",
                        "messages": messages
                    }
                ],
                "duration": 12.0
            }
            
            # Render with universal system
            final_video_str = await render_universal_video(universal_script, work_dir)
            final_video = Path(final_video_str) if final_video_str else None
            
            if final_video and final_video.exists():
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 80, "progress_message": "Финализируем видео..."}}
                )
                
                # Generate poster
                poster_url = await generate_poster_image(final_video, work_dir)
                
                # Move to uploads
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ APPLE_TEXT FORMAT ============
        elif format_id == "apple_text":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Рендерим Apple-style текст..."}}
            )
            
            # Get texts from script_data - check phrases first
            phrases = script_data.get("phrases", [])
            texts = []
            bg_colors = []
            
            for phrase in phrases:
                if isinstance(phrase, dict):
                    texts.append(phrase.get("text", ""))
                    # Background color
                    bg = phrase.get("bg", "white")
                    if bg == "black":
                        bg_colors.append((0, 0, 0))
                    else:
                        bg_colors.append((255, 255, 255))
                elif isinstance(phrase, str):
                    texts.append(phrase)
                    bg_colors.append((255, 255, 255))
            
            # Fallback to scenes if no phrases
            if not texts:
                for scene in script_data.get("scenes", []):
                    if scene.get("text"):
                        texts.append(scene.get("text"))
                        bg_colors.append((255, 255, 255))
            
            # Final title (brand name or title)
            final_title = script_data.get("final_title") or script_data.get("title")
            
            # Render with new function
            final_video_str = await render_apple_text_sequence(
                texts=texts if texts else ["Hello World"],
                output_dir=work_dir,
                fps=30,
                bg_colors=bg_colors if bg_colors else None,
                final_title=final_title
            )
            final_video = Path(final_video_str) if final_video_str else None
            
            if final_video:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 70, "progress_message": "Генерируем озвучку..."}}
                )
                
                full_script = script_data.get("full_script", "")
                if full_script:
                    audio_url = await generate_tts(full_script)
                    if audio_url:
                        audio_path = UPLOADS_DIR / audio_url.split("/")[-1]
                        if audio_path.exists():
                            video_with_audio = await add_audio_to_video(final_video, audio_path, work_dir)
                            if video_with_audio:
                                final_video = video_with_audio
                
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ KINETIC_TYPOGRAPHY FORMAT ============
        elif format_id == "kinetic_typography":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Рендерим кинетическую типографику..."}}
            )
            
            # Use professional PIL renderer
            final_video = await render_kinetic_typography(script_data, work_dir)
            
            if final_video:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 70, "progress_message": "Генерируем озвучку..."}}
                )
                
                full_script = script_data.get("full_script", "")
                if full_script:
                    audio_url = await generate_tts(full_script)
                    if audio_url:
                        audio_path = UPLOADS_DIR / audio_url.split("/")[-1]
                        if audio_path.exists():
                            video_with_audio = await add_audio_to_video(final_video, audio_path, work_dir)
                            if video_with_audio:
                                final_video = video_with_audio
                
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ LOGO_ANIMATION FORMAT ============
        elif format_id == "logo_animation":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Рендерим анимацию логотипа..."}}
            )
            
            # Import the new logo animation function
            from universal_effects import render_logo_animation as render_logo_anim_new
            
            # Get uploaded logo if available
            logo_path = None
            logo_url = project.get("logo_url")
            if logo_url and logo_url.startswith("/api/uploads/"):
                logo_path = UPLOADS_DIR / logo_url.split("/")[-1]
                if not logo_path.exists():
                    logo_path = None
            
            # Also check product_images for logo (user might upload logo there)
            if not logo_path:
                product_images = project.get("product_images", [])
                if product_images and len(product_images) > 0:
                    first_img = product_images[0]
                    if first_img.startswith("/api/uploads/"):
                        logo_path = UPLOADS_DIR / first_img.split("/")[-1]
                        if not logo_path.exists():
                            logo_path = None
            
            # Get brand name and bg color from script
            brand_name = script_data.get("brand_name", project.get("brand_name", "Brand"))
            bg_color_hex = script_data.get("bg_color", "#5865F2")
            
            # Get prompt and language from project
            user_prompt = project.get("prompt", "")
            lang = project.get("language", "auto")
            
            # Generate AI-driven logo animation script
            logo_script = await generate_logo_animation_script(user_prompt, brand_name, lang)
            
            # Update brand_name and bg_color from AI script
            brand_name = logo_script.get("brand_name", brand_name)
            bg_color_hex = logo_script.get("bg_color", bg_color_hex)
            effects = logo_script.get("effects", {"intro": "scale_fade", "outro": "none"})
            outro_repeat = logo_script.get("outro_repeat", 1)
            
            # Parse hex color
            try:
                bg_color_hex = bg_color_hex.lstrip("#")
                bg_color = tuple(int(bg_color_hex[i:i+2], 16) for i in (0, 2, 4))
            except:
                bg_color = (88, 101, 242)  # Discord blue default
            
            # Use the new professional logo animation with effects
            if logo_path and logo_path.exists():
                final_video_path = await render_logo_anim_new(
                    logo_path=str(logo_path),
                    brand_name=brand_name,
                    bg_color=bg_color,
                    output_dir=work_dir,
                    fps=30,
                    duration=4.0,
                    outro_effect=effects.get("outro", "none"),
                    outro_repeat=outro_repeat
                )
                final_video = Path(final_video_path) if final_video_path else None
            else:
                # No logo uploaded - create text-only brand animation using universal effects
                logger.warning("No logo uploaded, creating brand text animation")
                from universal_effects import render_professional_video
                scenes = [
                    {
                        "type": "gradient_text",
                        "duration": 3.0,
                        "trans_in": 0.3,
                        "trans_out": 0.2,
                        "background": "black",
                        "content": {
                            "text": brand_name,
                            "colors": [[bg_color[0], bg_color[1], bg_color[2]], [min(255, bg_color[0]+50), min(255, bg_color[1]+50), min(255, bg_color[2]+50)]],
                            "shimmer": True
                        }
                    }
                ]
                final_video_path = await render_professional_video(scenes, work_dir, fps=30)
                final_video = Path(final_video_path) if final_video_path else None
            
            if final_video:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 70, "progress_message": "Генерируем озвучку..."}}
                )
                
                full_script = script_data.get("full_script", "")
                if full_script:
                    audio_url = await generate_tts(full_script)
                    if audio_url:
                        audio_path = UPLOADS_DIR / audio_url.split("/")[-1]
                        if audio_path.exists():
                            video_with_audio = await add_audio_to_video(final_video, audio_path, work_dir)
                            if video_with_audio:
                                final_video = video_with_audio
                
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ PRODUCT_ADVERTISEMENT FORMAT ============
        elif format_id == "product_advertisement":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 20, "progress_message": "Подготавливаем рекламу продукта..."}}
            )
            
            # Process uploaded product images
            product_image_paths = []
            uploaded_images = project.get("product_images", [])
            
            if uploaded_images:
                for img_url in uploaded_images:
                    if img_url.startswith("/api/uploads/"):
                        img_path = UPLOADS_DIR / img_url.split("/")[-1]
                        if img_path.exists():
                            product_image_paths.append(img_path)
            
            # If no uploaded images, generate AI images for product scenes
            if not product_image_paths:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 30, "progress_message": "Генерируем изображения продукта..."}}
                )
                
                for i, scene in enumerate(scenes):
                    if scene.get("image_prompt") and not scene.get("text_overlay"):
                        img_prompt = scene.get("image_prompt", "")
                        img_url = await generate_image(img_prompt)
                        if img_url:
                            img_path = UPLOADS_DIR / img_url.split("/")[-1]
                            if img_path.exists():
                                product_image_paths.append(img_path)
                        
                        await db.video_projects.update_one(
                            {"id": project_id},
                            {"$set": {"progress": 30 + int(20 * (i + 1) / len(scenes)), "progress_message": f"Сгенерировано {i+1}/{len(scenes)} изображений..."}}
                        )
            
            # Process logo
            logo_path = None
            logo_url = project.get("logo_url")
            if logo_url and logo_url.startswith("/api/uploads/"):
                logo_path = UPLOADS_DIR / logo_url.split("/")[-1]
                if not logo_path.exists():
                    logo_path = None
            
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 60, "progress_message": "Рендерим рекламный ролик..."}}
            )
            
            # Render product advertisement
            final_video = await render_product_advertisement(
                script_data, 
                work_dir,
                product_image_paths,
                logo_path
            )
            
            if final_video:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 80, "progress_message": "Генерируем озвучку..."}}
                )
                
                full_script = script_data.get("full_script", "")
                if full_script:
                    audio_url = await generate_tts(full_script)
                    if audio_url:
                        audio_path = UPLOADS_DIR / audio_url.split("/")[-1]
                        if audio_path.exists():
                            video_with_audio = await add_audio_to_video(final_video, audio_path, work_dir)
                            if video_with_audio:
                                final_video = video_with_audio
                
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ SPOTIFY/BRAND DEMO FORMAT (EXACT) ============
        elif format_id == "spotify_demo":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Создаём ТОЧНУЮ копию Spotify эффектов..."}}
            )
            
            original_prompt = project.get("prompt", "")
            brand_name = "Spotify"
            
            prompt_lower = original_prompt.lower()
            if "spotify" in prompt_lower:
                brand_name = "Spotify"
            elif "tiktok" in prompt_lower:
                brand_name = "TikTok"
            
            tagline = scenes[0].get("text", "Music for everyone") if scenes else "Music for everyone"
            
            script_data = {
                "brand_name": brand_name,
                "tagline": tagline
            }
            
            # Use EXACT renderer with aurora gradient and UI cards
            final_video_str = await render_spotify_exact(script_data, work_dir)
            final_video = Path(final_video_str)
            
            if final_video.exists():
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ SAAS/DASHBOARD DEMO FORMAT (PRO) ============
        elif format_id == "saas_demo":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Создаём SaaS демо с 3D карточками..."}}
            )
            
            headline = scenes[0].get("text", "Build something.") if scenes else "Build something."
            
            script_data = {
                "headline": headline
            }
            
            # Use PRO renderer with 3D cards and gradient
            final_video_str = await render_dashboard_style(script_data, work_dir)
            final_video = Path(final_video_str)
            
            if final_video.exists():
                poster_url = await generate_poster_image(final_video, work_dir)
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # ============ GAMEPLAY_CLIP FORMAT ============
        elif format_id == "gameplay_clip":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 20, "progress_message": "Скачиваем YouTube видео..."}}
            )
            
            # Download YouTube clip
            youtube_url = project.get("youtube_url", "")
            yt_clip = await download_youtube_clip(youtube_url, work_dir, duration=30)
            
            if not yt_clip:
                # Create placeholder if YouTube download fails
                logger.warning("YouTube download failed, creating placeholder")
                yt_clip = work_dir / "yt_placeholder.mp4"
                cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=0x1a1a2e:s=720x768:d=30", 
                       "-c:v", "libx264", "-preset", "ultrafast", str(yt_clip)]
                proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
                await proc.communicate()
            
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 50, "progress_message": "Создаём геймплей..."}}
            )
            
            # Create gameplay clip
            gameplay_type = project.get("gameplay_type", "minecraft_parkour")
            gameplay_clip = await create_gameplay_clip(gameplay_type, work_dir, duration=30)
            
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 70, "progress_message": "Собираем split-screen видео..."}}
            )
            
            # Create split screen video
            if yt_clip and gameplay_clip:
                final_video = await create_split_screen_video(
                    yt_clip, gameplay_clip, work_dir, subtitles=scenes
                )
                
                if final_video:
                    # Generate poster
                    poster_url = await generate_poster_image(final_video, work_dir)
                    
                    # Move to uploads
                    final_name = f"video_{project_id}.mp4"
                    final_path = UPLOADS_DIR / final_name
                    final_video.rename(final_path)
                    video_url = f"/api/uploads/{final_name}"
        
        # ============ UNIVERSAL AI-POWERED FORMAT ============
        else:
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 25, "progress_message": "AI анализирует и создаёт эффекты..."}}
            )
            
            # Generate universal script with AI
            universal_script = await generate_universal_script(project["prompt"], project["language"])
            
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 40, "progress_message": "Рендерим видео с эффектами..."}}
            )
            
            # Render with universal effects system
            final_video_str = await render_universal_video(universal_script, work_dir)
            final_video = Path(final_video_str) if final_video_str else None
            
            if final_video and final_video.exists():
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 85, "progress_message": "Финализируем видео..."}}
                )
                
                # Generate poster
                poster_url = await generate_poster_image(final_video, work_dir)
                
                # Move to uploads
                final_name = f"video_{project_id}.mp4"
                final_path = UPLOADS_DIR / final_name
                final_video.rename(final_path)
                video_url = f"/api/uploads/{final_name}"
        
        # Cleanup work directory
        cleanup_work_dir(work_dir)
        
        # Final update
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "progress_message": "Готово!",
                "scenes": scenes,
                "audio_url": audio_url,
                "video_url": video_url,
                "poster_url": poster_url,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        import traceback
        traceback.print_exc()
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "error",
                "error": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        # Cleanup on error
        cleanup_work_dir(work_dir)

# ==================== API ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "Slind AI API"}


# ==================== AUTH ROUTES ====================

from fastapi.responses import RedirectResponse, Response

# REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH

@api_router.post("/auth/session")
async def exchange_session(request: SessionRequest, response: Response):
    """Exchange session_id for session_token and user data"""
    try:
        # Call Emergent Auth to get user data
        async with httpx.AsyncClient() as client:
            auth_response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": request.session_id}
            )
            
            if auth_response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid session")
            
            auth_data = auth_response.json()
        
        email = auth_data["email"]
        session_token = auth_data["session_token"]
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": email}, {"_id": 0})
        
        if existing_user:
            user_id = existing_user["user_id"]
            # Update user data if needed
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": {
                    "name": auth_data["name"],
                    "picture": auth_data.get("picture"),
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
        else:
            # Create new user
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            username = f"@{auth_data['name'].lower().replace(' ', '')}{uuid.uuid4().hex[:4]}"
            
            new_user = {
                "user_id": user_id,
                "email": email,
                "name": auth_data["name"],
                "picture": auth_data.get("picture"),
                "username": username,
                "plan": "free",
                "credits": 100,
                "created_at": datetime.now(timezone.utc)
            }
            await db.users.insert_one(new_user)
        
        # Create session
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        session_doc = {
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at,
            "created_at": datetime.now(timezone.utc)
        }
        
        # Delete old sessions for this user
        await db.user_sessions.delete_many({"user_id": user_id})
        await db.user_sessions.insert_one(session_doc)
        
        # Get updated user
        user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="none",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auth error: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@api_router.get("/auth/me")
async def get_current_user(request: Request):
    """Get current authenticated user"""
    # Get session token from cookie or header
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Find session
    session_doc = await db.user_sessions.find_one(
        {"session_token": session_token}, 
        {"_id": 0}
    )
    
    if not session_doc:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check expiry
    expires_at = session_doc["expires_at"]
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    # Get user
    user = await db.users.find_one(
        {"user_id": session_doc["user_id"]}, 
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_many({"session_token": session_token})
    
    response.delete_cookie(key="session_token", path="/")
    return {"message": "Logged out"}


# ==================== EMAIL AUTH ROUTES ====================

class EmailAuthRequest(BaseModel):
    email: str
    password: str


@api_router.post("/auth/register")
async def register_with_email(request: EmailAuthRequest):
    """Register new user with email and password"""
    import hashlib
    
    email = request.email.strip().lower()
    password = request.password
    
    # Validate email format
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # Create user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    name = email.split("@")[0]
    username = f"@{name}{uuid.uuid4().hex[:4]}"
    
    new_user = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "password_hash": password_hash,
        "picture": None,
        "username": username,
        "plan": "free",
        "credits": 100,
        "auth_type": "email",
        "created_at": datetime.now(timezone.utc)
    }
    await db.users.insert_one(new_user)
    
    # Create session
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    session_doc = {
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Return user data (without password_hash)
    return {
        "user_id": user_id,
        "email": email,
        "name": name,
        "username": username,
        "picture": None,
        "plan": "free",
        "credits": 100,
        "session_token": session_token
    }


@api_router.post("/auth/login")
async def login_with_email(request: EmailAuthRequest):
    """Login user with email and password"""
    import hashlib
    
    email = request.email.strip().lower()
    password = request.password
    
    logger.info(f"[LOGIN] Attempting login for email: {email}")
    
    # Find user
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user:
        logger.warning(f"[LOGIN] User not found: {email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    logger.info(f"[LOGIN] User found: {user.get('user_id')}, has_password_hash: {'password_hash' in user}")
    
    # Check if user has password (email auth)
    if "password_hash" not in user:
        logger.warning(f"[LOGIN] User {email} has no password_hash")
        raise HTTPException(status_code=401, detail="This account uses Google login")
    
    # Verify password
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    logger.info(f"[LOGIN] Computed hash: {password_hash[:20]}..., Stored hash: {user['password_hash'][:20]}...")
    if user["password_hash"] != password_hash:
        logger.warning(f"[LOGIN] Password mismatch for {email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create new session
    session_token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    # Delete old sessions
    await db.user_sessions.delete_many({"user_id": user["user_id"]})
    
    session_doc = {
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at,
        "created_at": datetime.now(timezone.utc)
    }
    await db.user_sessions.insert_one(session_doc)
    
    # Return user data (without password_hash)
    return {
        "user_id": user["user_id"],
        "email": user["email"],
        "name": user["name"],
        "username": user.get("username"),
        "picture": user.get("picture"),
        "plan": user.get("plan", "free"),
        "credits": user.get("credits", 100),
        "session_token": session_token
    }


# ==================== FORMAT ROUTES ====================
async def get_formats():
    """Get all video formats"""
    return {
        "formats": [f.model_dump() for f in VIDEO_FORMATS],
        "categories": FORMAT_CATEGORIES,
        "character_types": CHARACTER_TYPES,
        "gameplay_types": GAMEPLAY_TYPES
    }

@api_router.post("/video/generate")
async def generate_video(request: VideoGenerateRequest, background_tasks: BackgroundTasks):
    """Start video generation"""
    print(f"[VIDEO/GENERATE] prompt={request.prompt}, user_id={request.user_id}")
    
    project = VideoProject(
        prompt=request.prompt,
        format_id=request.format_id,
        language=request.language,
        youtube_url=request.youtube_url,
        character_type=request.character_type,
        gameplay_type=request.gameplay_type,
        product_images=request.product_images,
        logo_url=request.logo_url,
        brand_name=request.brand_name,
        user_id=request.user_id
    )
    
    # Save to DB
    doc = project.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    logger.info(f"[VIDEO/GENERATE] Saving project {project.id} with created_at: {doc['created_at']}")
    result = await db.video_projects.insert_one(doc)
    print(f"[VIDEO/GENERATE] Saved to DB: {result.inserted_id}")
    
    # Start background processing
    background_tasks.add_task(process_video_generation, project.id)
    
    return {"id": project.id, "status": "pending"}


@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (product image, logo, video, audio)"""
    # Validate file type - allow images, videos, and audio
    allowed_image_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"]
    allowed_video_types = ["video/mp4", "video/quicktime", "video/webm", "video/x-msvideo", "video/avi", "video/mov", "video/mpeg"]
    allowed_audio_types = ["audio/mpeg", "audio/mp3", "audio/wav", "audio/ogg", "audio/aac", "audio/x-m4a", "audio/mp4"]
    allowed_types = allowed_image_types + allowed_video_types + allowed_audio_types
    
    # Also check by file extension as fallback (some browsers send wrong content_type)
    ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    allowed_extensions = ["png", "jpg", "jpeg", "webp", "gif", "mp4", "mov", "webm", "avi", "mpeg", "mp3", "wav", "ogg", "aac", "m4a"]
    
    is_allowed = file.content_type in allowed_types or ext in allowed_extensions
    if not is_allowed:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Content-Type: {file.content_type}, Extension: {ext}")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOADS_DIR / filename
    
    # Save file with streaming (better for large files)
    try:
        with open(file_path, "wb") as f:
            # Read in chunks to handle large files
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                f.write(chunk)
        
        file_size = file_path.stat().st_size
        
        return {
            "url": f"/api/uploads/{filename}",
            "filename": filename,
            "content_type": file.content_type,
            "size": file_size
        }
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


class ChunkUploadInit(BaseModel):
    filename: str
    total_size: int
    total_chunks: int


class ChunkUploadData(BaseModel):
    upload_id: str
    chunk_index: int
    data: str  # base64 encoded chunk


@api_router.post("/upload/init")
async def init_chunked_upload(request: ChunkUploadInit):
    """Initialize a chunked upload session"""
    upload_id = str(uuid.uuid4())
    ext = request.filename.split(".")[-1].lower() if "." in request.filename else "mp4"
    
    # Create upload session in DB
    session = {
        "upload_id": upload_id,
        "filename": request.filename,
        "ext": ext,
        "total_size": request.total_size,
        "total_chunks": request.total_chunks,
        "received_chunks": [],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.upload_sessions.insert_one(session)
    
    # Create temp directory for chunks
    chunk_dir = UPLOADS_DIR / f"chunks_{upload_id}"
    chunk_dir.mkdir(exist_ok=True)
    
    return {"upload_id": upload_id, "status": "ready"}


@api_router.post("/upload/chunk")
async def upload_chunk(request: ChunkUploadData):
    """Upload a single chunk"""
    session = await db.upload_sessions.find_one({"upload_id": request.upload_id})
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    chunk_dir = UPLOADS_DIR / f"chunks_{request.upload_id}"
    if not chunk_dir.exists():
        chunk_dir.mkdir(exist_ok=True)
    
    # Decode and save chunk
    try:
        chunk_data = base64.b64decode(request.data)
        chunk_path = chunk_dir / f"chunk_{request.chunk_index:05d}"
        with open(chunk_path, "wb") as f:
            f.write(chunk_data)
        
        # Update session
        await db.upload_sessions.update_one(
            {"upload_id": request.upload_id},
            {"$push": {"received_chunks": request.chunk_index}}
        )
        
        return {"status": "ok", "chunk_index": request.chunk_index}
    except Exception as e:
        logger.error(f"Chunk upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/upload/complete")
async def complete_chunked_upload(upload_id: str):
    """Complete chunked upload by merging all chunks"""
    session = await db.upload_sessions.find_one({"upload_id": upload_id})
    if not session:
        raise HTTPException(status_code=404, detail="Upload session not found")
    
    chunk_dir = UPLOADS_DIR / f"chunks_{upload_id}"
    ext = session.get("ext", "mp4")
    filename = f"{uuid.uuid4()}.{ext}"
    final_path = UPLOADS_DIR / filename
    
    try:
        # Merge all chunks
        with open(final_path, "wb") as outfile:
            for i in range(session["total_chunks"]):
                chunk_path = chunk_dir / f"chunk_{i:05d}"
                if chunk_path.exists():
                    with open(chunk_path, "rb") as chunk_file:
                        outfile.write(chunk_file.read())
        
        # Cleanup chunks
        import shutil
        shutil.rmtree(chunk_dir, ignore_errors=True)
        
        # Delete session
        await db.upload_sessions.delete_one({"upload_id": upload_id})
        
        file_size = final_path.stat().st_size
        
        return {
            "url": f"/api/uploads/{filename}",
            "filename": filename,
            "size": file_size
        }
    except Exception as e:
        logger.error(f"Chunk merge failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/video/{project_id}")
async def get_video_project(project_id: str):
    """Get video project status and data"""
    project = await db.video_projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@api_router.get("/videos")
async def get_all_videos():
    """Get all video projects"""
    projects = await db.video_projects.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"projects": projects}


@api_router.get("/videos/user/{user_id}")
async def get_user_videos(user_id: str):
    """Get video projects for a specific user"""
    projects = await db.video_projects.find(
        {"user_id": user_id}, 
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return {"projects": projects}


class UpdateVideoRequest(BaseModel):
    prompt: Optional[str] = None
    title: Optional[str] = None


@api_router.patch("/videos/{video_id}")
async def update_video(video_id: str, request: UpdateVideoRequest):
    """Rename/update a video project"""
    update_data = {}
    if request.prompt is not None:
        update_data["prompt"] = request.prompt.strip()
    if request.title is not None:
        update_data["title"] = request.title.strip()

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await db.video_projects.update_one(
        {"id": video_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"success": True, "updated": update_data}


@api_router.delete("/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete a video project"""
    result = await db.video_projects.delete_one({"id": video_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Video not found")
    return {"success": True}


@api_router.post("/voice/transcribe")
async def transcribe_voice(file: UploadFile = File(...), language: Optional[str] = None):
    """Transcribe voice recording to text via OpenAI Whisper (Emergent LLM Key)"""
    from emergentintegrations.llm.openai import OpenAISpeechToText
    import tempfile

    emergent_key = os.environ.get("EMERGENT_LLM_KEY")
    if not emergent_key:
        raise HTTPException(status_code=500, detail="EMERGENT_LLM_KEY not configured")

    # Persist upload to a temp file with correct extension so Whisper accepts it
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty audio file")

    suffix = ".webm"
    if file.filename:
        for ext in (".webm", ".mp3", ".mp4", ".m4a", ".wav", ".mpeg", ".mpga"):
            if file.filename.lower().endswith(ext):
                suffix = ext
                break

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(content)
        tmp.flush()
        tmp.close()

        stt = OpenAISpeechToText(api_key=emergent_key)
        with open(tmp.name, "rb") as audio_file:
            kwargs = {"file": audio_file, "model": "whisper-1", "response_format": "json"}
            if language:
                kwargs["language"] = language
            response = await stt.transcribe(**kwargs)

        text = getattr(response, "text", "") or ""
        return {"text": text.strip()}
    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Whisper transcription failed")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        try:
            os.unlink(tmp.name)
        except Exception:
            pass


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    username: Optional[str] = None
    picture: Optional[str] = None


@api_router.put("/users/{user_id}")
async def update_user(user_id: str, request: UpdateUserRequest):
    """Update user profile"""
    update_data = {}
    
    if request.name is not None:
        update_data["name"] = request.name.strip()
    
    if request.username is not None:
        new_username = request.username.strip().lower()
        if len(new_username) < 3:
            raise HTTPException(status_code=400, detail="Username must be at least 3 characters")
        # Check if username is taken by another user
        existing = await db.users.find_one({"username": new_username, "user_id": {"$ne": user_id}})
        if existing:
            raise HTTPException(status_code=400, detail="Username already taken")
        update_data["username"] = new_username
    
    if request.picture is not None:
        update_data["picture"] = request.picture
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await db.users.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Return updated user data
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    return user


# ==================== USERNAME CHECK ====================

@api_router.get("/users/check-username/{username}")
async def check_username(username: str, exclude_user_id: Optional[str] = None):
    """Check if a username is available"""
    username = username.strip().lower()
    if len(username) < 3:
        return {"available": False, "reason": "Username must be at least 3 characters"}
    
    query = {"username": username}
    if exclude_user_id:
        query["user_id"] = {"$ne": exclude_user_id}
    
    existing = await db.users.find_one(query)
    return {"available": existing is None}


# ==================== TEAM & INVITATIONS ====================

class TeamInviteRequest(BaseModel):
    username: str


@api_router.get("/users/{user_id}/team")
async def get_user_team(user_id: str):
    """Get user's team members"""
    team_members = await db.team_members.find(
        {"owner_id": user_id},
        {"_id": 0}
    ).to_list(50)
    
    # Get member details
    members_with_info = []
    for member in team_members:
        user_info = await db.users.find_one(
            {"user_id": member["member_id"]},
            {"_id": 0, "password_hash": 0, "user_id": 1, "name": 1, "username": 1, "picture": 1}
        )
        if user_info:
            members_with_info.append({
                **member,
                "member_info": user_info
            })
    
    return {"team": members_with_info}


@api_router.post("/users/{user_id}/team/invite")
async def invite_to_team(user_id: str, request: TeamInviteRequest):
    """Send team invitation to a user by username"""
    target_username = request.username.strip().lower()
    
    if len(target_username) < 3:
        raise HTTPException(status_code=400, detail="Invalid username")
    
    # Find target user
    target_user = await db.users.find_one({"username": target_username}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    target_user_id = target_user["user_id"]
    
    # Can't invite yourself
    if target_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot invite yourself")
    
    # Check if already in team
    existing_member = await db.team_members.find_one({
        "owner_id": user_id,
        "member_id": target_user_id
    })
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already in your team")
    
    # Check if invitation already sent
    existing_invite = await db.team_invites.find_one({
        "from_user_id": user_id,
        "to_user_id": target_user_id,
        "status": "pending"
    })
    if existing_invite:
        raise HTTPException(status_code=400, detail="Invitation already sent")
    
    # Get sender info
    sender = await db.users.find_one({"user_id": user_id}, {"_id": 0, "name": 1, "username": 1})
    
    # Create invitation
    invite_id = f"invite_{uuid.uuid4().hex[:12]}"
    invite = {
        "id": invite_id,
        "from_user_id": user_id,
        "from_username": sender.get("username", sender.get("name", "User")),
        "to_user_id": target_user_id,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.team_invites.insert_one(invite)
    
    # Create notification for target user
    notification_id = f"notif_{uuid.uuid4().hex[:12]}"
    notification = {
        "id": notification_id,
        "user_id": target_user_id,
        "type": "team_invite",
        "title": "Team Invitation",
        "message": f"@{sender.get('username', sender.get('name', 'Someone'))} invited you to their team",
        "data": {"invite_id": invite_id, "from_user_id": user_id},
        "read": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.notifications.insert_one(notification)
    
    return {"success": True, "invite_id": invite_id}


@api_router.post("/team/invites/{invite_id}/accept")
async def accept_team_invite(invite_id: str):
    """Accept a team invitation"""
    invite = await db.team_invites.find_one({"id": invite_id}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invite["status"] != "pending":
        raise HTTPException(status_code=400, detail="Invitation is no longer pending")
    
    # Add to team
    team_member = {
        "id": f"member_{uuid.uuid4().hex[:12]}",
        "owner_id": invite["from_user_id"],
        "member_id": invite["to_user_id"],
        "joined_at": datetime.now(timezone.utc).isoformat()
    }
    await db.team_members.insert_one(team_member)
    
    # Update invite status
    await db.team_invites.update_one(
        {"id": invite_id},
        {"$set": {"status": "accepted"}}
    )
    
    return {"success": True}


@api_router.post("/team/invites/{invite_id}/decline")
async def decline_team_invite(invite_id: str):
    """Decline a team invitation"""
    result = await db.team_invites.update_one(
        {"id": invite_id, "status": "pending"},
        {"$set": {"status": "declined"}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invitation not found or already processed")
    
    return {"success": True}


@api_router.delete("/users/{user_id}/team/{member_id}")
async def remove_team_member(user_id: str, member_id: str):
    """Remove a member from team"""
    result = await db.team_members.delete_one({
        "owner_id": user_id,
        "member_id": member_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Team member not found")
    
    return {"success": True}


# ==================== NOTIFICATIONS ====================

@api_router.get("/users/{user_id}/notifications")
async def get_user_notifications(user_id: str, limit: int = 50):
    """Get user's notifications"""
    notifications = await db.notifications.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(limit)
    
    unread_count = await db.notifications.count_documents({
        "user_id": user_id,
        "read": False
    })
    
    return {"notifications": notifications, "unread_count": unread_count}


@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"success": True}


@api_router.put("/users/{user_id}/notifications/read-all")
async def mark_all_notifications_read(user_id: str):
    """Mark all user's notifications as read"""
    await db.notifications.update_many(
        {"user_id": user_id, "read": False},
        {"$set": {"read": True}}
    )
    
    return {"success": True}


@api_router.get("/uploads/{filename}")
async def get_upload(filename: str):
    """Serve uploaded files"""
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    media_types = {
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "webp": "image/webp",
        "gif": "image/gif",
        "mp4": "video/mp4",
        "mov": "video/quicktime",
        "webm": "video/webm",
        "avi": "video/x-msvideo",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "aac": "audio/aac",
        "m4a": "audio/mp4"
    }
    media_type = media_types.get(ext, "application/octet-stream")
    
    return FileResponse(file_path, media_type=media_type)


# ==================== SUBSCRIPTION PLANS ====================

SUBSCRIPTION_PLANS = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "name_ru": "Стартовый",
        "price": 7.99,
        "currency": "usd",
        "features": ["10 видео/месяц", "720p качество", "Базовые форматы"],
        "features_en": ["10 videos/month", "720p quality", "Basic formats"],
        "videos_per_month": 10
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "name_ru": "Про",
        "price": 19.00,
        "currency": "usd",
        "features": ["50 видео/месяц", "1080p качество", "Все форматы", "Приоритетная генерация"],
        "features_en": ["50 videos/month", "1080p quality", "All formats", "Priority generation"],
        "videos_per_month": 50
    },
    "unlimited": {
        "id": "unlimited",
        "name": "Unlimited",
        "name_ru": "Безлимит",
        "price": 79.00,
        "currency": "usd",
        "features": ["Безлимитные видео", "4K качество", "Все форматы", "API доступ", "Приоритетная поддержка"],
        "features_en": ["Unlimited videos", "4K quality", "All formats", "API access", "Priority support"],
        "videos_per_month": -1  # -1 = unlimited
    }
}


class SubscriptionRequest(BaseModel):
    plan_id: str
    origin_url: str


@api_router.get("/subscription/plans")
async def get_subscription_plans():
    """Get available subscription plans"""
    return {"plans": list(SUBSCRIPTION_PLANS.values())}


@api_router.post("/subscription/checkout")
async def create_subscription_checkout(request: SubscriptionRequest, http_request: Request):
    """Create a Stripe checkout session for subscription"""
    plan_id = request.plan_id
    origin_url = request.origin_url.rstrip('/')
    
    if plan_id not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid subscription plan")
    
    plan = SUBSCRIPTION_PLANS[plan_id]
    
    # Initialize Stripe
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Build URLs
    success_url = f"{origin_url}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(plan["price"]),
        currency=plan["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "videos_per_month": str(plan["videos_per_month"])
        }
    )
    
    try:
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "session_id": session.session_id,
            "plan_id": plan_id,
            "amount": plan["price"],
            "currency": plan["currency"],
            "payment_status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        await db.payment_transactions.insert_one(transaction)
        
        return {
            "url": session.url,
            "session_id": session.session_id
        }
    except Exception as e:
        logger.error(f"Stripe checkout error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/subscription/status/{session_id}")
async def get_subscription_status(session_id: str, http_request: Request):
    """Check subscription payment status"""
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    host_url = str(http_request.base_url).rstrip('/')
    webhook_url = f"{host_url}api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    try:
        status: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction in database
        if status.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": "paid",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency,
            "metadata": status.metadata
        }
    except Exception as e:
        logger.error(f"Stripe status check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks"""
    stripe_api_key = os.getenv("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update transaction based on webhook event
        if webhook_response.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": "paid",
                        "event_type": webhook_response.event_type,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ==================== MONTAGE ENDPOINTS ====================

@api_router.get("/montage/styles")
async def get_montage_styles():
    """Get available montage styles"""
    styles = []
    for style_id, config in MONTAGE_STYLES.items():
        styles.append({
            "id": style_id,
            "name": config["name"],
            "name_ru": config["name_ru"],
            "clip_duration": config["clip_duration"],
            "transitions": config["transitions"]
        })
    return {"styles": styles}


# =============================================================
# DEVICE MOCKUP VIDEO - Show video on 3D device
# =============================================================

class DeviceMockupRequest(BaseModel):
    """Request to create device mockup video"""
    video_url: str  # URL of uploaded video to show on device
    device_type: str = "phone"  # phone, tablet, laptop
    rotation: float = 12  # Base 3D rotation angle
    bg_color: List[int] = [80, 20, 20]  # Background gradient start color (dark red like reference)
    bg_color2: List[int] = None  # Background gradient end color (optional, auto-generated if not set)
    animation_style: str = "camera"  # "camera" (zoom+rotate), "float" (simple), "phone_text" (with text)
    text: str = ""  # Text to show alongside phone (for phone_text style)
    phone_position: str = "center"  # "center", "left", "right" - position of phone
    aspect_ratio: str = "9:16"  # "16:9" (landscape) or "9:16" (portrait)
    user_id: Optional[str] = None  # User ID for saving video to user account

@api_router.post("/device-mockup/create")
async def create_device_mockup(request: DeviceMockupRequest, background_tasks: BackgroundTasks):
    """
    Create video showing uploaded content on a 3D device (phone/tablet/laptop).
    Phone is ALWAYS FULLY VISIBLE - no cropping.
    
    Animation styles:
    - "camera": Camera movement animation (zoom + rotate) like reference video
    - "float": Simple floating animation with gentle movement
    - "phone_text": Phone on side with animated text
    
    Phone positions:
    - "center": Phone centered on screen
    - "left": Phone on left side
    - "right": Phone on right side
    """
    # Validate video exists
    video_url = request.video_url
    if not video_url.startswith("/api/uploads/"):
        raise HTTPException(status_code=400, detail="Invalid video URL. Upload video first.")
    
    video_filename = video_url.split("/")[-1]
    video_path = UPLOADS_DIR / video_filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found. Please upload again.")
    
    project_id = str(uuid.uuid4())
    
    style_desc = f"3D {request.device_type} ({request.animation_style})"
    if request.text:
        style_desc += f" + text: {request.text[:20]}..."
    
    # Create initial project record in DB so polling works
    current_time = datetime.now(timezone.utc).isoformat()
    logger.info(f"[DEVICE_MOCKUP] Creating project {project_id} at time: {current_time}")
    
    await db.video_projects.insert_one({
        "id": project_id,
        "prompt": style_desc,
        "format_id": "device_mockup",
        "user_id": request.user_id,
        "status": "processing",
        "progress": 10,
        "progress_message": "Создаём 3D анимацию...",
        "created_at": current_time,
        "updated_at": current_time
    })
    
    # Start background rendering
    background_tasks.add_task(
        process_device_mockup, 
        project_id, 
        str(video_path),
        request.device_type,
        request.rotation,
        tuple(request.bg_color),
        request.animation_style,
        request.text,
        request.phone_position,
        request.aspect_ratio
    )
    
    return {"id": project_id, "status": "processing"}


async def process_device_mockup(
    project_id: str, 
    video_path: str, 
    device_type: str,
    rotation: float,
    bg_color: tuple,
    animation_style: str = "reference",
    text: str = "",
    phone_position: str = "right",
    aspect_ratio: str = "16:9"
):
    """Background task to render video on device mockup"""
    try:
        logger.info(f"Starting device mockup render: {project_id} ({animation_style}, {aspect_ratio})")
        
        result = await render_video_on_device(
            video_path=video_path,
            output_dir=UPLOADS_DIR,
            device_type=device_type,
            rotation_y=rotation,
            fps=30,
            bg_color=bg_color,
            animation_style=animation_style,
            text=text,
            phone_position=phone_position,
            aspect_ratio=aspect_ratio
        )
        
        if result:
            # Move to final location
            final_name = f"device_{project_id}.mp4"
            final_path = UPLOADS_DIR / final_name
            Path(result).rename(final_path)
            video_url = f"/api/uploads/{final_name}"
            
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {
                    "status": "completed", 
                    "video_url": video_url,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }},
                upsert=True
            )
            logger.info(f"Device mockup done: {video_url}")
        else:
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"status": "failed", "error": "Render failed"}},
                upsert=True
            )
    except Exception as e:
        logger.error(f"Device mockup error: {e}")
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "failed", "error": str(e)}},
            upsert=True
        )


@api_router.post("/montage/create")
async def create_montage_project(request: MontageRequest, background_tasks: BackgroundTasks):
    """Start montage creation from uploaded video with AI prompt analysis"""
    
    # Validate video exists
    video_url = request.video_url
    if not video_url.startswith("/api/uploads/"):
        raise HTTPException(status_code=400, detail="Invalid video URL. Please upload a video first.")
    
    video_filename = video_url.split("/")[-1]
    video_path = UPLOADS_DIR / video_filename
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video not found. Please upload again.")
    
    # Detect style from prompt if auto
    style = request.style
    if style == "auto" and request.prompt:
        prompt_lower = request.prompt.lower()
        if any(kw in prompt_lower for kw in ["мем", "мемы", "смешн", "funny", "meme", "comedy"]):
            style = "meme"
        elif any(kw in prompt_lower for kw in ["кино", "cinematic", "элегант", "film"]):
            style = "cinematic"
        elif any(kw in prompt_lower for kw in ["youtube", "длинн", "обзор"]):
            style = "youtube"
        else:
            style = "tiktok"  # default for dynamic/fast content
    
    project = MontageProject(
        source_video_url=video_url,
        prompt=request.prompt,
        style=style,
        music_url=request.music_url
    )
    
    # Save to DB
    doc = project.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.montage_projects.insert_one(doc)
    
    # Start background processing
    background_tasks.add_task(process_montage, project.id, request.prompt, request.text_overlays)
    
    return {"id": project.id, "status": "pending", "style": style}


@api_router.get("/montage/{montage_id}")
async def get_montage_status(montage_id: str):
    """Get montage project status"""
    project = await db.montage_projects.find_one({"id": montage_id}, {"_id": 0})
    
    if not project:
        raise HTTPException(status_code=404, detail="Montage project not found")
    
    return project


async def process_montage(project_id: str, prompt: Optional[str] = None, text_overlays: Optional[List[Dict]] = None):
    """Background task to process montage creation with AI prompt analysis"""
    try:
        project = await db.montage_projects.find_one({"id": project_id})
        if not project:
            return
        
        # Update status
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "processing", "progress": 5, "progress_message": "AI анализирует ваш запрос..."}}
        )
        
        # Get video path
        video_url = project["source_video_url"]
        video_filename = video_url.split("/")[-1]
        video_path = UPLOADS_DIR / video_filename
        
        if not video_path.exists():
            raise Exception("Source video not found")
        
        style = project.get("style", "tiktok")
        
        # Create work directory
        work_dir = UPLOADS_DIR / f"montage_{project_id}"
        work_dir.mkdir(exist_ok=True)
        
        # Quick video info check
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {"progress": 15, "progress_message": "Анализируем видео..."}}
        )
        
        # OPTIMIZED: Fast analysis without heavy AI
        analysis = await analyze_video_for_montage(video_path, style)
        
        num_clips = len(analysis.get('clips', []))
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {"progress": 30, "progress_message": f"Нарезаем {num_clips} клипов...", "analysis": analysis}}
        )
        
        # Get music path if provided
        music_path = None
        music_url = project.get("music_url")
        if music_url and music_url.startswith("/api/uploads/"):
            music_filename = music_url.split("/")[-1]
            music_path = UPLOADS_DIR / music_filename
            if not music_path.exists():
                music_path = None
        
        # Create montage - OPTIMIZED with progress updates
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {"progress": 50, "progress_message": "Собираем монтаж..."}}
        )
        
        montage_video = await create_montage(
            video_path,
            work_dir,
            style=style,
            music_path=music_path,
            analysis=analysis
        )
        
        if not montage_video:
            raise Exception("Не удалось создать монтаж")
        
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {"progress": 85, "progress_message": "Финальная обработка..."}}
        )
        
        # Skip text overlays for speed (can be added later)
        # Add text overlays if provided
        # if text_overlays:
        #     montage_video = await add_text_overlay(montage_video, work_dir, text_overlays)
        
        # Move to final location
        final_name = f"montage_{project_id}.mp4"
        final_path = UPLOADS_DIR / final_name
        
        try:
            if montage_video != final_path:
                import shutil
                shutil.copy2(montage_video, final_path)
        except Exception as e:
            logger.warning(f"Copy failed, trying rename: {e}")
            montage_video.rename(final_path)
        
        video_url = f"/api/uploads/{final_name}"
        
        # Cleanup work directory
        try:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
        except:
            pass
        
        # Update project
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "progress_message": "Готово!",
                "video_url": video_url,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logger.info(f"Montage completed: {project_id}")
        
    except Exception as e:
        logger.error(f"Montage processing failed: {e}")
        await db.montage_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "error",
                "error": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
