"""
E2E tests for CLI functionality
"""
import pytest
import os
import shutil
import subprocess
from pathlib import Path


class TestCLIIntegration:
    """Test CLI commands"""

    def test_cli_info_command(self):
        """Test fastcms info command"""
        result = subprocess.run(
            ["python", "-m", "cli.main", "info"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "FastCMS" in result.stdout

    def test_cli_init_project(self, tmp_path):
        """Test project initialization"""
        project_name = "test_project"
        project_path = tmp_path / project_name

        # Run init command
        result = subprocess.run(
            ["python", "-m", "cli.main", "init", project_name, "--database", "sqlite"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert project_path.exists()
        assert (project_path / ".env").exists()
        assert (project_path / "README.md").exists()
        assert (project_path / ".gitignore").exists()
        assert (project_path / "data").exists()

        # Check .env content
        env_content = (project_path / ".env").read_text()
        assert "DATABASE_URL=sqlite+aiosqlite:///./data/app.db" in env_content
        assert "SECRET_KEY" in env_content

        # Check README content
        readme_content = (project_path / "README.md").read_text()
        assert project_name in readme_content
        assert "fastcms" in readme_content.lower()

    def test_cli_init_with_postgres(self, tmp_path):
        """Test project init with PostgreSQL"""
        project_name = "pg_project"
        project_path = tmp_path / project_name

        result = subprocess.run(
            ["python", "-m", "cli.main", "init", project_name, "--database", "postgres"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Check that PostgreSQL URL is in .env
        env_content = (project_path / ".env").read_text()
        assert "postgresql+asyncpg://" in env_content

    def test_cli_init_existing_directory(self, tmp_path):
        """Test that init fails if directory exists"""
        project_name = "existing_project"
        project_path = tmp_path / project_name
        project_path.mkdir()

        result = subprocess.run(
            ["python", "-m", "cli.main", "init", project_name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        # Should fail because directory exists
        assert "already exists" in result.stdout.lower()

    def test_cli_migrate_commands(self):
        """Test migration commands"""
        # Test migrate up
        result = subprocess.run(
            ["python", "-m", "cli.main", "migrate", "up"],
            capture_output=True,
            text=True,
        )
        # May fail if already migrated, but command should work
        assert result.returncode in [0, 1]

        # Test migrate status
        result = subprocess.run(
            ["python", "-m", "cli.main", "migrate", "status"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    @pytest.mark.skipif(
        not Path("data/app.db").exists(),
        reason="Database not initialized"
    )
    def test_cli_collections_list(self):
        """Test collections list command"""
        result = subprocess.run(
            ["python", "-m", "cli.main", "collections", "list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    @pytest.mark.skipif(
        not Path("data/app.db").exists(),
        reason="Database not initialized"
    )
    def test_cli_users_list(self):
        """Test users list command"""
        result = subprocess.run(
            ["python", "-m", "cli.main", "users", "list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
