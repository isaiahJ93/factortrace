from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
import jwt
import os
from app.core.config import settings
from datetime import datetime

router = APIRouter()

class VoucherVerification(BaseModel):
    token: str
    code: str

class VerificationResponse(BaseModel):
    valid: bool
    email: str = None
    company: str = None
    packageType: str = None
    expiresAt: int = None
    error: str = None

@router.post("/verify-access", response_model=VerificationResponse)
async def verify_voucher_access(verification: VoucherVerification):
    """Verify JWT token from voucher system"""
    try:
        # Get JWT secret from environment
        jwt_secret = settings.jwt_secret
        if not jwt_secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret not configured"
            )
        
        # Verify the token
        decoded = jwt.decode(verification.token, jwt_secret, algorithms=["HS256"])
        
        # Check if token matches the code
        if decoded.get('voucherCode') != verification.code:
            return VerificationResponse(valid=False, error="Code mismatch")
        
        # Check if token is expired
        valid_until = decoded.get('validUntil', 0)
        if valid_until < datetime.now().timestamp() * 1000:  # Convert to milliseconds
            return VerificationResponse(valid=False, error="Token expired")
        
        # Valid token!
        return VerificationResponse(
            valid=True,
            email=decoded.get('email'),
            company=decoded.get('company'),
            packageType=decoded.get('packageType'),
            expiresAt=valid_until
        )
        
    except jwt.ExpiredSignatureError:
        return VerificationResponse(valid=False, error="Token expired")
    except jwt.InvalidTokenError:
        return VerificationResponse(valid=False, error="Invalid token")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )
