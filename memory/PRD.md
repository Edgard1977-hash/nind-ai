# VidFlux AI - Product Requirements Document v10

## LATEST UPDATE (March 12, 2026)

### 3D iPhone 16 Model Integration ✅ COMPLETED
- Integrated user's GLTF 3D model of iPhone 16
- Pre-rendered 3D frames with Blender at angles: 8°, 12°, 16°
- Fast compositing: video frames overlaid on 3D iPhone screen
- Smooth floating animation (25px amplitude, 3.5s period)
- Rotation oscillation (±4° around base angle)

### Files Created
- `/app/backend/iphone_compositor.py` - Screen compositing logic
- `/app/backend/render_iphone_v2.py` - Blender render script
- `/app/backend/iphone_renders/` - Pre-rendered iPhone frames
- `/app/backend/iphone_model/source/iphone_simple.gltf` - Cleaned model

## IMPLEMENTED FEATURES

### 1. 3D Device Mockups (Real Model)
- User's iPhone 16 3D model rendered via Blender
- Screen replacement using color masking
- 60-frame video in ~20 seconds

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
