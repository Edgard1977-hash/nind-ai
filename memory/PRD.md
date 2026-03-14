# VidFlux AI - Product Requirements Document v11

## LATEST UPDATE (March 14, 2026)

### Cinematic iPhone Animation ✅ COMPLETED
- Added "cinematic" animation style matching reference video
- Pre-rendered 11 angles: 5°, 8°, 10°, 12°, 15°, 16°, 20°, 25°, 30°, 35°, 40°
- Animation phases:
  - 0-25%: iPhone enters with slight rotation (8-15°)
  - 25-50%: Rotation increases (15-25°), moves up
  - 50-75%: Strong rotation (25-35°), continues up
  - 75-100%: Maximum rotation (35-40°), final position
- Dark red gradient background (like reference)
- Smooth easing functions for organic motion
- Subtle wobble for natural feel
- No screen artifacts - clean masking

### Animation Styles Available
| Style | Description |
|-------|-------------|
| `cinematic` | Reference-style with dramatic rotation, dark gradient bg |
| `float` | Simple sine wave floating, customizable bg color |

## API Parameters

### POST /api/device-mockup/create
```json
{
  "video_url": "/api/uploads/video.mp4",
  "device_type": "phone",
  "rotation": 12,
  "bg_color": [100, 25, 25],
  "animation_style": "cinematic"
}
```

## Files Structure
```
/app/backend/
├── iphone_compositor.py      # Screen compositing + animations
├── iphone_renders/           # 11 pre-rendered angles
│   ├── iphone_rot_5.png
│   ├── iphone_rot_8.png
│   ├── iphone_rot_10.png
│   ├── iphone_rot_12.png
│   ├── iphone_rot_15.png
│   ├── iphone_rot_16.png
│   ├── iphone_rot_20.png
│   ├── iphone_rot_25.png
│   ├── iphone_rot_30.png
│   ├── iphone_rot_35.png
│   └── iphone_rot_40.png
├── render_iphone_v2.py       # Blender render script
├── universal_effects.py      # Main rendering engine
└── server.py                 # API endpoints
```

## Scene Types Available
| Type | Description |
|------|-------------|
| `calcom_text` | Text with fade + slide + purple emphasis |
| `calcom_chat` | iMessage-style chat bubble |
| `apple_text` | Simple fade + scale text |
| `zoom_text` | Text with camera zoom |
| `device_mockup` | 3D iPhone with cinematic animation |
| `logo_reveal` | Logo + brand name animation |
| `gradient_sweep` | Animated gradient across text |

## Pending Tasks
- P2: Improve gradient text effects quality
- Future: Sora 2 integration, Stripe subscriptions
