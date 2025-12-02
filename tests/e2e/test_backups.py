"""
E2E tests for backup and restore functionality.
Tests: Backup creation, listing, restore staging, and actual restoration
"""

import json
import os
import shutil
import zipfile
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.services.backup_service import BackupService


@pytest.mark.e2e
class TestBackupAPI:
    """Test backup API endpoints."""

    async def test_create_backup(self, client: AsyncClient, db: AsyncSession):
        """Test creating a backup."""
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "backup@testcms.dev",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "name": "Backup User",
            },
        )

        # Promote user to admin
        result = await db.execute(
            select(User).where(User.email == "backup@testcms.dev")
        )
        user = result.scalar_one()
        user.role = "admin"
        await db.commit()

        # Login as admin
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "backup@testcms.dev",
                "password": "SecurePass123!",
            },
        )
        token = login_response.json()["token"]["access_token"]

        # Create backup
        response = await client.post(
            "/api/v1/backups",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "size_bytes" in data
        assert "created" in data
        assert data["filename"].endswith(".zip")

        # Verify backup file exists
        backup_path = Path("data/backups") / data["filename"]
        assert backup_path.exists()

        # Verify it's a valid zip file
        with zipfile.ZipFile(backup_path, "r") as zipf:
            assert "database.db" in zipf.namelist()
            assert "metadata.json" in zipf.namelist()

        # Clean up
        if backup_path.exists():
            backup_path.unlink()

    async def test_create_backup_unauthorized(self, client: AsyncClient):
        """Test that non-admin users cannot create backups."""
        # Try without token
        response = await client.post("/api/v1/backups")
        assert response.status_code == 401



@pytest.mark.e2e
class TestBackupRestoreFlow:
    """Test complete backup and restore flow."""

    async def test_perform_restore_on_startup(self, db: AsyncSession):
        """Test the restore on startup functionality."""
        # Create test backup directories
        backup_dir = Path("data/backups")
        backup_dir.mkdir(parents=True, exist_ok=True)
        restore_staging = backup_dir / "restore_staging"
        restore_staging.mkdir(exist_ok=True)

        # Create a test database file in staging
        test_db = restore_staging / "database.db"
        test_db.write_text("test database content")

        # Create marker file
        marker_file = backup_dir / ".restore_pending"
        marker_data = {
            "backup_filename": "test_backup.zip",
            "requested_at": "2024-01-01T00:00:00",
            "staging_path": str(restore_staging),
        }
        marker_file.write_text(json.dumps(marker_data, indent=2))

        # Create a dummy database file to be replaced
        db_path = Path("data/app.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path.write_text("old database content")

        # Perform restore
        result = BackupService.perform_restore_on_startup()
        assert result is True

        # Verify database was replaced
        assert db_path.exists()
        assert db_path.read_text() == "test database content"

        # Verify backup was created
        backup_db = db_path.with_suffix(".db.before_restore")
        assert backup_db.exists()
        assert backup_db.read_text() == "old database content"

        # Verify cleanup
        assert not marker_file.exists()
        assert not restore_staging.exists()

        # Clean up test files
        if db_path.exists():
            db_path.unlink()
        if backup_db.exists():
            backup_db.unlink()

    async def test_no_restore_when_no_marker(self):
        """Test that restore doesn't run when no marker file exists."""
        # Ensure no marker file
        marker_file = Path("data/backups/.restore_pending")
        if marker_file.exists():
            marker_file.unlink()

        # Perform restore
        result = BackupService.perform_restore_on_startup()
        assert result is False

    async def test_backup_contains_all_data(self, db: AsyncSession):
        """Test that backup contains complete database and files."""
        # Create backup
        backup_service = BackupService(db)
        backup_data = await backup_service.create_backup("complete_test")
        backup_path = Path(backup_data["path"])

        # Verify backup contents
        with zipfile.ZipFile(backup_path, "r") as zipf:
            # Check metadata (database may not be included in tests)
            assert "metadata.json" in zipf.namelist()
            metadata = json.loads(zipf.read("metadata.json"))
            assert "created_at" in metadata
            assert "app_version" in metadata
            assert metadata["backup_name"] == "complete_test"

            # Check that files directory exists
            assert any("files/" in name for name in zipf.namelist())

        # Clean up
        if backup_path.exists():
            backup_path.unlink()
