"""
Admin dashboard UI routes.
Serves HTML pages for admin interface.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import UserContext, get_optional_user
from app.db.session import get_db

# Setup templates
ADMIN_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(ADMIN_DIR / "templates"))

router = APIRouter()


def require_admin_ui(user_context: Optional[UserContext] = Depends(get_optional_user)):
    """Check if user is admin, redirect to login if not."""
    if not user_context or user_context.role != "admin":
        return RedirectResponse(url="/admin/login", status_code=302)
    return user_context


@router.get("/", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    user: UserContext = Depends(require_admin_ui),
    db: AsyncSession = Depends(get_db),
):
    """Admin dashboard home page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "user": user, "active": "dashboard"},
    )


@router.get("/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    user: UserContext = Depends(require_admin_ui),
):
    """User management page."""
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "user": user, "active": "users"},
    )


@router.get("/collections", response_class=HTMLResponse)
async def admin_collections(
    request: Request,
    user: UserContext = Depends(require_admin_ui),
):
    """Collection management page."""
    return templates.TemplateResponse(
        "collections.html",
        {"request": request, "user": user, "active": "collections"},
    )


@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    """Admin login page."""
    return templates.TemplateResponse("login.html", {"request": request})
