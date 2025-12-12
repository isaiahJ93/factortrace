# backend/app/core/auth.py
"""
Authentication module with multi-tenant support.

This module provides:
- JWT validation (local or Supabase)
- tenant_id extraction from JWT claims
- CurrentUser dependency for endpoints

Security: All authenticated requests MUST have a valid tenant_id.
"""
import os
from typing import Optional
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.auth_schemas import CurrentUser, TokenPayload
from app.models.tenant import Tenant

# Security scheme
security = HTTPBearer(auto_error=False)

# Configuration (should come from settings in production)
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Development mode flag
DEV_MODE = os.getenv("ENVIRONMENT", "development") == "development"
DEV_TENANT_ID = os.getenv("DEV_TENANT_ID", "dev-tenant-00000000-0000-0000-0000-000000000000")


def decode_jwt(token: str) -> Optional[TokenPayload]:
    """
    Decode and validate a JWT token.

    Tries Supabase secret first, then falls back to local secret.
    """
    secrets_to_try = []

    if SUPABASE_JWT_SECRET:
        secrets_to_try.append(SUPABASE_JWT_SECRET)
    secrets_to_try.append(JWT_SECRET)

    for secret in secrets_to_try:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[JWT_ALGORITHM],
                options={"verify_exp": True}
            )
            return TokenPayload(**payload)
        except JWTError:
            continue

    return None


def create_access_token(
    user_id: str,
    email: str,
    tenant_id: str,
    is_super_admin: bool = False,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        user_id: User's unique identifier
        email: User's email
        tenant_id: User's tenant ID (REQUIRED)
        is_super_admin: Whether user has cross-tenant access
        expires_delta: Token expiration time

    Returns:
        Encoded JWT string
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=30)

    expire = datetime.utcnow() + expires_delta

    payload = {
        "sub": user_id,
        "email": email,
        "tenant_id": tenant_id,
        "is_super_admin": is_super_admin,
        "exp": expire,
        # Supabase-compatible format
        "app_metadata": {
            "tenant_id": tenant_id,
            "is_super_admin": is_super_admin,
        }
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Get the current authenticated user with tenant context.

    This is the primary authentication dependency for all endpoints.
    Returns a CurrentUser with tenant_id ALWAYS set.

    Security:
    - Validates JWT token
    - Extracts tenant_id from token claims
    - Verifies tenant exists and is active
    - Raises 401 if any validation fails

    Development mode:
    - If no token provided and DEV_MODE=True, returns a dev user
    - Dev user has a fixed tenant_id for testing
    """
    # Development mode: return mock user if no credentials
    if DEV_MODE and credentials is None:
        return CurrentUser(
            id="dev-user-001",
            email="dev@factortrace.local",
            tenant_id=DEV_TENANT_ID,
            is_active=True,
            is_superuser=False,
            is_super_admin=False,
            name="Development User"
        )

    # Production: require valid credentials
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Decode JWT
    payload = decode_jwt(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract tenant_id from payload
    tenant_id = payload.get_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing tenant_id",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify tenant exists and is active (skip in dev mode for performance)
    if not DEV_MODE:
        tenant = db.query(Tenant).filter(
            Tenant.id == tenant_id,
            Tenant.is_active == True
        ).first()

        if tenant is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive tenant",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # Build CurrentUser
    return CurrentUser(
        id=payload.sub,
        email=payload.email or "",
        tenant_id=tenant_id,
        is_active=True,
        is_superuser=False,
        is_super_admin=payload.is_super_admin,
        name=payload.user_metadata.get("name") if payload.user_metadata else None,
    )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[CurrentUser]:
    """
    Get current user if authenticated, None otherwise.

    Use this for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_super_admin_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """
    Require super-admin access.

    Use this dependency for admin endpoints that access cross-tenant data.
    """
    if not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super-admin access required"
        )
    return current_user


# Alias for backward compatibility
get_current_active_user = get_current_user
