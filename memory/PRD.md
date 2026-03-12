# VidFlux AI - Product Requirements Document v8

## LATEST UPDATE (March 12, 2026)

### Video Upload → 3D Device Mockup (FIXED)
- When user uploads video, it now creates 3D phone animation (not simple montage)
- Frontend sends to `/api/device-mockup/create` instead of `/api/montage/create`
- Progress polling via `/api/video/{id}` endpoint
- UI text updated to reflect 3D animation feature

## FIXED ISSUES (Previous)

### 1. Text Never Goes Outside Screen Bounds
- Added SAFE_MARGIN_X = 60px, SAFE_MARGIN_Y = 100px
- Auto-fit: text shrinks if too wide
- Position clamping to safe bounds

### 2. Proper Centering
- All text centered with correct calculations
- Emphasis words stay inline with rest of text

### 3. Correct Layering
- Background drawn first, text on top via alpha_composite
- No more text hidden by background

### 4. ZOOM Effects
- `apply_zoom_effect(img, zoom)` - zoom > 1.0 = closer, < 1.0 = farther
- `animate_zoom(progress, start, end)` - animated zoom
- New scene type: `zoom_text`

### 5. 3D Device Mockups
- `create_3d_phone_mockup(screen_content, rotation_y)` 
- Perspective transform for 3D effect
- Shadow included
- Ready for video playback on screen

## Scene Types Available

| Type | Description |
|------|-------------|
| `calcom_text` | Text with fade + slide + optional purple emphasis |
| `calcom_chat` | iMessage-style chat bubble with typing effect |
| `apple_text` | Simple fade + scale text |
| `zoom_text` | Text with camera zoom in/out |
| `device_mockup` | 3D phone mockup (for showing app interfaces) |
| `logo_reveal` | Logo + brand name animation |
| `gradient_sweep` | Animated gradient across text |

## Key Parameters

### Safe Bounds
```python
SAFE_MARGIN_X = 60   # pixels from left/right
SAFE_MARGIN_Y = 100  # pixels from top/bottom
MAX_TEXT_WIDTH = 960 # 1080 - 60*2
```

### Colors
```python
CALCOM_PURPLE = (138, 43, 226)  # Emphasis words
CALCOM_BLUE = (59, 130, 246)   # Chat sender bubbles
```

## Files Modified
- `/app/backend/universal_effects.py` - All rendering functions
- `/app/backend/server.py` - AI script generator, device mockup endpoint
- `/app/frontend/src/pages/CreatePage.jsx` - Video upload flow

## API Endpoints
- `POST /api/video/generate` - Generate video from text prompt
- `POST /api/device-mockup/create` - Create 3D device animation from uploaded video
- `GET /api/video/{id}` - Check video/mockup status

## Pending Tasks
- P1: Add animations to 3D devices (rotation, movement)
- P2: Improve gradient effects quality
- Future: Sora 2 integration, Stripe subscriptions
