# VidFlux AI - PRD

## Problem Statement
AI сервис для создания контент-видео. Пользователь вводит промт, умный AI движок анализирует его и автоматически определяет тип видео (новости, история, анимация диалога и т.д.). Создаёт видео с озвучкой, субтитрами и анимациями в формате 9:16.

## User Personas
- **Content Creator**: Создает вирусный контент для TikTok/Reels/Shorts
- **Маркетолог**: Быстро генерирует промо-видео для продуктов
- **Блогер**: Создает разнообразный контент без технических навыков

## Core Requirements
- Умный движок авто-определения типа видео по промту
- Генерация различных типов контента: новости, истории, диалоги, геймплей
- AI генерация: скрипт → изображения → TTS → сборка через ffmpeg
- Видео превью 9:16 с poster-изображениями
- Субтитры и Ken Burns анимации

## Tech Stack
- Frontend: React 19 + Tailwind + Shadcn/UI
- Backend: FastAPI + MongoDB
- AI: GPT-5.2 (scripts), Gemini Nano Banana (images), OpenAI TTS (voice)
- Video: ffmpeg для сборки видео

## What's Implemented (March 2026)

### Phase 1 - MVP
- [x] Landing page с hero-image и галереей видео
- [x] Космический "liquid glass" дизайн
- [x] Форма создания видео (CreatePage)
- [x] API: /api/formats, /api/video/generate, /api/video/{id}, /api/videos
- [x] Background video generation с progress polling
- [x] 10 форматов видео

### Phase 2 - Smart Engine
- [x] **Auto-detection формата** - AI анализирует промт и определяет лучший тип видео
- [x] **Анимация диалога (chat_animation)** - создаёт видео с анимированными сообщениями
- [x] **Poster images** - генерация превью для видео через ffmpeg
- [x] **Обновлённые UI компоненты** с poster поддержкой

### Video Formats (10 total)
1. news - Новостной
2. story - История
3. quiz - Викторина
4. meme - Мемы
5. educational - Образовательный
6. product - Обзор продукта
7. gameplay_clip - Геймплей + Клип
8. ai_story - AI История
9. character_explainer - Персонаж-объяснитель
10. **chat_animation** - Анимация диалога (NEW)

## API Endpoints
- `GET /api/formats` - Получить все форматы
- `POST /api/video/generate` - Запустить генерацию (format_id="auto" для авто-определения)
- `GET /api/video/{id}` - Статус и результат генерации
- `GET /api/videos` - Список всех проектов
- `GET /api/uploads/{filename}` - Файлы (видео, изображения)

## Known Limitations
- yt-dlp заблокирован в окружении - геймплей использует placeholder
- Emergent LLM Key имеет бюджет - при исчерпании генерация не работает

## Prioritized Backlog

### P0 (Critical) - DONE
- [x] Подключить CreatePage к бэкенду
- [x] Умный движок авто-определения типа
- [x] Poster-изображения для галереи
- [x] Формат анимации диалога

### P1 (High)
- [ ] Улучшить визуализацию poster (более яркие превью)
- [ ] Добавить выбор формата вручную в UI
- [ ] Разные голоса для TTS

### P2 (Medium)
- [ ] Авторизация пользователей
- [ ] История генераций
- [ ] Шаблоны промтов
- [ ] Шеринг в соцсети

## Architecture
```
/app/
├── backend/
│   ├── server.py          # API + AI orchestration
│   ├── video_service.py   # ffmpeg video assembly
│   └── uploads/           # Generated content
├── frontend/
│   └── src/pages/
│       ├── HomePage.jsx   # Gallery + navigation
│       ├── CreatePage.jsx # Prompt input
│       └── VideoPage.jsx  # Video player
└── docs/architecture/     # System design docs
```

## Next Steps
1. Пополнить бюджет Emergent LLM Key
2. Добавить выбор формата в UI (опционально)
3. Улучшить визуальные превью
