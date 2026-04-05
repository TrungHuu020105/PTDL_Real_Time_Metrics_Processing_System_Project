"""CRUD operations for database"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Metric
from app.schemas import MetricCreate


def create_metric(db: Session, metric: MetricCreate) -> Metric:
    """Create a single metric record"""
    # Use provided timestamp or current time (Vietnam timezone UTC+7)
    vietnam_tz = timezone(timedelta(hours=7))
    timestamp = metric.timestamp if metric.timestamp else datetime.now(vietnam_tz)
    
    db_metric = Metric(
        metric_type=metric.metric_type,
        value=metric.value,
        source=metric.source,
        timestamp=timestamp
    )
    db.add(db_metric)
    db.commit()
    db.refresh(db_metric)
    return db_metric


def create_metrics_bulk(db: Session, metrics: List[MetricCreate]) -> List[Metric]:
    """Create multiple metric records"""
    db_metrics = []
    for metric in metrics:
        vietnam_tz = timezone(timedelta(hours=7))
        timestamp = metric.timestamp if metric.timestamp else datetime.now(vietnam_tz)
        db_metric = Metric(
            metric_type=metric.metric_type,
            value=metric.value,
            source=metric.source,
            timestamp=timestamp
        )
        db_metrics.append(db_metric)
    
    db.add_all(db_metrics)
    db.commit()
    
    # Refresh all objects to get IDs
    for metric in db_metrics:
        db.refresh(metric)
    
    return db_metrics


def get_latest_metrics(db: Session) -> tuple:
    """Get latest values for each metric type"""
    latest_cpu = db.query(Metric).filter(
        Metric.metric_type == "cpu"
    ).order_by(Metric.timestamp.desc()).first()
    
    latest_memory = db.query(Metric).filter(
        Metric.metric_type == "memory"
    ).order_by(Metric.timestamp.desc()).first()
    
    latest_request_count = db.query(Metric).filter(
        Metric.metric_type == "request_count"
    ).order_by(Metric.timestamp.desc()).first()
    
    return latest_cpu, latest_memory, latest_request_count


def get_metrics_history(
    db: Session,
    metric_type: str,
    minutes: int = 5
) -> List[Metric]:
    """Get historical metrics for a specific type within a time range"""
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(minutes=minutes)
    
    metrics = db.query(Metric).filter(
        Metric.metric_type == metric_type,
        Metric.timestamp >= time_threshold
    ).order_by(Metric.timestamp.asc()).all()
    
    return metrics


def get_metrics_in_range(
    db: Session,
    metric_type: str,
    minutes: int
) -> List[Metric]:
    """Get metrics within a time range"""
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(minutes=minutes)
    
    metrics = db.query(Metric).filter(
        Metric.metric_type == metric_type,
        Metric.timestamp >= time_threshold
    ).order_by(Metric.timestamp.asc()).all()
    
    return metrics


def get_all_metrics_in_range(db: Session, minutes: int) -> tuple:
    """Get all metric types within a time range"""
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(minutes=minutes)
    
    cpu_metrics = db.query(Metric).filter(
        Metric.metric_type == "cpu",
        Metric.timestamp >= time_threshold
    ).all()
    
    memory_metrics = db.query(Metric).filter(
        Metric.metric_type == "memory",
        Metric.timestamp >= time_threshold
    ).all()
    
    request_count_metrics = db.query(Metric).filter(
        Metric.metric_type == "request_count",
        Metric.timestamp >= time_threshold
    ).all()
    
    return cpu_metrics, memory_metrics, request_count_metrics


def delete_old_metrics(db: Session, days: int = 30) -> int:
    """Delete metrics older than specified days (for maintenance)"""
    time_threshold = datetime.utcnow() - timedelta(days=days)
    
    deleted_count = db.query(Metric).filter(
        Metric.timestamp < time_threshold
    ).delete()
    
    db.commit()
    return deleted_count
