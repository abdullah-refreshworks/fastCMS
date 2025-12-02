"""
Admin UI routes for LangGraph plugin.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.dependencies import UserContext, get_optional_user
from fastapi.responses import RedirectResponse

router = APIRouter()

# Setup templates with access to both plugin and app templates
PLUGIN_DIR = Path(__file__).parent
APP_DIR = Path(__file__).parent.parent.parent / "app"
templates = Jinja2Templates(directory=[
    str(PLUGIN_DIR / "templates"),
    str(APP_DIR / "admin" / "templates"),
])


def require_admin(user_context: UserContext = Depends(get_optional_user)):
    """Require admin user."""
    if not user_context or user_context.role != "admin":
        return RedirectResponse(url="/admin/login", status_code=302)
    return user_context


@router.get("/", response_class=HTMLResponse)
async def workflows_list(
    request: Request,
    user: UserContext = Depends(require_admin),
):
    """List all workflows."""
    return templates.TemplateResponse(
        "workflows.html",
        {"request": request, "user": user},
    )


@router.get("/editor", response_class=HTMLResponse)
async def workflow_editor_new(
    request: Request,
    user: UserContext = Depends(require_admin),
):
    """Create new workflow."""
    return templates.TemplateResponse(
        "visual_editor.html",
        {"request": request, "user": user, "workflow_id": None},
    )


@router.get("/editor/{workflow_id}", response_class=HTMLResponse)
async def workflow_editor(
    request: Request,
    workflow_id: str,
    user: UserContext = Depends(require_admin),
):
    """Edit existing workflow."""
    return templates.TemplateResponse(
        "visual_editor.html",
        {"request": request, "user": user, "workflow_id": workflow_id},
    )


@router.get("/executions", response_class=HTMLResponse)
async def executions_list(
    request: Request,
    user: UserContext = Depends(require_admin),
):
    """List all executions."""
    return templates.TemplateResponse(
        "executions.html",
        {"request": request, "user": user},
    )
