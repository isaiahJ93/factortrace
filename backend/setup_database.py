# setup_database.py - Database setup and migration helper
import os
import sys
from sqlalchemy import create_engine, text
from alembic import command
from alembic.config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_type():
    """Check if using PostgreSQL or SQLite"""
    from app.core.config import settings
    db_url = settings.DATABASE_URL
    
    if db_url.startswith("postgresql"):
        return "postgresql"
    elif db_url.startswith("sqlite"):
        return "sqlite"
    else:
        return "unknown"

def create_enums_postgresql(engine):
    """Create enum types in PostgreSQL"""
    enum_definitions = [
        ("emissionscope", ['SCOPE_1', 'SCOPE_2', 'SCOPE_3']),
        ("datasourcetype", ['MEASURED', 'CALCULATED', 'ESTIMATED', 'DEFAULT']),
        ("voucherstatus", ['VALID', 'USED', 'EXPIRED', 'REVOKED']),
        ("paymentstatus", ['PENDING', 'COMPLETED', 'FAILED', 'REFUNDED'])
    ]
    
    with engine.connect() as conn:
        for enum_name, values in enum_definitions:
            try:
                # Check if enum exists
                result = conn.execute(
                    text(f"SELECT 1 FROM pg_type WHERE typname = :name"),
                    {"name": enum_name}
                )
                
                if not result.fetchone():
                    # Create enum
                    values_str = ', '.join([f"'{v}'" for v in values])
                    conn.execute(text(f"CREATE TYPE {enum_name} AS ENUM ({values_str})"))
                    logger.info(f"Created enum type: {enum_name}")
                else:
                    logger.info(f"Enum type already exists: {enum_name}")
                    
                conn.commit()
            except Exception as e:
                logger.error(f"Error creating enum {enum_name}: {e}")
                conn.rollback()

def setup_database():
    """Set up database with proper configuration"""
    from app.core.config import settings
    from app.core.database import engine, Base
    
    db_type = check_database_type()
    logger.info(f"Database type: {db_type}")
    logger.info(f"Database URL: {settings.DATABASE_URL.split('@')[0]}@***")
    
    try:
        # Test connection
        with engine.connect() as conn:
            if db_type == "postgresql":
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                logger.info(f"PostgreSQL version: {version}")
                
                # Create enums if PostgreSQL
                create_enums_postgresql(engine)
            else:
                result = conn.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                logger.info(f"SQLite version: {version}")
        
        # Import all models to ensure they're registered
        logger.info("Importing models...")
        from app.models import (
            user, voucher, payment, emission, emission_factor,
            evidence_document, data_quality
        )
        
        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

def run_migrations():
    """Run Alembic migrations"""
    try:
        # Get Alembic configuration
        alembic_cfg = Config("alembic.ini")
        
        # Check current revision
        logger.info("Checking current migration status...")
        from alembic import script
        from alembic.runtime import migration
        
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        
        from app.core.database import engine
        with engine.connect() as connection:
            context = migration.MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            
            if current_rev:
                logger.info(f"Current revision: {current_rev}")
            else:
                logger.info("No migrations applied yet")
                
            # Get pending migrations
            head_rev = script_dir.get_current_head()
            if current_rev != head_rev:
                logger.info(f"Pending migrations found. Head revision: {head_rev}")
                
                # Run migrations
                logger.info("Running migrations...")
                command.upgrade(alembic_cfg, "head")
                logger.info("✅ Migrations completed successfully!")
            else:
                logger.info("✅ Database is up to date!")
                
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def seed_initial_data():
    """Seed initial data for testing"""
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.emission_factor import EmissionFactor
    
    db = SessionLocal()
    try:
        # Check if we already have data
        user_count = db.query(User).count()
        if user_count > 0:
            logger.info(f"Database already has {user_count} users. Skipping seed.")
            return
            
        # Create admin user
        admin = User(
            email="admin@factortrace.com",
            full_name="Admin User",
            is_active=True,
            is_admin=True,
            company_name="FactorTrace",
            has_emissions_access=True
        )
        admin.set_password("admin123")  # Change in production!
        db.add(admin)
        
        # Add some basic emission factors
        factors = [
            {
                "name": "Electricity - Grid Average",
                "category": "energy",
                "subcategory": "electricity",
                "unit": "kWh",
                "co2e_per_unit": 0.4,
                "source": "EPA",
                "scope": "scope2"
            },
            {
                "name": "Natural Gas",
                "category": "energy",
                "subcategory": "natural_gas",
                "unit": "m3",
                "co2e_per_unit": 2.02,
                "source": "EPA",
                "scope": "scope1"
            },
            {
                "name": "Gasoline",
                "category": "transport",
                "subcategory": "fuel",
                "unit": "liter",
                "co2e_per_unit": 2.31,
                "source": "EPA",
                "scope": "scope1"
            }
        ]
        
        for factor_data in factors:
            factor = EmissionFactor(**factor_data)
            db.add(factor)
            
        db.commit()
        logger.info("✅ Initial data seeded successfully!")
        
    except Exception as e:
        logger.error(f"❌ Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("\n🚀 FactorTrace Database Setup\n")
    
    # Check if .env exists
    if not os.path.exists(".env"):
        print("❌ .env file not found! Please create it first.")
        print("Run: ./create_env.sh")
        sys.exit(1)
    
    # Setup database
    if setup_database():
        print("\n📦 Running migrations...")
        if run_migrations():
            print("\n🌱 Seeding initial data...")
            seed_initial_data()
            print("\n✅ Database setup complete!")
        else:
            print("\n❌ Migration failed. Please check the errors above.")
    else:
        print("\n❌ Database setup failed. Please check your DATABASE_URL in .env")