"""Database configuration and session management (PostgreSQL)."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from iot_backend.config import get_database_url


DATABASE_URL = get_database_url()

engine_kwargs = {
    "echo": False,  # Set to True for SQL query debugging
    "pool_pre_ping": True,
    # Avoid hanging forever when network/db has intermittent issues.
    "connect_args": {
        "connect_timeout": 5,
        # Postgres session-level timeouts to fail fast on DDL locks.
        # Keep statement timeout for safety, but relax lock timeout to reduce transient lock errors.
        "options": "-c statement_timeout=15000 -c lock_timeout=15000",
    },
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
    if _is_schema_auto_migrate_enabled():
        _run_schema_evolution()


def _is_schema_auto_migrate_enabled() -> bool:
    """
    Guard risky runtime DDL behind an explicit flag.
    Default OFF to avoid startup hangs from table locks.
    """
    return os.getenv("DB_AUTO_SCHEMA_MIGRATION", "false").strip().lower() in {"1", "true", "yes", "on"}


def _run_schema_evolution():
    """Best-effort runtime schema evolution (explicitly enabled only)."""
    _ensure_iot_device_columns()
    _cleanup_metric_columns()


def _ensure_iot_device_columns():
    """Best-effort schema evolution for existing iot_devices table."""
    alter_statements = [
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS environment_type VARCHAR(20) DEFAULT 'indoor'",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS location_query VARCHAR(255)",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS latitude FLOAT",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS longitude FLOAT",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS timezone_name VARCHAR(64)",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS task_description VARCHAR(500)",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS priority_level VARCHAR(20)",
        "ALTER TABLE iot_devices ADD COLUMN IF NOT EXISTS action_hint VARCHAR(500)",
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
        "ALTER TABLE metrics DROP COLUMN IF EXISTS timezone_name",
    ]
    with engine.begin() as conn:
        for sql in alter_statements:
            try:
                conn.exec_driver_sql(sql)
            except Exception:
                pass

