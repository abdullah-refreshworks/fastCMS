"""Settings model"""
from sqlalchemy import Column, String, Text, JSON, DateTime
from app.db.base import Base
from datetime import datetime, timezone


class Setting(Base):
    """System settings"""

    __tablename__ = "settings"

    id = Column(String(36), primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    category = Column(String(50), nullable=False, index=True)  # app, mail, backup, storage, logs
    description = Column(Text)
    created = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
