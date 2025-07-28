#!/usr/bin/env python3
"""Create database tables directly"""
from app.db.base import Base
from app.db.session import engine

# Import all models to ensure they're registered
from app.models.emission import Emission, EmissionFactor
from app.models.user import User

print("Creating database tables...")

# Create all tables
Base.metadata.create_all(bind=engine)

print("Tables created successfully!")

# List all tables
from sqlalchemy import inspect
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Tables in database: {tables}")