from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session
import stripe
import json
import logging
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.database import get_db
from app.models.payment import Payment
from app.models.voucher import Voucher
from app.services.email import email_service

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

def generate_voucher_code() -> str:
    """Generate a unique voucher code"""
    import secrets
    import string
    # Format: FT-XXXXX-XXX
    part1 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    part2 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(3))
    return f"FT-{part1}-{part2}"

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events"""
    
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid payload")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Handle checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        logger.info(f"Processing successful payment for session {session['id']}")
        
        # Create payment record
        payment = Payment(
            stripe_checkout_session_id=session['id'],
            stripe_payment_intent=session.get('payment_intent'),
            amount=session['amount_total'],
            currency=session['currency'],
            status='completed',
            customer_email=session['customer_details']['email'],
            customer_name=session['metadata'].get('company_name', ''),
            metadata=json.dumps(session['metadata'])
        )
        db.add(payment)
        db.commit()
        
        # Determine number of vouchers based on package type
        package_type = session['metadata'].get('package_type', 'single')
        voucher_counts = {
            'single': 1,
            'bundle-8': 8,
            'bundle-20': 20,
            'bundle-50': 50
        }
        num_vouchers = voucher_counts.get(package_type, 1)
        
        # Create vouchers
        vouchers_created = []
        for i in range(num_vouchers):
            voucher = Voucher(
                code=generate_voucher_code(),
                payment_id=payment.id,
                company_email=session['customer_details']['email'],
                company_name=session['metadata'].get('company_name', ''),
                valid_until=datetime.utcnow() + timedelta(days=365),
                is_used=False,
                status='active'
            )
            db.add(voucher)
            vouchers_created.append({
                'code': voucher.code,
                'valid_until': voucher.valid_until.isoformat()
            })
        
        db.commit()
        
        # Send email with voucher codes
        package_names = {
            'single': 'Single Compliance Voucher',
            'bundle-8': '8 Compliance Vouchers Bundle',
            'bundle-20': '20 Compliance Vouchers Bundle',
            'bundle-50': '50 Compliance Vouchers Bundle'
        }
        
        email_sent = email_service.send_voucher_email(
            to_email=session['customer_details']['email'],
            company_name=session['metadata'].get('company_name', 'Customer'),
            vouchers=vouchers_created,
            total_amount=session['amount_total'] / 100,  # Convert cents to euros
            package_name=package_names.get(package_type, 'Compliance Vouchers')
        )
        
        logger.info(f"Created {num_vouchers} vouchers for payment {payment.id}")
        logger.info(f"Email sent: {email_sent}")
    
    return {"status": "success"}

@router.get("/test")
async def test_webhook():
    """Test endpoint"""
    return {"status": "Webhook endpoint is working"}
