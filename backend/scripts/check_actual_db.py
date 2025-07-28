#!/usr/bin/env python3
"""Check what database is actually being used"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, SessionLocal
from sqlalchemy import text

print("=== ACTUAL DATABASE CHECK ===")
print(f"Engine URL: {engine.url}")

db = SessionLocal()
try:
    if 'postgresql' in str(engine.url):
        result = db.execute(text("SELECT version()")).scalar()
        print(f"Connected to PostgreSQL: {result[:50]}...")
    else:
        result = db.execute(text("SELECT sqlite_version()")).scalar()
        print(f"Connected to SQLite: {result}")
except Exception as e:
    print(f"Error: {e}")
finally:
    db.close()

# Also check settings
from app.core.config import settings
print(f"\nSettings DATABASE_URL: {settings.DATABASE_URL}")

# Check environment
print(f"\nEnvironment DATABASE_URL: {os.getenv('DATABASE_URL', 'Not set')}")
