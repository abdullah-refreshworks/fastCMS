"""Service for database backup and restore operations."""
import os
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import json

from app.core.config import settings
from app.core.exceptions import BadRequestException, NotFoundException


class BackupService:
    """Service for managing database backups and restores."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.backup_dir = Path("data/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(settings.DATABASE_URL.replace("sqlite+aiosqlite:///./", ""))

    async def create_backup(self, name: Optional[str] = None) -> dict:
        """
        Create a complete backup of the database and uploaded files.

        Returns:
            dict: Backup metadata including filename, size, and path
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        backup_filename = f"{backup_name}.zip"
        backup_path = self.backup_dir / backup_filename

        try:
            with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Backup database file
                if self.db_path.exists():
                    zipf.write(self.db_path, "database.db")

                # Backup uploaded files
                files_dir = Path(settings.LOCAL_STORAGE_PATH)
                if files_dir.exists():
                    for file_path in files_dir.rglob("*"):
                        if file_path.is_file():
                            arcname = f"files/{file_path.relative_to(files_dir)}"
                            zipf.write(file_path, arcname)

                # Add metadata
                metadata = {
                    "created_at": datetime.utcnow().isoformat(),
                    "app_version": settings.APP_VERSION,
                    "backup_name": backup_name,
                }
                zipf.writestr("metadata.json", json.dumps(metadata, indent=2))

            # Get backup file size
            backup_size = backup_path.stat().st_size

            return {
                "filename": backup_filename,
                "name": backup_name,
                "size": backup_size,
                "size_mb": round(backup_size / (1024 * 1024), 2),
                "created": datetime.utcnow().isoformat(),
                "path": str(backup_path),
            }

        except Exception as e:
            # Clean up failed backup
            if backup_path.exists():
                backup_path.unlink()
            raise BadRequestException(f"Failed to create backup: {str(e)}")

    async def list_backups(self) -> List[dict]:
        """
        List all available backups.

        Returns:
            List of backup metadata
        """
        backups = []

        for backup_file in self.backup_dir.glob("*.zip"):
            try:
                # Get file stats
                stat = backup_file.stat()
                size = stat.st_size
                created = datetime.fromtimestamp(stat.st_mtime)

                # Try to read metadata from zip
                metadata = {}
                try:
                    with zipfile.ZipFile(backup_file, "r") as zipf:
                        if "metadata.json" in zipf.namelist():
                            metadata = json.loads(zipf.read("metadata.json"))
                except Exception:
                    pass

                backups.append(
                    {
                        "filename": backup_file.name,
                        "name": backup_file.stem,
                        "size": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "created": metadata.get("created_at", created.isoformat()),
                        "app_version": metadata.get("app_version", "unknown"),
                    }
                )
            except Exception:
                continue

        # Sort by creation time, newest first
        backups.sort(key=lambda x: x["created"], reverse=True)
        return backups

    async def restore_backup(self, filename: str) -> dict:
        """
        Restore database and files from a backup.

        WARNING: This will overwrite the current database and files!

        Args:
            filename: Name of the backup file to restore

        Returns:
            dict: Restoration status and metadata
        """
        backup_path = self.backup_dir / filename

        if not backup_path.exists():
            raise NotFoundException(f"Backup file '{filename}' not found")

        try:
            # Create temporary restore directory
            temp_dir = self.backup_dir / "temp_restore"
            temp_dir.mkdir(exist_ok=True)

            # Extract backup
            with zipfile.ZipFile(backup_path, "r") as zipf:
                zipf.extractall(temp_dir)

            # Close database connections (important!)
            # This should be handled by the caller before calling restore

            # Restore database
            db_backup = temp_dir / "database.db"
            if db_backup.exists():
                # Backup current database first
                if self.db_path.exists():
                    current_backup = self.db_path.with_suffix(".db.bak")
                    shutil.copy2(self.db_path, current_backup)

                # Replace with backup
                shutil.copy2(db_backup, self.db_path)

            # Restore files
            files_backup = temp_dir / "files"
            if files_backup.exists():
                files_dir = Path(settings.LOCAL_STORAGE_PATH)

                # Backup current files
                if files_dir.exists():
                    current_files_backup = files_dir.parent / f"{files_dir.name}_bak"
                    if current_files_backup.exists():
                        shutil.rmtree(current_files_backup)
                    shutil.copytree(files_dir, current_files_backup)
                    shutil.rmtree(files_dir)

                # Restore from backup
                shutil.copytree(files_backup, files_dir)

            # Clean up temp directory
            shutil.rmtree(temp_dir)

            return {
                "status": "success",
                "message": f"Successfully restored backup '{filename}'",
                "restored_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            # Clean up temp directory on failure
            temp_dir = self.backup_dir / "temp_restore"
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            raise BadRequestException(f"Failed to restore backup: {str(e)}")

    async def delete_backup(self, filename: str) -> None:
        """
        Delete a backup file.

        Args:
            filename: Name of the backup file to delete
        """
        backup_path = self.backup_dir / filename

        if not backup_path.exists():
            raise NotFoundException(f"Backup file '{filename}' not found")

        try:
            backup_path.unlink()
        except Exception as e:
            raise BadRequestException(f"Failed to delete backup: {str(e)}")

    async def download_backup(self, filename: str) -> Path:
        """
        Get path to a backup file for download.

        Args:
            filename: Name of the backup file

        Returns:
            Path to the backup file
        """
        backup_path = self.backup_dir / filename

        if not backup_path.exists():
            raise NotFoundException(f"Backup file '{filename}' not found")

        return backup_path
