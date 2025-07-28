# app/middleware/rate_limit.py
"""Rate limiting middleware"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute", "1000 per hour"]
)

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> Response:
    """Custom rate limit exceeded handler"""
    response = JSONResponse(
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "type": "rate_limit_exceeded"
        },
        status_code=429
    )
    response.headers["Retry-After"] = str(exc.retry_after)
    return response

class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """Add rate limit headers to responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers if they exist in request state
        if hasattr(request.state, "view_rate_limit"):
            limit_value = request.state.view_rate_limit
            response.headers["X-RateLimit-Limit"] = str(limit_value)
            
            # In production, you'd track actual usage
            # For now, just show mock values
            response.headers["X-RateLimit-Remaining"] = str(max(0, limit_value - 1))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + 3600)
        
        return response


# app/middleware/security.py
"""Security middleware"""
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import re

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Remove server header
        response.headers.pop("Server", None)
        
        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate incoming requests"""
    
    # Dangerous paths that should be blocked
    BLOCKED_PATHS = [
        r"\.\.\/",  # Path traversal
        r"\.env",   # Environment files
        r"\.git",   # Git files
        r"wp-admin", # Common attack vectors
        r"phpmyadmin",
        r"admin\.php",
    ]
    
    async def dispatch(self, request: Request, call_next):
        # Check for dangerous paths
        path = request.url.path
        for pattern in self.BLOCKED_PATHS:
            if re.search(pattern, path, re.IGNORECASE):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Forbidden"}
                )
        
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 10 * 1024 * 1024:  # 10MB limit
            return JSONResponse(
                status_code=413,
                content={"detail": "Request entity too large"}
            )
        
        response = await call_next(request)
        return response


