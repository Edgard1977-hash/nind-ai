from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks
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
    format_id: str
    language: str = "auto"

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
    status: str = "pending"
    progress: int = 0
    progress_message: str = "Инициализация..."
    scenes: List[dict] = []
    audio_url: Optional[str] = None
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
]

FORMAT_CATEGORIES = {
    "all": {"name": "Все", "name_en": "All"},
    "informational": {"name": "Информационные", "name_en": "Informational"},
    "entertainment": {"name": "Развлекательные", "name_en": "Entertainment"},
    "commercial": {"name": "Коммерческие", "name_en": "Commercial"},
}

# ==================== AI SERVICES ====================

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
    """Background task to process video generation"""
    try:
        # Get project from DB
        project = await db.video_projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            return
        
        # Update status
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"status": "processing", "progress": 10, "progress_message": "Анализируем промт..."}}
        )
        
        # Step 1: Generate script
        script_data = await analyze_prompt_and_generate_script(
            project["prompt"], 
            project["format_id"],
            project["language"]
        )
        
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "progress": 20, 
                "progress_message": "Генерируем изображения...",
                "script": script_data.get("full_script", ""),
                "title": script_data.get("title", project["prompt"][:50])
            }}
        )
        
        # Step 2: Generate images for each scene
        scenes = script_data.get("scenes", [])
        total_scenes = len(scenes)
        
        for i, scene in enumerate(scenes):
            progress = 20 + int((i / total_scenes) * 50)
            await db.video_projects.update_one(
                {"id": project_id},
                {"$set": {"progress": progress, "progress_message": f"Генерируем изображение {i+1}/{total_scenes}..."}}
            )
            
            image_url = await generate_image(scene.get("image_prompt", scene.get("text", "")))
            scene["image_url"] = image_url
            
            # Small delay to avoid rate limiting
            await asyncio.sleep(1)
        
        # Step 3: Generate TTS
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {"progress": 80, "progress_message": "Генерируем озвучку..."}}
        )
        
        full_script = script_data.get("full_script", " ".join([s.get("text", "") for s in scenes]))
        audio_url = await generate_tts(full_script)
        
        # Final update
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "completed",
                "progress": 100,
                "progress_message": "Готово!",
                "scenes": scenes,
                "audio_url": audio_url,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
    except Exception as e:
        logger.error(f"Video generation error: {e}")
        await db.video_projects.update_one(
            {"id": project_id},
            {"$set": {
                "status": "error",
                "error": str(e),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )

# ==================== API ROUTES ====================

@api_router.get("/")
async def root():
    return {"message": "VidFlux AI API"}

@api_router.get("/formats")
async def get_formats():
    """Get all video formats"""
    return {
        "formats": [f.model_dump() for f in VIDEO_FORMATS],
        "categories": FORMAT_CATEGORIES
    }

@api_router.post("/video/generate")
async def generate_video(request: VideoGenerateRequest, background_tasks: BackgroundTasks):
    """Start video generation"""
    project = VideoProject(
        prompt=request.prompt,
        format_id=request.format_id,
        language=request.language
    )
    
    # Save to DB
    doc = project.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.video_projects.insert_one(doc)
    
    # Start background processing
    background_tasks.add_task(process_video_generation, project.id)
    
    return {"id": project.id, "status": "pending"}

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
    
    media_type = "image/png" if filename.endswith(".png") else "audio/mpeg"
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
