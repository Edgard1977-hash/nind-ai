# VidFlux AI - PRD

## Problem Statement
AI сервис для создания контент-видео. Пользователь вводит промт, умный AI движок анализирует его и автоматически определяет тип видео. Создаёт видео с профессиональными анимациями в формате 9:16.

## What's Implemented (March 2026)

### Core Features ✅
- Landing page с галереей видео
- Умный движок авто-определения типа видео
- **PIL/Pillow рендерер** для профессиональных анимаций
- **Upload API** для загрузки изображений продуктов и логотипов

### Animation Formats (5 профессиональных форматов)

| Format | Описание | Особенности |
|--------|----------|-------------|
| **chat_animation** | iMessage-стиль диалог | Скруглённые баблы, тени, slide-in анимация, typing indicator |
| **apple_text** | Apple презентация | Чередование белый/чёрный фон, fade transitions |
| **kinetic_typography** | Слово за словом | Плавное появление с easing |
| **logo_animation** | Интро бренда | Glow эффект, scale animation |
| **product_advertisement** | Реклама продукта | Apple-стиль, руки, ракурсы, бренд reveal, gradient text |

### Technical Implementation
- **Рендерер:** PIL/Pillow (покадровый рендеринг)
- **FPS:** 30
- **Разрешение:** 1080x1920 (9:16 Full HD)
- **Кодек:** H.264
- **Анимации:** ease_out_cubic, ease_in_out_sine

### Product Advertisement Feature (NEW)
- **Загрузка изображений продукта** через `/api/upload`
- **Загрузка логотипа** бренда
- **AI-генерация** изображений если не загружены
- **Сцены:**
  1. Продукт крупным планом (опционально с руками)
  2. Продукт с другого ракурса
  3. Brand reveal (логотип + название с градиентом)
  4. Tagline (опционально)

## Architecture
```
/app/backend/
├── server.py              # API + AI orchestration + Upload endpoint
├── video_service.py       # Basic ffmpeg functions
├── animation_renderer.py  # Professional PIL renderer (5 formats)
└── uploads/               # Generated content + uploaded files
```

## API Endpoints
- `POST /api/video/generate` - format_id: "auto", "chat_animation", "product_advertisement", etc.
- `POST /api/upload` - Upload product images or logos
- `GET /api/video/{id}` - статус генерации
- `GET /api/formats` - список форматов (14)

## Known Limitations
- Emergent LLM Key бюджет (используются fallback скрипты)
- yt-dlp заблокирован
- ffmpeg требует переустановки при рестарте контейнера

## Next Steps (P1)
- [ ] Добавить видео-генерацию рук с продуктом через Sora/AI
- [ ] Загрузка своего логотипа для logo_animation
- [ ] Улучшить типографику (custom fonts)
- [ ] Добавить 3D рендеринг продукта
