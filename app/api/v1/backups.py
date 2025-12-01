"""Backups API endpoints"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.services.backup_service import BackupService
from app.db.models.backup import Backup
from app.db.models.user import User

router = APIRouter()


@router.post("/backups", dependencies=[Depends(require_admin)])
async def create_backup(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new backup (admin only)"""
    service = BackupService(db)
    backup = await service.create_backup(created_by=user.id)

    return {
        "id": backup.id,
        "filename": backup.filename,
        "size_bytes": backup.size_bytes,
        "status": backup.status,
        "created": backup.created.isoformat(),
    }


@router.get("/backups", dependencies=[Depends(require_admin)])
async def list_backups(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List all backups (admin only)"""
    # Get total count
    count_result = await db.execute(select(Backup))
    total = len(count_result.scalars().all())

    # Calculate pagination
    offset = (page - 1) * per_page
    total_pages = (total + per_page - 1) // per_page

    result = await db.execute(
        select(Backup).order_by(Backup.created.desc()).limit(per_page).offset(offset)
    )
    backups = result.scalars().all()

    return {
        "items": [
            {
                "id": b.id,
                "filename": b.filename,
                "size": b.size_bytes,
                "path": b.location,
                "status": b.status,
                "created": b.created.isoformat(),
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
        success = await service.restore_backup(backup_id)
        return {"success": success, "message": "Backup restored successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restore failed: {str(e)}")


@router.delete("/backups/{backup_id}", dependencies=[Depends(require_admin)])
async def delete_backup(
    backup_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a backup (admin only)"""
    service = BackupService(db)
    deleted = await service.delete_backup(backup_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Backup not found")

    return {"deleted": True}
