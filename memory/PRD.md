# VidFlux AI - Product Requirements Document

## Original Problem Statement
AI video generation service that creates professional-grade animations from text prompts.
User requirements:
- Apple-style text animations with word-by-word reveal
- Shape animations (circles, rectangles, etc.) with gradients
- Logo animations with rotation and scale effects
- UI element rendering (forms, chat bubbles)
- Professional motion graphics quality

## What's Been Implemented (March 11, 2026)

### Core Video Engine (`/app/backend/universal_effects.py`)
- **Text Animations:**
  - Word-by-word reveal with scale + fade + slide (Apple-style)
  - Gradient text with shimmer effect
  - Underline animations for emphasis
  
- **Shape Animations:**
  - Gradient circles with glow effect
  - Gradient rectangles with rounded corners
  - Multiple shapes composition with staggered animation
  
- **UI Elements:**
  - Chat message bubbles (iMessage-style)
  - Form fields with animated appearance
  - Buttons with shadow effects

- **Logo Animation (FIXED - March 11, 2026):**
  - Horizontal layout: Logo LEFT, Text RIGHT (like Discord reference)
  - Phase 1: Logo appears alone in center
  - Phase 2: Logo moves left, text fades in on right
  - Phase 3: Static final state with optional outro effects
  - Auto-scaling to fit 85% of screen width
  - Proper centering as a group
  - Support for bounce and pulse outro effects

### AI Script Generation (`/app/backend/server.py`)
- Smart prompt analysis to detect intent (text vs shapes vs UI vs logo)
- Automatic scene type selection with keyword detection
- Support for all visual element types
- Logo animation routing for "логотип", "logo", "бренд" keywords

### Technical Stack
- Backend: FastAPI + Pillow (PIL) + ffmpeg
- Frontend: React
- Font: Inter (system-installed via fonts-inter package)
- Video Format: 1080x1920 vertical, H.264 + AAC
- AI: GPT-5.2 via Emergent LLM Key

## API Endpoints
- `POST /api/video/generate` - Start video generation
- `GET /api/video/{id}` - Get video status and URL
- `POST /api/upload` - Upload files (logos, images)
- `GET /api/uploads/{filename}` - Serve generated files

## Scene Types Supported
1. `text` - Apple-style word-by-word animation
2. `gradient_text` - Gradient colored text with shimmer
3. `circle` - Gradient circle with glow
4. `rect` - Gradient rectangle with rounded corners
5. `shapes` - Multiple shapes composition
6. `ui_form` - Form with input fields and button
7. `chat` - Chat message bubbles
8. `logo_animation` - Logo with horizontal layout (logo LEFT, text RIGHT)

## Backlog / Future Tasks

### P0 (High Priority)
- [x] Apple-style text animations
- [x] Shape rendering (circles, rectangles)
- [x] Logo animations with uploaded logo - FIXED
- [ ] Camera movements (pan, zoom) - NOT YET IMPLEMENTED
- [ ] Parallax effects - NOT YET IMPLEMENTED
- [ ] 3D card transforms - NOT YET IMPLEMENTED

### P1 (Medium Priority)
- [ ] Sora 2 AI video generation integration
- [ ] Stock video search
- [ ] More advanced easing curves
- [ ] Dynamic text animations (wobble, shimmer, word-by-word reveal)

### P2 (Low Priority)
- [ ] User authentication
- [ ] Stripe subscriptions (currently in test mode)
- [ ] Video template marketplace

## Known Issues
- ffmpeg and fonts-inter must be installed manually each session (environmental constraint)
- Browser video playback may have issues when TTS audio is shorter than video duration

## Files Reference
- `/app/backend/universal_effects.py` - Main rendering engine (logo animation at line 561)
- `/app/backend/server.py` - FastAPI app with all endpoints
- `/app/frontend/src/pages/CreatePage.jsx` - Video creation UI
- `/app/frontend/src/pages/VideoPage.jsx` - Video result display

## Recent Changes Log

### March 11, 2026 - Logo Animation Fix
- Fixed logo animation to match Discord reference video
- Implemented proper horizontal layout: Logo LEFT, Text RIGHT
- Added auto-scaling logic to fit composition within 85% of screen width
- Fixed element sizing to be visible and proportional
- Added proper error logging for ffmpeg encoding
- Animation phases:
  1. Logo appears alone in center (0-1s)
  2. Logo moves left, text fades in (1-2s)
  3. Static final state with optional outro (2-4s)
