from fastapi import APIRouter, Request, Response, Depends
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

def generate_voucher_code() -> str:
    """Generate a unique voucher code"""
    import secrets
    import string
    part1 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    part2 = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(3))
    return f"FT-{part1}-{part2}"

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Process Stripe webhook events"""
    payload = await request.body()
    
    try:
        # Parse the event (in production, verify signature first)
        event = json.loads(payload)
        
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
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
            
            # Create vouchers based on amount
            num_vouchers = 20 if session['amount_total'] == 1000000 else 1  # €10,000 = 20 vouchers
            
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
                vouchers_created.append({'code': voucher.code})
            
            db.commit()
            
            # Send email
            email_service.send_voucher_email(
                to_email=session['customer_details']['email'],
                company_name=session['metadata'].get('company_name', 'Customer'),
                vouchers=vouchers_created,
                total_amount=session['amount_total'] / 100,
                package_name='20 Compliance Vouchers Bundle'
            )
            
            logger.info(f"Processed payment {payment.id}, created {num_vouchers} vouchers")
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
    
    return Response(status_code=200)

@router.get("/test")
async def test():
    return {"status": "webhook endpoint ready"}
