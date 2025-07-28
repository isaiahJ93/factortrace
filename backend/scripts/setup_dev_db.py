#!/usr/bin/env python3
"""Setup development database with SQLite"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from app.db.base import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_sqlite_db():
    """Create SQLite database with all tables"""
    
    # Ensure .env uses SQLite
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Update DATABASE_URL if needed
        if 'DATABASE_URL' not in content:
            content += '\nDATABASE_URL=sqlite:///./factortrace.db\n'
        elif 'postgresql://' in content:
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if line.startswith('DATABASE_URL') and 'postgresql://' in line:
                    new_lines.append('DATABASE_URL=sqlite:///./factortrace.db')
                else:
                    new_lines.append(line)
            content = '\n'.join(new_lines)
            
        with open(env_path, 'w') as f:
            f.write(content)
    else:
        with open(env_path, 'w') as f:
            f.write('DATABASE_URL=sqlite:///./factortrace.db\n')
    
    logger.info("✅ Updated .env to use SQLite")
    
    # Create engine
    engine = create_engine('sqlite:///./factortrace.db')
    
    # Drop all tables and recreate
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("✅ SQLite database created successfully!")
        logger.info("📁 Database file: ./factortrace.db")
    except Exception as e:
        logger.error(f"❌ Error creating database: {e}")
        raise

if __name__ == "__main__":
    setup_sqlite_db()
