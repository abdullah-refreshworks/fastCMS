"""Backups API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.services.backup_service import BackupService
from app.db.models.user import User

router = APIRouter()


@router.post("/backups", dependencies=[Depends(require_admin)])
async def create_backup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new backup (admin only)"""
    service = BackupService(db)
    backup = await service.create_backup()

    return {
        "id": backup["name"],
        "filename": backup["filename"],
        "size_bytes": backup["size"],
        "status": "completed",
        "created": backup["created"],
    }


@router.get("/backups", dependencies=[Depends(require_admin)])
async def list_backups(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all backups (admin only)"""
    service = BackupService(db)
    all_backups = await service.list_backups()

    # Calculate pagination
    total = len(all_backups)
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page

    # Get page of backups
    backups = all_backups[offset:offset + per_page]

    return {
        "items": [
            {
                "id": b["name"],
                "filename": b["filename"],
                "size": b["size"],
                "path": b["filename"],
                "status": "completed",
                "created": b["created"],
            }
            for b in backups
        ],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
    }


@router.post("/backups/{backup_id}/restore", dependencies=[Depends(require_admin)])
async def restore_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Restore from a backup (admin only)"""
    service = BackupService(db)
    try:
        # backup_id is the filename (without .zip or with .zip)
        filename = backup_id if backup_id.endswith(".zip") else f"{backup_id}.zip"
        result = await service.restore_backup(filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/backups/{backup_id}", dependencies=[Depends(require_admin)])
async def delete_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a backup (admin only)"""
    service = BackupService(db)
    try:
        # backup_id is the filename (without .zip or with .zip)
        filename = backup_id if backup_id.endswith(".zip") else f"{backup_id}.zip"
        await service.delete_backup(filename)
        return {"deleted": True}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
