# VidFlux AI - Product Requirements Document

## Original Problem Statement
AI video generation service that creates professional-grade animations from text prompts.

## Implemented Effects (March 11, 2026)

### NEW EFFECTS ADDED (Based on Video Analysis)

1. **Smooth Fade Text** (`smooth_text`)
   - Clean fade-in with scale (0.95→1.0)
   - Optional slide from left/right/bottom
   - Cubic easing for professional feel

2. **Animated Gradient Sweep** (`gradient_sweep`)
   - Purple→white gradient sweeps across text
   - Like MacBook Neo advertisement
   - Configurable sweep speed and colors

3. **Multi-line Sequential** (`multiline`)
   - Multiple lines appear one after another
   - Staggered timing with fade+slide
   - Like Cal.com video style

4. **Chat Bubbles with Typing** (`chat_typing`)
   - iMessage-style bubbles
   - Character-by-character typing effect
   - Sender/receiver positioning

### Existing Effects
- `text` - Word-by-word Apple-style reveal
- `gradient_text` - Static gradient on text
- `chat` - Centered chat bubbles
- `circle`, `rect`, `shapes` - Geometric shapes
- `logo_animation` - Logo + text horizontal layout

## Auto-Dependency Installation
Server now auto-installs `ffmpeg` and `fonts-inter` on startup.
No more manual installation needed!

## API Usage Examples

```json
// Gradient sweep effect
{
  "type": "gradient_sweep",
  "duration": 2.0,
  "bg_color": [0, 0, 0],
  "content": {
    "text": "MacBook Neo",
    "base_color": [100, 100, 100],
    "font_size": 150
  }
}

// Smooth fade text
{
  "type": "smooth_text", 
  "duration": 1.5,
  "bg_color": [255, 255, 255],
  "content": {
    "text": "Hello World",
    "color": [0, 0, 0],
    "slide_from": "right"
  }
}

// Multi-line sequential
{
  "type": "multiline",
  "duration": 3.0,
  "bg_color": [0, 0, 0],
  "content": {
    "lines": ["First Line", "Second Line", "Third Line"],
    "font_sizes": [140, 120, 100]
  }
}
```

## Key Files
- `/app/backend/universal_effects.py` - All rendering functions
- `/app/backend/server.py` - API with auto-dependency install

## Backlog
- [ ] Camera movements (pan/zoom)
- [ ] Parallax effects  
- [ ] 3D card transforms
- [ ] Sora 2 integration
- [ ] Stock video search
