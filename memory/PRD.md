# VidFlux AI - Product Requirements Document v12

## LATEST UPDATE (March 14, 2026)

### Fixed Issues ✅
1. **Purple/pink artifact REMOVED** - Screen is now clean
2. **Smooth animation** - Interpolation between pre-rendered angles
3. **Video displays correctly on iPhone screen**
4. **Shadow under phone added**

### Animation Styles Available
| Style | Description |
|-------|-------------|
| `float` | Simple sine wave floating, smooth rotation interpolation |
| `cinematic` | Dramatic rotation 8°→35° with easing, scaling |
| `phone_text` | Phone on side + animated text fade-in |

### How It Works
1. Pre-rendered iPhone at angles: 5°, 8°, 10°, 12°, 15°, 16°, 20°, 25°, 30°, 35°, 40°
2. `get_raw_screen_mask()` - extracts mask from ORIGINAL render (with pink)
3. `remove_pink_from_render()` - replaces pink with black
4. `blend_iphone_renders()` - smoothly interpolates between two angles + returns mask
5. `composite_video_on_screen()` - places video using mask

### API Parameters
```json
POST /api/device-mockup/create
{
  "video_url": "/api/uploads/video.mp4",
  "device_type": "phone",
  "rotation": 12,
  "bg_color": [60, 80, 60],  // Greenish gradient
  "animation_style": "float",  // or "cinematic", "phone_text"
  "text": "Your Text Here",  // For phone_text style
  "phone_position": "left"   // or "right"
}
```

### Files
```
/app/backend/
├── iphone_compositor.py      # v3 - fixed pink artifacts, smooth interpolation
├── iphone_renders/           # 11 pre-rendered angles (5° to 40°)
├── universal_effects.py      # render_video_on_device()
└── server.py                 # API endpoints
```

### Key Functions
- `blend_iphone_renders(angle)` → (image, mask)
- `composite_video_on_screen(iphone, mask, video)` → composited
- `create_simple_float_frame()` - floating animation
- `create_smooth_phone_frame()` - cinematic animation
- `create_phone_with_text_frame()` - phone + text layout

## Pending Tasks
- Test phone_text animation with real content
- Future: Sora 2 integration, Stripe subscriptions
