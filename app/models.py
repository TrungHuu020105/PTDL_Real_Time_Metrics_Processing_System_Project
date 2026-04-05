"""SQLAlchemy ORM models"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from app.database import Base


class Metric(Base):
    """Metric record model"""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), index=True, nullable=False)  # cpu, memory, request_count
    value = Column(Float, nullable=False)
    source = Column(String(100), nullable=False)  # e.g., "server_1", "server_2"
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), index=True, nullable=False)

    # Composite index for efficient time-range queries
    __table_args__ = (
        Index('idx_metric_type_timestamp', 'metric_type', 'timestamp'),
    )

    def __repr__(self):
        return f"<Metric(type={self.metric_type}, value={self.value}, source={self.source}, time={self.timestamp})>"
