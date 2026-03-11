# VidFlux AI - Product Requirements Document

## Original Problem Statement
AI video generation service that creates professional-grade animations from text prompts.

## What's Been Implemented (March 11, 2026)

### Logo Animation - FIXED
- Horizontal layout: Logo LEFT, Text RIGHT
- Animation phases:
  1. Logo appears alone in center (0-1s)
  2. Logo moves left, text fades in (1-2s)
  3. Static final state (2-4s)
- Auto-scaling with minimum 180px font size protection
- Works with any logo aspect ratio (square or wide)

### Core Video Engine
- Text Animations: Word-by-word reveal, gradient text with shimmer
- Shape Animations: Gradient circles/rectangles with glow
- UI Elements: Chat bubbles, form fields

### Technical Stack
- Backend: FastAPI + Pillow (PIL) + ffmpeg
- Frontend: React
- Font: Inter (MUST be installed: `apt-get install fonts-inter`)
- Video: 1080x1920 vertical, H.264 + AAC

## CRITICAL: System Dependencies
Before EACH session, run:
```bash
apt-get update && apt-get install -y ffmpeg fonts-inter && fc-cache -f
```

## API Endpoints
- `POST /api/video/generate` - Start video generation
- `GET /api/video/{id}` - Get video status and URL
- `POST /api/upload` - Upload files
- `GET /api/uploads/{filename}` - Serve files

## Backlog

### P0 (High Priority)
- [x] Logo animations - DONE
- [ ] Camera movements (pan, zoom)
- [ ] Parallax effects
- [ ] 3D card transforms

### P1 (Medium Priority)
- [ ] Sora 2 AI video generation
- [ ] Stock video search

### P2 (Low Priority)
- [ ] User authentication
- [ ] Stripe subscriptions
- [ ] Video template marketplace

## Key Files
- `/app/backend/universal_effects.py` - Rendering engine
- `/app/backend/server.py` - API endpoints
