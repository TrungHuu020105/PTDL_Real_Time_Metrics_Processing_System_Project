"""SQLAlchemy ORM models"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, Float, String, DateTime, Index
from app.database import Base


class Metric(Base):
    """Metric record model"""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), index=True, nullable=False)  # cpu, memory
    value = Column(Float, nullable=False)
    source = Column(String(100), nullable=False)  # e.g., "server_1", "server_2"
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), index=True, nullable=False)

    # Composite index for efficient time-range queries
    __table_args__ = (
        Index('idx_metric_type_timestamp', 'metric_type', 'timestamp'),
    )

    def __repr__(self):
        return f"<Metric(type={self.metric_type}, value={self.value}, source={self.source}, time={self.timestamp})>"


class Alert(Base):
    """Alert record model - stores triggered alerts"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), index=True, nullable=False)  # cpu, memory, temperature, etc
    status = Column(String(20), index=True, nullable=False)  # 'warning' or 'critical'
    current_value = Column(Float, nullable=False)  # Current metric value when alert triggered
    threshold = Column(Float, nullable=False)  # Threshold that was exceeded
    message = Column(String(255), nullable=False)  # Alert message
    source = Column(String(100), nullable=False, default="system")  # Source of the metric
    created_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), index=True, nullable=False)
    resolved_at = Column(DateTime, nullable=True)  # When alert was resolved (if applicable)

    # Composite index for efficient querying
    __table_args__ = (
        Index('idx_alert_status_created', 'status', 'created_at'),
        Index('idx_alert_metric_created', 'metric_type', 'created_at'),
    )

    def __repr__(self):
        return f"<Alert(type={self.metric_type}, status={self.status}, value={self.current_value}, at={self.created_at})>"
