#!/usr/bin/env python
"""Setup database tables"""
import sys
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from app.db.database import engine
from app.db.base import Base

# Import models to register them
try:
    from app.models.emission import Emission
    print("✓ Emission model imported")
except ImportError as e:
    print(f"✗ Failed to import Emission model: {e}")

# Create tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ Database tables created!")

# Show tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nCreated tables: {tables}")
