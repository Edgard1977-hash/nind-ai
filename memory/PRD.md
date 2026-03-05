# VidFlux AI - PRD

## Problem Statement
AI сервис для создания контент-видео. Пользователь вводит промт, умный AI движок анализирует его и автоматически определяет тип видео. Создаёт видео с озвучкой, субтитрами и анимациями в формате 9:16.

## User Personas
- **Content Creator**: Создает вирусный контент для TikTok/Reels/Shorts
- **Маркетолог**: Быстро генерирует промо-видео
- **Блогер**: Создает разнообразный контент без технических навыков

## Core Requirements
- Умный движок авто-определения типа видео по промту
- Генерация различных типов контента
- AI генерация: скрипт → видео → TTS → сборка через ffmpeg
- Видео превью 9:16 с poster-изображениями

## Tech Stack
- Frontend: React 19 + Tailwind + Shadcn/UI
- Backend: FastAPI + MongoDB
- AI: GPT-5.2 (scripts), Gemini Nano Banana (images), OpenAI TTS (voice)
- Video: ffmpeg для сборки видео

## What's Implemented (March 2026)

### Phase 1 - MVP ✅
- [x] Landing page с hero-image и галереей видео
- [x] Космический "liquid glass" дизайн
- [x] Форма создания видео (CreatePage)
- [x] API endpoints
- [x] Background video generation с progress polling

### Phase 2 - Smart Engine ✅
- [x] Auto-detection формата по промту
- [x] Poster images для превью видео

### Phase 3 - New Animation Formats ✅ (NEW!)
На основе анализа пользовательских видео-примеров добавлены:

1. **Анимация диалога (chat_animation)** - iMessage стиль
   - Чёрный фон (#000000)
   - Синие баблы для получателя (#007AFF)
   - Серые баблы для отправителя (#292929)
   - Индикатор печатания (3 точки)
   - Header с именем контакта

2. **Apple Text (apple_text)** - минималистичные презентации
   - Чередование белый/чёрный фон
   - Большой bold sans-serif текст
   - Подчёркивание для акцента

3. **Kinetic Typography (kinetic_typography)** - слово за словом
   - Динамичное появление слов
   - Центрированный layout
   - Настраиваемые цвета

4. **Logo Animation (logo_animation)** - интро бренда
   - Иконка + название бренда
   - Опциональный tagline
   - Настраиваемые цвета фона

### Video Formats (13 total)
| ID | Название | Описание |
|----|----------|----------|
| news | Новостной | Новостные репортажи |
| story | История | Нарративы |
| quiz | Викторина | Интерактивный контент |
| meme | Мемы | Вирусный контент |
| educational | Образовательный | Обучающий контент |
| product | Обзор продукта | Товарные презентации |
| gameplay_clip | Геймплей + Клип | Split-screen видео |
| ai_story | AI История | AI-генерированные истории |
| character_explainer | Персонаж-объяснитель | Образовательные видео |
| **chat_animation** | Анимация диалога | iMessage стиль (NEW) |
| **apple_text** | Текст Apple | Минималистичные презентации (NEW) |
| **kinetic_typography** | Кинетическая типографика | Слово за словом (NEW) |
| **logo_animation** | Анимация логотипа | Интро бренда (NEW) |

## API Endpoints
- `GET /api/formats` - Получить все форматы (13)
- `POST /api/video/generate` - Запустить генерацию (format_id="auto" для авто-определения)
- `GET /api/video/{id}` - Статус и результат генерации
- `GET /api/videos` - Список всех проектов
- `GET /api/uploads/{filename}` - Файлы (видео, изображения)

## Known Limitations
- yt-dlp заблокирован - геймплей использует placeholder
- Emergent LLM Key имеет бюджет - при исчерпании используются fallback скрипты

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- [x] Умный движок авто-определения типа
- [x] Анимация диалога (iMessage стиль)
- [x] Apple Text анимация
- [x] Kinetic Typography
- [x] Logo Animation
- [x] Poster-изображения для галереи

### P1 (High)
- [ ] Улучшить визуальный стиль chat_animation (тени, скругления)
- [ ] Добавить звуковые эффекты к анимациям
- [ ] Выбор формата вручную в UI

### P2 (Medium)
- [ ] Авторизация пользователей
- [ ] История генераций
- [ ] Шаблоны промтов

## Architecture
```
/app/
├── backend/
│   ├── server.py          # API + AI orchestration + script generators
│   ├── video_service.py   # ffmpeg video assembly (5 new functions)
│   └── uploads/           # Generated content
├── frontend/
│   └── src/pages/
│       ├── HomePage.jsx   # Gallery + navigation
│       ├── CreatePage.jsx # Prompt input
│       └── VideoPage.jsx  # Video player
└── docs/architecture/     # System design docs
```

## Recent Changes (March 5, 2026)
1. Добавлены 4 новых формата анимации на основе анализа видео-примеров
2. Обновлен auto-detection для распознавания новых форматов
3. Реализованы генераторы скриптов для каждого формата
4. Все форматы протестированы и работают
