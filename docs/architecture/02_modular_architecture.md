# 2. МОДУЛЬНАЯ АРХИТЕКТУРА

## 2.1 Общая схема системы

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VIDFLUX AI STUDIO                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      FRONTEND LAYER                              │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │    │
│  │  │  Web    │  │ Mobile  │  │   API   │  │  SDK    │            │    │
│  │  │   App   │  │   App   │  │ Gateway │  │ Client  │            │    │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │    │
│  └───────┼────────────┼────────────┼────────────┼──────────────────┘    │
│          └────────────┴─────┬──────┴────────────┘                       │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    API GATEWAY / ROUTER                          │    │
│  │         Load Balancing │ Auth │ Rate Limiting │ Caching         │    │
│  └──────────────────────────────┬──────────────────────────────────┘    │
│                                 ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    AI ORCHESTRATOR (BRAIN)                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │    │
│  │  │   Prompt     │  │    Task      │  │   Resource   │          │    │
│  │  │ Interpreter  │  │  Scheduler   │  │  Optimizer   │          │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │    │
│  └──────────────────────────┬──────────────────────────────────────┘    │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    CONTENT ENGINES                               │    │
│  │                                                                   │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │    │
│  │  │  VIDEO  │ │ANIMATION│ │GRAPHICS │ │BRANDING │ │  TEXT   │   │    │
│  │  │ ENGINE  │ │ ENGINE  │ │ ENGINE  │ │ ENGINE  │ │ ENGINE  │   │    │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │    │
│  │       │           │           │           │           │         │    │
│  └───────┼───────────┼───────────┼───────────┼───────────┼─────────┘    │
│          └───────────┴─────┬─────┴───────────┴───────────┘              │
│                            ▼                                             │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      AI MODELS LAYER                             │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │    │
│  │  │  LLM   │ │ Image  │ │ Video  │ │ Audio  │ │ Voice  │        │    │
│  │  │ GPT-5  │ │NanoBan │ │ Sora   │ │ Music  │ │  TTS   │        │    │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                      DATA & STORAGE                              │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │    │
│  │  │MongoDB  │  │  Redis  │  │   S3    │  │   CDN   │            │    │
│  │  │Projects │  │  Cache  │  │ Assets  │  │ Delivery│            │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Независимые контент-движки

### VIDEO ENGINE

```python
class VideoEngine:
    """
    Полный движок генерации видео-контента
    """
    
    CAPABILITIES = [
        "generate_from_scratch",      # Генерация видео с нуля
        "auto_montage",               # Автоматический монтаж
        "talking_head",               # Говорящая голова с AI-аватаром
        "explainer_video",            # Объясняющие ролики
        "storytelling",               # Истории
        "ugc_style",                  # UGC стиль
        "advertisement",              # Рекламные креативы
        "tutorial",                   # Обучающие видео
        "highlight_extraction",       # Нарезка лучших моментов
        "broll_addition",             # Добавление B-roll
        "subtitle_generation",        # Генерация субтитров
        "translation",                # Автоперевод
        "voiceover",                  # Озвучка разными голосами
        "trend_montage"               # Монтаж под тренды
    ]
    
    MODULES = {
        "script_generator": ScriptModule,
        "storyboard_creator": StoryboardModule,
        "image_generator": ImageGenModule,
        "video_generator": VideoGenModule,
        "avatar_engine": AvatarModule,
        "lipsync_engine": LipsyncModule,
        "voiceover_engine": VoiceoverModule,
        "subtitle_engine": SubtitleModule,
        "montage_engine": MontageModule,
        "effects_engine": EffectsModule,
        "render_engine": RenderModule
    }
    
    FORMATS = {
        "tiktok": {"resolution": "1080x1920", "duration": "15-60s", "fps": 30},
        "reels": {"resolution": "1080x1920", "duration": "15-90s", "fps": 30},
        "shorts": {"resolution": "1080x1920", "duration": "15-60s", "fps": 30},
        "youtube": {"resolution": "1920x1080", "duration": "any", "fps": 30},
        "story": {"resolution": "1080x1920", "duration": "15s", "fps": 30},
        "square": {"resolution": "1080x1080", "duration": "any", "fps": 30}
    }
```

### ANIMATION ENGINE

```python
class AnimationEngine:
    """
    Движок анимации и motion graphics
    """
    
    CAPABILITIES = [
        "logo_animation",             # Анимация логотипа
        "text_animation",             # Анимация текста
        "motion_graphics",            # Motion graphics
        "infographic_animation",      # Анимированная инфографика
        "character_animation",        # Анимация персонажей
        "2d_animation",               # 2D анимация
        "3d_animation",               # 3D анимация (базовая)
        "loop_animation",             # Луп-анимации
        "intro_outro",                # Интро/аутро
        "ui_animation",               # Анимация интерфейсов
        "dialog_animation",           # Анимация диалогов
        "meme_animation"              # Мем-анимации
    ]
    
    MODULES = {
        "keyframe_engine": KeyframeModule,
        "easing_library": EasingModule,
        "particle_system": ParticleModule,
        "morphing_engine": MorphModule,
        "path_animator": PathModule,
        "character_rigger": RigModule,
        "expression_engine": ExpressionModule,
        "render_engine": AnimRenderModule
    }
```

### GRAPHICS ENGINE

```python
class GraphicsEngine:
    """
    Движок генерации статичной графики
    """
    
    CAPABILITIES = [
        "product_card",               # Карточки товаров
        "banner",                     # Баннеры
        "youtube_thumbnail",          # Превью YouTube
        "poster",                     # Постеры
        "social_post",                # Посты для соцсетей
        "ad_creative",                # Рекламные креативы
        "infographic",                # Инфографика
        "cover_art",                  # Обложки
        "presentation_slide",         # Слайды презентаций
        "email_graphics",             # Графика для email
        "marketplace_images"          # Изображения для маркетплейсов
    ]
    
    MODULES = {
        "layout_engine": LayoutModule,
        "image_generator": ImageGenModule,
        "typography_engine": TypographyModule,
        "color_engine": ColorModule,
        "effects_engine": GraphicEffectsModule,
        "template_engine": TemplateModule,
        "export_engine": ExportModule
    }
```

### BRANDING ENGINE

```python
class BrandingEngine:
    """
    Движок создания брендинга
    """
    
    CAPABILITIES = [
        "logo_design",                # Дизайн логотипа
        "brand_identity",             # Фирменный стиль
        "color_palette",              # Цветовая палитра
        "typography_system",          # Типографика
        "brand_guide",                # Бренд-гайд
        "mascot_design",              # Дизайн маскота
        "packaging_design",           # Упаковка
        "business_card",              # Визитки
        "letterhead",                 # Фирменный бланк
        "social_kit"                  # Комплект для соцсетей
    ]
    
    MODULES = {
        "concept_generator": ConceptModule,
        "logo_generator": LogoGenModule,
        "color_theory_engine": ColorTheoryModule,
        "font_selector": FontModule,
        "mockup_engine": MockupModule,
        "guide_generator": GuideGenModule
    }
```

### TEXT ENGINE

```python
class TextEngine:
    """
    Движок генерации текстового контента
    """
    
    CAPABILITIES = [
        "script_writing",             # Сценарии
        "viral_format",               # Вирусные форматы
        "product_description",        # Описания товаров
        "storytelling",               # Сторителлинг
        "hooks_generation",           # Хуки
        "cta_generation",             # Call-to-action
        "content_plan",               # Контент-планы
        "dialog_writing",             # Диалоги
        "joke_generation",            # Шутки
        "meme_text",                  # Тексты для мемов
        "email_funnel",               # Email-воронки
        "auto_scenario"               # АВТО-СЦЕНАРИЙ (вирусное видео)
    ]
    
    AUTO_SCENARIO_PIPELINE = {
        "steps": [
            "niche_analysis",          # Анализ ниши
            "trend_detection",         # Определение трендов
            "viral_pattern_matching",  # Поиск вирусных паттернов
            "hook_generation",         # Генерация хука
            "story_arc_creation",      # Создание арки истории
            "cta_optimization",        # Оптимизация CTA
            "full_script_assembly",    # Сборка полного сценария
            "auto_production_trigger"  # Запуск автопроизводства
        ]
    }
```

## 2.3 Подключаемые модели

```python
MODEL_REGISTRY = {
    "llm": {
        "primary": "openai/gpt-5.2",
        "fallback": "anthropic/claude-sonnet-4.5",
        "fast": "openai/gpt-4o-mini",
        "creative": "anthropic/claude-opus-4.5"
    },
    "image_generation": {
        "primary": "gemini/nano-banana",
        "quality": "openai/gpt-image-1",
        "fast": "stability/sdxl-turbo"
    },
    "video_generation": {
        "primary": "openai/sora-2",
        "alternative": "runway/gen-3"
    },
    "voice": {
        "tts": "openai/tts-1-hd",
        "voice_clone": "elevenlabs/voice-clone",
        "multilingual": "openai/whisper"
    },
    "audio": {
        "music": "suno/v4",
        "sfx": "elevenlabs/sfx"
    },
    "avatar": {
        "talking_head": "heygen/avatar",
        "lipsync": "wav2lip/hd"
    }
}
```

## 2.4 Масштабируемые блоки

```
┌────────────────────────────────────────────────────────────────┐
│                    SCALABLE PROCESSING BLOCKS                   │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐   │
│  │  COMPUTE     │     │   QUEUE      │     │   STORAGE    │   │
│  │  CLUSTER     │     │   SYSTEM     │     │   CLUSTER    │   │
│  │              │     │              │     │              │   │
│  │ ┌──┐ ┌──┐   │     │  Redis/Bull  │     │  S3/MinIO    │   │
│  │ │W1│ │W2│   │◄───►│              │◄───►│              │   │
│  │ └──┘ └──┘   │     │ Priority Q   │     │ Hot/Cold     │   │
│  │ ┌──┐ ┌──┐   │     │ Retry Logic  │     │ Tiering      │   │
│  │ │W3│ │W4│   │     │ Dead Letter  │     │ CDN Cache    │   │
│  │ └──┘ └──┘   │     │              │     │              │   │
│  │   ↑ Auto    │     │              │     │              │   │
│  │   Scale     │     │              │     │              │   │
│  └──────────────┘     └──────────────┘     └──────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    GPU POOL                               │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │  │
│  │  │ Video   │  │ Image   │  │ Audio   │  │ General │     │  │
│  │  │ Render  │  │ Gen     │  │Process  │  │ Purpose │     │  │
│  │  │ A100x4  │  │ A100x2  │  │ T4x2    │  │ A10Gx4  │     │  │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```
