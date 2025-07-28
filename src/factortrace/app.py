from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from fastapi import FastAPI

def create_app() -> FastAPI:
    app = FastAPI(title="FactorTrace API")

    from factortrace.routes import register_routers
    register_routers(app)

    return app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Application factory pattern for creating FastAPI instances.
    This prevents circular imports and allows for easy testing.
    
    Returns:
        FastAPI: Configured application instance
    """
    
    # Lifespan context manager for startup/shutdown events
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Handle application lifecycle events"""
        # Startup
        logger.info("FactorTrace API starting up...")
        yield
        # Shutdown
        logger.info("FactorTrace API shutting down...")
    
    # Create app instance
    app = FastAPI(
        title="FactorTrace Scope 3 Compliance API",
        description="Enterprise-grade Scope 3 emissions tracking and CSRD/ESRS compliance tool",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Register routers - using deferred imports to prevent circular dependencies
    _register_routers(app)
    
    # Register exception handlers
    _register_exception_handlers(app)
    
    # Register startup events
    _register_startup_events(app)
    
    return app


def _register_routers(app: FastAPI) -> None:
    """
    Register all application routers.
    Uses deferred imports to prevent circular dependencies.
    """
    # Import routers inside function to avoid circular imports
    from factortrace.routes.admin import router as admin_router
    from factortrace.api.routes_voucher import router as voucher_router
    from factortrace.routes.compliance import router as compliance_router
    from factortrace.routes.export import router as export_router
    from factortrace.routes.generate import router as generate_router
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Application health check endpoint"""
        return {"status": "healthy", "service": "factortrace-api"}
    
    # Register routers with proper prefixes
    app.include_router(admin_router, prefix="/admin", tags=["admin"])
    app.include_router(voucher_router, prefix="/api/v1/vouchers", tags=["vouchers"])
    app.include_router(compliance_router, prefix="/api/v1/compliance", tags=["compliance"])
    app.include_router(export_router, prefix="/api/v1/export", tags=["export"])
    app.include_router(generate_router, prefix="/api/v1/generate", tags=["generate"])
    
    logger.info("All routers registered successfully")


def _register_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers"""
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTP exceptions with custom responses"""
        # For API endpoints, return JSON
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.status_code,
                        "message": exc.detail,
                        "type": "http_error",
                    }
                },
            )
        
        # For admin/web endpoints, return HTML (if templates are available)
        try:
            from factortrace.routes.admin import templates
            
            if exc.status_code == HTTP_500_INTERNAL_SERVER_ERROR:
                return templates.TemplateResponse(
                    "500.html",
                    {
                        "request": request,
                        "status_code": exc.status_code,
                        "detail": exc.detail,
                    },
                    status_code=exc.status_code,
                )
            
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "status_code": exc.status_code,
                    "detail": exc.detail,
                },
                status_code=exc.status_code,
            )
        except ImportError:
            # Fallback to JSON if templates not available
            return JSONResponse(
                status_code=exc.status_code,
                content={"error": {"code": exc.status_code, "message": exc.detail}},
            )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed messages"""
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "type": "validation_error",
                    "details": exc.errors(),
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions"""
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                    "type": "internal_error",
                }
            },
        )


def _register_startup_events(app: FastAPI) -> None:
    """Register startup events and initialization logic"""
    
    @app.on_event("startup")
    async def initialize_database():
        """Initialize database connections and tables"""
        try:
            # Lazy import to avoid circular dependencies
            from factortrace.routes.admin import init_db
            
            init_db()
            logger.info("Database initialized successfully")
        except ImportError:
            logger.warning("Database initialization skipped - admin module not found")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            # Don't fail startup - allow app to run even if DB init fails

            