# VidFlux AI - PRD

## Problem Statement
AI сервис для создания контент-видео. Пользователь вводит промт, умный AI движок анализирует его и автоматически определяет тип видео. Создаёт видео с профессиональными анимациями в формате 9:16.

## What's Implemented (March 2026)

### Core Features ✅
- Landing page с галереей видео
- Умный движок авто-определения типа видео
- **PIL/Pillow рендерер** для профессиональных анимаций

### Animation Formats (4 профессиональных формата)

| Format | Описание | Особенности |
|--------|----------|-------------|
| **chat_animation** | iMessage-стиль диалог | Скруглённые баблы, тени, slide-in анимация, typing indicator |
| **apple_text** | Apple презентация | Чередование белый/чёрный фон, fade transitions |
| **kinetic_typography** | Слово за словом | Плавное появление с easing |
| **logo_animation** | Интро бренда | Glow эффект, scale animation |

### Technical Implementation
- **Рендерер:** PIL/Pillow (покадровый рендеринг)
- **FPS:** 30
- **Разрешение:** 720x1280 (9:16)
- **Кодек:** H.264
- **Анимации:** ease_out_cubic, ease_in_out_sine

## Architecture
```
/app/backend/
├── server.py              # API + AI orchestration
├── video_service.py       # Basic ffmpeg functions
├── animation_renderer.py  # Professional PIL renderer (NEW)
└── uploads/               # Generated content
```

## API Endpoints
- `POST /api/video/generate` - format_id: "auto", "chat_animation", "apple_text", etc.
- `GET /api/video/{id}` - статус генерации
- `GET /api/formats` - список форматов (13)

## Known Limitations
- Emergent LLM Key бюджет (используются fallback скрипты)
- yt-dlp заблокирован

## Next Steps (P1)
- [ ] Добавить звуковые эффекты (клик при появлении сообщения)
- [ ] Загрузка своего логотипа для logo_animation
- [ ] Улучшить типографику (custom fonts)
