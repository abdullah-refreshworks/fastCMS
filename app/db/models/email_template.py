"""Email template model"""
from sqlalchemy import Column, String, Text, Boolean, DateTime
from app.db.base import Base
from datetime import datetime, timezone


class EmailTemplate(Base):
    """Customizable email templates"""

    __tablename__ = "email_templates"

    id = Column(String(36), primary_key=True)
    key = Column(String(100), unique=True, nullable=False, index=True)  # verification, password_reset, welcome
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text)
    variables = Column(Text)  # JSON list of available variables
    enabled = Column(Boolean, default=True)
    created = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
