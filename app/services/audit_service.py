"""
Audit Service for security event logging.

Provides centralized audit logging for security-relevant events.
"""

import json
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.audit_log import AuditLog

logger = get_logger(__name__)


class EventType(str, Enum):
    """Audit event types."""
    AUTH = "auth"
    USER = "user"
    API_KEY = "api_key"
    TWO_FACTOR = "two_factor"
    COLLECTION = "collection"
    RECORD = "record"
    FILE = "file"
    ADMIN = "admin"
    SYSTEM = "system"
    SECURITY = "security"


class EventAction(str, Enum):
    """Audit event actions."""
    # Auth events
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    PASSWORD_CHANGE = "password_change"
    PASSWORD_RESET = "password_reset"

    # User events
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ROLE_CHANGE = "role_change"
    VERIFY_EMAIL = "verify_email"

    # 2FA events
    SETUP = "setup"
    ENABLE = "enable"
    DISABLE = "disable"
    VERIFY = "verify"
    BACKUP_CODES_REGEN = "backup_codes_regen"
    BACKUP_CODE_USED = "backup_code_used"

    # API Key events
    REVOKE = "revoke"
    REVOKE_ALL = "revoke_all"

    # Data events
    EXPORT = "export"
    IMPORT = "import"
    BULK_UPDATE = "bulk_update"
    BULK_DELETE = "bulk_delete"

    # Admin events
    SETTINGS_CHANGE = "settings_change"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"

    # Security events
    RATE_LIMIT = "rate_limit"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCESS_DENIED = "access_denied"


class Severity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Outcome(str, Enum):
    """Event outcome."""
    SUCCESS = "success"
    FAILURE = "failure"
    ERROR = "error"


class AuditService:
    """Service for managing audit logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        event_type: EventType,
        event_action: EventAction,
        description: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        severity: Severity = Severity.INFO,
        outcome: Outcome = Outcome.SUCCESS,
        error_message: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.

        Args:
            event_type: Category of the event
            event_action: Specific action performed
            description: Human-readable description
            user_id: ID of the user performing the action
            user_email: Email of the user (for display)
            ip_address: Client IP address
            user_agent: Client user agent
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            details: Additional event data as dictionary
            severity: Event severity level
            outcome: Event outcome (success/failure/error)
            error_message: Error details if outcome is failure/error

        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            event_type=event_type.value,
            event_action=event_action.value,
            description=description,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details) if details else None,
            severity=severity.value,
            outcome=outcome.value,
            error_message=error_message,
        )

        self.db.add(audit_log)
        await self.db.commit()
        await self.db.refresh(audit_log)

        # Log critical events to application log as well
        if severity == Severity.CRITICAL:
            logger.warning(
                f"AUDIT CRITICAL: {event_type.value}.{event_action.value} - {description}",
                extra={
                    "user_id": user_id,
                    "ip_address": ip_address,
                    "outcome": outcome.value,
                },
            )

        return audit_log

    # Convenience methods for common events

    async def log_login(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        method: str = "password",
    ) -> AuditLog:
        """Log successful login."""
        return await self.log(
            event_type=EventType.AUTH,
            event_action=EventAction.LOGIN,
            description=f"User logged in via {method}",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"method": method},
        )

    async def log_login_failed(
        self,
        email: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        reason: str = "invalid_credentials",
    ) -> AuditLog:
        """Log failed login attempt."""
        return await self.log(
            event_type=EventType.AUTH,
            event_action=EventAction.LOGIN_FAILED,
            description=f"Failed login attempt for {email}",
            user_email=email,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"reason": reason},
            severity=Severity.WARNING,
            outcome=Outcome.FAILURE,
        )

    async def log_logout(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log user logout."""
        return await self.log(
            event_type=EventType.AUTH,
            event_action=EventAction.LOGOUT,
            description="User logged out",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
        )

    async def log_password_change(
        self,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log password change."""
        return await self.log(
            event_type=EventType.AUTH,
            event_action=EventAction.PASSWORD_CHANGE,
            description="Password changed",
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            severity=Severity.WARNING,
        )

    async def log_2fa_event(
        self,
        action: EventAction,
        user_id: str,
        user_email: str,
        ip_address: Optional[str] = None,
        success: bool = True,
    ) -> AuditLog:
        """Log 2FA-related event."""
        descriptions = {
            EventAction.SETUP: "2FA setup initiated",
            EventAction.ENABLE: "2FA enabled",
            EventAction.DISABLE: "2FA disabled",
            EventAction.VERIFY: "2FA verification",
            EventAction.BACKUP_CODES_REGEN: "Backup codes regenerated",
            EventAction.BACKUP_CODE_USED: "Backup code used for login",
        }

        return await self.log(
            event_type=EventType.TWO_FACTOR,
            event_action=action,
            description=descriptions.get(action, f"2FA {action.value}"),
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            severity=Severity.WARNING if action == EventAction.DISABLE else Severity.INFO,
            outcome=Outcome.SUCCESS if success else Outcome.FAILURE,
        )

    async def log_api_key_event(
        self,
        action: EventAction,
        user_id: str,
        user_email: str,
        key_id: Optional[str] = None,
        key_name: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log API key event."""
        descriptions = {
            EventAction.CREATE: f"API key created: {key_name}",
            EventAction.UPDATE: f"API key updated: {key_name}",
            EventAction.DELETE: f"API key deleted: {key_name}",
            EventAction.REVOKE: f"API key revoked: {key_name}",
            EventAction.REVOKE_ALL: "All API keys revoked",
        }

        return await self.log(
            event_type=EventType.API_KEY,
            event_action=action,
            description=descriptions.get(action, f"API key {action.value}"),
            user_id=user_id,
            user_email=user_email,
            resource_type="api_key",
            resource_id=key_id,
            ip_address=ip_address,
            details={"key_name": key_name} if key_name else None,
        )

    async def log_admin_action(
        self,
        action: EventAction,
        user_id: str,
        user_email: str,
        description: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """Log administrative action."""
        return await self.log(
            event_type=EventType.ADMIN,
            event_action=action,
            description=description,
            user_id=user_id,
            user_email=user_email,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            details=details,
            severity=Severity.WARNING,
        )

    async def log_security_event(
        self,
        action: EventAction,
        description: str,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """Log security-related event."""
        severity = Severity.WARNING
        if action in [EventAction.SUSPICIOUS_ACTIVITY, EventAction.ACCESS_DENIED]:
            severity = Severity.CRITICAL

        return await self.log(
            event_type=EventType.SECURITY,
            event_action=action,
            description=description,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            details=details,
            severity=severity,
        )

    # Query methods

    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: Optional[str] = None,
        event_action: Optional[str] = None,
        user_id: Optional[str] = None,
        severity: Optional[str] = None,
        outcome: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        ip_address: Optional[str] = None,
    ) -> List[AuditLog]:
        """
        Query audit logs with filters.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            event_type: Filter by event type
            event_action: Filter by event action
            user_id: Filter by user ID
            severity: Filter by severity
            outcome: Filter by outcome
            from_date: Filter from date
            to_date: Filter to date
            ip_address: Filter by IP address

        Returns:
            List of matching audit logs
        """
        query = select(AuditLog)

        if event_type:
            query = query.where(AuditLog.event_type == event_type)
        if event_action:
            query = query.where(AuditLog.event_action == event_action)
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        if severity:
            query = query.where(AuditLog.severity == severity)
        if outcome:
            query = query.where(AuditLog.outcome == outcome)
        if from_date:
            query = query.where(AuditLog.created >= from_date)
        if to_date:
            query = query.where(AuditLog.created <= to_date)
        if ip_address:
            query = query.where(AuditLog.ip_address == ip_address)

        query = query.order_by(AuditLog.created.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_user_activity(
        self,
        user_id: str,
        limit: int = 50,
    ) -> List[AuditLog]:
        """Get recent activity for a specific user."""
        return await self.get_logs(user_id=user_id, limit=limit)

    async def get_security_events(
        self,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get security-related events."""
        query = select(AuditLog).where(
            AuditLog.event_type.in_([
                EventType.SECURITY.value,
                EventType.AUTH.value,
                EventType.TWO_FACTOR.value,
                EventType.API_KEY.value,
            ])
        )

        if severity:
            query = query.where(AuditLog.severity == severity)

        query = query.order_by(AuditLog.created.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_failed_logins(
        self,
        ip_address: Optional[str] = None,
        from_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get failed login attempts."""
        query = select(AuditLog).where(
            AuditLog.event_type == EventType.AUTH.value,
            AuditLog.event_action == EventAction.LOGIN_FAILED.value,
        )

        if ip_address:
            query = query.where(AuditLog.ip_address == ip_address)
        if from_date:
            query = query.where(AuditLog.created >= from_date)

        query = query.order_by(AuditLog.created.desc()).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_failed_logins(
        self,
        ip_address: str,
        since: datetime,
    ) -> int:
        """Count failed logins from an IP since a given time."""
        query = select(func.count(AuditLog.id)).where(
            AuditLog.event_type == EventType.AUTH.value,
            AuditLog.event_action == EventAction.LOGIN_FAILED.value,
            AuditLog.ip_address == ip_address,
            AuditLog.created >= since,
        )
        result = await self.db.execute(query)
        return result.scalar() or 0

    async def get_statistics(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Get audit log statistics."""
        query = select(AuditLog)

        if from_date:
            query = query.where(AuditLog.created >= from_date)
        if to_date:
            query = query.where(AuditLog.created <= to_date)

        # Get counts by event type
        type_query = select(
            AuditLog.event_type,
            func.count(AuditLog.id).label("count"),
        ).group_by(AuditLog.event_type)

        if from_date:
            type_query = type_query.where(AuditLog.created >= from_date)
        if to_date:
            type_query = type_query.where(AuditLog.created <= to_date)

        type_result = await self.db.execute(type_query)
        by_type = {row.event_type: row.count for row in type_result}

        # Get counts by severity
        severity_query = select(
            AuditLog.severity,
            func.count(AuditLog.id).label("count"),
        ).group_by(AuditLog.severity)

        if from_date:
            severity_query = severity_query.where(AuditLog.created >= from_date)
        if to_date:
            severity_query = severity_query.where(AuditLog.created <= to_date)

        severity_result = await self.db.execute(severity_query)
        by_severity = {row.severity: row.count for row in severity_result}

        # Get counts by outcome
        outcome_query = select(
            AuditLog.outcome,
            func.count(AuditLog.id).label("count"),
        ).group_by(AuditLog.outcome)

        if from_date:
            outcome_query = outcome_query.where(AuditLog.created >= from_date)
        if to_date:
            outcome_query = outcome_query.where(AuditLog.created <= to_date)

        outcome_result = await self.db.execute(outcome_query)
        by_outcome = {row.outcome: row.count for row in outcome_result}

        return {
            "by_event_type": by_type,
            "by_severity": by_severity,
            "by_outcome": by_outcome,
            "total": sum(by_type.values()),
        }

    async def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """Delete audit logs older than retention period."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        result = await self.db.execute(
            delete(AuditLog).where(AuditLog.created < cutoff)
        )
        await self.db.commit()

        deleted = result.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old audit log entries")

        return deleted


# Helper function to get audit service without importing db everywhere
async def get_audit_service(db: AsyncSession) -> AuditService:
    """Factory function to create audit service."""
    return AuditService(db)
