# VidFlux AI - Product Requirements Document

## Implemented Cal.com Style (March 11, 2026)

### EXACT REPLICATION of Cal.com Video
Based on frame-by-frame analysis:

**Text Animation (calcom_text):**
- Fade in: 0 -> 255 alpha over 0.5s
- Slide up: 30px -> 0px with ease_out_cubic
- Scale: 0.9 -> 1.0
- Emphasis word: bounce effect with purple color (#8A2BE2)
- Font: Inter Bold, black on white background

**Chat Bubbles (calcom_chat):**
- iMessage style rounded rectangles
- Blue (#3B82F6) for sender (right side)
- Gray for receiver (left side)
- Typing effect: characters appear one by one
- Slide in from edge with ease_out_cubic

**Colors:**
- Background: White (#FFFFFF)
- Text: Black (#000000)
- Emphasis: Purple (#8A2BE2)
- Chat sender: Blue (#3B82F6)

### Scene Types
1. `calcom_text` - Text with optional emphasis word
2. `calcom_chat` - Chat bubble with typing effect  
3. `apple_text` - Simple fade + scale text
4. `logo_reveal` - Logo + brand name animation

### API Usage
```json
POST /api/video/generate
{
  "prompt": "We have all been there. Are you free Tuesday? cal.com"
}
```

AI automatically generates appropriate scene sequence.

## Key Files
- `/app/backend/universal_effects.py` - Rendering functions
- `/app/backend/server.py` - API and AI script generator
