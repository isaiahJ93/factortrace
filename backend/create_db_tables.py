# backend/create_db_tables.py
"""
Quick script to create database tables for development
Run this to set up your database structure
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.db.database import engine
from app.db.base import Base

# Import all models to register them
from app.models.emission import Emission, EmissionFactor

def create_tables():
    """Create all database tables"""
    print("🔧 Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        # Show created tables
        print("\n📊 Created tables:")
        for table in Base.metadata.sorted_tables:
            print(f"  - {table.name}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

def drop_tables():
    """Drop all tables (use with caution!)"""
    response = input("⚠️  Are you sure you want to drop all tables? (yes/no): ")
    if response.lower() == 'yes':
        print("🗑️  Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped")
    else:
        print("❌ Operation cancelled")

def main():
    """Main function with menu"""
    print("🚀 FactorTrace Database Setup")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--drop':
            drop_tables()
        elif sys.argv[1] == '--recreate':
            drop_tables()
            create_tables()
    else:
        create_tables()

if __name__ == "__main__":
    main()