# VidFlux AI - Product Requirements Document v9

## LATEST UPDATE (March 12, 2026)

### 3D iPhone 16 Mockup with Floating Animation ✅
- Created realistic iPhone 16 frame with:
  - Titanium body (Natural Titanium color)
  - Dynamic Island with camera
  - Side buttons (Action, Volume, Power)
  - Rounded screen corners
- Added smooth floating animation:
  - 20px amplitude up/down movement
  - 3 second period
  - Subtle rotation oscillation (±5°)
- Video upload → 3D device animation flow working

### Video Upload → 3D Device Mockup ✅
- Frontend sends to `/api/device-mockup/create`
- Background processing with progress tracking
- Polling via `/api/video/{id}` endpoint

## IMPLEMENTED FEATURES

### 1. Text Never Goes Outside Screen Bounds
- SAFE_MARGIN_X = 60px, SAFE_MARGIN_Y = 100px
- Auto-fit: text shrinks if too wide
- Position clamping to safe bounds

### 2. 3D Device Mockups
- `create_iphone_16_frame()` - Realistic iPhone 16 frame
- `create_3d_phone_mockup()` - 3D perspective + floating animation
- `render_video_on_device()` - Full video rendering pipeline

### 3. Animation Effects
- Floating: sine wave 20px amplitude
- Rotation: ±5° oscillation
- Soft shadow under device

## Scene Types Available

| Type | Description |
|------|-------------|
| `calcom_text` | Text with fade + slide + optional purple emphasis |
| `calcom_chat` | iMessage-style chat bubble with typing effect |
| `apple_text` | Simple fade + scale text |
| `zoom_text` | Text with camera zoom in/out |
| `device_mockup` | 3D iPhone mockup (for showing app interfaces) |
| `logo_reveal` | Logo + brand name animation |
| `gradient_sweep` | Animated gradient across text |

## API Endpoints
- `POST /api/video/generate` - Generate video from text prompt
- `POST /api/device-mockup/create` - Create 3D device animation from uploaded video
- `GET /api/video/{id}` - Check video/mockup status

## Files Modified
- `/app/backend/universal_effects.py` - iPhone 16 frame + floating animation
- `/app/backend/server.py` - Device mockup endpoint with DB tracking
- `/app/frontend/src/pages/CreatePage.jsx` - Video upload flow

## Pending Tasks
- P2: Improve gradient effects quality
- Future: Sora 2 integration, Stripe subscriptions
