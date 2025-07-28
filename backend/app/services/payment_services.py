# app/services/payment_service.py (CREATE NEW FILE)
import stripe
import logging
from typing import Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.voucher import Voucher
from app.models.payment import Payment
from app.services.email_service import EmailService
from app.core.database import get_db
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)
stripe.api_key = settings.STRIPE_SECRET_KEY

class PaymentService:
    def __init__(self):
        self.email_service = EmailService()
        self._processed_events = set()  # In production, use Redis
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def create_checkout_session(
        self, 
        company_email: str,
        company_name: str,
        success_url: str,
        cancel_url: str
    ) -> Dict:
        """Create Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': settings.STRIPE_PRICE_ID,
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                customer_email=company_email,
                metadata={
                    'company_name': company_name,
                    'product': 'emissions_voucher'
                },
                payment_intent_data={
                    'metadata': {
                        'company_name': company_name,
                        'company_email': company_email
                    }
                }
            )
            
            logger.info(f"Created checkout session {session.id} for {company_email}")
            return {"checkout_url": session.url, "session_id": session.id}
            
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {e}")
            raise
            
    async def handle_webhook(self, payload: bytes, sig_header: str, db: Session) -> Dict:
        """Handle Stripe webhook with idempotency"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            logger.error(f"Invalid payload: {e}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {e}")
            raise
            
        # Idempotency check
        if event['id'] in self._processed_events:
            logger.info(f"Duplicate event {event['id']} ignored")
            return {"status": "duplicate_ignored"}
            
        try:
            if event['type'] == 'checkout.session.completed':
                await self._handle_successful_payment(event['data']['object'], db)
            elif event['type'] == 'payment_intent.payment_failed':
                await self._handle_failed_payment(event['data']['object'], db)
                
            self._processed_events.add(event['id'])
            return {"status": "processed"}
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}", exc_info=True)
            raise
            
    async def _handle_successful_payment(self, session: Dict, db: Session):
        """Process successful payment and create voucher"""
        try:
            # Record payment
            payment = Payment(
                stripe_session_id=session['id'],
                stripe_payment_intent=session['payment_intent'],
                amount=session['amount_total'],
                currency=session['currency'],
                status='completed',
                customer_email=session['customer_email'],
                metadata=session.get('metadata', {})
            )
            db.add(payment)
            db.flush()
            
            # Generate voucher
            voucher = Voucher(
                payment_id=payment.id,
                code=self._generate_voucher_code(),
                company_email=session['customer_email'],
                company_name=session['metadata'].get('company_name', ''),
                valid_until=datetime.utcnow().replace(year=datetime.utcnow().year + 1),
                is_used=False
            )
            db.add(voucher)
            db.commit()
            
            # Queue email sending
            await self.email_service.send_voucher_email(
                to_email=voucher.company_email,
                company_name=voucher.company_name,
                voucher_code=voucher.code,
                valid_until=voucher.valid_until
            )
            
            logger.info(f"Successfully processed payment for {session['customer_email']}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing payment: {e}", exc_info=True)
            # In production, add to dead letter queue for manual processing
            raise
            
    def _generate_voucher_code(self) -> str:
        """Generate unique voucher code"""
        import secrets
        return f"FT-{datetime.utcnow().year}-{secrets.token_urlsafe(8).upper()}"