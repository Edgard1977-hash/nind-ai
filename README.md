# nind

nind is an AI video studio. This repository runs without the Emergent hosting platform: authentication, model calls, and file paths are configured with environment variables and public SDKs.

Two generation modes:

- **Basic (Базовая)** — a scene plan from the text model, stills from the image model (Gemini “Nano Banana”, with an OpenRouter fallback), then an ffmpeg Ken Burns montage.
- **Enhanced (Улучшенная)** — reserved for generated video (Kling, Wan, Veo, or an aggregator). The API and the create UI accept the mode. Until `VIDEO_PROVIDER` is implemented, the request returns a clear “coming soon / provider not configured” error and does not spend credits.

Payments are not active. Stripe checkout from the prototype is disabled; Whop is planned for a later change.

## What you need

- Python 3.12, Node 20, ffmpeg
- MongoDB, either local or [MongoDB Atlas](https://www.mongodb.com/atlas)
- API keys listed below (only the ones for the features you turn on)

## Run the API

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env
uvicorn server:app --reload --port 8000
```

`GET /api/health` reports which providers have keys. `GET /api/formats` lists video formats.

## Run the web app

```bash
cd frontend
yarn install
cp .env.example .env
yarn start
```

Leave `REACT_APP_BACKEND_URL` empty in development. The dev server proxies `/api` to `http://localhost:8000`. Set it to the public API origin (no trailing slash) when the API is on another host.

## Tests

```bash
cd backend
pytest tests/test_auth_and_modes.py
```

The suite uses an in-memory database and mocked providers. It covers register, login, legacy SHA-256 passwords, `/api/auth/me`, a missing token on a protected route, Basic mode going through the text and image providers, and Enhanced mode returning “not configured”.

## Docker

From the repo root, with `backend/.env` filled in:

```bash
# API on :8000, site on :8080. Mongo is not started; use Atlas in MONGO_URL.
docker compose up --build

# Or a local MongoDB. Set MONGO_URL=mongodb://mongo:27017 in backend/.env first.
docker compose --profile local-mongo up --build
```

The frontend image is nginx. It serves the build and proxies `/api` to the backend, so the browser can keep `REACT_APP_BACKEND_URL` empty.

## Environment variables

See `backend/.env.example` and `frontend/.env.example` for the full list and comments. The owner has to provide:

| Variable | Where to get it |
| --- | --- |
| `MONGO_URL`, `DB_NAME` | A local MongoDB or an Atlas connection string |
| `JWT_SECRET` | `openssl rand -hex 32` |
| `CORS_ORIGINS`, `PUBLIC_BACKEND_URL`, `FRONTEND_URL` | The real browser origin and the public API origin |
| `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` | Google Cloud Console → APIs & Services → Credentials → OAuth client ID (Web). Authorized redirect URI: `{PUBLIC_BACKEND_URL}/api/auth/google/callback` |
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys — Basic script, image fallback, and voiceover |
| `OPENROUTER_MODEL` | Any OpenRouter model id, default `openai/gpt-4o-mini` |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey — image generation with `gemini-2.5-flash-image` |
| `STT_API_KEY`, `STT_BASE_URL`, `STT_MODEL` | OpenAI (`https://api.openai.com/v1`, `whisper-1`) or Groq (`https://api.groq.com/openai/v1`, `whisper-large-v3`, key at https://console.groq.com/keys) |
| `TTS_PROVIDER`, `TTS_BASE_URL`, `TTS_MODEL`, `TTS_VOICE`, `TTS_AUDIO_FORMAT` | Basic voiceover. Default is OpenRouter chat-audio: `TTS_PROVIDER=openrouter`, `TTS_BASE_URL=https://openrouter.ai/api/v1`, `TTS_MODEL=openai/gpt-audio-mini`, `TTS_VOICE=marin`. `openai/gpt-audio-mini` is not served by `/audio/speech`, so the app streams `POST /chat/completions` with `modalities: ["text","audio"]`. `OPENROUTER_API_KEY` alone is enough. Set `TTS_PROVIDER=speech` plus `TTS_API_KEY` (or `OPENAI_API_KEY`) and `TTS_MODEL=tts-1` to use a classic speech endpoint instead |

## Basic video

With `OPENROUTER_API_KEY` set (and no Gemini key), Basic mode writes a narration, speaks the full script, generates photoreal 9:16 stills, then builds an ffmpeg montage:

1. The script model (`OPENROUTER_MODEL`) returns a narration split across 6–8 scenes.
2. Voiceover uses `openai/gpt-audio-mini` on OpenRouter. The picker offers female, male, and neutral voices; Marin is the default.
3. Scene lengths follow the voiceover. Each still gets a slow Ken Burns move (zoom in, zoom out, pan left, pan right, pan up) and a hard cut.
4. Captions are short spoken phrases, bold white with a black stroke, in the lower middle of the frame.
5. A quiet bed is mixed under the voice. It is synthesized with ffmpeg (brown noise and two soft tones), not a licensed music catalog. Set `BASIC_AMBIENT_BED=0` to leave it out. There is no separate music API key.

`VIDEO_PROVIDER` stays empty until a video-model adapter is added.

## Auth

Email and password are hashed with bcrypt. Accounts that still have the old unsalted SHA-256 hash are upgraded on a successful login. Sessions are JWTs in an httpOnly cookie and in the JSON body (`token`) for the SPA. Protected routes ignore `user_id` in the body and use the token. Google sign-in is an authorization-code redirect handled by this API.

Generating a video deducts `GENERATION_CREDIT_COST` (default 10) and refunds the credits if the provider fails.

## Not in this change

- Video-model providers for Enhanced mode
- Whop billing (Stripe routes answer 501)
- Apple sign-in (the button was only a second link to the old hosted login)
