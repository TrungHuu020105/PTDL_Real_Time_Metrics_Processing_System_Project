"""
Migration script to add missing columns to existing database
"""

import sqlite3
import os

db_path = "metrics.db"

if not os.path.exists(db_path):
    print(f"✗ Database file '{db_path}' not found")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1] for row in cursor.fetchall()}
    
    # Add missing columns
    if 'is_approved' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN is_approved BOOLEAN DEFAULT 0")
        print("✓ Added is_approved column")
    
    if 'approved_by' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN approved_by INTEGER")
        print("✓ Added approved_by column")
    
    if 'approved_at' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN approved_at DATETIME")
        print("✓ Added approved_at column")
    
    conn.commit()
    print("✓ Database migration completed successfully")
    
except sqlite3.OperationalError as e:
    print(f"✗ Database migration failed: {e}")
finally:
    conn.close()
