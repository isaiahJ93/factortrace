#!/usr/bin/env python3
"""
Initialize GHG Protocol migrations
Run this after adding all the new models
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import command
from alembic.config import Config
from app.db.base import Base, import_all_models
from app.core.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_ghg_migration():
    """Create migration for new GHG models"""
    try:
        # Import all models to ensure they're registered
        imported, failed = import_all_models()
        logger.info(f"Imported {len(imported)} models, {len(failed)} failed")
        
        # Create Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Create migration
        command.revision(
            alembic_cfg,
            autogenerate=True,
            message="add_comprehensive_ghg_protocol_models"
        )
        
        logger.info("✅ Migration created successfully")
        logger.info("Run 'alembic upgrade head' to apply the migration")
        
    except Exception as e:
        logger.error(f"Failed to create migration: {e}")
        raise

if __name__ == "__main__":
    create_ghg_migration()