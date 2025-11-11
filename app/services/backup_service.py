"""Backup service for creating system backups"""
import os
import zipfile
import shutil
from datetime import datetime, timezone
from pathlib import Path
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.readonly import ReadOnlyContext
from app.core.config import settings
from app.db.models.backup import Backup
from app.core.logging import get_logger

logger = get_logger(__name__)


class BackupService:
    """Service for system backups"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backup_dir = Path("./data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def create_backup(self, created_by: Optional[str] = None) -> Backup:
        """
        Create a full system backup

        Args:
            created_by: Optional user ID who initiated backup

        Returns:
            Backup record
        """
        backup_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}_{backup_id[:8]}.zip"
        backup_path = self.backup_dir / filename

        # Create backup record
        backup = Backup(
            id=backup_id,
            filename=filename,
            size_bytes=0,
            location="local",
            status="pending",
            created_by=created_by,
        )
        self.db.add(backup)
        await self.db.commit()

        try:
            # Enable read-only mode during backup
            async with ReadOnlyContext("Backup in progress"):
                # Create ZIP archive
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    # Backup database
                    if os.path.exists("./data/app.db"):
                        zipf.write("./data/app.db", "app.db")

                    # Backup files
                    files_dir = Path("./data/files")
                    if files_dir.exists():
                        for file_path in files_dir.rglob("*"):
                            if file_path.is_file():
                                arcname = file_path.relative_to("./data")
                                zipf.write(file_path, arcname)

                    # Backup .env
                    if os.path.exists(".env"):
                        zipf.write(".env", ".env")

                # Update backup record
                backup.size_bytes = backup_path.stat().st_size
                backup.status = "completed"
                backup.completed_at = datetime.now(timezone.utc)
                await self.db.commit()

                logger.info(f"Backup created: {filename} ({backup.size_bytes} bytes)")

        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            backup.status = "failed"
            backup.error = str(e)
            await self.db.commit()
            raise

        return backup

    async def restore_backup(self, backup_id: str) -> bool:
        """
        Restore from a backup

        Args:
            backup_id: Backup ID to restore

        Returns:
            Success status
        """
        from sqlalchemy import select

        result = await self.db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup or backup.status != "completed":
            raise ValueError("Backup not found or not completed")

        backup_path = self.backup_dir / backup.filename

        if not backup_path.exists():
            raise ValueError("Backup file not found")

        try:
            async with ReadOnlyContext("Restore in progress"):
                # Extract ZIP archive
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall("./data")

                logger.info(f"Backup restored: {backup.filename}")
                return True

        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            raise

    async def delete_backup(self, backup_id: str) -> bool:
        """Delete a backup"""
        from sqlalchemy import select, delete

        result = await self.db.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()

        if not backup:
            return False

        # Delete file
        backup_path = self.backup_dir / backup.filename
        if backup_path.exists():
            backup_path.unlink()

        # Delete record
        await self.db.execute(delete(Backup).where(Backup.id == backup_id))
        await self.db.commit()

        return True
