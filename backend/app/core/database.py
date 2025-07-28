"""
Database configuration
IMPROVED VERSION - Dr. Chen-Nakamura enhancements
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
from app.core.config import settings
import logging
import os

# IMPROVEMENT: Add async support preparation
try:
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
    ASYNC_AVAILABLE = True
except ImportError:
    ASYNC_AVAILABLE = False

logger = logging.getLogger(__name__)

# Determine database type
is_sqlite = str(settings.database_url).startswith("sqlite")
is_postgresql = str(settings.database_url).startswith("postgresql")

# IMPROVEMENT: Better connection pool configuration
if is_sqlite:
    # SQLite doesn't benefit from connection pooling
    engine = create_engine(
        str(settings.database_url),
        connect_args={"check_same_thread": False},
        echo=settings.debug,
        poolclass=NullPool  # IMPROVEMENT: No pooling for SQLite
    )
    
    # Enable foreign keys and optimize SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # IMPROVEMENT: Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")  # IMPROVEMENT: Faster writes
        cursor.execute("PRAGMA cache_size=10000")  # IMPROVEMENT: Larger cache
        cursor.execute("PRAGMA temp_store=MEMORY")  # IMPROVEMENT: Memory temp tables
        cursor.close()
else:
    # PostgreSQL with optimized pooling
    engine = create_engine(
        str(settings.database_url),
        echo=settings.debug,
        # IMPROVEMENT: Optimized connection pool settings
        pool_size=20,
        max_overflow=40,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,   # Recycle connections after 1 hour
    )

# IMPROVEMENT: Create async engine if PostgreSQL and async available
async_engine = None
AsyncSessionLocal = None

if is_postgresql and ASYNC_AVAILABLE:
    try:
        # Convert sync URL to async
        async_url = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")
        async_engine = create_async_engine(
            async_url,
            echo=settings.debug,
            pool_size=20,
            max_overflow=40,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        
        AsyncSessionLocal = async_sessionmaker(
            async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Async database engine created successfully")
    except Exception as e:
        logger.warning(f"Failed to create async engine: {e}. Falling back to sync only.")
        async_engine = None

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# IMPROVEMENT: Async session dependency
async def get_async_db():
    """Get async database session (PostgreSQL only)"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database not available. Use PostgreSQL for async support.")
    
    async with AsyncSessionLocal() as session:
        yield session

# IMPROVEMENT: Unified session getter
def get_db_session(prefer_async: bool = False):
    """
    Get appropriate database session based on configuration
    
    Args:
        prefer_async: If True and available, return async session
    
    Returns:
        Database session (async or sync based on availability)
    """
    if prefer_async and AsyncSessionLocal is not None:
        return get_async_db()
    return get_db()

# Health check
def check_database_connection():
    try:
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_pool_status() -> dict:
    """Get database connection pool status"""
    # IMPROVEMENT: More detailed pool status
    pool_info = {
        "database_type": "sqlite" if is_sqlite else "postgresql",
        "async_available": async_engine is not None,
    }
    
    if hasattr(engine.pool, 'size'):
        pool_info.update({
            "pool_size": engine.pool.size(),
            "checked_out_connections": engine.pool.checked_out(),
            "overflow": engine.pool.overflow(),
            "total": engine.pool.size() + engine.pool.overflow()
        })
    else:
        pool_info.update({
            "pool_size": "N/A (NullPool)",
            "checked_out_connections": 0,
            "overflow": 0,
            "total": 0
        })
    
    return pool_info

async def check_database_health() -> dict:
    """Check database health status"""
    health_info = {
        "status": "unknown",
        "database": "disconnected",
        "pool_status": get_pool_status(),
        "checks": {}
    }
    
    # IMPROVEMENT: Comprehensive health checks
    try:
        # Check sync connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            result.fetchone()
        health_info["checks"]["sync_connection"] = "ok"
        
        # Check async connection if available
        if async_engine:
            async with async_engine.connect() as conn:
                await conn.execute("SELECT 1")
            health_info["checks"]["async_connection"] = "ok"
        
        # IMPROVEMENT: Check database version
        with engine.connect() as conn:
            if is_postgresql:
                result = conn.execute("SELECT version()")
                version = result.fetchone()[0]
                health_info["database_version"] = version
            elif is_sqlite:
                result = conn.execute("SELECT sqlite_version()")
                version = result.fetchone()[0]
                health_info["database_version"] = f"SQLite {version}"
        
        health_info["status"] = "healthy"
        health_info["database"] = "connected"
        
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_info["status"] = "unhealthy"
        health_info["error"] = str(e)
    
    return health_info

# IMPROVEMENT: Database initialization helper
def init_db():
    """Initialize database tables"""
    try:
        # Import all models to ensure they're registered
        from app.models import user, emission, emission_factor
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

# IMPROVEMENT: Cleanup function
def dispose_engines():
    """Dispose of database engines (cleanup)"""
    try:
        engine.dispose()
        if async_engine:
            async_engine.dispose()
        logger.info("Database engines disposed successfully")
    except Exception as e:
        logger.error(f"Error disposing engines: {e}")