# 🎬 VIDFLUX AI STUDIO - Архитектура универсального креативного движка

## Версия: 2.0 Architecture Blueprint
## Дата: Март 2026

---

# 1. УНИВЕРСАЛЬНЫЙ ИНТЕРПРЕТАТОР ПРОМТОВ

## 1.1 Система определения типа запроса

```
┌─────────────────────────────────────────────────────────────────┐
│                    PROMPT INTERPRETER ENGINE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Prompt ──► NLP Analyzer ──► Intent Classifier ──► Router  │
│                      │                   │                │      │
│                      ▼                   ▼                ▼      │
│              Entity Extraction    Category Detection   Pipeline  │
│              - Keywords           - Video              Selection │
│              - Entities           - Animation                    │
│              - Context            - Graphics                     │
│              - Tone               - Branding                     │
│              - Platform           - Text                         │
│              - Format             - Hybrid                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Intent Classification Model

```python
INTENT_CATEGORIES = {
    "video_generation": {
        "triggers": ["видео", "ролик", "клип", "тикток", "рилс", "шортс"],
        "sub_intents": [
            "from_scratch",      # Генерация с нуля
            "edit_existing",     # Монтаж загруженного
            "auto_montage",      # Автоматический монтаж
            "talking_head",      # Говорящая голова
            "explainer",         # Объяснение с персонажем
            "storytelling",      # История
            "advertisement",     # Реклама
            "ugc_style",         # UGC стиль
            "tutorial"           # Обучающее
        ]
    },
    "animation": {
        "triggers": ["анимация", "motion", "интро", "аутро", "лого анимация"],
        "sub_intents": [
            "logo_animation",
            "text_animation", 
            "character_animation",
            "motion_graphics",
            "infographic_animation",
            "loop_animation",
            "meme_animation"
        ]
    },
    "graphics": {
        "triggers": ["картинка", "баннер", "постер", "карточка", "превью"],
        "sub_intents": [
            "product_card",
            "banner",
            "youtube_thumbnail",
            "poster",
            "social_media_post",
            "ad_creative",
            "infographic"
        ]
    },
    "branding": {
        "triggers": ["лого", "бренд", "фирменный стиль", "айдентика"],
        "sub_intents": [
            "logo_design",
            "brand_identity",
            "color_palette",
            "brand_guide",
            "mascot_design",
            "packaging"
        ]
    },
    "text_content": {
        "triggers": ["сценарий", "текст", "история", "диалог", "описание"],
        "sub_intents": [
            "script",
            "viral_format",
            "product_description",
            "storytelling_text",
            "hooks_cta",
            "content_plan"
        ]
    },
    "hybrid": {
        "triggers": ["полный контент", "всё для", "комплексный"],
        "sub_intents": [
            "video_plus_graphics",
            "animation_plus_voiceover",
            "ai_influencer",
            "trend_based_content",
            "niche_content_pack"
        ]
    }
}
```

### Prompt Analysis Pipeline

```
┌────────────────────────────────────────────────────────────────────┐
│                      PROMPT ANALYSIS FLOW                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. TOKENIZATION & NLP                                              │
│     ├── Language detection (RU/EN/Multi)                           │
│     ├── Named Entity Recognition                                    │
│     ├── Keyword extraction                                          │
│     └── Sentiment analysis                                          │
│                                                                     │
│  2. CONTEXT EXTRACTION                                              │
│     ├── Platform detection (TikTok, YouTube, Instagram, etc.)      │
│     ├── Format detection (short/long, vertical/horizontal)         │
│     ├── Style detection (professional, casual, funny, etc.)        │
│     ├── Audience detection (B2B, B2C, age group)                   │
│     └── Goal detection (viral, sales, education, brand)            │
│                                                                     │
│  3. INTENT SCORING                                                  │
│     ├── Primary intent (highest confidence)                        │
│     ├── Secondary intents                                          │
│     ├── Ambiguity score                                            │
│     └── Clarification needed flag                                  │
│                                                                     │
│  4. TASK DECOMPOSITION                                              │
│     ├── Break into subtasks                                        │
│     ├── Determine dependencies                                     │
│     ├── Estimate resources                                         │
│     └── Create execution plan                                      │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

## 1.2 Task Decomposition Engine

```python
class TaskDecomposer:
    """
    Разбивает высокоуровневый запрос на атомарные задачи
    """
    
    TASK_TEMPLATES = {
        "video_from_scratch": [
            {"type": "script_generation", "priority": 1},
            {"type": "storyboard_creation", "priority": 2},
            {"type": "image_generation", "priority": 3, "parallel": True},
            {"type": "voiceover_generation", "priority": 3, "parallel": True},
            {"type": "music_selection", "priority": 3, "parallel": True},
            {"type": "video_assembly", "priority": 4},
            {"type": "subtitle_generation", "priority": 5},
            {"type": "final_render", "priority": 6}
        ],
        
        "explainer_with_character": [
            {"type": "script_generation", "priority": 1},
            {"type": "character_selection", "priority": 2},
            {"type": "scene_breakdown", "priority": 3},
            {"type": "character_animation", "priority": 4, "parallel": True},
            {"type": "voiceover_generation", "priority": 4, "parallel": True},
            {"type": "background_generation", "priority": 4, "parallel": True},
            {"type": "compositing", "priority": 5},
            {"type": "subtitle_generation", "priority": 6},
            {"type": "final_render", "priority": 7}
        ],
        
        "brand_package": [
            {"type": "brand_analysis", "priority": 1},
            {"type": "color_palette_generation", "priority": 2},
            {"type": "logo_generation", "priority": 3},
            {"type": "typography_selection", "priority": 3, "parallel": True},
            {"type": "brand_guide_creation", "priority": 4},
            {"type": "asset_generation", "priority": 5}
        ]
    }
```

## 1.3 Pipeline Selection Matrix

```
┌─────────────────┬──────────────────────────────────────────────────┐
│    INTENT       │              SELECTED PIPELINE                    │
├─────────────────┼──────────────────────────────────────────────────┤
│ Short Video     │ Script → Images → Ken Burns → TTS → Assembly     │
│ Talking Head    │ Script → Avatar → Lipsync → Background → Render  │
│ Explainer       │ Script → Character → Animation → Voice → Compose │
│ Logo Animation  │ Logo → Motion Path → Effects → Render            │
│ Product Card    │ Product Info → Layout → Image Gen → Typography   │
│ Brand Package   │ Analysis → Colors → Logo → Guide → Assets        │
│ Viral Script    │ Trend Analysis → Hook Gen → Story → CTA          │
│ Auto-Scenario   │ Niche → Trends → Script → Full Production        │
└─────────────────┴──────────────────────────────────────────────────┘
```
