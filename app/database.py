"""Database configuration and session management (PostgreSQL)."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_database_url


DATABASE_URL = get_database_url()

engine_kwargs = {
    "echo": False,  # Set to True for SQL query debugging
    "pool_pre_ping": True,
}

# Create engine
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    _ensure_iot_device_columns()
    _cleanup_metric_columns()


def _ensure_iot_device_columns():
    """Best-effort schema evolution for existing iot_devices table."""
    alter_statements = [
        "ALTER TABLE iot_devices ADD COLUMN environment_type VARCHAR(20) DEFAULT 'indoor'",
        "ALTER TABLE iot_devices ADD COLUMN location_query VARCHAR(255)",
        "ALTER TABLE iot_devices ADD COLUMN latitude FLOAT",
        "ALTER TABLE iot_devices ADD COLUMN longitude FLOAT",
        "ALTER TABLE iot_devices ADD COLUMN timezone_name VARCHAR(64)",
        "ALTER TABLE iot_devices ADD COLUMN task_description VARCHAR(500)",
        "ALTER TABLE iot_devices ADD COLUMN priority_level VARCHAR(20)",
        "ALTER TABLE iot_devices ADD COLUMN action_hint VARCHAR(500)",
    ]

    with engine.begin() as conn:
        for sql in alter_statements:
            try:
                conn.exec_driver_sql(sql)
            except Exception:
                # Ignore if column already exists or dialect-specific limitation.
                pass


def _cleanup_metric_columns():
    """Best-effort cleanup for metrics table schema."""
    alter_statements = [
        "ALTER TABLE metrics DROP COLUMN timezone_name",
    ]
    with engine.begin() as conn:
        for sql in alter_statements:
            try:
                conn.exec_driver_sql(sql)
            except Exception:
                pass
