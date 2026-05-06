"""Database configuration and session management (Azure SQL only)."""

from sqlalchemy import create_engine
from sqlalchemy import text
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
    _ensure_notification_columns()


def _ensure_notification_columns():
    """Best-effort schema patch for Azure SQL user notification fields."""
    statements = [
        "IF COL_LENGTH('users', 'notification_email') IS NULL ALTER TABLE users ADD notification_email NVARCHAR(100) NULL;",
        "IF COL_LENGTH('users', 'email_enabled') IS NULL ALTER TABLE users ADD email_enabled BIT NOT NULL CONSTRAINT DF_users_email_enabled DEFAULT 0;",
        "IF COL_LENGTH('users', 'telegram_chat_id') IS NULL ALTER TABLE users ADD telegram_chat_id NVARCHAR(64) NULL;",
        "IF COL_LENGTH('users', 'telegram_enabled') IS NULL ALTER TABLE users ADD telegram_enabled BIT NOT NULL CONSTRAINT DF_users_telegram_enabled DEFAULT 0;",
        "IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'uq_users_telegram_chat_id' AND object_id = OBJECT_ID('users')) "
        "CREATE UNIQUE INDEX uq_users_telegram_chat_id ON users(telegram_chat_id) WHERE telegram_chat_id IS NOT NULL;",
        """
        IF OBJECT_ID('user_notification_targets', 'U') IS NULL
        CREATE TABLE user_notification_targets (
            id INT IDENTITY(1,1) PRIMARY KEY,
            user_id INT NOT NULL,
            target_type NVARCHAR(20) NOT NULL,
            target_value NVARCHAR(255) NOT NULL,
            is_enabled BIT NOT NULL CONSTRAINT DF_notification_targets_enabled DEFAULT 1,
            created_at DATETIME2 NOT NULL CONSTRAINT DF_notification_targets_created DEFAULT SYSUTCDATETIME()
        );
        """,
        """
        IF NOT EXISTS (
            SELECT 1 FROM sys.indexes
            WHERE name = 'uq_notification_target_user_type_value'
              AND object_id = OBJECT_ID('user_notification_targets')
        )
        CREATE UNIQUE INDEX uq_notification_target_user_type_value
        ON user_notification_targets(user_id, target_type, target_value);
        """,
    ]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
