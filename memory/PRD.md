# VidFlux AI - PRD

## Problem Statement
AI сервис для создания контент-видео. Пользователь вводит промт, умный AI движок анализирует его и автоматически определяет тип видео. Создаёт видео с профессиональными анимациями в формате 9:16.

## What's Implemented (March 2026)

### Core Features ✅
- Landing page с галереей видео
- Умный движок авто-определения типа видео
- **PIL/Pillow рендерер** для профессиональных анимаций
- **Upload API** для загрузки изображений продуктов и логотипов
- **Stripe Подписки** — 3 плана ($7.99, $19, $79)

### Animation Formats (5 профессиональных форматов)

| Format | Описание | Особенности |
|--------|----------|-------------|
| **chat_animation** | iMessage-стиль диалог | Scale-up + fade-in, мягкие тени, падающие деньги overlay, реакции-эмодзи |
| **apple_text** | Apple презентация | Word-by-word появление, градиентный текст (синий→фиолетовый), подчёркивание |
| **kinetic_typography** | Слово за словом | Плавное появление с easing |
| **logo_animation** | Интро бренда | Glow эффект, scale animation, поддержка загруженного логотипа |
| **product_advertisement** | Реклама продукта | Apple-стиль, руки, ракурсы, бренд reveal, gradient text |

### AI Видеомонтаж ✅ NEW
| Стиль | Описание | Переходы |
|-------|----------|----------|
| **TikTok/Reels** | Быстрый, динамичный | glitch, flash, zoom, shake |
| **YouTube** | Плавный, профессиональный | fade, dissolve, slide |
| **Мемы/Комедия** | Весёлый, мемный | hard_cut, zoom_in, shake, flash |
| **Кинематографичный** | Элегантный, киношный | fade, dissolve, wipe |

Функции монтажа:
- AI анализирует видео и находит интересные моменты
- Автоматические переходы между клипами
- AI подбирает звуковые эффекты по контексту
- Наложение фоновой музыки (загрузка пользователем)
- Текстовые оверлеи

### Subscription Plans ✅
| План | Цена | Видео/месяц | Качество |
|------|------|-------------|----------|
| Starter | $7.99 | 10 | 720p |
| Pro | $19.00 | 50 | 1080p |
| Unlimited | $79.00 | ∞ | 4K |

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
- `GET /api/formats` - список форматов (15)
- `GET /api/subscription/plans` - список планов подписки
- `POST /api/subscription/checkout` - создать Stripe сессию
- `GET /api/subscription/status/{session_id}` - статус оплаты
- `POST /api/webhook/stripe` - Stripe webhook

## Known Limitations
- Emergent LLM Key бюджет (используются fallback скрипты)
- yt-dlp заблокирован
- ffmpeg требует переустановки при рестарте контейнера

## Recent Fixes (March 8, 2026)
- ✅ **File Upload Bug Fixed** — Расширена валидация типов файлов в `/api/upload`:
  - Добавлены видео форматы: mp4, mov, webm, avi, mpeg
  - Добавлены аудио форматы: mp3, wav, ogg, aac, m4a
  - Fallback проверка по расширению файла (когда браузер отправляет неверный content_type)
- ✅ **AI Монтаж теперь работает** — можно загружать видео и создавать монтажи

## Pending User Verification
- [ ] Apple Text Animation — исправлена обрезка видео (убран флаг `-shortest`)
- [ ] Logo Animation — исправлена передача загруженного логотипа в рендерер

## Next Steps (P1)
- [ ] Интеграция Sora 2 для AI видео-генерации
- [ ] Поиск стоковых видео (Pexels API)
- [ ] Система аутентификации пользователей
- [ ] Улучшить типографику (custom fonts)
- [ ] Добавить 3D рендеринг продукта
