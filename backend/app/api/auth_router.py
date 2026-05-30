"""Authentication endpoints: Google OAuth login, callback, and current user."""

from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_dependencies import get_current_user
from app.auth.google_oauth import login_redirect, oauth_callback
from app.core.database import get_db
from app.models.user_models import User

router = APIRouter()


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    avatar_url: str | None
    status: str

    model_config = {"from_attributes": True}


@router.get("/login", response_class=RedirectResponse)
async def login(request: Request) -> RedirectResponse:
    """Redirect to Google OAuth consent screen."""
    return login_redirect(request)


@router.get("/callback", response_class=RedirectResponse)
async def callback(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    """Exchange Google auth code, upsert user, issue JWT, redirect to frontend."""
    return await oauth_callback(request, db)


@router.get("/me", response_model=UserOut)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the currently authenticated user's profile."""
    return current_user
