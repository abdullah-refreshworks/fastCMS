"""Backup and restore API endpoints (admin only)."""
from typing import List
from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.services.backup_service import BackupService

router = APIRouter()


class BackupCreate(BaseModel):
    """Schema for creating a backup."""

    name: str | None = None


class BackupResponse(BaseModel):
    """Response schema for backup metadata."""

    filename: str
    name: str
    size: int
    size_mb: float
    created: str
    app_version: str | None = None


class BackupCreateResponse(BaseModel):
    """Response schema for backup creation."""

    filename: str
    name: str
    size: int
    size_mb: float
    created: str
    path: str


class RestoreResponse(BaseModel):
    """Response schema for restore operation."""

    status: str
    message: str
    restored_at: str


@router.post("/backups", response_model=BackupCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_backup(
    data: BackupCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Create a new backup of the database and files.

    - **Admin only**
    - Creates a compressed backup including database and uploaded files
    - Stored in data/backups/ directory
    """
    service = BackupService(db)
    return await service.create_backup(name=data.name)


@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    List all available backups.

    - **Admin only**
    - Returns metadata for all backup files
    """
    service = BackupService(db)
    return await service.list_backups()


@router.get("/backups/{filename}/download")
async def download_backup(
    filename: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Download a backup file.

    - **Admin only**
    - Returns the backup as a ZIP file
    """
    service = BackupService(db)
    backup_path = await service.download_backup(filename)

    return FileResponse(
        path=backup_path,
        filename=filename,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/backups/{filename}/restore", response_model=RestoreResponse)
async def restore_backup(
    filename: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Restore from a backup file.

    ⚠️ **WARNING**: This will overwrite the current database and files!

    - **Admin only**
    - Backs up current data before restoring
    - Server restart required after restore
    """
    service = BackupService(db)
    return await service.restore_backup(filename)


@router.delete("/backups/{filename}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup(
    filename: str,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Delete a backup file.

    - **Admin only**
    - Permanently deletes the backup file
    """
    service = BackupService(db)
    await service.delete_backup(filename)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
