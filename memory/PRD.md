# VidFlux AI - PRD

## Problem Statement
AI сервис для создания контент-видео. Пользователь вводит краткий промт, выбирает формат видео через полноэкранный модал с поиском и фильтрацией. AI анализирует промт, генерирует изображения (Nano Banana), создает озвучку (OpenAI TTS) и собирает видео в формате 9:16.

## User Personas
- **Content Creator**: Создает вирусный контент для TikTok/Reels/Shorts
- **Маркетолог**: Быстро генерирует промо-видео для продуктов
- **Новостник**: Создает новостные сводки с визуалом

## Core Requirements
- Ввод промта с выбором формата видео
- Полноэкранный модал выбора формата (поиск + категории + карточки 2xN)
- AI генерация: скрипт → изображения → TTS → сборка
- Видео превью 9:16 с Ken Burns анимациями
- Субтитры и новостной тикер

## Tech Stack
- Frontend: React 19 + Tailwind + Shadcn/UI
- Backend: FastAPI + MongoDB
- AI: Gemini Nano Banana (images), OpenAI TTS (voice), GPT-5.2 (scripts)

## What's Implemented (March 2026)
- [x] Landing page с hero-input и quick hints
- [x] Полноэкранный Format Selector Modal с поиском и фильтрацией
- [x] 6 форматов видео: News, Story, Quiz, Meme, Educational, Product
- [x] API: /api/formats, /api/video/generate, /api/video/{id}, /api/videos
- [x] Background video generation с progress polling
- [x] Video Player с Ken Burns анимациями
- [x] Generation Progress компонент со степами
- [x] TTS интеграция (OpenAI)
- [x] Image generation интеграция (Nano Banana)
- [x] Script generation (GPT-5.2)
- [x] Responsive design (mobile + desktop)

## Prioritized Backlog

### P0 (Critical)
- [ ] Video export/download функция
- [ ] Реальная сборка видео (ffmpeg)

### P1 (High)
- [ ] Галерея созданных видео
- [ ] Редактирование сгенерированного контента
- [ ] Мемы overlay (выезжающие с боков)
- [ ] Разные голоса для TTS

### P2 (Medium)
- [ ] Авторизация пользователей
- [ ] История генераций
- [ ] Шаблоны промтов
- [ ] Шеринг в соцсети

## Next Tasks
1. Добавить ffmpeg для реальной сборки видео
2. Реализовать download функцию
3. Добавить мем overlays для новостного формата
4. Создать галерею видео пользователя
