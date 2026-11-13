
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String
from sqlalchemy.sql import func

from src.utils.db import Base

class OutboxEvent(Base):
    __tablename__ = "outbox_event"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        String(36),
        unique=True,
        nullable=False,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )

    event_type = Column(String(100), nullable=False)
    topic = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)

    published = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    published_at = Column(DateTime(timezone=True), nullable=True)

class ProcessedEvent(Base):
    __tablename__ = "processed_event"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(
        String(36),
        unique=True,
        nullable=False,
        index=True,
    )

    processed_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )