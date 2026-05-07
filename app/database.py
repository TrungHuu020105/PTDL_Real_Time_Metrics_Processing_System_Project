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
