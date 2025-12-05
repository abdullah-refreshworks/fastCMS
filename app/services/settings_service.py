"""Settings management service"""
import uuid
import json
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.models.settings import Setting
from app.core.logging import get_logger

logger = get_logger(__name__)


class SettingsService:
    """Service for system settings management"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Dict[str, Any] = {}

    async def get(self, key: str, default: Any = None) -> Any:
        """Get setting value by key"""
        if key in self._cache:
            return self._cache[key]

        result = await self.db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            self._cache[key] = setting.value
            return setting.value

        return default

    async def set(
        self,
        key: str,
        value: Any,
        category: str = "app",
        description: Optional[str] = None
    ) -> Setting:
        """Set or update setting"""
        result = await self.db.execute(select(Setting).where(Setting.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
            setting.updated = datetime.now(timezone.utc)
            if description:
                setting.description = description
        else:
            setting = Setting(
                id=str(uuid.uuid4()),
                key=key,
                value=value,
                category=category,
                description=description,
            )
            self.db.add(setting)

        await self.db.commit()
        self._cache[key] = value

        logger.info(f"Setting updated: {key}")
        return setting

    async def get_category(self, category: str) -> Dict[str, Any]:
        """Get all settings in a category"""
        result = await self.db.execute(
            select(Setting).where(Setting.category == category)
        )
        settings = result.scalars().all()
        return {s.key: {"value": s.value, "description": s.description} for s in settings}

    async def get_all(self) -> Dict[str, Dict[str, Any]]:
        """Get all settings grouped by category"""
        result = await self.db.execute(select(Setting))
        settings = result.scalars().all()

        grouped = {}
        for setting in settings:
            if setting.category not in grouped:
                grouped[setting.category] = {}
            grouped[setting.category][setting.key] = {
                "value": setting.value,
                "description": setting.description,
            }

        return grouped

    async def delete(self, key: str) -> bool:
        """Delete a setting"""
        from sqlalchemy import delete as sql_delete

        result = await self.db.execute(
            sql_delete(Setting).where(Setting.key == key)
        )
        await self.db.commit()

        if key in self._cache:
            del self._cache[key]

        return result.rowcount > 0

    def clear_cache(self) -> None:
        """Clear settings cache"""
        self._cache.clear()


# Default settings
DEFAULT_SETTINGS = {
    "app": {
        "app_name": {"value": "FastCMS", "description": "Application name"},
        "app_url": {"value": "http://localhost:8000", "description": "Application URL"},
        "rate_limit_per_minute": {"value": 100, "description": "Rate limit per minute"},
        "rate_limit_per_hour": {"value": 1000, "description": "Rate limit per hour"},
    },
    "auth": {
        "password_auth_enabled": {"value": True, "description": "Enable password authentication"},
        "otp_enabled": {"value": False, "description": "Enable OTP (email code) authentication"},
        "mfa_enabled": {"value": False, "description": "Enable Multi-Factor Authentication"},
        "oauth_enabled": {"value": True, "description": "Enable OAuth2 authentication"},
        "oauth_auto_create_user": {"value": True, "description": "Auto-create user on first OAuth login"},
        "oauth_link_by_email": {"value": True, "description": "Link OAuth to existing user by email"},
        "password_min_length": {"value": 8, "description": "Minimum password length"},
        "password_require_upper": {"value": False, "description": "Require uppercase letter"},
        "password_require_number": {"value": False, "description": "Require number"},
        "password_require_special": {"value": False, "description": "Require special character"},
        "token_expiry_hours": {"value": 24, "description": "Access token expiry (hours)"},
        "refresh_token_expiry_days": {"value": 7, "description": "Refresh token expiry (days)"},
        "verification_required": {"value": False, "description": "Require email verification"},
    },
    "mail": {
        "smtp_host": {"value": "", "description": "SMTP server host"},
        "smtp_port": {"value": 587, "description": "SMTP server port"},
        "smtp_user": {"value": "", "description": "SMTP username"},
        "smtp_password": {"value": "", "description": "SMTP password"},
        "from_email": {"value": "noreply@fastcms.dev", "description": "From email address"},
        "from_name": {"value": "FastCMS", "description": "From name"},
    },
    "backup": {
        "enabled": {"value": True, "description": "Enable automated backups"},
        "cron_schedule": {"value": "0 2 * * *", "description": "Cron schedule (2 AM daily)"},
        "retention_days": {"value": 30, "description": "Keep backups for N days"},
        "s3_enabled": {"value": False, "description": "Upload to S3"},
        "s3_bucket": {"value": "", "description": "S3 bucket name"},
    },
    "storage": {
        "type": {"value": "local", "description": "Storage type (local/s3/azure)"},
        "max_file_size": {"value": 10485760, "description": "Max file size (10MB)"},
        # S3 settings
        "s3_bucket": {"value": "", "description": "S3 bucket name"},
        "s3_region": {"value": "", "description": "S3 region"},
        "s3_access_key": {"value": "", "description": "S3 access key"},
        "s3_secret_key": {"value": "", "description": "S3 secret key"},
        "s3_endpoint": {"value": "", "description": "S3 custom endpoint (optional)"},
        # Azure settings
        "azure_container": {"value": "", "description": "Azure container name"},
        "azure_connection_string": {"value": "", "description": "Azure connection string"},
        "azure_account_name": {"value": "", "description": "Azure storage account name"},
        "azure_account_key": {"value": "", "description": "Azure storage account key"},
    },
    "logs": {
        "enabled": {"value": True, "description": "Enable request logging"},
        "retention_days": {"value": 7, "description": "Keep logs for N days"},
        "log_body": {"value": False, "description": "Log request/response bodies"},
    },
}


async def init_default_settings(db: AsyncSession) -> None:
    """Initialize default settings if not exist"""
    service = SettingsService(db)

    for category, settings in DEFAULT_SETTINGS.items():
        for key, data in settings.items():
            existing = await service.get(key)
            if existing is None:
                await service.set(
                    key=key,
                    value=data["value"],
                    category=category,
                    description=data["description"],
                )

    logger.info("Default settings initialized")
