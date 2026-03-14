# VidFlux AI - Product Requirements Document v10

## LATEST UPDATE (March 14, 2026)

### CRITICAL RULE APPLIED ✅
**Phone is ALWAYS COMPLETELY VISIBLE** - no cropping, no cutting, entire device visible at all times.

### What Was Fixed
1. **Phone FULLY visible** - PIL-based mockup ensures complete visibility
2. **Realistic iPhone mockup** - Frame, buttons, Dynamic Island, 3D depth shadow
3. **Camera animation** - Smooth rotation from +25° to -25° and back
4. **Red gradient background** - Matches reference video
5. **9:16 and 16:9 formats** - Both supported
6. **Phone scale 60%** - Takes 60% of screen height with safe margins

### Animation Rules Implemented

1. **Full animation (camera style):**
   - Phone can be left, center, or right
   - Smooth rotation animation (+25° → -25° → +10°)
   - Gentle floating effect
   - Device ALWAYS fully visible

2. **Simple float animation:**
   - Default position: center
   - Gentle oscillation (±15° rotation)
   - Subtle vertical floating

3. **Phone + Text layout:**
   - Phone on left or right (70% size)
   - Animated text on opposite side
   - Staggered text reveal

### Technical Implementation

**iphone_compositor.py v9:**
- `create_iphone_frame()` - Creates realistic iPhone mockup with bezel, buttons, Dynamic Island
- `composite_video_on_phone()` - Places video content in screen area
- `apply_3d_transform()` - Perspective transform for 3D rotation
- `render_full_phone_animation()` - Main animation with FULL VISIBILITY guarantee

**Phone Mockup Details:**
- Frame size: 400x820 pixels (before scaling)
- Bezel thickness: 12px
- Corner radius: 55px
- Dynamic Island: 110x32px
- Side buttons with 3D highlight

**Safe Margins:**
- Vertical: 12% top and bottom
- Horizontal: 15% left and right
- Phone scale: 60% of available height

### API Parameters

```json
POST /api/device-mockup/create
{
  "video_url": "/api/uploads/video.mp4",
  "device_type": "phone",
  "bg_color": [100, 20, 20],      // Gradient start (red)
  "bg_color2": [20, 5, 5],        // Gradient end (dark red)
  "animation_style": "camera",    // "camera", "float", "phone_text"
  "phone_position": "center",     // "center", "left", "right"
  "aspect_ratio": "9:16"          // "9:16" or "16:9"
}
```

### Files
```
/app/backend/
├── iphone_compositor.py      # v9 - FULL VISIBILITY mockup
├── universal_effects.py      # render_video_on_device()
├── server.py                 # API endpoints
└── iphone_15_model/          # New iPhone 15 Pro 3D model (for future use)
```

## Completed Tasks
1. ✅ Phone ALWAYS FULLY VISIBLE
2. ✅ Realistic iPhone mockup
3. ✅ Camera animation (rotation)
4. ✅ Float animation
5. ✅ Red gradient background
6. ✅ 9:16 and 16:9 formats
7. ✅ Phone positions (center/left/right)
8. ✅ Phone + text layout

## Pending Tasks (P1)
- Use real 3D iPhone 15 Pro model renders (Blender rendering in progress)
- Add more gradient presets (green, blue, purple)
- Integrate into universal AI generator

## Future Tasks (P2+)
- Sora 2 video generation
- Stock video search
- User authentication
- Stripe subscriptions
- Template marketplace
