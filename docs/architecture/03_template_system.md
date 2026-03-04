# 3. СИСТЕМА ШАБЛОНОВ

## 3.1 Структура шаблонов

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEMPLATE SYSTEM                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  TEMPLATE = {                                                    │
│      "metadata": {                                               │
│          "id", "name", "category", "tags",                      │
│          "platform", "goal", "niche", "rating"                  │
│      },                                                          │
│      "structure": {                                              │
│          "sections", "timing", "layout", "animations"           │
│      },                                                          │
│      "assets": {                                                 │
│          "fonts", "colors", "images", "sounds", "effects"       │
│      },                                                          │
│      "variables": {                                              │
│          "text_slots", "image_slots", "color_overrides"         │
│      },                                                          │
│      "ai_hints": {                                               │
│          "style_prompt", "tone", "pacing", "transitions"        │
│      }                                                           │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 3.2 Шаблоны под ниши

```python
NICHE_TEMPLATES = {
    # ═══════════════════════════════════════════════════════════
    # E-COMMERCE / МАРКЕТПЛЕЙСЫ
    # ═══════════════════════════════════════════════════════════
    "ecommerce": {
        "product_showcase": {
            "description": "Демонстрация товара с эффектами",
            "duration": "15-30s",
            "structure": [
                {"type": "hook", "duration": 2, "text": "Вау-эффект"},
                {"type": "product_reveal", "duration": 5, "animation": "3d_rotate"},
                {"type": "features", "duration": 10, "style": "bullet_points"},
                {"type": "price_cta", "duration": 3, "urgency": True}
            ]
        },
        "unboxing": {
            "description": "Распаковка товара",
            "style": "ugc",
            "pov": "first_person"
        },
        "comparison": {
            "description": "Сравнение с конкурентами",
            "layout": "split_screen"
        },
        "review_compilation": {
            "description": "Нарезка отзывов",
            "source": "user_reviews"
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # ОБРАЗОВАНИЕ / ИНФОБИЗНЕС
    # ═══════════════════════════════════════════════════════════
    "education": {
        "explainer_kitten": {
            "description": "Объясняют котята",
            "character": "kitten",
            "tone": "fun_educational",
            "structure": [
                {"type": "hook_question", "duration": 3},
                {"type": "character_intro", "duration": 2},
                {"type": "explanation_points", "duration": 20, "count": 3},
                {"type": "recap", "duration": 5},
                {"type": "cta", "duration": 3}
            ]
        },
        "tutorial": {
            "description": "Пошаговое обучение",
            "style": "screen_recording_plus_avatar"
        },
        "myth_buster": {
            "description": "Разрушаем мифы",
            "format": "before_after"
        },
        "quick_tip": {
            "description": "Быстрый совет",
            "duration": "15s",
            "format": "vertical"
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # РАЗВЛЕЧЕНИЯ / ВИРУСНЫЙ КОНТЕНТ
    # ═══════════════════════════════════════════════════════════
    "entertainment": {
        "story_time": {
            "description": "Истории/Сторителлинг",
            "mood": ["scary", "funny", "dramatic", "mysterious"],
            "narration": "voiceover"
        },
        "chat_story": {
            "description": "Видео-переписка",
            "format": "messenger_style",
            "suspense": True
        },
        "ranking": {
            "description": "Топ-N рейтинг",
            "transitions": "countdown",
            "music": "building_tension"
        },
        "reaction": {
            "description": "Реакция на контент",
            "layout": "picture_in_picture"
        },
        "meme_compilation": {
            "description": "Подборка мемов",
            "auto_timing": True
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # БИЗНЕС / B2B
    # ═══════════════════════════════════════════════════════════
    "business": {
        "company_intro": {
            "description": "Презентация компании",
            "tone": "professional",
            "duration": "60-90s"
        },
        "case_study": {
            "description": "Кейс клиента",
            "structure": ["problem", "solution", "results"]
        },
        "product_demo": {
            "description": "Демо продукта",
            "style": "screen_capture_plus_voiceover"
        },
        "testimonial": {
            "description": "Отзыв клиента",
            "format": "talking_head"
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # ЛИЧНЫЙ БРЕНД / ЭКСПЕРТЫ
    # ═══════════════════════════════════════════════════════════
    "personal_brand": {
        "expert_tip": {
            "description": "Совет эксперта",
            "format": "talking_head",
            "duration": "30-60s"
        },
        "day_in_life": {
            "description": "День из жизни",
            "style": "vlog",
            "ugc": True
        },
        "hot_take": {
            "description": "Острое мнение",
            "hook": "controversial",
            "engagement": "high"
        },
        "ama_format": {
            "description": "Ответы на вопросы",
            "source": "comments"
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # НЕДВИЖИМОСТЬ
    # ═══════════════════════════════════════════════════════════
    "real_estate": {
        "property_tour": {
            "description": "Тур по объекту",
            "style": "cinematic",
            "music": "ambient"
        },
        "area_guide": {
            "description": "Гид по району",
            "format": "infographic_video"
        },
        "price_breakdown": {
            "description": "Разбор цены",
            "visualization": "animated_numbers"
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # ФИТНЕС / ЗДОРОВЬЕ
    # ═══════════════════════════════════════════════════════════
    "fitness": {
        "workout_guide": {
            "description": "Тренировка",
            "format": "split_screen",
            "timer": True
        },
        "transformation": {
            "description": "Трансформация",
            "format": "before_after",
            "music": "motivational"
        },
        "nutrition_tip": {
            "description": "Совет по питанию",
            "character": "nutritionist_avatar"
        }
    },
    
    # ═══════════════════════════════════════════════════════════
    # РЕСТОРАНЫ / ЕДА
    # ═══════════════════════════════════════════════════════════
    "food": {
        "recipe": {
            "description": "Рецепт",
            "style": "overhead_shot",
            "speed": "timelapse"
        },
        "restaurant_promo": {
            "description": "Промо ресторана",
            "mood": "appetizing",
            "shots": "food_porn"
        },
        "mukbang": {
            "description": "Мукбанг",
            "format": "eating_show"
        }
    }
}
```

## 3.3 Шаблоны под платформы

```python
PLATFORM_TEMPLATES = {
    "tiktok": {
        "specs": {
            "resolution": "1080x1920",
            "duration": "15-60s",
            "aspect_ratio": "9:16",
            "fps": 30,
            "format": "mp4"
        },
        "best_practices": {
            "hook_duration": 1.5,  # Секунды на захват внимания
            "text_safe_zone": {"top": 150, "bottom": 200},
            "trending_sounds": True,
            "captions": "always",
            "cta_position": "end"
        },
        "templates": [
            "trending_transition",
            "duet_format",
            "stitch_format",
            "green_screen",
            "voiceover_story"
        ]
    },
    
    "instagram_reels": {
        "specs": {
            "resolution": "1080x1920",
            "duration": "15-90s",
            "aspect_ratio": "9:16",
            "fps": 30
        },
        "best_practices": {
            "aesthetic": "polished",
            "branding": "subtle",
            "cta": "link_in_bio"
        }
    },
    
    "youtube_shorts": {
        "specs": {
            "resolution": "1080x1920",
            "duration": "15-60s",
            "aspect_ratio": "9:16"
        },
        "best_practices": {
            "hook": "question_or_statement",
            "pacing": "fast",
            "subscribe_reminder": True
        }
    },
    
    "youtube_long": {
        "specs": {
            "resolution": "1920x1080",
            "duration": "8-15min",
            "aspect_ratio": "16:9"
        },
        "best_practices": {
            "intro": "15-30s",
            "chapters": True,
            "end_screen": "20s",
            "cards": "strategic_placement"
        },
        "templates": [
            "tutorial_format",
            "listicle_format",
            "documentary_style",
            "vlog_style",
            "interview_format"
        ]
    },
    
    "instagram_stories": {
        "specs": {
            "resolution": "1080x1920",
            "duration": "15s",
            "sequence": "up_to_10"
        },
        "best_practices": {
            "interactive": ["polls", "questions", "sliders"],
            "swipe_up": True,
            "highlights": "branded"
        }
    },
    
    "linkedin": {
        "specs": {
            "resolution": "1920x1080",
            "duration": "30-90s",
            "aspect_ratio": "16:9"
        },
        "best_practices": {
            "tone": "professional",
            "captions": "required",
            "branding": "corporate"
        }
    }
}
```

## 3.4 Шаблоны под цели

```python
GOAL_TEMPLATES = {
    # ═══════════════════════════════════════════════════════════
    # ВИРУСНОСТЬ
    # ═══════════════════════════════════════════════════════════
    "viral": {
        "hooks": [
            "Controversial statement",
            "Unexpected reveal",
            "Relatable pain point",
            "Curiosity gap",
            "Pattern interrupt"
        ],
        "structures": {
            "story_arc": {
                "setup": 3,        # секунды
                "tension": 15,
                "climax": 5,
                "resolution": 3
            },
            "loop_worthy": {
                "seamless_loop": True,
                "rewatch_trigger": "hidden_detail"
            }
        },
        "engagement_triggers": [
            "Ask question in comments",
            "Create debate",
            "Save for later CTA",
            "Tag a friend"
        ]
    },
    
    # ═══════════════════════════════════════════════════════════
    # ПРОДАЖИ
    # ═══════════════════════════════════════════════════════════
    "sales": {
        "frameworks": {
            "AIDA": ["Attention", "Interest", "Desire", "Action"],
            "PAS": ["Problem", "Agitate", "Solution"],
            "BAB": ["Before", "After", "Bridge"]
        },
        "urgency_elements": [
            "Limited time",
            "Limited quantity",
            "Price increase",
            "Exclusive offer"
        ],
        "social_proof": [
            "Testimonials",
            "Numbers/Stats",
            "Celebrity endorsement",
            "User generated content"
        ],
        "cta_types": [
            "Shop now",
            "Learn more",
            "Get started",
            "Claim offer"
        ]
    },
    
    # ═══════════════════════════════════════════════════════════
    # ЭКСПЕРТНОСТЬ / АВТОРИТЕТ
    # ═══════════════════════════════════════════════════════════
    "authority": {
        "content_pillars": [
            "Educational deep-dives",
            "Industry insights",
            "Case studies",
            "Predictions/Trends",
            "Myth busting"
        ],
        "credibility_elements": [
            "Data visualization",
            "Source citations",
            "Professional aesthetics",
            "Consistent branding"
        ],
        "engagement_style": "Thought leadership"
    },
    
    # ═══════════════════════════════════════════════════════════
    # УЗНАВАЕМОСТЬ БРЕНДА
    # ═══════════════════════════════════════════════════════════
    "brand_awareness": {
        "consistency": {
            "colors": "brand_palette",
            "fonts": "brand_fonts",
            "tone": "brand_voice",
            "logo_placement": "standard"
        },
        "storytelling": {
            "brand_story": True,
            "values_showcase": True,
            "behind_scenes": True
        },
        "memorability": [
            "Signature transitions",
            "Sonic branding",
            "Visual motifs",
            "Catchphrases"
        ]
    },
    
    # ═══════════════════════════════════════════════════════════
    # КОНВЕРСИЯ
    # ═══════════════════════════════════════════════════════════
    "conversion": {
        "funnel_stage_content": {
            "awareness": "Entertainment/Education",
            "consideration": "Comparison/Demo",
            "decision": "Testimonials/Offers",
            "retention": "Tips/Community"
        },
        "optimization": {
            "a_b_testing": True,
            "hook_variations": 3,
            "cta_variations": 2
        }
    }
}
```

## 3.5 Template Inheritance System

```python
class TemplateInheritance:
    """
    Система наследования шаблонов
    """
    
    HIERARCHY = {
        "base": {
            # Базовые настройки для всех шаблонов
            "transitions": "smooth",
            "text_animation": "fade_in",
            "safe_zones": True
        },
        "platform_specific": {
            # Наследует от base + добавляет специфику платформы
            "parent": "base",
            "overrides": ["specs", "safe_zones", "cta_position"]
        },
        "niche_specific": {
            # Наследует от platform + добавляет специфику ниши
            "parent": "platform_specific",
            "overrides": ["tone", "pace", "visual_style"]
        },
        "goal_specific": {
            # Наследует от niche + добавляет специфику цели
            "parent": "niche_specific",
            "overrides": ["hooks", "cta", "structure"]
        },
        "custom": {
            # Полностью кастомный шаблон
            "parent": "goal_specific",
            "overrides": ["all"]
        }
    }
```
