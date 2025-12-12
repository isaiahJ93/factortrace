from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
import stripe
import secrets
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.core.auth import get_current_user
from app.schemas.auth_schemas import CurrentUser
from app.core.tenant import tenant_query
from app.models.voucher import Voucher
from app.models.payment import Payment

router = APIRouter()

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY

class CheckoutRequest(BaseModel):
    company_email: str
    company_name: str
    success_url: str
    cancel_url: str

class CheckoutResponse(BaseModel):
    checkout_url: str
    session_id: str

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    request: CheckoutRequest,
    db: Session = Depends(get_db)
):
    """Create a Stripe checkout session for voucher purchase"""
    
    try:
        # Create checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': settings.STRIPE_PRICE_ID,
                'quantity': 1,
            }],
            mode='payment',
            success_url=request.success_url + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.cancel_url,
            customer_email=request.company_email,
            metadata={
                'company_name': request.company_name,
                'company_email': request.company_email,
            }
        )
        
        # Create payment record
        payment = Payment(
            stripe_checkout_session_id=session.id,
            amount=session.amount_total,
            currency=session.currency,
            status='pending',
            customer_email=request.company_email,
            customer_name=request.company_name,
            metadata=str({
                'company_name': request.company_name,
                'company_email': request.company_email,
            })
        )
        db.add(payment)
        db.commit()
        
        return CheckoutResponse(
            checkout_url=session.url,
            session_id=session.id
        )
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks"""
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Update payment
        payment = db.query(Payment).filter(
            Payment.stripe_checkout_session_id == session['id']
        ).first()
        
        if payment:
            payment.status = 'succeeded'
            payment.stripe_payment_intent_id = session.get('payment_intent')
            
            # Generate voucher
            voucher_code = f"FT-{secrets.token_hex(4).upper()}"
            voucher = Voucher(
                code=voucher_code,
                payment_id=payment.id,
                company_email=session['customer_email'],
                company_name=session['metadata']['company_name'],
                valid_until=datetime.utcnow() + timedelta(days=365),
                is_used=False,
                status='VALID'
            )
            db.add(voucher)
            db.commit()
            
            # TODO: Send email with voucher
    
    return {"status": "success"}

@router.get("/")
async def list_vouchers(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    """List vouchers for the current tenant"""
    # MULTI-TENANT: Always filter by tenant_id
    vouchers = tenant_query(db, Voucher, current_user.tenant_id).all()
    return {"vouchers": vouchers}
