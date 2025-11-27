# app/core/supabase_auth.py
"""
Complete Supabase authentication with voucher code login
Handles: Email + Code → Supabase Auth → Session → Calculator Access
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
from jose import JWTError, jwt
import logging

from app.db.session import get_db

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class AuthConfig:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
    JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SUPABASE_JWT_SECRET", ""))
    JWT_ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Security scheme
security = HTTPBearer(auto_error=False)

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VoucherLoginRequest(BaseModel):
    """Request for voucher code login"""
    email: EmailStr
    voucher_code: str

class VoucherLoginResponse(BaseModel):
    """Response after successful login"""
    success: bool
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    voucher_activated: bool
    calculator_access: bool
    message: str

class TokenData(BaseModel):
    """JWT Token payload"""
    user_id: str
    email: str
    voucher_code: Optional[str] = None
    voucher_id: Optional[str] = None
    session_id: Optional[str] = None

class CurrentUser(BaseModel):
    """Current authenticated user"""
    user_id: str
    email: str
    voucher_code: Optional[str] = None
    voucher_id: Optional[str] = None
    is_authenticated: bool = True

# ============================================================================
# SUPABASE AUTH SERVICE
# ============================================================================

class SupabaseAuthService:
    """
    Handles Supabase authentication with voucher codes
    """
    
    def __init__(self):
        """Initialize Supabase clients"""
        if not AuthConfig.SUPABASE_URL or not AuthConfig.SUPABASE_ANON_KEY:
            logger.warning("Supabase credentials not configured")
            self.client = None
            self.admin_client = None
        else:
            # Public client for regular operations
            self.client: Client = create_client(
                AuthConfig.SUPABASE_URL,
                AuthConfig.SUPABASE_ANON_KEY
            )
            
            # Admin client for service operations (if service key provided)
            if AuthConfig.SUPABASE_SERVICE_KEY:
                self.admin_client: Client = create_client(
                    AuthConfig.SUPABASE_URL,
                    AuthConfig.SUPABASE_SERVICE_KEY
                )
            else:
                self.admin_client = self.client
    
    async def login_with_voucher(
        self,
        email: str,
        voucher_code: str,
        db: Session
    ) -> VoucherLoginResponse:
        """
        Authenticate user with email and voucher code
        
        Flow:
        1. Verify voucher code exists in Supabase
        2. Check if voucher is already used
        3. Create/get user in Supabase
        4. Link voucher to user
        5. Generate access token
        """
        
        if not self.client:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service not configured"
            )
        
        try:
            # Clean voucher code (remove dashes, uppercase)
            clean_code = voucher_code.replace("-", "").strip().upper()
            
            # Step 1: Verify voucher in Supabase
            voucher_result = self.admin_client.table('vouchers').select("*").eq(
                'code', clean_code
            ).single().execute()
            
            if not voucher_result.data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid voucher code"
                )
            
            voucher = voucher_result.data
            
            # Step 2: Check voucher status
            if voucher.get('status') == 'REDEEMED':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This voucher has already been used"
                )
            
            if voucher.get('status') != 'ACTIVE':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Voucher is not active (status: {voucher.get('status')})"
                )
            
            # Check expiration
            expires_at = voucher.get('expires_at')
            if expires_at:
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if expiry_date < datetime.utcnow():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Voucher has expired"
                    )
            
            # Step 3: Create or get user
            user_id = await self._get_or_create_user(email)
            
            # Step 4: Link voucher to user and mark as redeemed
            update_result = self.admin_client.table('vouchers').update({
                'status': 'REDEEMED',
                'redeemed_at': datetime.utcnow().isoformat(),
                'redeemed_by': user_id,
                'redeemed_email': email
            }).eq('code', clean_code).execute()
            
            # Step 5: Create session in your database
            session_token = secrets.token_urlsafe(32)
            
            # Store session in your PostgreSQL database
            db.execute("""
                INSERT INTO user_sessions (
                    session_token, supabase_user_id, voucher_id, 
                    created_at, expires_at, ip_address
                ) VALUES (
                    :token, :user_id, :voucher_id,
                    NOW(), NOW() + INTERVAL '24 hours', :ip
                )
            """, {
                'token': session_token,
                'user_id': user_id,
                'voucher_id': voucher.get('id'),
                'ip': '0.0.0.0'  # You'll pass actual IP from request
            })
            db.commit()
            
            # Step 6: Generate JWT token
            access_token = self._create_access_token(
                user_id=user_id,
                email=email,
                voucher_code=clean_code,
                voucher_id=voucher.get('id')
            )
            
            return VoucherLoginResponse(
                success=True,
                access_token=access_token,
                user_id=user_id,
                email=email,
                voucher_activated=True,
                calculator_access=True,
                message="Successfully authenticated with voucher"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )
    
    async def _get_or_create_user(self, email: str) -> str:
        """
        Get existing user or create new one in Supabase
        """
        try:
            # Try to get existing user
            result = self.admin_client.auth.admin.list_users()
            
            for user in result:
                if user.email == email:
                    return user.id
            
            # Create new user if doesn't exist
            # Generate random password (user won't use it, they login with voucher)
            temp_password = secrets.token_urlsafe(32)
            
            create_result = self.admin_client.auth.admin.create_user({
                'email': email,
                'password': temp_password,
                'email_confirm': True  # Auto-confirm email
            })
            
            return create_result.user.id
            
        except Exception as e:
            logger.error(f"User creation error: {str(e)}")
            # If admin API not available, use regular sign up
            temp_password = secrets.token_urlsafe(32)
            result = self.client.auth.sign_up({
                'email': email,
                'password': temp_password
            })
            return result.user.id if result.user else None
    
    def _create_access_token(
        self,
        user_id: str,
        email: str,
        voucher_code: Optional[str] = None,
        voucher_id: Optional[str] = None
    ) -> str:
        """
        Create JWT access token
        """
        payload = {
            'user_id': user_id,
            'email': email,
            'voucher_code': voucher_code,
            'voucher_id': voucher_id,
            'exp': datetime.utcnow() + timedelta(minutes=AuthConfig.ACCESS_TOKEN_EXPIRE_MINUTES),
            'iat': datetime.utcnow()
        }
        
        # Use Supabase JWT secret if available
        secret = AuthConfig.JWT_SECRET or AuthConfig.SUPABASE_ANON_KEY
        
        return jwt.encode(payload, secret, algorithm=AuthConfig.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """
        Verify JWT token and return token data
        """
        try:
            secret = AuthConfig.JWT_SECRET or AuthConfig.SUPABASE_ANON_KEY
            payload = jwt.decode(token, secret, algorithms=[AuthConfig.JWT_ALGORITHM])
            
            return TokenData(
                user_id=payload.get('user_id'),
                email=payload.get('email'),
                voucher_code=payload.get('voucher_code'),
                voucher_id=payload.get('voucher_id')
            )
        except JWTError:
            return None

# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

# Singleton instance
_auth_service: Optional[SupabaseAuthService] = None

def get_auth_service() -> SupabaseAuthService:
    """Get or create auth service instance"""
    global _auth_service
    if _auth_service is None:
        _auth_service = SupabaseAuthService()
    return _auth_service

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: SupabaseAuthService = Depends(get_auth_service),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Get current authenticated user from JWT token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = auth_service.verify_token(credentials.credentials)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify session is still valid in database
    session = db.execute("""
        SELECT * FROM user_sessions 
        WHERE supabase_user_id = :user_id 
        AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
    """, {'user_id': token_data.user_id}).fetchone()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return CurrentUser(
        user_id=token_data.user_id,
        email=token_data.email,
        voucher_code=token_data.voucher_code,
        voucher_id=token_data.voucher_id
    )

async def require_calculator_access(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    Require authenticated user with calculator access
    """
    # Check if report already generated (which locks access)
    session = db.execute("""
        SELECT report_generated, calculator_access_allowed 
        FROM user_sessions 
        WHERE supabase_user_id = :user_id 
        AND expires_at > NOW()
        ORDER BY created_at DESC
        LIMIT 1
    """, {'user_id': current_user.user_id}).fetchone()
    
    if session and session['report_generated']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Calculator access has been locked after report generation"
        )
    
    return current_user

# ============================================================================
# API ENDPOINTS
# ============================================================================

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

@router.post("/login", response_model=VoucherLoginResponse)
async def login_with_voucher(
    request: VoucherLoginRequest,
    db: Session = Depends(get_db),
    auth_service: SupabaseAuthService = Depends(get_auth_service)
):
    """
    Login with email and voucher code
    
    This is the main authentication endpoint that:
    1. Validates the voucher code
    2. Creates/gets user in Supabase
    3. Returns JWT token for accessing calculator
    """
    return await auth_service.login_with_voucher(
        email=request.email,
        voucher_code=request.voucher_code,
        db=db
    )

@router.get("/me")
async def get_current_user_info(
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    return current_user

@router.post("/logout")
async def logout(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout and invalidate session
    """
    # Invalidate session in database
    db.execute("""
        UPDATE user_sessions 
        SET expires_at = NOW() 
        WHERE supabase_user_id = :user_id
    """, {'user_id': current_user.user_id})
    db.commit()
    
    return {"success": True, "message": "Logged out successfully"}