"""Request logging service"""
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.db.models.logs import RequestLog
from app.core.logging import get_logger

logger = get_logger(__name__)


class LogService:
    """Service for request logs"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_log(
        self,
        method: str,
        url: str,
        status_code: int,
        duration_ms: int,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        auth_user_id: Optional[str] = None,
        request_body: Optional[str] = None,
        response_body: Optional[str] = None,
        error: Optional[str] = None,
    ) -> RequestLog:
        """Create a request log entry"""
        log = RequestLog(
            id=str(uuid.uuid4()),
            method=method,
            url=url,
            status_code=status_code,
            duration_ms=duration_ms,
            user_agent=user_agent,
            ip_address=ip_address,
            auth_user_id=auth_user_id,
            request_body=request_body,
            response_body=response_body,
            error=error,
        )
        self.db.add(log)
        await self.db.commit()
        return log

    async def get_logs(
        self,
        limit: int = 100,
        offset: int = 0,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        user_id: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[RequestLog]:
        """Get logs with filters"""
        query = select(RequestLog)

        if method:
            query = query.where(RequestLog.method == method)
        if status_code:
            query = query.where(RequestLog.status_code == status_code)
        if user_id:
            query = query.where(RequestLog.auth_user_id == user_id)
        if from_date:
            query = query.where(RequestLog.created >= from_date)
        if to_date:
            query = query.where(RequestLog.created <= to_date)

        query = query.order_by(RequestLog.created.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def cleanup_old_logs(self, retention_days: int = 7) -> int:
        """Delete logs older than retention period"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

        result = await self.db.execute(
            delete(RequestLog).where(RequestLog.created < cutoff)
        )
        await self.db.commit()

        deleted = result.rowcount
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old log entries")

        return deleted

    async def get_statistics(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> dict:
        """Get log statistics"""
        query = select(
            func.count(RequestLog.id).label("total"),
            func.avg(RequestLog.duration_ms).label("avg_duration"),
            func.count(
                func.case((RequestLog.status_code >= 500, 1))
            ).label("errors_5xx"),
            func.count(
                func.case((RequestLog.status_code >= 400, 1))
            ).label("errors_4xx"),
        )

        if from_date:
            query = query.where(RequestLog.created >= from_date)
        if to_date:
            query = query.where(RequestLog.created <= to_date)

        result = await self.db.execute(query)
        row = result.first()

        return {
            "total_requests": row.total or 0,
            "avg_duration_ms": round(row.avg_duration or 0, 2),
            "errors_5xx": row.errors_5xx or 0,
            "errors_4xx": row.errors_4xx or 0,
        }
