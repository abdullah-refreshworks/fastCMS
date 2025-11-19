"""Settings API endpoints"""
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.db.session import get_db
from app.core.dependencies import require_admin
from app.services.settings_service import SettingsService

router = APIRouter()


class SettingUpdate(BaseModel):
    key: str
    value: Any
    category: str = "app"
    description: str = None


@router.get("/settings", dependencies=[Depends(require_admin)])
async def get_all_settings(db: AsyncSession = Depends(get_db)):
    """Get all settings (admin only)"""
    service = SettingsService(db)
    return await service.get_all()


@router.get("/settings/{category}", dependencies=[Depends(require_admin)])
async def get_category_settings(
    category: str,
    db: AsyncSession = Depends(get_db),
):
    """Get settings by category (admin only)"""
    service = SettingsService(db)
    return await service.get_category(category)


@router.post("/settings", dependencies=[Depends(require_admin)])
async def update_setting(
    setting: SettingUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a setting (admin only)"""
    service = SettingsService(db)
    result = await service.set(
        key=setting.key,
        value=setting.value,
        category=setting.category,
        description=setting.description,
    )
    return {
        "id": result.id,
        "key": result.key,
        "value": result.value,
        "category": result.category,
    }


@router.delete("/settings/{key}", dependencies=[Depends(require_admin)])
async def delete_setting(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a setting (admin only)"""
    service = SettingsService(db)
    deleted = await service.delete(key)
    return {"deleted": deleted}
