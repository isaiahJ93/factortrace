# app/services/voucher_service.py
"""
Bulletproof voucher redemption service with Supabase integration
Handles race conditions, atomic operations, and session management
"""

import secrets
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
import redis.asyncio as redis
from sqlalchemy import select, update, and_, or_, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import httpx
from pydantic import BaseModel
import jwt
from functools import wraps
import time

# Supabase client
from supabase import create_client, Client

# Local imports
from app.core.config import settings
from app.db.session import get_db
from app.models.voucher import Voucher, VoucherStatus, UserSession, GeneratedReport, VoucherAuditLog


# ============================================================================
# CONFIGURATION
# ============================================================================

class VoucherConfig:
    """Configuration for voucher system"""
    VOUCHER_LENGTH = 16
    SESSION_DURATION_HOURS = 24
    VOUCHER_EXPIRY_DAYS = 90
    MAX_REDEMPTION_ATTEMPTS = 3
    RATE_LIMIT_WINDOW = 60  # seconds
    LOCK_TIMEOUT = 5  # seconds for distributed lock
    
    # Redis keys
    REDIS_VOUCHER_PREFIX = "voucher:"
    REDIS_SESSION_PREFIX = "session:"
    REDIS_LOCK_PREFIX = "lock:voucher:"
    REDIS_RATE_LIMIT_PREFIX = "ratelimit:"


# ============================================================================
# MODELS
# ============================================================================

class VoucherRedemptionRequest(BaseModel):
    """Request model for voucher redemption"""
    code: str
    supabase_token: str  # JWT from Supabase auth

class VoucherRedemptionResponse(BaseModel):
    """Response model for voucher redemption"""
    success: bool
    message: str
    session_token: Optional[str] = None
    voucher_id: Optional[str] = None
    calculator_access: bool = False
    export_access: bool = False

class SessionValidationResponse(BaseModel):
    """Response model for session validation"""
    valid: bool
    voucher_id: Optional[str] = None
    report_generated: bool = False
    calculator_access: bool = False
    export_access: bool = False


# ============================================================================
# VOUCHER SERVICE
# ============================================================================

class VoucherService:
    """
    High-performance voucher management service with Supabase integration
    Implements ACID transactions, distributed locking, and race condition prevention
    """
    
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
        self.redis_client = None
        self._init_redis()
    
    async def _init_redis(self):
        """Initialize Redis connection for distributed locking"""
        try:
            self.redis_client = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis connection failed, using database locks only: {e}")
    
    # ========================================================================
    # VOUCHER GENERATION
    # ========================================================================
    
    def generate_voucher_code(self) -> str:
        """
        Generate cryptographically secure voucher code
        Format: XXXX-XXXX-XXXX-XXXX
        """
        code = secrets.token_urlsafe(VoucherConfig.VOUCHER_LENGTH)[:16].upper()
        return f"{code[:4]}-{code[4:8]}-{code[8:12]}-{code[12:16]}"
    
    async def create_voucher_from_stripe(
        self,
        db: Session,
        stripe_session_id: str,
        stripe_payment_intent_id: str,
        customer_email: str,
        amount: int,
        currency: str = "EUR"
    ) -> Dict[str, Any]:
        """
        Create voucher after successful Stripe payment
        Called from webhook handler
        """
        try:
            # Generate unique code
            max_attempts = 10
            voucher_code = None
            
            for _ in range(max_attempts):
                code = self.generate_voucher_code()
                # Check uniqueness
                existing = db.query(Voucher).filter(Voucher.code == code).first()
                if not existing:
                    voucher_code = code
                    break
            
            if not voucher_code:
                raise ValueError("Failed to generate unique voucher code")
            
            # Create voucher in database
            voucher = Voucher(
                code=voucher_code,
                stripe_checkout_session_id=stripe_session_id,
                stripe_payment_intent_id=stripe_payment_intent_id,
                status=VoucherStatus.ACTIVE,
                activated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=VoucherConfig.VOUCHER_EXPIRY_DAYS),
                purchase_email=customer_email,
                purchase_amount=amount,
                currency=currency
            )
            
            db.add(voucher)
            db.commit()
            
            # Create in Supabase for user access
            await self._sync_voucher_to_supabase(voucher)
            
            # Log creation
            audit_log = VoucherAuditLog(
                action="CREATED",
                success=True,
                voucher_id=voucher.id,
                metadata={"source": "stripe_webhook"}
            )
            db.add(audit_log)
            db.commit()
            
            return {
                "success": True,
                "voucher_code": voucher_code,
                "voucher_id": str(voucher.id),
                "expires_at": voucher.expires_at.isoformat()
            }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create voucher: {str(e)}"
            )
    
    # ========================================================================
    # VOUCHER REDEMPTION (CORE LOGIC)
    # ========================================================================
    
    async def redeem_voucher(
        self,
        db: Session,
        code: str,
        supabase_token: str,
        ip_address: str,
        user_agent: str
    ) -> VoucherRedemptionResponse:
        """
        Atomic voucher redemption with race condition prevention
        Uses pessimistic locking and distributed locks
        """
        # Validate Supabase token
        user_id = await self._validate_supabase_token(supabase_token)
        if not user_id:
            return VoucherRedemptionResponse(
                success=False,
                message="Invalid authentication token"
            )
        
        # Clean voucher code
        clean_code = code.replace("-", "").upper()
        
        # Rate limiting check
        if not await self._check_rate_limit(user_id, ip_address):
            return VoucherRedemptionResponse(
                success=False,
                message="Too many redemption attempts. Please try again later."
            )
        
        # Distributed lock acquisition (if Redis available)
        lock_acquired = False
        lock_key = f"{VoucherConfig.REDIS_LOCK_PREFIX}{clean_code}"
        
        try:
            if self.redis_client:
                lock_acquired = await self._acquire_distributed_lock(lock_key)
                if not lock_acquired:
                    return VoucherRedemptionResponse(
                        success=False,
                        message="Another redemption in progress. Please try again."
                    )
            
            # Execute atomic redemption with database transaction
            result = await self._execute_atomic_redemption(
                db, clean_code, user_id, ip_address, user_agent
            )
            
            return result
            
        finally:
            # Release distributed lock
            if lock_acquired and self.redis_client:
                await self._release_distributed_lock(lock_key)
    
    async def _execute_atomic_redemption(
        self,
        db: Session,
        code: str,
        user_id: str,
        ip_address: str,
        user_agent: str
    ) -> VoucherRedemptionResponse:
        """
        Execute voucher redemption within database transaction
        Uses SELECT FOR UPDATE for row-level locking
        """
        try:
            # Start transaction with highest isolation level
            db.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
            
            # Lock voucher row (pessimistic locking)
            voucher = db.query(Voucher).filter(
                Voucher.code == code
            ).with_for_update(nowait=True).first()
            
            # Validate voucher exists
            if not voucher:
                self._log_audit(db, None, user_id, "REDEMPTION_ATTEMPT", 
                              False, "Invalid voucher code", ip_address)
                return VoucherRedemptionResponse(
                    success=False,
                    message="Invalid voucher code"
                )
            
            # Check if already redeemed
            if voucher.status == VoucherStatus.REDEEMED:
                self._log_audit(db, voucher.id, user_id, "REDEMPTION_ATTEMPT",
                              False, "Already redeemed", ip_address)
                return VoucherRedemptionResponse(
                    success=False,
                    message="This voucher has already been used"
                )
            
            # Check if expired
            if voucher.expires_at < datetime.utcnow():
                voucher.status = VoucherStatus.EXPIRED
                db.commit()
                self._log_audit(db, voucher.id, user_id, "REDEMPTION_ATTEMPT",
                              False, "Expired", ip_address)
                return VoucherRedemptionResponse(
                    success=False,
                    message="This voucher has expired"
                )
            
            # Check if active
            if voucher.status != VoucherStatus.ACTIVE:
                self._log_audit(db, voucher.id, user_id, "REDEMPTION_ATTEMPT",
                              False, f"Status: {voucher.status}", ip_address)
                return VoucherRedemptionResponse(
                    success=False,
                    message=f"Voucher is not active (status: {voucher.status})"
                )
            
            # Generate secure session token
            session_token = self._generate_session_token()
            
            # Create user session
            session = UserSession(
                session_token=session_token,
                supabase_user_id=user_id,
                voucher_id=voucher.id,
                report_generated=False,
                calculator_access_allowed=True,
                export_access_allowed=True,
                expires_at=datetime.utcnow() + timedelta(hours=VoucherConfig.SESSION_DURATION_HOURS),
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.add(session)
            
            # Update voucher status
            voucher.status = VoucherStatus.REDEEMED
            voucher.redeemed_at = datetime.utcnow()
            voucher.supabase_user_id = user_id
            
            # Log successful redemption
            self._log_audit(db, voucher.id, user_id, "REDEEMED",
                          True, "Success", ip_address, {"session_id": str(session.id)})
            
            # Commit transaction
            db.commit()
            
            # Cache session in Redis for fast lookups
            if self.redis_client:
                await self._cache_session(session)
            
            return VoucherRedemptionResponse(
                success=True,
                message="Voucher successfully redeemed",
                session_token=session_token,
                voucher_id=str(voucher.id),
                calculator_access=True,
                export_access=True
            )
            
        except OperationalError as e:
            # Lock acquisition failed (row is locked)
            db.rollback()
            return VoucherRedemptionResponse(
                success=False,
                message="Voucher is being processed. Please try again."
            )
        except Exception as e:
            db.rollback()
            print(f"Redemption error: {str(e)}")
            return VoucherRedemptionResponse(
                success=False,
                message="An error occurred during redemption"
            )
    
    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================
    
    async def validate_session(
        self,
        db: Session,
        session_token: str
    ) -> SessionValidationResponse:
        """
        Validate session and check access permissions
        Uses Redis cache for performance
        """
        # Check Redis cache first
        if self.redis_client:
            cached = await self._get_cached_session(session_token)
            if cached:
                return SessionValidationResponse(**cached)
        
        # Database lookup
        session = db.query(UserSession).filter(
            UserSession.session_token == session_token,
            UserSession.expires_at > datetime.utcnow()
        ).first()
        
        if not session:
            return SessionValidationResponse(valid=False)
        
        # Update last activity
        session.last_activity_at = datetime.utcnow()
        db.commit()
        
        response = SessionValidationResponse(
            valid=True,
            voucher_id=str(session.voucher_id),
            report_generated=session.report_generated,
            calculator_access=session.calculator_access_allowed,
            export_access=session.export_access_allowed
        )
        
        # Update cache
        if self.redis_client:
            await self._cache_session(session)
        
        return response
    
    async def lock_session_after_report(
        self,
        db: Session,
        session_token: str,
        report_data: Dict[str, Any]
    ) -> bool:
        """
        Lock session after report generation
        Implements immediate post-generation lockdown
        """
        try:
            # Get session with lock
            session = db.query(UserSession).filter(
                UserSession.session_token == session_token
            ).with_for_update().first()
            
            if not session or session.report_generated:
                return False
            
            # Create report record
            report = GeneratedReport(
                voucher_id=session.voucher_id,
                session_id=session.id,
                supabase_user_id=session.supabase_user_id,
                report_data=report_data,
                report_type="SCOPE3_EMISSIONS",
                ip_address=session.ip_address
            )
            db.add(report)
            
            # Lock the session
            session.report_generated = True
            session.report_generated_at = datetime.utcnow()
            session.report_id = report.id
            session.calculator_access_allowed = False
            session.export_access_allowed = False
            
            # Log lockdown
            self._log_audit(
                db, session.voucher_id, session.supabase_user_id,
                "SESSION_LOCKED", True, "Report generated",
                session.ip_address, {"report_id": str(report.id)}
            )
            
            db.commit()
            
            # Clear cache
            if self.redis_client:
                await self._invalidate_session_cache(session_token)
            
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Session lock error: {str(e)}")
            return False
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _generate_session_token(self) -> str:
        """Generate cryptographically secure session token"""
        return secrets.token_urlsafe(32)
    
    async def _validate_supabase_token(self, token: str) -> Optional[str]:
        """Validate Supabase JWT and extract user ID"""
        try:
            # Verify with Supabase
            user = self.supabase.auth.get_user(token)
            return user.user.id if user else None
        except Exception:
            return None
    
    async def _check_rate_limit(self, user_id: str, ip_address: str) -> bool:
        """Check rate limiting for redemption attempts"""
        if not self.redis_client:
            return True  # Skip if Redis not available
        
        key = f"{VoucherConfig.REDIS_RATE_LIMIT_PREFIX}{user_id}:{ip_address}"
        try:
            current = await self.redis_client.incr(key)
            if current == 1:
                await self.redis_client.expire(key, VoucherConfig.RATE_LIMIT_WINDOW)
            return current <= VoucherConfig.MAX_REDEMPTION_ATTEMPTS
        except Exception:
            return True  # Allow on Redis error
    
    async def _acquire_distributed_lock(self, key: str) -> bool:
        """Acquire distributed lock using Redis"""
        if not self.redis_client:
            return True
        
        try:
            result = await self.redis_client.set(
                key, "1", nx=True, ex=VoucherConfig.LOCK_TIMEOUT
            )
            return result is not None
        except Exception:
            return True  # Allow on Redis error
    
    async def _release_distributed_lock(self, key: str):
        """Release distributed lock"""
        if self.redis_client:
            try:
                await self.redis_client.delete(key)
            except Exception:
                pass
    
    async def _cache_session(self, session: UserSession):
        """Cache session in Redis"""
        if not self.redis_client:
            return
        
        key = f"{VoucherConfig.REDIS_SESSION_PREFIX}{session.session_token}"
        data = {
            "valid": True,
            "voucher_id": str(session.voucher_id),
            "report_generated": session.report_generated,
            "calculator_access": session.calculator_access_allowed,
            "export_access": session.export_access_allowed
        }
        
        try:
            ttl = int((session.expires_at - datetime.utcnow()).total_seconds())
            await self.redis_client.setex(key, ttl, json.dumps(data))
        except Exception:
            pass
    
    async def _get_cached_session(self, session_token: str) -> Optional[Dict]:
        """Get cached session from Redis"""
        if not self.redis_client:
            return None
        
        key = f"{VoucherConfig.REDIS_SESSION_PREFIX}{session_token}"
        try:
            data = await self.redis_client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None
    
    async def _invalidate_session_cache(self, session_token: str):
        """Invalidate session cache"""
        if self.redis_client:
            key = f"{VoucherConfig.REDIS_SESSION_PREFIX}{session_token}"
            try:
                await self.redis_client.delete(key)
            except Exception:
                pass
    
    def _log_audit(
        self,
        db: Session,
        voucher_id: Optional[UUID],
        user_id: Optional[str],
        action: str,
        success: bool,
        message: str,
        ip_address: str,
        metadata: Optional[Dict] = None
    ):
        """Log audit trail entry"""
        try:
            audit = VoucherAuditLog(
                action=action,
                success=success,
                error_message=message if not success else None,
                voucher_id=voucher_id,
                supabase_user_id=user_id,
                ip_address=ip_address,
                metadata=metadata
            )
            db.add(audit)
            db.commit()
        except Exception as e:
            print(f"Audit log error: {str(e)}")
    
    async def _sync_voucher_to_supabase(self, voucher: Voucher):
        """Sync voucher to Supabase for user visibility"""
        try:
            # Insert into Supabase vouchers table
            self.supabase.table('vouchers').insert({
                'id': str(voucher.id),
                'code': voucher.code,
                'status': voucher.status.value,
                'expires_at': voucher.expires_at.isoformat(),
                'purchase_email': voucher.purchase_email
            }).execute()
        except Exception as e:
            print(f"Supabase sync error: {str(e)}")


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

# Singleton instance
_voucher_service: Optional[VoucherService] = None

async def get_voucher_service() -> VoucherService:
    """Get or create voucher service instance"""
    global _voucher_service
    if _voucher_service is None:
        _voucher_service = VoucherService()
    return _voucher_service
