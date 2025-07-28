from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class CheckoutRequest(BaseModel):
    company_email: str
    company_name: str
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(request: CheckoutRequest):
    """Create a Stripe checkout session"""
    # For now, return a mock response
    return CheckoutResponse(
        checkout_url=f"https://checkout.stripe.com/test_session",
        session_id="cs_test_123456"
    )

@router.get("/")
async def list_vouchers():
    """List all vouchers"""
    return {"vouchers": []}
