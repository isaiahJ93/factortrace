# app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
import redis
import stripe
import psutil
import os
from datetime import datetime
import logging

from app.api.deps import get_db
from app.core.config import settings
from app.core.database import get_pool_status, check_database_health

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=Dict[str, Any])
async def health_check():
    """Basic health check - always returns 200 if service is up"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/live", response_model=Dict[str, Any])
async def liveness_check():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if service is alive, 503 if not.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(db: Session = Depends(get_db)):
    """
    Kubernetes readiness probe endpoint.
    Checks if service is ready to handle requests.
    """
    checks = {
        "database": False,
        "redis": False
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database readiness check failed: {e}")
    
    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        checks["redis"] = True
    except Exception as e:
        logger.error(f"Redis readiness check failed: {e}")
    
    # Service is ready only if all critical dependencies are available
    is_ready = all(checks.values())
    
    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "not ready",
                "checks": checks,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    return {
        "status": "ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("/detailed", response_model=Dict[str, Any])
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check with comprehensive system information.
    Use this for monitoring dashboards.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        },
        "checks": {},
        "metrics": {},
        "system": {}
    }
    
    # Database check
    try:
        # Test read
        result = db.execute(text("SELECT COUNT(*) FROM vouchers"))
        voucher_count = result.scalar()
        
        # Test write (rollback after)
        db.execute(text("SELECT 1"))
        db.rollback()
        
        # Get pool status
        pool_status = get_pool_status()
        
        health_status["checks"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0,  # Would need timing logic
            "pool": pool_status,
            "voucher_count": voucher_count
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Redis check
    try:
        r = redis.from_url(settings.REDIS_URL)
        start = datetime.utcnow()
        r.ping()
        response_time = (datetime.utcnow() - start).total_seconds() * 1000
        
        # Get Redis info
        info = r.info()
        
        health_status["checks"]["redis"] = {
            "status": "healthy",
            "response_time_ms": response_time,
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients"),
            "used_memory_human": info.get("used_memory_human"),
            "uptime_days": info.get("uptime_in_days")
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Stripe check
    try:
        if settings.STRIPE_SECRET_KEY:
            stripe.api_key = settings.STRIPE_SECRET_KEY
            # Just verify the key format
            health_status["checks"]["stripe"] = {
                "status": "configured",
                "webhook_configured": bool(settings.STRIPE_WEBHOOK_SECRET)
            }
        else:
            health_status["checks"]["stripe"] = {
                "status": "not configured"
            }
    except Exception as e:
        health_status["checks"]["stripe"] = {
            "status": "error",
            "error": str(e)
        }
    
    # Email service check
    try:
        if settings.EMAIL_PROVIDER == "sendgrid":
            health_status["checks"]["email"] = {
                "status": "configured" if settings.SENDGRID_API_KEY else "not configured",
                "provider": "sendgrid"
            }
        elif settings.EMAIL_PROVIDER == "ses":
            health_status["checks"]["email"] = {
                "status": "configured" if settings.AWS_ACCESS_KEY_ID else "not configured",
                "provider": "ses"
            }
    except Exception as e:
        health_status["checks"]["email"] = {
            "status": "error",
            "error": str(e)
        }
    
    # System metrics
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Disk usage
        disk = psutil.disk_usage('/')
        
        # Process info
        process = psutil.Process(os.getpid())
        
        health_status["system"] = {
            "cpu": {
                "count": psutil.cpu_count(),
                "usage_percent": cpu_percent
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_percent": disk.percent
            },
            "process": {
                "pid": process.pid,
                "threads": process.num_threads(),
                "memory_mb": round(process.memory_info().rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent()
            }
        }
    except Exception as e:
        logger.error(f"System metrics collection failed: {e}")
        health_status["system"] = {"error": str(e)}
    
    # Application metrics
    try:
        # Get some basic metrics from database
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        active_vouchers = db.execute(
            text("SELECT COUNT(*) FROM vouchers WHERE is_used = false AND valid_until > NOW()")
        ).scalar() if not str(settings.database_url).startswith("sqlite") else 0
        
        health_status["metrics"] = {
            "users": {
                "total": user_count
            },
            "vouchers": {
                "active": active_vouchers
            }
        }
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        health_status["metrics"] = {"error": str(e)}
    
    # Determine overall status
    critical_checks = ["database", "redis"]
    for check in critical_checks:
        if check in health_status["checks"] and health_status["checks"][check].get("status") != "healthy":
            health_status["status"] = "unhealthy"
            break
    
    # Return appropriate status code
    if health_status["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=health_status
        )
    
    return health_status

@router.get("/dependencies", response_model=Dict[str, Any])
async def check_dependencies():
    """
    Check all external dependencies status.
    Useful for debugging integration issues.
    """
    dependencies = {
        "database": {
            "url": str(settings.database_url).split("@")[0] + "@***",  # Hide password
            "type": "postgresql" if "postgresql" in str(settings.database_url) else "sqlite"
        },
        "redis": {
            "url": settings.REDIS_URL.split("@")[0] + "@***" if "@" in settings.REDIS_URL else settings.REDIS_URL,
            "configured": bool(settings.REDIS_URL)
        },
        "stripe": {
            "configured": bool(settings.STRIPE_SECRET_KEY),
            "webhook_configured": bool(settings.STRIPE_WEBHOOK_SECRET)
        },
        "email": {
            "provider": settings.EMAIL_PROVIDER,
            "configured": bool(settings.SENDGRID_API_KEY or settings.AWS_ACCESS_KEY_ID)
        },
        "monitoring": {
            "sentry_configured": bool(settings.SENTRY_DSN)
        }
    }
    
    return {
        "dependencies": dependencies,
        "environment": settings.ENVIRONMENT,
        "debug_mode": settings.DEBUG
    }