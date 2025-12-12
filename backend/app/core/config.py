"""
Configuration and Dependencies for GHG Protocol Scope 3 Calculator
Settings management and dependency injection setup
"""

import os
from functools import lru_cache
from typing import AsyncGenerator, Optional, Dict, Any, TYPE_CHECKING, List
from datetime import datetime, timedelta
import secrets

from pydantic_settings import BaseSettings
from pydantic import Field, validator, field_validator
from pydantic import SecretStr
from pydantic.networks import  RedisDsn, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import redis.asyncio as redis
import boto3
from botocore.config import Config
import aiohttp
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import sentry_sdk
from prometheus_client import CollectorRegistry


# Security
security = HTTPBearer()


class Settings(BaseSettings):
    PROJECT_NAME: str = "GHG Protocol Scope 3 Calculator"
    VERSION: str = "1.0.0"
    """Application settings with environment variable support"""
    
    # Application
    app_name: str = "GHG Protocol Scope 3 Calculator"
    app_version: str = "1.0.0"
    environment: str = Field("development", env="ENVIRONMENT")
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    
    # API
    api_prefix: str = "/api/v1"
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    allowed_origins: List[str] = Field("*", env="ALLOWED_ORIGINS")
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    db_pool_size: int = Field(5, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(10, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(30, env="DB_POOL_TIMEOUT")
    database_pool_size: int = Field(20, env="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(10, env="DATABASE_MAX_OVERFLOW")
    database_echo: bool = Field(False, env="DATABASE_ECHO")
    
    # Redis
    redis_url: RedisDsn = Field("redis://localhost:6379", env="REDIS_URL")
    redis_pool_size: int = Field(10, env="REDIS_POOL_SIZE")
    cache_ttl: int = Field(3600, env="CACHE_TTL")  # seconds
    
    # Stripe
    stripe_secret_key: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    stripe_publishable_key: Optional[str] = Field(None, env="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    stripe_price_id_basic: Optional[str] = Field(None, env="STRIPE_PRICE_ID_BASIC")
    stripe_price_id_pro: Optional[str] = Field(None, env="STRIPE_PRICE_ID_PRO")
    
    # XBRL/XSD Configuration
    xsd_base_path: str = Field("./schemas/xsd", env="XSD_BASE_PATH")
    
    # Authentication
    secret_key: SecretStr = Field(..., env="SECRET_KEY")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # AWS
    aws_access_key_id: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional["SecretStr"] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    jwt_secret: str = Field(default="", env="JWT_SECRET")
    aws_region: str = Field("us-east-1", env="AWS_REGION")
    s3_bucket: str = Field("ghg-calculator", env="S3_BUCKET")
    
    # External APIs
    epa_api_key: Optional["SecretStr"] = Field(None, env="EPA_API_KEY")
    ecoinvent_api_key: Optional["SecretStr"] = Field(None, env="ECOINVENT_API_KEY")

    # Supabase (optional - for auth/storage)
    supabase_url: Optional[str] = Field(None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(None, env="SUPABASE_KEY")

    # Email
    sendgrid_api_key: Optional[str] = Field(None, env="SENDGRID_API_KEY")

    # Monitoring
    sentry_dsn: Optional["HttpUrl"] = Field(None, env="SENTRY_DSN")
    prometheus_enabled: bool = Field(True, env="PROMETHEUS_ENABLED")
    
    # Celery
    celery_broker_url: str = Field("redis://localhost:6379/0", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field("redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(100, env="RATE_LIMIT_REQUESTS")
    rate_limit_period: int = Field(60, env="RATE_LIMIT_PERIOD")  # seconds
    
    # Features
    enable_uncertainty_analysis: bool = Field(True, env="ENABLE_UNCERTAINTY")
    monte_carlo_iterations: int = Field(10000, env="MONTE_CARLO_ITERATIONS")
    enable_external_providers: bool = Field(True, env="ENABLE_EXTERNAL_PROVIDERS")
    
    # Commented out to allow SQLite
    # @field_validator("database_url", mode="before")
    def validate_database_url(cls, v):
        print(f"DEBUG: validate_database_url called with: {v}")
        if isinstance(v, str):
            # Don't convert SQLite URLs
            if v.startswith("sqlite"):
                return v
            # Only convert PostgreSQL URLs to asyncpg
            elif v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://")
        return v
    
    @field_validator("allowed_origins", mode="before")
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Example env file content
        env_file_content_example = """
# Application
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ghg_calculator

# Redis
REDIS_URL=redis://localhost:6379

# Authentication
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AWS
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
S3_BUCKET=ghg-calculator-reports

# External APIs
EPA_API_KEY=your-epa-api-key

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
"""


@lru_cache()
def get_settings() -> "Settings":
    """Get cached settings instance"""
    return Settings()


# Database Setup
class DatabaseManager:
    """Manage database connections and sessions"""
    
    def __init__(self, settings: "Settings"):
        self.settings = settings
        self._engine: Optional["AsyncEngine"] = None
        self._sessionmaker: Optional[sessionmaker] = None
        
    async def initialize(self):
        """Initialize database engine and sessionmaker"""
        self._engine = create_async_engine(
            str(self.settings.database_url),
            echo=self.settings.database_echo,
            pool_size=self.settings.database_pool_size,
            max_overflow=self.settings.database_max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            poolclass=NullPool if self.settings.environment == "test" else None
        )
        
        self._sessionmaker = sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
        
        # Create tables in development
        if self.settings.environment == "development":
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
    async def close(self):
        """Close database connections"""
        if self._engine:
            await self._engine.dispose()
            
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session"""
        if not self._sessionmaker:
            await self.initialize()
            
        async with self._sessionmaker() as session:
            try:
                yield session
            finally:
                await session.close()


# Singleton database manager
_db_manager: Optional["DatabaseManager"] = None


async def get_db_manager() -> "DatabaseManager":
    """Get database manager instance"""
    global _db_manager
    if not _db_manager:
        _db_manager = DatabaseManager(get_settings())
        await _db_manager.initialize()
    return _db_manager


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    db_manager = await get_db_manager()
    async for session in db_manager.get_session():
        yield session


# Cache Setup
class CachePool:
    """Redis connection pool manager"""
    
    def __init__(self, settings: "Settings"):
        self.settings = settings
        self._pool: Optional[redis.ConnectionPool] = None
        self._redis: Optional[redis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection pool"""
        self._pool = redis.ConnectionPool.from_url(
            str(self.settings.redis_url),
            max_connections=self.settings.redis_pool_size,
            decode_responses=True
        )
        self._redis = redis.Redis(connection_pool=self._pool)
        
    async def close(self):
        """Close Redis connections"""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
            
    async def get_redis(self) -> redis.Redis:
        """Get Redis client"""
        if not self._redis:
            await self.initialize()
        return self._redis


# Singleton cache pool
_cache_pool: Optional["CachePool"] = None


async def get_cache_pool() -> "CachePool":
    """Get cache pool instance"""
    global _cache_pool
    if not _cache_pool:
        _cache_pool = CachePool(get_settings())
        await _cache_pool.initialize()
    return _cache_pool


async def get_cache() -> redis.Redis:
    """Dependency to get Redis client"""
    cache_pool = await get_cache_pool()
    return await cache_pool.get_redis()


# AWS Clients
@lru_cache()
def get_s3_client():
    """Get configured S3 client"""
    settings = get_settings()
    
    config = Config(
        region_name=settings.aws_region,
        retries={'max_attempts': 3, 'mode': 'adaptive'}
    )
    
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        return boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key.get_secret_value(),
            config=config
        )
    else:
        # Use IAM role
        return boto3.client('s3', config=config)


# Authentication Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings)
) -> "User":
    """Validate JWT token and return current user"""
    token = credentials.credentials
    
    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # In production, would fetch from database
        user = User(
            id=user_id,
            email=payload.get("email"),
            name=payload.get("name"),
            is_active=payload.get("is_active", True),
            is_admin=payload.get("is_admin", False)
        )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_organization(
    current_user: "User" = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> "Organization":
    """Get organization for current user"""
    # In production, would fetch from database based on user
    # For now, return mock organization
    return Organization(
        id="550e8400-e29b-41d4-a716-446655440000",
        name="Example Corp",
        industry="Manufacturing",
        reporting_year=2024,
        locations=["US", "EU", "CN"]
    )


# Repository Dependencies
async def get_cache_manager(
    cache: redis.Redis = Depends(get_cache)
) -> "CacheManager":
    """Get cache manager instance"""
    manager = CacheManager()
    manager._redis = cache
    return manager


async def get_emission_factor_repository(
    db: AsyncSession = Depends(get_db),
    cache_manager: "CacheManager" = Depends(get_cache_manager),
    settings: Settings = Depends(get_settings)
) -> "EmissionFactorRepository":
    """Get emission factor repository with external providers"""
    
    # Create database repository
    db_repo = DatabaseEmissionFactorRepository(db, cache_manager)
    
    if not settings.enable_external_providers:
        return db_repo
        
    # Add external providers
    providers = []
    
    if settings.epa_api_key:
        providers.append(
            EPAEmissionFactorProvider(
                api_key=settings.epa_api_key.get_secret_value()
            )
        )
        
    providers.append(DEFRAEmissionFactorProvider())
    
    # Return composite repository
    return CompositeEmissionFactorRepository(
        primary_repo=db_repo,
        providers=providers,
        cache=cache_manager
    )


async def get_activity_data_repository(
    db: AsyncSession = Depends(get_db)
) -> "ActivityDataRepository":
    """Get activity data repository"""
    return ActivityDataRepository(db)


async def get_calculation_result_repository(
    db: AsyncSession = Depends(get_db)
) -> "CalculationResultRepository":
    """Get calculation result repository"""
    return CalculationResultRepository(db)


async def get_audit_log_repository(
    db: AsyncSession = Depends(get_db)
) -> "AuditLogRepository":
    """Get audit log repository"""
    return AuditLogRepository(db)


async def get_organization_repository(
    db: AsyncSession = Depends(get_db)
) -> "OrganizationRepository":
    """Get organization repository"""
    return OrganizationRepository(db)


# Service Dependencies
async def get_calculation_service(
    ef_repo: "EmissionFactorRepository" = Depends(get_emission_factor_repository),
    ad_repo: "ActivityDataRepository" = Depends(get_activity_data_repository),
    calc_repo: "CalculationResultRepository" = Depends(get_calculation_result_repository),
    audit_repo: "AuditLogRepository" = Depends(get_audit_log_repository),
    cache: redis.Redis = Depends(get_cache)
) -> "CalculationService":
    """Get calculation service"""
    return CalculationService(
        ef_repo=ef_repo,
        ad_repo=ad_repo,
        calc_repo=calc_repo,
        audit_repo=audit_repo,
        cache=cache
    )


async def get_reporting_service(
    calc_repo: "CalculationResultRepository" = Depends(get_calculation_result_repository),
    org_repo: "OrganizationRepository" = Depends(get_organization_repository),
    s3_client = Depends(get_s3_client)
) -> "ReportingService":
    """Get reporting service"""
    return ReportingService(
        calc_repo=calc_repo,
        org_repo=org_repo,
        s3_client=s3_client
    )


# Rate Limiting
class RateLimiter:
    """Simple rate limiter using Redis"""
    
    def __init__(
        self,
        redis_client: redis.Redis,
        requests: int = 100,
        period: int = 60
    ):
        self.redis = redis_client
        self.requests = requests
        self.period = period
        
    async def check_rate_limit(self, key: str) -> bool:
        """Check if rate limit exceeded"""
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, self.period)
            return current <= self.requests
        except Exception:
            # Fail open
            return True


async def rate_limit_dependency(
    request: Request,
    current_user: "User" = Depends(get_current_user),
    cache: redis.Redis = Depends(get_cache),
    settings: Settings = Depends(get_settings)
):
    """Rate limiting dependency"""
    if not settings.rate_limit_enabled:
        return
        
    limiter = RateLimiter(
        cache,
        settings.rate_limit_requests,
        settings.rate_limit_period
    )
    
    # Rate limit by user ID
    key = f"rate_limit:{current_user.id}:{request.url.path}"
    
    if not await limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


# Monitoring
def setup_monitoring(settings: "Settings"):
    """Setup monitoring integrations"""
    
    # Sentry
    if settings.sentry_dsn:
        sentry_sdk.init(
            dsn=str(settings.sentry_dsn),
            environment=settings.environment,
            traces_sample_rate=0.1 if settings.environment == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.environment == "production" else 1.0,
        )
        
    # Prometheus
    if settings.prometheus_enabled:
        # Registry is created in main app
        pass


# Startup and Shutdown
async def startup_handler():
    """Application startup handler"""
    settings = get_settings()
    
    # Setup monitoring
    setup_monitoring(settings)
    
    # Initialize database
    await get_db_manager()
    
    # Initialize cache
    await get_cache_pool()
    
    # Log startup
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version} "
        f"in {settings.environment} mode"
    )


async def shutdown_handler():
    """Application shutdown handler"""
    # Close database connections
    if _db_manager:
        await _db_manager.close()
        
    # Close cache connections
    if _cache_pool:
        await _cache_pool.close()
        
    # Log shutdown
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down application")


# Helper functions
def create_access_token(
    data: dict,
    settings: Settings = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    if not settings:
        settings = get_settings()
        
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm
    )
    
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    # In production, use proper password hashing (bcrypt, argon2, etc.)
    import hashlib
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash password"""
    # In production, use proper password hashing
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


def generate_api_key() -> str:
    """Generate secure API key"""
    return secrets.token_urlsafe(32)


# Environment-specific configurations
def get_database_url(environment: str) -> str:
    """Get environment-specific database URL"""
    urls = {
        "development": "postgresql://dev:devpass@localhost:5432/ghg_dev",
        "test": "postgresql://test:testpass@localhost:5432/ghg_test",
        "production": os.getenv("DATABASE_URL")
    }
    return urls.get(environment, urls["development"])


def get_log_config(environment: str) -> dict:
    """Get environment-specific logging configuration"""
    base_config = {
        "version": 1,
        "disable_existing_loggers": "False",
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "json": {
                "format": "%(asctime)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "default",
                "stream": "ext://sys.stdout"
            }
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"]
        }
    }
    
    if environment == "production":
        # Add production handlers (e.g., file, remote logging)
        base_config["handlers"]["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "/var/log/ghg_calculator/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        }
        base_config["root"]["handlers"].append("file")
        
    return base_config


# Create settings instance
settings = Settings()