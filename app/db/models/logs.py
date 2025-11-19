"""Request logs model"""
from sqlalchemy import Column, String, Integer, Text, DateTime, Index
from app.db.base import Base
from datetime import datetime, timezone


class RequestLog(Base):
    """Request logs for all API calls"""

    __tablename__ = "request_logs"

    id = Column(String(36), primary_key=True)
    method = Column(String(10), nullable=False, index=True)
    url = Column(Text, nullable=False)
    status_code = Column(Integer, nullable=False, index=True)
    duration_ms = Column(Integer, nullable=False)  # milliseconds
    user_agent = Column(Text)
    ip_address = Column(String(45), index=True)
    auth_user_id = Column(String(36), index=True)
    request_body = Column(Text)
    response_body = Column(Text)
    error = Column(Text)
    created = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    __table_args__ = (
        Index("idx_logs_created", "created"),
        Index("idx_logs_status", "status_code"),
        Index("idx_logs_user", "auth_user_id"),
    )
