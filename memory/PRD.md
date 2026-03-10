# VidFlux AI - PRD

## Original Problem Statement
Создать AI сервис для генерации контент-видео с динамическими эффектами:
- Градиенты и переливания (aurora-style)
- Анимации текста (Apple-стиль: волна сверху/снизу, масштабирование)
- Диалоги/сообщения в стиле iMessage
- Универсальная система эффектов с AI-оркестрацией

## Architecture

### Backend (FastAPI)
- `/app/backend/server.py` - Main API, AI orchestration
- `/app/backend/universal_effects.py` - Universal effects rendering system (NEW)
- `/app/backend/exact_effects.py` - Legacy exact effects (deprecated)
- `/app/backend/uploads/` - Generated videos storage

### Frontend (React)
- `/app/frontend/src/pages/CreatePage.jsx` - Main creation page (prompt + video upload)
- `/app/frontend/src/pages/VideoPage.jsx` - Video result display
- `/app/frontend/src/pages/PricingPage.jsx` - Subscription plans

## Current Status

### Completed Features ✅
- **Universal Effects System** - Dynamic AI-powered video generation
- **Chat/Dialog Animation** - iMessage-style bubbles with:
  - Large, readable text
  - Proper rounded corners
  - Message tails
  - Typing indicator animation
  - Morphing from typing to message bubble
- **Text Animations** (Apple-style):
  - Scale up with bounce
  - Wave from top (letters fall)
  - Wave from bottom (letters rise)
  - Fade from blur
- **Gradient Backgrounds** - Aurora/shimmer gradients
- **Gradient Text** - Text with color gradients and shimmer
- **Chunked File Upload** - Large video uploads support
- **AI Format Detection** - Smart prompt analysis

### What Works
1. `POST /api/video/generate` - Creates videos with dynamic effects
2. Chat dialogs render with proper iMessage styling
3. Gradient backgrounds animate smoothly
4. Text animations work (wave_down, wave_up, scale_up)
5. Video playback on result page works
6. Download functionality works

### Known Issues
1. **ffmpeg not persistent** - Need to reinstall after container restart
2. **Rendering speed** - Complex videos may take 15-30 seconds
3. **Morphing animation** - Can be smoother for chat bubbles

## API Endpoints

### Video Generation
- `POST /api/video/generate` - Generate video from prompt
- `GET /api/video/{id}` - Get video status/result
- `GET /api/uploads/{filename}` - Serve video file

### File Upload
- `POST /api/upload/init` - Initialize chunked upload
- `POST /api/upload/chunk` - Upload chunk
- `POST /api/upload/complete` - Complete upload

## Database Schema
- Collection: `video_projects`
- Fields: id, status, progress, prompt, format_id, video_url, etc.

## Upcoming Tasks
- P0: Sora 2 Integration for AI video clips
- P1: Stock video search (Pexels)
- P2: User authentication system
- P3: Stripe live mode

## Last Updated
2024-03-10 - Universal effects system v2 implemented with improved chat bubbles
