"""Google OAuth 2.0 flow: login redirect, callback, and token issuance."""

from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Request
from fastapi.responses import RedirectResponse
from jose import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.settings import settings
from app.models.user_models import User

_GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

_SCOPES = "openid email profile"


def _build_auth_url(state: str = "") -> str:
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": _SCOPES,
        "access_type": "offline",
        "state": state,
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{_GOOGLE_AUTH_URL}?{query}"


async def _exchange_code(code: str) -> dict:
    """Exchange authorization code for Google tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            _GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    if resp.status_code != 200:
        raise AppError(502, "OAuthError", "Failed to exchange code with Google.")
    return resp.json()


async def _get_userinfo(access_token: str) -> dict:
    """Fetch user profile from Google using an access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            _GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
    if resp.status_code != 200:
        raise AppError(502, "OAuthError", "Failed to fetch user info from Google.")
    return resp.json()


async def _upsert_user(db: AsyncSession, userinfo: dict) -> User:
    """Insert or update a User row from Google userinfo payload."""
    google_sub = userinfo.get("sub", "")
    email = userinfo.get("email", "")

    result = await db.execute(select(User).where(User.google_sub == google_sub))
    user = result.scalar_one_or_none()

    if user is None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            full_name=userinfo.get("name"),
            google_sub=google_sub,
            avatar_url=userinfo.get("picture"),
            status="active",
        )
        db.add(user)
    else:
        user.full_name = userinfo.get("name", user.full_name)
        user.avatar_url = userinfo.get("picture", user.avatar_url)
        user.google_sub = google_sub

    await db.flush()
    return user


def _issue_jwt(user: User) -> str:
    """Create a signed JWT for the given user."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def login_redirect(_request: Request) -> RedirectResponse:
    """Redirect the browser to Google's OAuth consent screen."""
    return RedirectResponse(_build_auth_url())


async def oauth_callback(request: Request, db: AsyncSession) -> RedirectResponse:
    """Handle Google OAuth callback: exchange code, upsert user, issue JWT."""
    code = request.query_params.get("code")
    if not code:
        raise AppError(400, "OAuthError", "Missing authorization code.")

    tokens = await _exchange_code(code)
    userinfo = await _get_userinfo(tokens["access_token"])
    user = await _upsert_user(db, userinfo)
    jwt_token = _issue_jwt(user)

    origins = settings.cors_origins_list
    frontend_url = origins[0] if origins else "http://localhost:3000"
    return RedirectResponse(f"{frontend_url}/login?token={jwt_token}")
