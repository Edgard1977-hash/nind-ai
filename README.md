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
| `OPENROUTER_API_KEY` | https://openrouter.ai/keys — text scripts, and image fallback |
| `OPENROUTER_MODEL` | Any OpenRouter model id, default `openai/gpt-4o-mini` |
| `GEMINI_API_KEY` | https://aistudio.google.com/apikey — image generation with `gemini-2.5-flash-image` |
| `STT_API_KEY`, `STT_BASE_URL`, `STT_MODEL` | OpenAI (`https://api.openai.com/v1`, `whisper-1`) or Groq (`https://api.groq.com/openai/v1`, `whisper-large-v3`, key at https://console.groq.com/keys) |
| `TTS_API_KEY`, `TTS_BASE_URL`, `TTS_MODEL`, `TTS_VOICE` | An OpenAI-compatible speech endpoint. `OPENAI_API_KEY` is used when `TTS_API_KEY` is empty |

`VIDEO_PROVIDER` stays empty until a video-model adapter is added.

## Auth

Email and password are hashed with bcrypt. Accounts that still have the old unsalted SHA-256 hash are upgraded on a successful login. Sessions are JWTs in an httpOnly cookie and in the JSON body (`token`) for the SPA. Protected routes ignore `user_id` in the body and use the token. Google sign-in is an authorization-code redirect handled by this API.

Generating a video deducts `GENERATION_CREDIT_COST` (default 10) and refunds the credits if the provider fails.

## Not in this change

- Video-model providers for Enhanced mode
- Whop billing (Stripe routes answer 501)
- Apple sign-in (the button was only a second link to the old hosted login)
