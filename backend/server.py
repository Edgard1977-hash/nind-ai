from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import asyncio
import base64
import json
import httpx

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
    render_product_advertisement
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
    """Smart AI engine - analyze prompt and auto-detect the best video type"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"detect-{uuid.uuid4()}",
            system_message="You are a smart content classifier for video generation."
        )
        chat.with_model("openai", "gpt-5.2")
        
        detection_prompt = f"""Analyze this user prompt and determine the best video type to create.

Available video types:
1. "chat_animation" - For dialog/conversation/messages animations (e.g., "make animation of chat with client", "show dialog between...", "animate our conversation", "переписка", "диалог", "сообщения")
2. "apple_text" - For minimalist text presentations like Apple style (e.g., "make text like Apple", "simple text animation", "презентация текста")
3. "kinetic_typography" - For dynamic word-by-word text animations (e.g., "animate words", "kinetic text", "слова по очереди")
4. "logo_animation" - For brand/logo reveal animations (e.g., "animate my logo", "brand intro", "анимация логотипа", "интро бренда")
5. "product_advertisement" - For product showcase/advertisement videos like Apple ads (e.g., "product ad", "реклама продукта", "реклама товара", "showcase product", "advertise my product", "MacBook ad style", "iPhone style ad", "показать товар", "рекламный ролик")
6. "news" - For news reports, current events, breaking news
7. "ai_story" - For stories, narratives, tales, fiction
8. "character_explainer" - For educational explanations with cute characters
9. "gameplay_clip" - For gaming content with YouTube clips

User prompt: "{prompt}"

Respond ONLY with a JSON object:
{{
    "format_id": "the_best_matching_type",
    "confidence": 0.0-1.0,
    "reason": "brief explanation",
    "detected_language": "ru" or "en",
    "extracted_data": {{}}
}}

Important rules:
- If user mentions dialog, chat, conversation, messages, or provides a conversation in brackets [] or quotes, choose "chat_animation"
- If user mentions Apple, minimalist text, presentation, choose "apple_text"
- If user mentions word animation, kinetic, dynamic text, choose "kinetic_typography"
- If user mentions logo, brand, intro, choose "logo_animation"
- If user mentions product ad, product advertisement, товар, реклама, showcase, commercial, or wants to advertise a physical product, choose "product_advertisement"
"""
        
        msg = UserMessage(text=detection_prompt)
        response = await chat.send_message(msg)
        
        # Parse JSON
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            result = json.loads(response[json_start:json_end])
            return result
    except Exception as e:
        logger.warning(f"Auto-detection failed, using fallback: {e}")
    
    # Fallback detection based on keywords
    prompt_lower = prompt.lower()
    
    # Check for chat/dialog keywords
    chat_keywords = ['диалог', 'сообщен', 'переписк', 'чат', 'chat', 'dialog', 'message', 'conversation', 'беседа']
    if any(kw in prompt_lower for kw in chat_keywords) or '[' in prompt or '«' in prompt:
        return {"format_id": "chat_animation", "confidence": 0.8, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Check for Apple/minimalist text
    apple_keywords = ['apple', 'минимал', 'презентац', 'текст простой', 'simple text']
    if any(kw in prompt_lower for kw in apple_keywords):
        return {"format_id": "apple_text", "confidence": 0.7, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Check for kinetic typography
    kinetic_keywords = ['kinetic', 'кинетик', 'слово за слов', 'word by word', 'динамич', 'типограф']
    if any(kw in prompt_lower for kw in kinetic_keywords):
        return {"format_id": "kinetic_typography", "confidence": 0.7, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Check for logo
    logo_keywords = ['лого', 'logo', 'бренд', 'brand', 'интро', 'intro']
    if any(kw in prompt_lower for kw in logo_keywords):
        return {"format_id": "logo_animation", "confidence": 0.7, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Check for product advertisement
    product_keywords = ['реклам', 'товар', 'продукт', 'product', 'advertis', 'showcase', 'commercial', 'macbook', 'iphone', 'показать продукт']
    if any(kw in prompt_lower for kw in product_keywords):
        return {"format_id": "product_advertisement", "confidence": 0.8, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Check for news
    news_keywords = ['новост', 'news', 'breaking', 'событи', 'сегодня', 'headline']
    if any(kw in prompt_lower for kw in news_keywords):
        return {"format_id": "news", "confidence": 0.7, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Check for story
    story_keywords = ['истор', 'story', 'расскажи', 'tell', 'tale', 'сказк']
    if any(kw in prompt_lower for kw in story_keywords):
        return {"format_id": "ai_story", "confidence": 0.7, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}
    
    # Default to ai_story
    return {"format_id": "ai_story", "confidence": 0.5, "detected_language": "ru" if any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя') else "en"}


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
            system_message="You follow user instructions EXACTLY. Never translate, never add extra content."
        )
        chat.with_model("openai", "gpt-5.2")
        
        system_prompt = f"""Create Apple-style minimalist text animation.

CRITICAL RULES:
1. Use EXACTLY the text the user provides - DO NOT translate it
2. DO NOT add text that user didn't ask for
3. If user specifies colors (like "blue gradient", "голубой"), use those EXACT colors
4. Keep the EXACT language user wrote in - if they wrote "Go make content", keep it as "Go make content"

Style: Clean, bold, impactful. Like Apple keynotes.
- Alternating white and black backgrounds
- One underlined word for emphasis (optional)

Color codes for gradients:
- "голубо-синий" / "blue" = ["#00D4FF", "#0066FF"]
- "зелёный" / "green" = ["#00FF87", "#00D4AA"]  
- "фиолетовый" / "purple" = ["#9D4EDD", "#7B2CBF"]
- "оранжевый" / "orange" = ["#FF6B35", "#FF8C42"]

Return JSON:
{{
    "title": "Title from user prompt",
    "phrases": [
        {{"text": "EXACT user text phrase 1", "bg": "white"}},
        {{"text": "EXACT user text phrase 2", "bg": "black"}},
        {{"text": "Brand/Final text", "bg": "white", "gradient_colors": ["#color1", "#color2"]}}
    ],
    "full_script": "All text for TTS"
}}

If user asks for gradient on brand name at the end, add "gradient_colors" to that phrase.

User prompt: {prompt}"""
        
        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"Apple text script generation failed: {e}")
    
    # Fallback
    if is_russian:
        return {
            "title": "Презентация",
            "phrases": [
                {"text": "Давайте создадим", "bg": "white"},
                {"text": "Что-то невероятное", "bg": "white"},
                {"text": "Просто. Чисто.", "bg": "black"},
                {"text": "Как Apple.", "bg": "white", "underline": "Apple"}
            ],
            "full_script": "Давайте создадим что-то невероятное. Просто. Чисто. Как Apple."
        }
    else:
        return {
            "title": "Presentation",
            "phrases": [
                {"text": "Let's create", "bg": "white"},
                {"text": "Something amazing", "bg": "white"},
                {"text": "Simple. Clean.", "bg": "black"},
                {"text": "Like Apple.", "bg": "white", "underline": "Apple"}
            ],
            "full_script": "Let's create something amazing. Simple. Clean. Like Apple."
        }


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


async def generate_logo_animation_script(prompt: str, language: str) -> dict:
    """Generate script for logo animation"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.getenv("EMERGENT_LLM_KEY")
    is_russian = language == "ru" or (language == "auto" and any(c in prompt for c in 'абвгдежзийклмнопрстуфхцчшщъыьэюя'))
    
    try:
        chat = LlmChat(
            api_key=api_key,
            session_id=f"logo-{uuid.uuid4()}",
            system_message="You help create brand identity and logo animation content."
        )
        chat.with_model("openai", "gpt-5.2")
        
        lang_instruction = "Respond in Russian." if is_russian else "Respond in English."
        
        system_prompt = f"""Create content for a logo/brand animation.
{lang_instruction}

Extract or suggest:
- Brand name from the prompt
- Optional tagline
- Brand colors (suggest modern, appealing colors)

Return JSON:
{{
    "title": "Brand Animation",
    "brand_name": "Brand Name",
    "tagline": "Optional tagline or slogan",
    "bg_color": "#7289da",
    "text_color": "#ffffff",
    "full_script": "Brand name and tagline for TTS"
}}

User prompt: {prompt}"""
        
        msg = UserMessage(text=system_prompt)
        response = await chat.send_message(msg)
        
        json_start = response.find('{')
        json_end = response.rfind('}') + 1
        if json_start != -1 and json_end > json_start:
            return json.loads(response[json_start:json_end])
    except Exception as e:
        logger.warning(f"Logo animation script generation failed: {e}")
    
    # Fallback - extract brand name from prompt
    words = prompt.split()
    brand_name = words[0].capitalize() if words else "Brand"
    
    return {
        "title": f"{brand_name} Animation",
        "brand_name": brand_name,
        "tagline": "",
        "bg_color": "#7289da",
        "text_color": "#ffffff",
        "full_script": brand_name
    }


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
    
    try:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        chat = LlmChat(
            api_key=api_key,
            session_id=f"img-{uuid.uuid4()}",
            system_message="You are a helpful AI assistant"
        )
        chat.with_model("gemini", "gemini-3-pro-image-preview").with_params(modalities=["image", "text"])
        
        msg = UserMessage(text=f"Generate a professional, high-quality vertical image (9:16 aspect ratio) for video content: {prompt}")
        
        text, images = await chat.send_message_multimodal_response(msg)
        
        if images and len(images) > 0:
            # Save image to file
            img_id = str(uuid.uuid4())
            img_path = UPLOADS_DIR / f"{img_id}.png"
            image_bytes = base64.b64decode(images[0]['data'])
            with open(img_path, "wb") as f:
                f.write(image_bytes)
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
        if format_id == "chat_animation":
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
        
        # ============ CHAT_ANIMATION FORMAT ============
        if format_id == "chat_animation":
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": 30, "progress_message": "Рендерим анимацию диалога..."}}
            )
            
            # Use professional PIL renderer
            final_video = await render_chat_animation(script_data, work_dir)
            
            if final_video:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 70, "progress_message": "Генерируем озвучку..."}}
                )
                
                # Generate TTS for narration
                full_script = script_data.get("full_script", "")
                if full_script:
                    audio_url = await generate_tts(full_script)
                    
                    if audio_url:
                        await db.video_projects.update_one(
                            {"id": project_id},
                            {"$set": {"progress": 85, "progress_message": "Добавляем озвучку..."}}
                        )
                        
                        audio_path = UPLOADS_DIR / audio_url.split("/")[-1]
                        if audio_path.exists():
                            video_with_audio = await add_audio_to_video(final_video, audio_path, work_dir)
                            if video_with_audio:
                                final_video = video_with_audio
                
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
            
            # Use professional PIL renderer
            final_video = await render_apple_text_animation(script_data, work_dir)
            
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
            
            # Use professional PIL renderer
            final_video = await render_logo_animation(script_data, work_dir)
            
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
        
        # ============ OTHER FORMATS (with images) ============
        else:
            # Generate images and create video scenes
            scene_videos = []
            total_scenes = len(scenes)
            
            for i, scene in enumerate(scenes):
                progress = 20 + int((i / max(total_scenes, 1)) * 40)
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": progress, "progress_message": f"Генерируем сцену {i+1}/{total_scenes}..."}}
                )
                
                # Generate image
                image_url = await generate_image(scene.get("image_prompt", scene.get("text", "")))
                scene["image_url"] = image_url
                
                # Create video from image with Ken Burns effect
                if image_url:
                    full_image_url = f"http://localhost:8001{image_url}"
                    scene_video = await create_image_video(
                        full_image_url, 
                        work_dir, 
                        duration=scene.get("duration", 4.0),
                        animation=scene.get("animation", "zoom_in")
                    )
                    if scene_video:
                        scene_videos.append(scene_video)
                
                await asyncio.sleep(0.5)
            
            # Concatenate all scene videos
            if scene_videos:
                await db.video_projects.update_one(
                    {"id": project_id},
                    {"$set": {"progress": 65, "progress_message": "Собираем видео..."}}
                )
                
                concat_video = await concatenate_videos(scene_videos, work_dir)
                
                if concat_video:
                    # Add subtitles
                    await db.video_projects.update_one(
                        {"id": project_id},
                        {"$set": {"progress": 75, "progress_message": "Добавляем субтитры..."}}
                    )
                    
                    # Create subtitle timing based on scenes
                    subtitles = []
                    current_time = 0
                    for scene in scenes:
                        duration = scene.get("duration", 4.0)
                        subtitles.append({
                            "text": scene.get("text", ""),
                            "timestamp_start": current_time,
                            "timestamp_end": current_time + duration,
                            "highlight": scene.get("highlight", False)
                        })
                        current_time += duration
                    
                    subtitled_video = await add_subtitles_to_video(concat_video, subtitles, work_dir)
                    final_video = subtitled_video or concat_video
                    
                    # Generate TTS
                    await db.video_projects.update_one(
                        {"id": project_id},
                        {"$set": {"progress": 85, "progress_message": "Генерируем озвучку..."}}
                    )
                    
                    full_script = script_data.get("full_script", " ".join([s.get("text", "") for s in scenes]))
                    audio_url = await generate_tts(full_script)
                    
                    # Add audio to video
                    if audio_url:
                        await db.video_projects.update_one(
                            {"id": project_id},
                            {"$set": {"progress": 92, "progress_message": "Добавляем озвучку к видео..."}}
                        )
                        
                        audio_path = UPLOADS_DIR / audio_url.split("/")[-1]
                        if audio_path.exists():
                            video_with_audio = await add_audio_to_video(final_video, audio_path, work_dir)
                            if video_with_audio:
                                final_video = video_with_audio
                    
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
    return {"message": "VidFlux AI API"}

@api_router.get("/formats")
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
    project = VideoProject(
        prompt=request.prompt,
        format_id=request.format_id,
        language=request.language,
        youtube_url=request.youtube_url,
        character_type=request.character_type,
        gameplay_type=request.gameplay_type,
        product_images=request.product_images,
        logo_url=request.logo_url,
        brand_name=request.brand_name
    )
    
    # Save to DB
    doc = project.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.video_projects.insert_one(doc)
    
    # Start background processing
    background_tasks.add_task(process_video_generation, project.id)
    
    return {"id": project.id, "status": "pending"}


@api_router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file (product image, logo, etc.)"""
    # Validate file type
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "video/mp4"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type not allowed. Allowed: {allowed_types}")
    
    # Generate unique filename
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    filename = f"{uuid.uuid4()}.{ext}"
    file_path = UPLOADS_DIR / filename
    
    # Save file
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    return {
        "url": f"/api/uploads/{filename}",
        "filename": filename,
        "content_type": file.content_type,
        "size": len(content)
    }

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

@api_router.get("/uploads/{filename}")
async def get_upload(filename: str):
    """Serve uploaded files"""
    file_path = UPLOADS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on extension
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".mp4"):
        media_type = "video/mp4"
    elif filename.endswith(".mp3"):
        media_type = "audio/mpeg"
    elif filename.endswith(".wav"):
        media_type = "audio/wav"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(file_path, media_type=media_type)

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
