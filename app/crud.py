"""CRUD operations for database"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Metric, Alert, User, Device, UserDevicePermission, IoTDevice, ServerSubscriptionRequest
from app.schemas import MetricCreate, AlertCreate, UserRegister, DeviceCreate


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


# ============== USER CRUD OPERATIONS ==============

def create_user(db: Session, user: UserRegister, hashed_password: str) -> User:
    """Create a new user (auto-approve admin users)"""
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
        # Auto-approve admin users, regular users need approval
        is_approved=True if user.role == "admin" else False,
        approved_at=datetime.now(timezone(timedelta(hours=7))) if user.role == "admin" else None
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session) -> List[User]:
    """Get all users"""
    return db.query(User).all()


# ============== USER APPROVAL ==============

def get_pending_users(db: Session) -> List[User]:
    """Get users pending approval"""
    return db.query(User).filter(User.is_approved == False).all()


def approve_user(db: Session, user_id: int, admin_id: int) -> Optional[User]:
    """Admin approves a user"""
    vietnam_tz = timezone(timedelta(hours=7))
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        user.is_approved = True
        user.approved_by = admin_id
        user.approved_at = datetime.now(vietnam_tz)
        db.commit()
        db.refresh(user)
    
    return user


def reject_user(db: Session, user_id: int) -> bool:
    """Admin rejects a user (delete pending user)"""
    user = db.query(User).filter(User.id == user_id, User.is_approved == False).first()
    
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def delete_user(db: Session, user_id: int) -> bool:
    """Admin deletes any user (approved or pending)"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if user:
        # Delete user permissions first
        db.query(UserDevicePermission).filter(UserDevicePermission.user_id == user_id).delete()
        # Delete user
        db.delete(user)
        db.commit()
        return True
    return False


# ============== DEVICE MANAGEMENT ==============

def create_device(db: Session, device: DeviceCreate, admin_id: int) -> Device:
    """Create a new device"""
    db_device = Device(
        name=device.name,
        device_type=device.device_type,
        source=device.source,
        location=device.location,
        created_by=admin_id
    )
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device


def get_all_devices(db: Session) -> List[Device]:
    """Get all devices"""
    return db.query(Device).filter(Device.is_active == True).all()


def get_device_by_id(db: Session, device_id: int) -> Optional[Device]:
    """Get device by ID"""
    return db.query(Device).filter(Device.id == device_id).first()


def get_device_by_source(db: Session, source: str) -> Optional[Device]:
    """Get device by source identifier"""
    return db.query(Device).filter(Device.source == source).first()


def delete_device(db: Session, device_id: int) -> bool:
    """Soft delete device (mark inactive)"""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if device:
        device.is_active = False
        db.commit()
        return True
    return False


def update_device(db: Session, device_id: int, name: str, device_type: str = None, location: str = None) -> Optional[Device]:
    """Update device information (name, device_type, location)"""
    device = db.query(Device).filter(Device.id == device_id).first()
    
    if device:
        device.name = name
        if device_type:
            device.device_type = device_type
        if location:
            device.location = location
        db.commit()
        db.refresh(device)
    
    return device


# ============== USER-DEVICE PERMISSIONS ==============

def grant_device_permission(db: Session, user_id: int, device_id: int, admin_id: int) -> UserDevicePermission:
    """Grant user access to a device"""
    # Check if permission already exists
    existing = db.query(UserDevicePermission).filter(
        UserDevicePermission.user_id == user_id,
        UserDevicePermission.device_id == device_id
    ).first()
    
    if existing:
        return existing
    
    permission = UserDevicePermission(
        user_id=user_id,
        device_id=device_id,
        granted_by=admin_id
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def revoke_device_permission(db: Session, user_id: int, device_id: int) -> bool:
    """Revoke user access to a device"""
    permission = db.query(UserDevicePermission).filter(
        UserDevicePermission.user_id == user_id,
        UserDevicePermission.device_id == device_id
    ).first()
    
    if permission:
        db.delete(permission)
        db.commit()
        return True
    return False


def get_user_devices(db: Session, user_id: int) -> List[Device]:
    """Get all devices a user has access to"""
    permissions = db.query(UserDevicePermission).filter(
        UserDevicePermission.user_id == user_id
    ).all()
    
    device_ids = [p.device_id for p in permissions]
    devices = db.query(Device).filter(Device.id.in_(device_ids), Device.is_active == True).all()
    return devices


def get_device_users(db: Session, device_id: int) -> List[User]:
    """Get all users with access to a device"""
    permissions = db.query(UserDevicePermission).filter(
        UserDevicePermission.device_id == device_id
    ).all()
    
    user_ids = [p.user_id for p in permissions]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return users


def get_user_accessible_sources(db: Session, user_id: int) -> List[str]:
    """Get list of metric sources (device sources) the user has access to"""
    sources = []
    
    # Admin users can see all devices
    user = get_user_by_id(db, user_id)
    if user and user.role == "admin":
        # Admins see all active Device sources
        devices = db.query(Device).filter(Device.is_active == True).all()
        sources.extend([d.source for d in devices])
        
        # Admins see all active IoT device sources
        iot_devices = db.query(IoTDevice).filter(IoTDevice.is_active == True).all()
        sources.extend([d.source for d in iot_devices])
    else:
        # Regular users see:
        # 1. Devices they have permission for (from UserDevicePermission)
        devices = get_user_devices(db, user_id)
        sources.extend([d.source for d in devices])
        
        # 2. IoT devices they own
        iot_devices = db.query(IoTDevice).filter(
            IoTDevice.user_id == user_id,
            IoTDevice.is_active == True
        ).all()
        sources.extend([d.source for d in iot_devices])
    
    return sources


def get_latest_metrics_for_user(db: Session, user_id: int) -> tuple:
    """Get latest values for each metric type, filtered by user's accessible devices"""
    accessible_sources = get_user_accessible_sources(db, user_id)
    
    if not accessible_sources:
        return None, None
    
    latest_cpu = db.query(Metric).filter(
        Metric.metric_type == "cpu",
        Metric.source.in_(accessible_sources)
    ).order_by(Metric.timestamp.desc()).first()
    
    latest_memory = db.query(Metric).filter(
        Metric.metric_type == "memory",
        Metric.source.in_(accessible_sources)
    ).order_by(Metric.timestamp.desc()).first()
    
    return latest_cpu, latest_memory


def get_metrics_history_for_user(
    db: Session,
    user_id: int,
    metric_type: str,
    minutes: int = 5
) -> List[Metric]:
    """Get historical metrics for a specific type, filtered by user's accessible devices"""
    accessible_sources = get_user_accessible_sources(db, user_id)
    
    if not accessible_sources:
        return []
    
    vietnam_tz = timezone(timedelta(hours=7))
    time_threshold = datetime.now(vietnam_tz) - timedelta(minutes=minutes)
    
    metrics = db.query(Metric).filter(
        Metric.metric_type == metric_type,
        Metric.source.in_(accessible_sources),
        Metric.timestamp >= time_threshold
    ).order_by(Metric.timestamp.asc()).all()
    
    return metrics


# ============== SERVER SUBSCRIPTION REQUESTS ==============

def create_subscription_request(db: Session, user_id: int, server_id: int) -> ServerSubscriptionRequest:
    """User creates a subscription request for a server"""
    # Check if request already pending
    existing = db.query(ServerSubscriptionRequest).filter(
        ServerSubscriptionRequest.user_id == user_id,
        ServerSubscriptionRequest.server_id == server_id,
        ServerSubscriptionRequest.status == "pending"
    ).first()
    
    if existing:
        return existing
    
    request = ServerSubscriptionRequest(
        user_id=user_id,
        server_id=server_id,
        status="pending"
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return request


def get_pending_subscription_requests(db: Session) -> List[ServerSubscriptionRequest]:
    """Admin views all pending subscription requests"""
    return db.query(ServerSubscriptionRequest).filter(
        ServerSubscriptionRequest.status == "pending"
    ).order_by(ServerSubscriptionRequest.requested_at.desc()).all()


def approve_subscription_request(db: Session, request_id: int, admin_id: int) -> Optional[ServerSubscriptionRequest]:
    """Admin approves a subscription request - creates subscription"""
    from app.models import ServerSubscription
    
    req = db.query(ServerSubscriptionRequest).filter(ServerSubscriptionRequest.id == request_id).first()
    
    if not req:
        return None
    
    # Mark request as approved
    vietnam_tz = timezone(timedelta(hours=7))
    req.status = "approved"
    req.approved_by = admin_id
    req.approved_at = datetime.now(vietnam_tz)
    
    # Create subscription
    subscription = ServerSubscription(
        user_id=req.user_id,
        server_id=req.server_id
    )
    db.add(subscription)
    db.commit()
    db.refresh(req)
    return req


def reject_subscription_request(db: Session, request_id: int, reason: str = None) -> Optional[ServerSubscriptionRequest]:
    """Admin rejects a subscription request"""
    req = db.query(ServerSubscriptionRequest).filter(ServerSubscriptionRequest.id == request_id).first()
    
    if not req:
        return None
    
    vietnam_tz = timezone(timedelta(hours=7))
    req.status = "rejected"
    req.rejection_reason = reason
    req.approved_at = datetime.now(vietnam_tz)  # Reuse for rejection timestamp
    db.commit()
    db.refresh(req)
    return req


def get_user_subscription_requests(db: Session, user_id: int) -> List[ServerSubscriptionRequest]:
    """User views their own subscription requests"""
    return db.query(ServerSubscriptionRequest).filter(
        ServerSubscriptionRequest.user_id == user_id
    ).order_by(ServerSubscriptionRequest.requested_at.desc()).all()
