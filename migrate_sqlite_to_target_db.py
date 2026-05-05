"""Migrate data from local SQLite metrics.db to Azure SQL target DB.

Usage:
  1) Set DB_SERVER/DB_DATABASE/DB_USERNAME/DB_PASSWORD in .env
  2) Run: python migrate_sqlite_to_target_db.py
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.config  # noqa: F401 - load .env via config side effects
from app.config import get_database_url
from app.models import (
    Base,
    Metric,
    Alert,
    User,
    Device,
    UserDevicePermission,
    IoTDevice,
    AvailableServer,
    ServerSubscription,
    ServerSubscriptionRequest,
)


def main():
    source_url = "sqlite:///metrics.db"
    target_url = get_database_url()

    source_engine = create_engine(source_url, connect_args={"check_same_thread": False})
    target_engine = create_engine(target_url, pool_pre_ping=True)

    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)

    Base.metadata.create_all(bind=target_engine)

    source_db = SourceSession()
    target_db = TargetSession()

    models_in_order = [
        User,
        Device,
        UserDevicePermission,
        IoTDevice,
        AvailableServer,
        ServerSubscription,
        ServerSubscriptionRequest,
        Metric,
        Alert,
    ]

    try:
        for model in models_in_order:
            rows = source_db.query(model).all()
            if not rows:
                print(f"[SKIP] {model.__tablename__}: 0 rows")
                continue

            target_db.query(model).delete()
            target_db.flush()

            payload = [{c.name: getattr(r, c.name) for c in model.__table__.columns} for r in rows]
            target_db.bulk_insert_mappings(model, payload)
            target_db.commit()
            print(f"[OK] {model.__tablename__}: migrated {len(rows)} rows")
    finally:
        source_db.close()
        target_db.close()

    print("Migration completed.")


if __name__ == "__main__":
    main()
