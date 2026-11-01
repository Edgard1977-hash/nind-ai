"""Email/password and Google OAuth sessions.

Passwords are stored with bcrypt. Accounts created by the previous build used
unsalted SHA-256; a successful login rewrites those hashes to bcrypt.

Sessions are JWTs. The token is set as an httpOnly cookie and also returned
to the client so a cross-origin SPA can send ``Authorization: Bearer``.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional
from urllib.parse import urlencode

import httpx
import jwt
from fastapi import HTTPException, Request, Response

try:
    import bcrypt
except ImportError:  # pragma: no cover - dependency is required at runtime
    bcrypt = None

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
COOKIE_NAME = "access_token"


def _secret() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")
    return secret


def _expire_days() -> int:
    try:
        return max(1, int(os.getenv("JWT_EXPIRE_DAYS", "7")))
    except ValueError:
        return 7


def hash_password(password: str) -> str:
    if bcrypt is None:
        raise HTTPException(status_code=500, detail="bcrypt is not installed")
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """Return ``(matches, should_upgrade_from_legacy_sha256)``."""
    if not stored:
        return False, False
    if stored.startswith("$2"):
        if bcrypt is None:
            return False, False
        try:
            return bcrypt.checkpw(password.encode("utf-8"), stored.encode("utf-8")), False
        except ValueError:
            return False, False
    legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if hmac.compare_digest(legacy, stored):
        return True, True
    return False, False


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=_expire_days())).timestamp()),
    }
    return jwt.encode(payload, _secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


def cookie_settings() -> dict:
    secure = os.getenv("JWT_COOKIE_SECURE", "false").lower() in ("1", "true", "yes")
    samesite = os.getenv("JWT_COOKIE_SAMESITE", "lax").lower()
    if samesite not in ("lax", "strict", "none"):
        samesite = "lax"
    if samesite == "none":
        secure = True
    return {"secure": secure, "samesite": samesite}


def set_auth_cookie(response: Response, token: str) -> None:
    settings = cookie_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings["secure"],
        samesite=settings["samesite"],
        path="/",
        max_age=_expire_days() * 24 * 60 * 60,
    )


def clear_auth_cookie(response: Response) -> None:
    response.delete_cookie(key=COOKIE_NAME, path="/")


def read_token(request: Request) -> Optional[str]:
    cookie = request.cookies.get(COOKIE_NAME)
    if cookie:
        return cookie
    # Accept the previous cookie name so already-issued sessions keep working
    # only when they are JWTs. Opaque Emergent session tokens will fail decode.
    legacy = request.cookies.get("session_token")
    header = request.headers.get("Authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip()
    return legacy


def public_user(user: dict, token: Optional[str] = None) -> dict:
    payload = {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "name": user.get("name"),
        "username": user.get("username"),
        "picture": user.get("picture"),
        "plan": user.get("plan", "free"),
        "credits": user.get("credits", 0),
    }
    if token:
        payload["token"] = token
    return payload


def _allowed_frontends() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    origins = [item.strip().rstrip("/") for item in raw.split(",") if item.strip() and item.strip() != "*"]
    extra = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
    if extra and extra not in origins:
        origins.append(extra)
    return origins or ["http://localhost:3000"]


def safe_frontend_url(candidate: Optional[str]) -> str:
    allowed = _allowed_frontends()
    if candidate:
        cleaned = candidate.strip().rstrip("/")
        for origin in allowed:
            if cleaned == origin or cleaned.startswith(origin + "/"):
                return cleaned
    return allowed[0]


def google_redirect_uri() -> str:
    explicit = os.getenv("GOOGLE_REDIRECT_URI", "").strip()
    if explicit:
        return explicit
    base = os.getenv("PUBLIC_BACKEND_URL", "").strip().rstrip("/")
    if not base:
        raise HTTPException(
            status_code=500,
            detail="Set PUBLIC_BACKEND_URL or GOOGLE_REDIRECT_URI for Google OAuth",
        )
    return f"{base}/api/auth/google/callback"


def google_client() -> tuple[str, str]:
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    return client_id, client_secret


def build_google_authorize_url(next_url: Optional[str]) -> str:
    client_id, _secret_unused = google_client()
    destination = safe_frontend_url(next_url)
    state = jwt.encode(
        {
            "next": destination,
            "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
        },
        _secret(),
        algorithm="HS256",
    )
    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": google_redirect_uri(),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def decode_oauth_state(state: str) -> str:
    try:
        payload = jwt.decode(state, _secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=400, detail="Invalid OAuth state") from exc
    return safe_frontend_url(payload.get("next"))


async def exchange_google_code(code: str) -> dict:
    client_id, client_secret = google_client()
    async with httpx.AsyncClient(timeout=30) as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": google_redirect_uri(),
                "grant_type": "authorization_code",
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Google token exchange failed")
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=401, detail="Google did not return an access token")
        profile = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile.status_code != 200:
            raise HTTPException(status_code=401, detail="Google userinfo request failed")
        return profile.json()


async def upsert_google_user(db, profile: dict) -> dict:
    email = (profile.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Google account has no email")
    existing = await db.users.find_one({"email": email})
    now = datetime.now(timezone.utc)
    if existing:
        await db.users.update_one(
            {"user_id": existing["user_id"]},
            {
                "$set": {
                    "name": profile.get("name") or existing.get("name") or email.split("@")[0],
                    "picture": profile.get("picture") or existing.get("picture"),
                    "google_sub": profile.get("id") or existing.get("google_sub"),
                    "updated_at": now,
                }
            },
        )
        user = await db.users.find_one({"user_id": existing["user_id"]}, {"_id": 0, "password_hash": 0})
        return user
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    name = profile.get("name") or email.split("@")[0]
    username = f"{name.lower().replace(' ', '')}{uuid.uuid4().hex[:4]}"
    doc = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "picture": profile.get("picture"),
        "username": username,
        "google_sub": profile.get("id"),
        "plan": "free",
        "credits": int(os.getenv("SIGNUP_CREDITS", "100")),
        "auth_type": "google",
        "created_at": now,
    }
    await db.users.insert_one(doc)
    doc.pop("_id", None)
    return doc


def _validate_email(email: str) -> str:
    cleaned = email.strip().lower()
    if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Invalid email format")
    return cleaned


def _validate_password(password: str) -> None:
    if not password or len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")


async def register_with_email(db, email: str, password: str) -> tuple[dict, str]:
    email = _validate_email(email)
    _validate_password(password)
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    name = email.split("@")[0]
    username = f"{name}{uuid.uuid4().hex[:4]}"
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "password_hash": hash_password(password),
        "picture": None,
        "username": username,
        "plan": "free",
        "credits": int(os.getenv("SIGNUP_CREDITS", "100")),
        "auth_type": "email",
        "created_at": now,
    }
    await db.users.insert_one(doc)
    token = create_access_token(user_id, email)
    return doc, token


async def login_with_email(db, email: str, password: str) -> tuple[dict, str]:
    email = _validate_email(email)
    user = await db.users.find_one({"email": email})
    if not user or "password_hash" not in user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    matches, upgrade = verify_password(password, user["password_hash"])
    if not matches:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if upgrade:
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": {"password_hash": hash_password(password)}},
        )
    token = create_access_token(user["user_id"], email)
    safe = await db.users.find_one({"user_id": user["user_id"]}, {"_id": 0, "password_hash": 0})
    return safe or user, token


async def user_from_request(db, request: Request) -> dict:
    token = read_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def build_require_user(get_db: Callable[[], Any]):
    async def require_user(request: Request) -> dict:
        return await user_from_request(get_db(), request)

    return require_user
