"""
Admin UI routes for LangGraph plugin.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.dependencies import UserContext, get_optional_user
from app.core.security import create_access_token

router = APIRouter()

# Setup templates with access to both plugin and app templates
PLUGIN_DIR = Path(__file__).parent
APP_DIR = Path(__file__).parent.parent.parent / "app"
templates = Jinja2Templates(directory=[
    str(PLUGIN_DIR / "templates"),
    str(APP_DIR / "admin" / "templates"),
])


def require_admin(user_context: Optional[UserContext] = Depends(get_optional_user)):
    """Check if user is admin, redirect to login if not."""
    if not user_context or user_context.role != "admin":
        return RedirectResponse(url="/admin/login", status_code=302)
    return user_context


@router.get("/", response_class=HTMLResponse)
async def workflows_list(
    request: Request,
    user = Depends(require_admin),
):
    """List all workflows."""
    # If user is not authenticated, require_admin returns RedirectResponse
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "workflows.html",
        {"request": request, "user": user},
    )


@router.get("/editor", response_class=HTMLResponse)
async def workflow_editor_new(
    request: Request,
    user = Depends(require_admin),
):
    """Create new workflow."""
    # If user is not authenticated, require_admin returns RedirectResponse
    if isinstance(user, RedirectResponse):
        return user

    # Generate access token for API calls
    access_token = create_access_token({"sub": user.user_id, "role": user.role})

    return templates.TemplateResponse(
        "visual_editor.html",
        {"request": request, "user": user, "workflow_id": None, "access_token": access_token},
    )


@router.get("/editor/{workflow_id}", response_class=HTMLResponse)
async def workflow_editor(
    request: Request,
    workflow_id: str,
    user = Depends(require_admin),
):
    """Edit existing workflow."""
    # If user is not authenticated, require_admin returns RedirectResponse
    if isinstance(user, RedirectResponse):
        return user

    # Generate access token for API calls
    access_token = create_access_token({"sub": user.user_id, "role": user.role})

    return templates.TemplateResponse(
        "visual_editor.html",
        {"request": request, "user": user, "workflow_id": workflow_id, "access_token": access_token},
    )


@router.get("/executions", response_class=HTMLResponse)
async def executions_list(
    request: Request,
    user = Depends(require_admin),
):
    """List all executions."""
    # If user is not authenticated, require_admin returns RedirectResponse
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "executions.html",
        {"request": request, "user": user},
    )
