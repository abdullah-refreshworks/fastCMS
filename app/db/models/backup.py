"""Backup records model"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from app.db.base import Base
from datetime import datetime, timezone


class Backup(Base):
    """Backup records"""

    __tablename__ = "backups"

    id = Column(String(36), primary_key=True)
    filename = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    location = Column(String(20), nullable=False)  # local or s3
    s3_key = Column(String(500))
    status = Column(String(20), nullable=False, index=True)  # pending, completed, failed
    error = Column(Text)
    created_by = Column(String(36))
    created = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    completed_at = Column(DateTime)
