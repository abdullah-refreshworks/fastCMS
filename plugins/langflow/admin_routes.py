"""
Langflow plugin admin UI routes.
"""

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from jinja2 import ChoiceLoader, FileSystemLoader

from app.core.dependencies import UserContext, get_optional_user
from plugins.langflow.config import LangflowConfig

logger = logging.getLogger(__name__)

router = APIRouter()

# Templates directory - include both plugin templates and admin templates
plugin_templates_dir = Path(__file__).parent / "templates"
admin_templates_dir = Path(__file__).parent.parent.parent / "app" / "admin" / "templates"

# Create templates with multiple directories
templates = Jinja2Templates(directory=str(plugin_templates_dir))
templates.env.loader = ChoiceLoader([
    FileSystemLoader(str(plugin_templates_dir)),
    FileSystemLoader(str(admin_templates_dir)),
])


def require_admin(user_context: Optional[UserContext] = Depends(get_optional_user)):
    """Check if user is admin, redirect to login if not."""
    if not user_context or user_context.role != "admin":
        return RedirectResponse(url="/admin/login", status_code=302)
    return user_context


def get_langflow_config() -> LangflowConfig:
    """Get Langflow configuration from environment."""
    return LangflowConfig()


@router.get("/", response_class=HTMLResponse)
async def langflow_admin(
    request: Request,
    user: UserContext = Depends(require_admin),
    config: LangflowConfig = Depends(get_langflow_config),
):
    """
    Langflow admin page.

    Shows embedded Langflow UI or link to external Langflow instance.
    """
    # Handle redirect response from require_admin
    if isinstance(user, RedirectResponse):
        return user

    return templates.TemplateResponse(
        "langflow.html",
        {
            "request": request,
            "user": user,
            "langflow_url": config.langflow_url,
            "embed_ui": config.embed_ui,
            "active": "langflow",
        },
    )
