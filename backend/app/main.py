# app/main.py
"""
FactorTrace API - Production-ready FastAPI application
Implements ESRS E1 compliance platform with Stripe payments
"""
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
import logging
import time
import uuid
import os
from typing import Dict, Any, Optional

# Import settings and database
from app.core.config import settings
from app.core.database import engine, Base
# from .db.database import create_db_and_tables
from .api.v1.api import api_router


# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.environment == "production" else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Optional imports with graceful fallback
try:
    import sentry_sdk
    from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False
    logger.warning("Sentry SDK not installed - error tracking disabled")

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    RATE_LIMIT_AVAILABLE = True
    
    # Create limiter instance
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["100 per minute", "1000 per hour"]
    )
except ImportError:
    RATE_LIMIT_AVAILABLE = False
    logger.warning("SlowAPI not installed - rate limiting disabled")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} API v{settings.app_version}...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database: {str(settings.database_url).split('@')[-1] if '@' in str(settings.database_url) else 'local'}")
    
    # Create database tables
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Create required directories
    for directory in ["uploads", "logs", "temp"]:
        Path(directory).mkdir(exist_ok=True)
    
    # Initialize Sentry if available and configured
    if SENTRY_AVAILABLE and getattr(settings, "SENTRY_DSN", None) and settings.environment == "production":
        sentry_sdk.init(
            dsn=getattr(settings, "SENTRY_DSN", None),
            environment=settings.environment,
            traces_sample_rate=0.1,
        )
        logger.info("Sentry error tracking initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down FactorTrace API...")
    engine.dispose()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # await create_db_and_tables()
    yield
    # Shutdown
    pass

app = FastAPI(
    title=settings.app_name,
    openapi_url=f"{settings.api_prefix}/openapi.json",
    lifespan=lifespan
)

app.include_router(api_router, prefix=settings.api_prefix)

# EMERGENCY FIX - Direct emissions router include
try:
    from app.api.v1.endpoints.emissions import router as emissions_router
    app.include_router(emissions_router, prefix="/api/v1/emissions", tags=["emissions"])
    logger.info("✅ Emissions router manually included")
except Exception as e:
    logger.error(f"❌ Failed to include emissions router: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="ESRS E1 Emissions Compliance Platform API",
    version=settings.app_version,
    openapi_url=f"{settings.api_prefix}/openapi.json" if settings.environment != "production" else None,
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan
)

# Add rate limiter if available
if RATE_LIMIT_AVAILABLE:
    app.state.limiter = limiter
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        response = JSONResponse(
            content={
                "detail": f"Rate limit exceeded: {exc.detail}",
                "type": "rate_limit_exceeded"
            },
            status_code=429
        )
        response.headers["Retry-After"] = str(60)  # Retry after 60 seconds
        return response

# Security middleware
if settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_origins
    )

# CORS middleware - configure properly
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Process-Time"],
)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response

# Request ID and logging middleware
@app.middleware("http")
async def add_request_id_and_logging(request: Request, call_next):
    # Generate request ID
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Log request
    logger.info(
        f"[{request_id}] {request.client.host} - "
        f"{request.method} {request.url.path}"
    )
    
    # Time the request
    start_time = time.time()
    
    # Process request
    try:
        response = await call_next(request)
    except Exception as e:
        # Log unhandled exceptions
        logger.error(f"[{request_id}] Unhandled exception: {e}", exc_info=True)
        raise
    
    # Calculate process time
    process_time = time.time() - start_time
    
    # Add headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    # Log response
    logger.info(
        f"[{request_id}] Completed - "
        f"status: {response.status_code}, "
        f"duration: {process_time:.3f}s"
    )
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, 'request_id', 'unknown')
    
    # Log the full exception
    logger.error(f"[{request_id}] Unhandled exception: {exc}", exc_info=True)
    
    # Send to Sentry if available
    if SENTRY_AVAILABLE and getattr(settings, "SENTRY_DSN", None):
        import sentry_sdk
        sentry_sdk.capture_exception(exc)
    
    # Return appropriate error response
    if settings.environment == "production":
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
                "support": "Please contact support@factortrace.com with the request ID"
            }
        )
    else:
        # Development mode - include error details
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": str(exc),
                "request_id": request_id,
                "type": type(exc).__name__,
                "traceback": "See logs for full traceback"
            }
        )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Return JSON response instead of trying to render HTML
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Import and include API router
try:
    from app.api.v1.api import api_router
    app.include_router(api_router, prefix=settings.api_prefix)
    logger.info(f"API router mounted at {settings.api_prefix}")
except ImportError as e:
    logger.error(f"Failed to import API router: {e}")

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "environment": settings.environment,
        "docs": "/docs" if settings.environment != "production" else "Disabled in production",
        "health": "/health",
        "api": settings.api_prefix
    }

# Basic health check
@app.get("/health", tags=["health"])
async def health_check():
    """Basic health check for load balancers"""
    return {
        "status": "healthy",
        "service": "factortrace-api",
        "version": settings.app_version
    }

# Detailed health check
@app.get("/health/detailed", tags=["health"])
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with dependency status"""
    from app.core.database import check_database_health
    
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {}
    }
    
    # Check database
    try:
        db_healthy = check_database_health()
        health_status["checks"]["database"] = {
            "status": "healthy" if db_healthy else "unhealthy",
            "type": "postgresql" if "postgresql" in str(settings.database_url) else "sqlite"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis if configured
    if settings.redis_url:
        try:
            import redis
            r = redis.from_url(settings.redis_url)
            r.ping()
            health_status["checks"]["redis"] = {"status": "healthy"}
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health_status["status"] = "degraded"
    
    # Check critical services
    health_status["checks"]["stripe"] = {
        "status": "configured" if settings.stripe_secret_key else "not_configured"
    }
    
    health_status["checks"]["email"] = {
        "status": "configured" if settings.sendgrid_api_key else "not_configured"
    }
    
    # System metrics
    try:
        import psutil
        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        }
    except ImportError:
        pass
    
    return health_status

# Prometheus metrics endpoint (optional)
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus-compatible metrics endpoint"""
    metrics_data = []
    
    # Basic API metrics
    metrics_data.append('# HELP factortrace_api_up API status (1=up, 0=down)')
    metrics_data.append('# TYPE factortrace_api_up gauge')
    metrics_data.append('factortrace_api_up 1')
    
    # Version info
    metrics_data.append('# HELP factortrace_api_info API version information')
    metrics_data.append('# TYPE factortrace_api_info gauge')
    metrics_data.append(f'factortrace_api_info{{version="{settings.app_version}",environment="{settings.environment}"}} 1')
    
    return "\n".join(metrics_data)

@app.get("/api/v1/emissions")
async def get_emissions(scope: int = 3):
    """Temporary emissions endpoint"""
    return {
        "emissions": [
            {
                "id": "em_2023_machinery_001",
                "category": "Machinery & Equipment",
                "subcategory": "2. Capital Goods",
                "framework": "EPA EEIO",
                "amount": 0,
                "unit": "EUR",
                "percentage": 10,
                "evidenceCount": 0,
                "evidenceRequired": True
            },
            {
                "id": "em_2023_construction_001",
                "category": "Buildings & Construction",
                "subcategory": "2. Capital Goods",
                "framework": "EPA EEIO",
                "amount": 0,
                "unit": "EUR",
                "percentage": 10,
                "evidenceCount": 0,
                "evidenceRequired": True
            }
        ]
    }

@app.post("/api/v1/emissions/{emission_id}/evidence")
async def upload_evidence(emission_id: str):
    """Temporary evidence upload endpoint"""
    return {
        "evidenceId": f"evd_{datetime.now().timestamp()}",
        "emissionId": emission_id,
        "status": "success"
    }

# Also add this health check if missing:
@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "api_version": "v1"}

# Add Sentry middleware if available
if SENTRY_AVAILABLE and getattr(settings, "SENTRY_DSN", None):
    app.add_middleware(SentryAsgiMiddleware)

# Log startup configuration
logger.info("=" * 50)
logger.info(f"FactorTrace API v{settings.app_version} initialized")
logger.info(f"Environment: {settings.environment}")
logger.info(f"CORS Origins: {settings.allowed_origins}")
logger.info(f"Rate Limiting: {'Enabled' if RATE_LIMIT_AVAILABLE else 'Disabled'}")
logger.info(f"Error Tracking: Disabled")
logger.info("=" * 50)