# Slind AI - Product Requirements Document

## Original Problem Statement
AI-powered content generation platform (video, motion design, logos, promo videos). The user requested a modern, dark-themed UI with Google/Apple authentication and seamless content generation.

## Core Features

### 1. Main Page UI ✅
- Dark background (#0C0C0E) with cyan gradient glow
- Animated heading cycling through "Сделаю [видео-монтаж]", "Сделаю [логотип]", etc.
- Multi-line text input with icons (file attachment, audio, submit)
- Profile icon with credits display for logged-in users

### 2. Authentication
- **Google Auth** ✅ (implemented via Emergent-managed OAuth)
- **Apple Auth** ⏳ (not implemented)
- Slide-up popup for login/registration
- Service name: "Slind AI"

### 3. Video Generation ✅
- `/api/video/generate` - AI video generation from prompts
- `/api/device-mockup/create` - 3D phone animation with user video
- Progress tracking on `/video/:id` page
- Multiple video formats supported (see VIDEO_FORMATS in server.py)

### 4. User Profile
- Team management (add users by @username)
- Avatar, username, subscription plan display
- Generated videos list

### 5. File Uploads
- Thumbnail previews above text input
- Progress indicator for video uploads
- Chunked uploads for large files

## Architecture

```
/app/
├── backend/
│   ├── server.py           # FastAPI server, auth, video generation
│   ├── video_service.py    # Video processing utilities
│   ├── universal_effects.py # 3D device mockup rendering
│   └── animation_renderer.py # Animation effects
└── frontend/
    ├── src/
    │   ├── pages/
    │   │   ├── MainPage.jsx    # Main UI
    │   │   ├── CreatePage.jsx  # Legacy create page
    │   │   └── VideoPage.jsx   # Video progress/result
    │   └── components/custom/
    │       ├── AuthPopup.jsx   # Login modal
    │       ├── AuthCallback.jsx # OAuth callback handler
    │       └── ProfilePage.jsx # User profile
    └── package.json
```

## API Endpoints

- `POST /api/video/generate` - Start video generation
- `GET /api/video/:id` - Get video status/result
- `POST /api/device-mockup/create` - Create 3D phone animation
- `POST /api/auth/google` - Start Google OAuth
- `POST /api/auth/callback` - OAuth callback
- `GET /api/auth/me` - Get current user

## On Hold / Future Tasks
- 3D iPhone animation refinement (video spilling over bezel issue)
- Stripe subscriptions
- Sora 2 Integration
- Stock Video Search
- Marketplace for video templates

## Changelog

### 2026-04-25 (motion text engine)
- **Добавлено 5 типов кинетической типографии** на основе анализа референсных видео (`/app/backend/motion_text_effects.py`):
  1. `motion_blur_in` — Apple keynote blur-in (по буквам/словам, gaussian blur 22px → 0)
  2. `motion_char_fade` — char-by-char fade + 16px slide-up + опциональный gradient orange→purple на emphasis_word
  3. `motion_apple_scale` — word-by-word scale 0.9→1.0 + slide-from-left 22px + fade
  4. `motion_word_slide` — word slide-in слева с soft drop shadow (gaussian blur 0.6)
  5. `motion_fade_underline` — char-by-char fade + scale + slide-up + animated draw-underline на emphasis_words
- Все стили зарегистрированы в `render_universal_video` (`universal_effects.py`) и в LLM-промпте `generate_universal_script` (`server.py`)
- Sanity-test: `/app/backend/tests/test_motion_text_effects.py` — все 5 эффектов рендерятся без ошибок
- Реальная end-to-end проверка: prompt "Apple keynote style…" → LLM выдала сцены с `motion_blur_in`, `motion_char_fade` (gradient on "Manage"), `motion_apple_scale` → видео завершилось 100%

### 2026-02-21 (session 2, part 2)
- **Voice Assistant — полноценная интеграция Whisper**
  - Backend: `POST /api/voice/transcribe` принимает audio (webm/wav/mp3/m4a) → `OpenAISpeechToText` (whisper-1) через EMERGENT_LLM_KEY → возвращает `{text}`. Проверено curl.
  - Frontend: `VoiceAssistantPage` теперь пишет с микрофона через `MediaRecorder`, показывает живую **waveform**-визуализацию (Canvas + AnalyserNode) под глазами, автоматически транскрибирует запись и шлёт результат в `POST /api/video/generate`.
  - Когда поле ввода пустое — справа показывается **mic-кнопка** (белая → красная с пульсом при записи). Когда есть текст/вложения — классический send (стрелка).
  - Статус-лейбл под волной: «Слушаю...», «Распознаю речь...», «Отправляю запрос...».
  - Очистка MediaStream/AudioContext на unmount и после записи.

### 2026-02-21 (session 2)
- **P1 выполнено: 3-точечное меню на карточках видео (Download / Edit / Delete)**
  - Frontend: исправлены опечатки `setOpenMenuId` → `setOpenMenu` в `handleDownload/Delete/Edit`
  - `handleEdit` реализован через `window.prompt` + `PATCH /api/videos/{id}` (переименование)
  - `handleDownload` теперь корректно обрабатывает абсолютные URL
  - `handleDelete` очищает и `userVideos`, и `generatingVideos`
  - Backend: новые endpoints `DELETE /api/videos/{id}` и `PATCH /api/videos/{id}` с UpdateVideoRequest
- Voice Assistant Page: глаза 108×210 (десктоп), увеличены поле ввода (64px) и кнопка-плюс (64×64)

### 2026-02-21
- Added dedicated Voice Assistant page at `/voice` (VoiceAssistantPage.jsx)
  - AI eyes with appear/blink/listen/speak animations (68x112 px)
  - Smooth black gradient fade at bottom of page
  - Input row: `#212121` plus button (left), `#212121` input field, white send arrow button inside input
  - Back button (top-left) to return to `/`
- Wired mic button (both anonymous & logged-in variants) in MainPage.jsx to navigate('/voice')
- Fixed broken CSS where `.voice-assistant-page` rules were injected inside an unclosed `.voice-status p` selector

### 2025-03-18
- Fixed video generation from MainPage (was TODO, now implemented)
- Added loading state to submit button
- Generation now redirects to /video/:id page

### Previous
- Implemented new dark-themed UI
- Added Google OAuth via Emergent-managed service
- Created MainPage, AuthPopup, ProfilePage, VideoPage components

## [2026-02-04] UI Bug Fix Batch
- Light theme: expanded to cover main pages, upgrade/pricing cards, profile, hero subtitles, credits bar, buttons
- Popup overlay: removed dark backdrop dimming (transparent) per user request
- Popups (Language, Confirm, Appearance): rewrote swipe-to-close using pointer events (mouse + touch), smooth slide-down animation continues from drag position; tap-outside also triggers the same slide-down
- Language popup: removed cyan tint on selected item — only white border shows selection; border-radius bumped +5px (19→24); inter-item gap increased (10→16px)
- Upgrade page: explicit text colors in light/dark; pricing-card-top + pricing-card-bottom overrides for light theme

