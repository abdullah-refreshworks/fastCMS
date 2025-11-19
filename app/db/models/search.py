"""
Full-Text Search models for SQLite FTS5
"""
from sqlalchemy import Column, String, Text, DateTime, Index
from app.db.base import Base
from datetime import datetime, timezone


class SearchIndex(Base):
    """
    Tracks which collections have FTS enabled
    """

    __tablename__ = "search_indexes"

    id = Column(String(36), primary_key=True)
    collection_name = Column(String(100), unique=True, nullable=False, index=True)
    indexed_fields = Column(Text, nullable=False)  # JSON array of field names
    created = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (Index("idx_search_collection", "collection_name"),)
