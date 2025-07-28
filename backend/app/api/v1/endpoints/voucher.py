from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe
import secrets
from typing import Optional

from app.core.config import settings
from app.core.database import get_db

router = APIRouter()

# Configure Stripe
stripe.api_key = settings.stripe_secret_key

# Your real Stripe price IDs
PRICE_IDS = {
    'single': 'price_1Rkh4iDuhtIL48LYDzQ4naW7',      # €950
    'bundle-8': 'price_1Rkh5JDuhtIL48LYrVFkNMLN',    # €5,000
    'bundle-20': 'price_1Rkh6BDuhtIL48LYZFerFW52',   # €10,000
    'bundle-50': 'price_1Rkh6iDuhtIL48LYC3stXrV0'    # €15,000
}

class CheckoutRequest(BaseModel):
    company_email: str
    company_name: str
    success_url: str
    cancel_url: str
    package_type: Optional[str] = 'single'

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for voucher purchase"""
    
    # Get the price ID for the selected package
    price_id = PRICE_IDS.get(request.package_type, PRICE_IDS['single'])
    
    print(f"Creating checkout for package: {request.package_type}, price_id: {price_id}")
    # Check if Stripe is properly configured
    if not stripe.api_key or not stripe.api_key.startswith('sk_test_'):
        return CheckoutResponse(
            checkout_url="https://checkout.stripe.com/test_session",
            session_id="cs_test_mock_" + secrets.token_hex(8)
        )
    
    try:
        # Create real Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url,
            metadata={
                'company_name': request.company_name,
                'company_email': request.company_email,
                'package_type': request.package_type,
            }
        )
        
        print(f"Stripe session created: {session.id}")
        
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.InvalidRequestError as e:
        print(f"Stripe error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        print(f"General error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "status": "Voucher API is working", 
        "stripe_configured": bool(stripe.api_key),
        "price_ids": list(PRICE_IDS.keys()),
        "key_starts_with": stripe.api_key[:15] if stripe.api_key else "Not set"
    }

@router.get("/")
async def list_vouchers():
    """List vouchers endpoint"""
    return {"vouchers": [], "message": "Voucher endpoint is working"}
