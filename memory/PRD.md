# VidFlux AI - Product Requirements Document v14

## LATEST UPDATE (March 14, 2026)

### Critical Rule Applied ✅
**Phone is ALWAYS FULLY VISIBLE** - no cropping, no cutting, no visual errors allowed.

### What Was Fixed
1. **Phone fully visible** - `phone_scale_start=0.50`, `phone_scale_end=0.75` ensure phone never exceeds 75% of screen
2. **Safe margins** - 10% horizontal, 8% vertical margins prevent edge cropping
3. **Camera animation** - zoom + rotate like reference video
4. **Float animation** - simple gentle floating
5. **9:16 & 16:9 support** - both portrait and landscape formats
6. **Gradient backgrounds** - custom colors with spotlight effect
7. **Phone positions** - center, left, right

### Animation System (iphone_compositor.py v8)

**Animation Styles:**
| Style | Description |
|-------|-------------|
| `camera` | Camera movement (zoom + rotate) - like reference video |
| `float` | Simple floating with gentle rotation (±15°) |
| `phone_text` | Phone on side with animated text |

**Scale Parameters (ensures FULL visibility):**
- `phone_scale_start = 0.50` - Phone takes 50% of screen at start
- `phone_scale_end = 0.75` - Phone takes max 75% at end (zoom in)
- Margins: 10% horizontal, 8% vertical

**Phone Positions:**
- `center` - Centered on screen (default)
- `left` - Left side with margin
- `right` - Right side with margin

**Aspect Ratios:**
- `9:16` - Portrait (1080x1920) - default
- `16:9` - Landscape (1920x1080)

### API Endpoints

```json
POST /api/device-mockup/create
{
  "video_url": "/api/uploads/video.mp4",
  "device_type": "phone",
  "bg_color": [80, 20, 20],       // Gradient start (dark red)
  "bg_color2": [25, 8, 8],        // Gradient end (optional)
  "animation_style": "camera",    // "camera", "float", "phone_text"
  "phone_position": "center",     // "center", "left", "right"
  "aspect_ratio": "9:16",         // "9:16" or "16:9"
  "text": "Your Text"             // For phone_text style only
}
```

### Test Results (Session 8)
- **Backend Tests:** 100% (15/15 passed)
- **Phone FULLY visible:** ✅ Verified at all progress points
- **Camera animation:** ✅ Working
- **Float animation:** ✅ Working
- **9:16 portrait:** ✅ Working
- **16:9 landscape:** ✅ Working
- **Positions (center/left/right):** ✅ Working
- **Custom gradients:** ✅ Working

### Files Structure
```
/app/backend/
├── iphone_compositor.py      # v8 - ALWAYS FULLY VISIBLE guarantee
├── iphone_renders/           # Pre-rendered iPhone angles
├── universal_effects.py      # render_video_on_device()
├── server.py                 # API endpoints
└── tests/
    ├── test_device_mockup_v8.py
    └── test_api_quick.py
```

## Animation Rules (MUST FOLLOW)

1. **Full animation request:**
   - Phone can be left, center, or right
   - Use smooth animations (camera zoom+rotate or float)
   - Device MUST be fully visible, no cropping

2. **Simple 3D phone request:**
   - Default position: center
   - User can specify left/right
   - User chooses format (16:9 or 9:16)

3. **Background gradients:**
   - System correctly applies user-specified gradients
   - Default: dark red gradient like reference

4. **Quality rule:**
   - Result MUST look quality and complete
   - If phone is cropped/deformed = INCORRECT
   - If animation looks bad = INCORRECT

## Completed Tasks
1. ✅ 3D iPhone mockup rendering
2. ✅ Phone ALWAYS FULLY VISIBLE
3. ✅ Camera animation (zoom + rotate)
4. ✅ Float animation (gentle floating)
5. ✅ 9:16 and 16:9 formats
6. ✅ Custom gradient backgrounds
7. ✅ Phone positions (center/left/right)
8. ✅ Phone + text layout

## Pending Tasks (P1)
- Integrate device_mockup into universal AI generator
- Add tablet/laptop device types with same quality

## Future Tasks (P2+)
- Sora 2 video generation
- Stock video search
- User authentication
- Stripe subscriptions
- Template marketplace
