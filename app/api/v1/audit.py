"""
API endpoints for Audit Log management.
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.db.session import get_db
from app.services.audit_service import AuditService

router = APIRouter()


# ===== Schemas =====


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: str
    event_type: str
    event_action: str
    severity: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    description: str
    details: Optional[str] = None
    outcome: str
    error_message: Optional[str] = None
    created: datetime


class AuditStatisticsResponse(BaseModel):
    """Audit log statistics response."""

    by_event_type: dict[str, int]
    by_severity: dict[str, int]
    by_outcome: dict[str, int]
    total: int


class PaginatedAuditLogsResponse(BaseModel):
    """Paginated audit logs response."""

    items: List[AuditLogResponse]
    total: int
    limit: int
    offset: int


# ===== Endpoints =====


@router.get(
    "",
    response_model=PaginatedAuditLogsResponse,
    summary="List audit logs",
    description="Query audit logs with filters. Admin only.",
)
async def list_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    event_action: Optional[str] = Query(None, description="Filter by event action"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    outcome: Optional[str] = Query(None, description="Filter by outcome"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    _: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List audit logs with optional filters."""
    service = AuditService(db)

    logs = await service.get_logs(
        limit=limit,
        offset=offset,
        event_type=event_type,
        event_action=event_action,
        user_id=user_id,
        severity=severity,
        outcome=outcome,
        from_date=from_date,
        to_date=to_date,
        ip_address=ip_address,
    )

    return {
        "items": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "event_action": log.event_action,
                "severity": log.severity,
                "user_id": log.user_id,
                "user_email": log.user_email,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "description": log.description,
                "details": log.details,
                "outcome": log.outcome,
                "error_message": log.error_message,
                "created": log.created,
            }
            for log in logs
        ],
        "total": len(logs),  # Note: For full pagination, add count query
        "limit": limit,
        "offset": offset,
    }


@router.get(
    "/security",
    response_model=List[AuditLogResponse],
    summary="Get security events",
    description="Get security-related audit events. Admin only.",
)
async def get_security_events(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000),
    _: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Get security-related events."""
    service = AuditService(db)
    logs = await service.get_security_events(severity=severity, limit=limit)

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "event_action": log.event_action,
            "severity": log.severity,
            "user_id": log.user_id,
            "user_email": log.user_email,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "details": log.details,
            "outcome": log.outcome,
            "error_message": log.error_message,
            "created": log.created,
        }
        for log in logs
    ]


@router.get(
    "/failed-logins",
    response_model=List[AuditLogResponse],
    summary="Get failed login attempts",
    description="Get failed login attempts. Admin only.",
)
async def get_failed_logins(
    ip_address: Optional[str] = Query(None, description="Filter by IP address"),
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    limit: int = Query(100, ge=1, le=1000),
    _: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Get failed login attempts."""
    service = AuditService(db)
    logs = await service.get_failed_logins(
        ip_address=ip_address,
        from_date=from_date,
        limit=limit,
    )

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "event_action": log.event_action,
            "severity": log.severity,
            "user_id": log.user_id,
            "user_email": log.user_email,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "details": log.details,
            "outcome": log.outcome,
            "error_message": log.error_message,
            "created": log.created,
        }
        for log in logs
    ]


@router.get(
    "/user/{user_id}",
    response_model=List[AuditLogResponse],
    summary="Get user activity",
    description="Get activity log for a specific user. Admin only.",
)
async def get_user_activity(
    user_id: str,
    limit: int = Query(50, ge=1, le=500),
    _: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Get activity for a specific user."""
    service = AuditService(db)
    logs = await service.get_user_activity(user_id=user_id, limit=limit)

    return [
        {
            "id": log.id,
            "event_type": log.event_type,
            "event_action": log.event_action,
            "severity": log.severity,
            "user_id": log.user_id,
            "user_email": log.user_email,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "description": log.description,
            "details": log.details,
            "outcome": log.outcome,
            "error_message": log.error_message,
            "created": log.created,
        }
        for log in logs
    ]


@router.get(
    "/statistics",
    response_model=AuditStatisticsResponse,
    summary="Get audit statistics",
    description="Get audit log statistics. Admin only.",
)
async def get_audit_statistics(
    from_date: Optional[datetime] = Query(None, description="Filter from date"),
    to_date: Optional[datetime] = Query(None, description="Filter to date"),
    _: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get audit log statistics."""
    service = AuditService(db)
    return await service.get_statistics(from_date=from_date, to_date=to_date)


@router.delete(
    "/cleanup",
    summary="Cleanup old audit logs",
    description="Delete audit logs older than retention period. Admin only.",
)
async def cleanup_audit_logs(
    retention_days: int = Query(90, ge=7, le=365, description="Retention period in days"),
    _: Any = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cleanup old audit logs."""
    service = AuditService(db)
    deleted = await service.cleanup_old_logs(retention_days=retention_days)

    return {
        "deleted": deleted,
        "message": f"Deleted {deleted} audit logs older than {retention_days} days",
    }
