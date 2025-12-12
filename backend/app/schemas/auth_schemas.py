# app/schemas/auth_schemas.py
"""
Authentication schemas - includes multi-tenant CurrentUser.

CurrentUser is the canonical representation of the authenticated user
with tenant_id required for all tenant-scoped operations.
"""
from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional


class CurrentUser(BaseModel):
    """
    Authenticated user with tenant context.

    This is the canonical user representation used throughout the application.
    tenant_id is REQUIRED and extracted from JWT claims (app_metadata).

    Security: All endpoint handlers should use this for tenant-scoped operations.
    """
    id: str
    email: str
    tenant_id: str  # REQUIRED - from JWT app_metadata
    is_active: bool = True
    is_superuser: bool = False  # Tenant-level admin
    is_super_admin: bool = False  # Platform-level super-admin (cross-tenant)

    # Optional profile fields
    name: Optional[str] = None
    company_name: Optional[str] = None

    # Voucher context (optional, for voucher-based auth)
    voucher_code: Optional[str] = None
    voucher_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @property
    def can_access_all_tenants(self) -> bool:
        """Check if user has cross-tenant access (super-admin only)."""
        return self.is_super_admin


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    email: EmailStr
    password: str
    name: Optional[str] = None
    tenant_id: Optional[str] = None  # If not provided, use default tenant

    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v


class UserResponse(BaseModel):
    """Schema for user response (public fields only)."""
    id: int
    email: str
    name: Optional[str]
    tenant_id: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenPayload(BaseModel):
    """
    Expected JWT payload structure.

    tenant_id should be in app_metadata for Supabase JWTs.
    """
    sub: str  # User ID
    email: Optional[str] = None
    tenant_id: Optional[str] = None  # Direct claim or from app_metadata
    is_super_admin: bool = False
    exp: Optional[int] = None

    # Supabase-specific metadata
    app_metadata: Optional[dict] = None
    user_metadata: Optional[dict] = None

    def get_tenant_id(self) -> Optional[str]:
        """
        Extract tenant_id from payload.

        Checks direct claim first, then app_metadata.
        """
        if self.tenant_id:
            return self.tenant_id
        if self.app_metadata and 'tenant_id' in self.app_metadata:
            return self.app_metadata['tenant_id']
        return None