"""SQLAlchemy ORM models"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, Float, String, DateTime, Index, Boolean
from app.database import Base


class Metric(Base):
    """Metric record model"""
    __tablename__ = "metrics"

    id = Column(Integer, primary_key=True, index=True)
    event_ts = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), index=True, nullable=False)
    sensor_id = Column(String(100), nullable=False, index=True)
    location = Column(String(255), nullable=True)
    metric_type = Column(String(50), index=True, nullable=False)  # temperature, humidity, soil_moisture, ...
    metric_value = Column(Float, nullable=False)
    unit = Column(String(50), nullable=True)

    # Composite index for efficient time-range queries
    __table_args__ = (
        Index('idx_metric_type_event_ts', 'metric_type', 'event_ts'),
    )

    def __repr__(self):
        return f"<Metric(sensor={self.sensor_id}, type={self.metric_type}, value={self.metric_value}, time={self.event_ts})>"


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
    created_at = Column(DateTime, default=datetime.now, index=True, nullable=False)
    resolved_at = Column(DateTime, nullable=True)  # When alert was resolved (if applicable)

    # Composite index for efficient querying
    __table_args__ = (
        Index('idx_alert_status_created', 'status', 'created_at'),
        Index('idx_alert_metric_created', 'metric_type', 'created_at'),
    )

    def __repr__(self):
        return f"<Alert(type={self.metric_type}, status={self.status}, value={self.current_value}, at={self.created_at})>"


class User(Base):
    """User account model for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    notification_email = Column(String(100), nullable=True)
    email_enabled = Column(Boolean, default=False, nullable=False)
    telegram_chat_id = Column(String(64), unique=True, nullable=True)
    telegram_enabled = Column(Boolean, default=False, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="user")  # 'admin' or 'user'
    is_active = Column(Boolean, default=True, nullable=False)
    is_approved = Column(Boolean, default=False, nullable=False)  # Admin must approve
    approved_by = Column(Integer, nullable=True)  # Admin ID who approved
    approved_at = Column(DateTime, nullable=True)  # When approved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)

    def __repr__(self):
        return f"<User(username={self.username}, role={self.role}, approved={self.is_approved})>"


class UserNotificationTarget(Base):
    """Per-user notification targets (multiple telegram chat ids / emails)."""
    __tablename__ = "user_notification_targets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    target_type = Column(String(20), nullable=False, index=True)  # telegram | email
    target_value = Column(String(255), nullable=False)
    is_enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)


class Device(Base):
    """Device model for managing sources (servers, IoT devices)"""
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Device name (e.g., "Server 1", "Temperature Sensor 1")
    device_type = Column(String(50), nullable=False)  # 'cpu', 'memory', 'temperature', 'humidity', etc
    source = Column(String(100), unique=True, nullable=False, index=True)  # Unique identifier for metrics
    location = Column(String(255), nullable=True)  # Physical location
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, nullable=False)  # Admin ID who created
    created_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)

    def __repr__(self):
        return f"<Device(name={self.name}, type={self.device_type}, source={self.source})>"


class UserDevicePermission(Base):
    """Permissions linking users to devices they can view"""
    __tablename__ = "user_device_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # User ID
    device_id = Column(Integer, nullable=False, index=True)  # Device ID
    granted_by = Column(Integer, nullable=False)  # Admin ID who granted
    granted_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)

    def __repr__(self):
        return f"<UserDevicePermission(user_id={self.user_id}, device_id={self.device_id})>"


class IoTDevice(Base):
    """IoT Device model - User-owned and managed"""
    __tablename__ = "iot_devices"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Owner/creator
    name = Column(String(100), nullable=False)  # Device name (e.g., "Room 1 Temperature")
    device_type = Column(String(50), nullable=False)  # temperature, humidity, soil_moisture, light_intensity, pressure
    source = Column(String(100), unique=True, nullable=False, index=True)  # Unique identifier for metrics
    location = Column(String(255), nullable=True)  # Physical location
    environment_type = Column(String(20), nullable=False, default="indoor")  # indoor | outdoor
    location_query = Column(String(255), nullable=True)  # Raw user location string for geocoding/weather
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone_name = Column(String(64), nullable=True)
    task_description = Column(String(500), nullable=True)
    priority_level = Column(String(20), nullable=True)  # low | medium | high
    action_hint = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Alert threshold fields - upper and lower bounds
    alert_enabled = Column(Boolean, default=False, nullable=False)  # Enable/disable alerts for this device
    lower_threshold = Column(Float, nullable=True)  # Lower threshold (values below this trigger alert)
    upper_threshold = Column(Float, nullable=True)  # Upper threshold (values above this trigger alert)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)

    def __repr__(self):
        return f"<IoTDevice(user_id={self.user_id}, name={self.name}, type={self.device_type})>"


class AvailableServer(Base):
    """Available Server model - Admin-created, User can subscribe"""
    __tablename__ = "available_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # Server name (e.g., "4-Core Ubuntu Server")
    specs = Column(String(255), nullable=True)  # Specifications (e.g., "4-Core, 8GB RAM, Ubuntu 22.04")
    cpu_cores = Column(Integer, nullable=True)  # Number of CPU cores
    ram_gb = Column(Integer, nullable=True)  # RAM in gigabytes
    os_type = Column(String(50), nullable=True)  # Ubuntu, Windows, RHEL, etc
    is_available = Column(Boolean, default=True, nullable=False, index=True)
    price_per_hour = Column(Float, nullable=True)  # Optional pricing
    created_by = Column(Integer, nullable=False)  # Admin ID who created
    created_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)

    def __repr__(self):
        return f"<AvailableServer(name={self.name}, cores={self.cpu_cores}, available={self.is_available})>"


class ServerSubscription(Base):
    """Server Subscription model - User subscribes to monitor servers"""
    __tablename__ = "server_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # Subscriber
    server_id = Column(Integer, nullable=False, index=True)  # Server being subscribed to
    subscription_duration_months = Column(Integer, nullable=False, default=1)  # Duration in months (1, 3, 6, 12)
    subscribed_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)
    expiration_date = Column(DateTime, nullable=False)  # When subscription expires

    def __repr__(self):
        return f"<ServerSubscription(user_id={self.user_id}, server_id={self.server_id}, expires={self.expiration_date})>"


class ServerSubscriptionRequest(Base):
    """Server Subscription Request - User requests to subscribe, admin approves/rejects"""
    __tablename__ = "server_subscription_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)  # User requesting
    server_id = Column(Integer, nullable=False, index=True)  # Server requested
    subscription_duration_months = Column(Integer, nullable=False, default=1)  # Requested duration in months (1, 3, 6, 12)
    status = Column(String(20), default="pending", nullable=False)  # pending, approved, rejected
    requested_at = Column(DateTime, default=lambda: datetime.now(timezone(timedelta(hours=7))), nullable=False)
    approved_by = Column(Integer, nullable=True)  # Admin ID who approved
    approved_at = Column(DateTime, nullable=True)
    rejection_reason = Column(String(255), nullable=True)  # Reason for rejection

    def __repr__(self):
        return f"<ServerSubscriptionRequest(user_id={self.user_id}, server_id={self.server_id}, duration={self.subscription_duration_months}m, status={self.status})>"
