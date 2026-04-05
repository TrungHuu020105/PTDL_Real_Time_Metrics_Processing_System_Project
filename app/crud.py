"""CRUD operations for database"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Metric, Alert
from app.schemas import MetricCreate, AlertCreate


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
    
    return latest_cpu, latest_memory


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
    
    return cpu_metrics, memory_metrics


def delete_old_metrics(db: Session, days: int = 30) -> int:
    """Delete metrics older than specified days (for maintenance)"""
    time_threshold = datetime.utcnow() - timedelta(days=days)
    
    deleted_count = db.query(Metric).filter(
        Metric.timestamp < time_threshold
    ).delete()
    
    db.commit()
    return deleted_count


# ============== ALERT CRUD OPERATIONS ==============

def create_alert(db: Session, alert: AlertCreate) -> Alert:
    """Create a new alert record"""
    db_alert = Alert(
        metric_type=alert.metric_type,
        status=alert.status,
        current_value=alert.current_value,
        threshold=alert.threshold,
        message=alert.message,
        source=alert.source
    )
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_recent_alerts(db: Session, hours: int = 24, limit: int = 100) -> List[Alert]:
    """Get recent alerts from last N hours"""
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(hours=hours)
    
    alerts = db.query(Alert).filter(
        Alert.created_at >= time_threshold
    ).order_by(Alert.created_at.desc()).limit(limit).all()
    
    return alerts


def get_unresolved_alerts(db: Session) -> List[Alert]:
    """Get all unresolved alerts (resolved_at is NULL)"""
    alerts = db.query(Alert).filter(
        Alert.resolved_at == None
    ).order_by(Alert.created_at.desc()).all()
    
    return alerts


def get_alerts_by_metric(db: Session, metric_type: str, hours: int = 24) -> List[Alert]:
    """Get alerts for a specific metric type"""
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(hours=hours)
    
    alerts = db.query(Alert).filter(
        Alert.metric_type == metric_type,
        Alert.created_at >= time_threshold
    ).order_by(Alert.created_at.desc()).all()
    
    return alerts


def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
    """Mark an alert as resolved"""
    vietnam_tz = timezone(timedelta(hours=7))
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    
    if alert:
        alert.resolved_at = datetime.now(vietnam_tz)
        db.commit()
        db.refresh(alert)
    
    return alert


def delete_old_alerts(db: Session, days: int = 15) -> int:
    """Delete all alerts older than specified days (default: 15 days)"""
    # Use Vietnam timezone for consistency
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(days=days)
    
    # Delete ALL alerts (both resolved and unresolved) older than threshold
    deleted_count = db.query(Alert).filter(
        Alert.created_at < time_threshold
    ).delete()
    
    db.commit()
    return deleted_count
