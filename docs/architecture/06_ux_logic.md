# 6. UX-ЛОГИКА И РЕЖИМЫ РАБОТЫ

## 6.1 Обзор режимов

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         UX MODES                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │             │  │             │  │             │  │             │   │
│   │   SIMPLE    │  │     PRO     │  │    AUTO     │  │  CREATIVE   │   │
│   │    MODE     │  │    MODE     │  │    MODE     │  │ EXPERIMENT  │   │
│   │             │  │             │  │             │  │             │   │
│   │  "Быстро    │  │  "Полный    │  │  "AI       │  │  "Безумные  │   │
│   │   и просто" │  │   контроль" │  │   решает"   │  │   идеи"     │   │
│   │             │  │             │  │             │  │             │   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│         │                │                │                │            │
│         ▼                ▼                ▼                ▼            │
│   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│   │ Минимум     │  │ Все         │  │ Только      │  │ Рандомные   │   │
│   │ настроек    │  │ параметры   │  │ промт       │  │ комбинации  │   │
│   │ Шаблоны     │  │ Ручная      │  │ AI выбирает │  │ A/B тесты   │   │
│   │ 1-клик      │  │ настройка   │  │ всё         │  │ Surprise me │   │
│   └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 6.2 SIMPLE MODE (Простой режим)

```python
class SimpleModeUI:
    """
    Интерфейс для новичков и быстрого создания
    """
    
    PHILOSOPHY = """
    - Минимум решений для пользователя
    - Максимум AI-автоматизации
    - Готовые пресеты и шаблоны
    - Результат за 1-3 клика
    """
    
    FLOW = {
        "step_1": {
            "name": "Выбор цели",
            "options": [
                {"id": "viral_video", "label": "Вирусное видео", "icon": "🔥"},
                {"id": "product_promo", "label": "Продвижение товара", "icon": "🛍️"},
                {"id": "education", "label": "Обучающий контент", "icon": "📚"},
                {"id": "brand_story", "label": "История бренда", "icon": "✨"},
                {"id": "entertainment", "label": "Развлечение", "icon": "🎬"}
            ]
        },
        
        "step_2": {
            "name": "Ввод промта",
            "placeholder": "О чём будет ваш контент?",
            "examples": [
                "Топ-5 способов заработать",
                "Обзор нового iPhone",
                "Страшная история на ночь"
            ],
            "ai_suggestions": True
        },
        
        "step_3": {
            "name": "Выбор стиля",
            "auto_suggest": True,  # AI предлагает лучший
            "options": [
                {"id": "trending", "label": "В тренде"},
                {"id": "professional", "label": "Профессионально"},
                {"id": "fun", "label": "Весело"},
                {"id": "dramatic", "label": "Драматично"}
            ]
        },
        
        "step_4": {
            "name": "Генерация",
            "button": "Создать ✨",
            "estimated_time": "2-5 минут"
        }
    }
    
    # Скрытые настройки (AI выбирает автоматически)
    AUTO_SETTINGS = [
        "format",          # 9:16, 16:9, 1:1
        "duration",        # Оптимальная длительность
        "transitions",     # Переходы
        "music",           # Музыка
        "color_grading",   # Цветокоррекция
        "font",            # Шрифт
        "animation_style"  # Стиль анимации
    ]
```

## 6.3 PRO MODE (Профессиональный режим)

```python
class ProModeUI:
    """
    Интерфейс для профессионалов с полным контролем
    """
    
    PHILOSOPHY = """
    - Полный контроль над каждым параметром
    - Timeline-редактор
    - Слоёвая система
    - Прецизионная настройка
    - Экспорт в любом формате
    """
    
    PANELS = {
        "left_sidebar": {
            "project_tree": True,       # Дерево проекта
            "asset_library": True,      # Библиотека ассетов
            "template_browser": True,   # Браузер шаблонов
            "ai_suggestions": True      # AI-подсказки
        },
        
        "main_area": {
            "preview": {
                "type": "canvas",
                "zoom": True,
                "rulers": True,
                "guides": True,
                "safe_zones": True
            },
            "timeline": {
                "type": "multi_track",
                "tracks": ["video", "audio", "text", "effects"],
                "keyframes": True,
                "markers": True,
                "snapping": True
            }
        },
        
        "right_sidebar": {
            "properties": True,         # Свойства элемента
            "effects": True,            # Эффекты
            "animations": True,         # Анимации
            "ai_tools": True            # AI инструменты
        },
        
        "bottom_panel": {
            "console": True,            # Консоль
            "history": True,            # История действий
            "render_queue": True        # Очередь рендера
        }
    }
    
    TOOLS = {
        "selection": ["select", "multi_select", "lasso"],
        "text": ["text_add", "text_edit", "text_style"],
        "media": ["import", "trim", "split", "speed"],
        "effects": ["filters", "transitions", "animations"],
        "audio": ["volume", "fade", "ducking", "sync"],
        "ai": ["enhance", "upscale", "denoise", "style_transfer"]
    }
    
    KEYBOARD_SHORTCUTS = {
        "space": "play_pause",
        "j": "backward",
        "l": "forward",
        "k": "stop",
        "i": "mark_in",
        "o": "mark_out",
        "ctrl+s": "save",
        "ctrl+z": "undo",
        "ctrl+shift+z": "redo",
        "ctrl+e": "export",
        "ctrl+g": "ai_generate"
    }
```

## 6.4 AUTO MODE (Автоматический режим)

```python
class AutoModeUI:
    """
    Полностью автоматический режим - AI делает всё
    """
    
    PHILOSOPHY = """
    - Один промт = готовый результат
    - AI принимает все решения
    - Минимальное участие пользователя
    - Максимальная скорость
    """
    
    INTERFACE = {
        "main_input": {
            "type": "chat",
            "placeholder": "Опишите что хотите создать...",
            "voice_input": True,
            "file_upload": True
        },
        
        "ai_conversation": {
            "clarifying_questions": True,  # AI может задать уточняющие вопросы
            "suggestions": True,           # AI предлагает улучшения
            "alternatives": True           # AI показывает варианты
        },
        
        "result_area": {
            "live_preview": True,
            "progress_indicator": True,
            "iteration_options": [
                "Сделай короче",
                "Добавь драмы",
                "Сделай смешнее",
                "Другой стиль"
            ]
        }
    }
    
    AI_DECISION_AREAS = [
        "content_type",         # Тип контента
        "format_selection",     # Выбор формата
        "style_selection",      # Выбор стиля
        "music_selection",      # Выбор музыки
        "voice_selection",      # Выбор голоса
        "color_scheme",         # Цветовая схема
        "typography",           # Типографика
        "transitions",          # Переходы
        "pacing",               # Темп
        "structure"             # Структура
    ]
    
    EXAMPLE_PROMPTS = [
        "Сделай вирусное видео про криптовалюту для TikTok",
        "Создай рекламу моего продукта [загружено фото]",
        "Анимированный логотип для моего бренда",
        "Смешное видео с объясняющими котятами про инвестиции",
        "Сторителлинг видео - страшная история"
    ]
```

## 6.5 CREATIVE EXPERIMENT MODE (Креативный эксперимент)

```python
class CreativeExperimentUI:
    """
    Режим для экспериментов и A/B тестирования
    """
    
    PHILOSOPHY = """
    - Генерация множества вариантов
    - Неожиданные комбинации
    - A/B тестирование
    - Surprise me функция
    - Выход за рамки
    """
    
    FEATURES = {
        "variation_generator": {
            "description": "Создание N вариантов контента",
            "options": {
                "count": [3, 5, 10],
                "variation_level": ["subtle", "moderate", "wild"],
                "variation_axes": [
                    "style",
                    "tone",
                    "structure",
                    "visuals",
                    "music",
                    "pacing"
                ]
            }
        },
        
        "surprise_me": {
            "description": "AI создаёт неожиданный контент",
            "randomness_level": ["low", "medium", "high", "chaos"],
            "constraints": {
                "keep_topic": True,     # Сохранить тему
                "keep_brand": False,    # Не привязываться к бренду
                "safe_mode": True       # Без NSFW
            }
        },
        
        "style_fusion": {
            "description": "Смешивание несовместимых стилей",
            "examples": [
                "Corporate + Meme",
                "Horror + Cute",
                "Vintage + Cyberpunk",
                "Minimalist + Maximalist"
            ]
        },
        
        "ab_testing": {
            "description": "Создание вариантов для тестирования",
            "test_elements": [
                "hooks",
                "thumbnails",
                "cta",
                "music",
                "color_scheme"
            ],
            "analytics_integration": True
        },
        
        "trend_remix": {
            "description": "Адаптация трендов под ваш контент",
            "sources": ["tiktok", "instagram", "youtube"],
            "auto_detect": True
        }
    }
    
    EXPERIMENT_PRESETS = [
        {
            "name": "Hook Варианты",
            "generates": 5,
            "varies": ["hook_text", "hook_visual", "hook_timing"]
        },
        {
            "name": "Стиль Рулетка",
            "generates": 3,
            "varies": ["visual_style", "music_genre", "color_palette"]
        },
        {
            "name": "Формат Тест",
            "generates": 3,
            "varies": ["duration", "aspect_ratio", "platform_optimization"]
        },
        {
            "name": "Полный Хаос",
            "generates": 5,
            "varies": ["everything"],
            "randomness": "high"
        }
    ]
```

## 6.6 Mode Switching & Persistence

```python
class ModeManager:
    """
    Управление режимами и переключение
    """
    
    async def switch_mode(self, user_id: str, new_mode: str):
        """
        Переключение режима с сохранением контекста
        """
        
        current_mode = await self.get_user_mode(user_id)
        current_state = await self.save_state(user_id)
        
        # Адаптация состояния под новый режим
        adapted_state = self.adapt_state(current_state, current_mode, new_mode)
        
        # Применение нового режима
        await self.apply_mode(user_id, new_mode, adapted_state)
        
        # Аналитика
        await self.track_mode_switch(user_id, current_mode, new_mode)
    
    def adapt_state(self, state: dict, from_mode: str, to_mode: str) -> dict:
        """
        Адаптация состояния проекта при смене режима
        """
        
        if from_mode == "simple" and to_mode == "pro":
            # Раскрытие скрытых настроек
            state["show_advanced"] = True
            state["timeline_visible"] = True
            
        elif from_mode == "pro" and to_mode == "simple":
            # Скрытие сложных настроек, сохранение результата
            state["show_advanced"] = False
            state["preserved_settings"] = state.get("advanced_settings")
            
        elif to_mode == "auto":
            # Сброс ручных настроек, AI возьмёт управление
            state["ai_controlled"] = True
            
        return state
    
    USER_MODE_PREFERENCES = {
        "default_mode": "auto",
        "remember_last_mode": True,
        "mode_per_project_type": {
            "quick_content": "simple",
            "brand_work": "pro",
            "experiments": "creative"
        }
    }
```

## 6.7 Onboarding Flow

```python
ONBOARDING = {
    "welcome": {
        "title": "Добро пожаловать в VidFlux AI Studio",
        "subtitle": "Создавайте любой контент с помощью AI"
    },
    
    "questions": [
        {
            "q": "Какой контент вы создаёте чаще всего?",
            "options": [
                "Видео для соцсетей",
                "Рекламные материалы",
                "Образовательный контент",
                "Развлекательный контент",
                "Брендинг"
            ],
            "affects": "default_templates"
        },
        {
            "q": "Какой у вас опыт работы с видеоредакторами?",
            "options": [
                "Новичок",
                "Базовый",
                "Продвинутый",
                "Профессионал"
            ],
            "affects": "default_mode"
        },
        {
            "q": "На какую платформу вы чаще всего публикуете?",
            "options": [
                "TikTok",
                "Instagram",
                "YouTube",
                "LinkedIn",
                "Разные платформы"
            ],
            "affects": "default_format"
        }
    ],
    
    "mode_recommendation": {
        "beginner": "simple",
        "intermediate": "auto",
        "advanced": "pro",
        "experimental": "creative"
    }
}
```
