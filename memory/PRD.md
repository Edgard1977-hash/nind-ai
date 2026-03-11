# VidFlux AI - Product Requirements Document

## Original Problem Statement
AI video generation service that creates professional-grade animations from text prompts.

## Implemented Effects (March 11, 2026)

### APPLE TEXT ANIMATION (NEW - Based on Video Analysis)
Exact replication of @adobebasics TikTok video:
- Text appears with fade + scale (0.85→1.0) + slide up (30px)
- Alternating black/white backgrounds between scenes
- Final title with emphasis at the end
- Cubic easing for smooth professional feel

**Usage:**
```json
{
  "prompt": "Анимация текста: Первая фраза, Вторая фраза, Третья фраза",
  "format_id": "apple_text"
}
```

### Other Effects
- `gradient_sweep` - Animated gradient sweep across text
- `smooth_text` - Fade + scale + slide text reveal
- `multiline` - Sequential multi-line text appearance
- `chat_typing` - Chat bubbles with typing effect
- `logo_animation` - Logo + text horizontal layout

## Auto-Dependency Installation
Server auto-installs `ffmpeg` and `fonts-inter` on startup.

## API Endpoints
- `POST /api/video/generate` - Start video generation
- `GET /api/video/{id}` - Get video status and URL

## Key Files
- `/app/backend/universal_effects.py` - Rendering functions
- `/app/backend/server.py` - API endpoints

## Backlog
- [ ] Camera movements (pan/zoom)
- [ ] Parallax effects
- [ ] 3D card transforms
- [ ] Sora 2 integration
