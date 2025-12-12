# app/services/stripe_checkout.py
"""
Stripe Checkout Service for Supplier Self-Serve Flow.

Handles:
- create_checkout_session(email, product) → Stripe URL
- handle_checkout_complete(session_id) → creates voucher, starts wizard
- Webhook handling for checkout.session.completed

This enables the €500 magic moment: Pay → Complete Wizard → Get Report.
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.voucher import Voucher, VoucherStatus
from app.models.payment import Payment
from app.models.tenant import Tenant
from app.models.wizard import ComplianceWizardSession, WizardStatus

logger = logging.getLogger(__name__)

# Configure Stripe
stripe.api_key = settings.stripe_secret_key


# =============================================================================
# PRODUCT CONFIGURATION
# =============================================================================

PRODUCTS = {
    "csrd_report": {
        "name": "CSRD Compliance Report",
        "description": "Complete Scope 3 emissions report with CSRD/ESRS alignment",
        "price_cents": 50000,  # €500
        "currency": "eur",
    },
    "csrd_basic": {
        "name": "CSRD Basic Report",
        "description": "Basic emissions calculation and summary report",
        "price_cents": 25000,  # €250
        "currency": "eur",
    },
}


# =============================================================================
# CHECKOUT SESSION CREATION
# =============================================================================

def create_checkout_session(
    db: Session,
    *,
    email: str,
    company_name: str,
    product: str = "csrd_report",
    success_url: str,
    cancel_url: str,
) -> Tuple[str, str]:
    """
    Create a Stripe checkout session for supplier purchase.

    Args:
        db: Database session
        email: Supplier email address
        company_name: Supplier company name
        product: Product type (csrd_report, csrd_basic)
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled

    Returns:
        Tuple of (checkout_url, session_id)

    Raises:
        ValueError: If product not found or Stripe not configured
        stripe.error.StripeError: If Stripe API fails
    """
    if not settings.stripe_secret_key:
        raise ValueError("Stripe is not configured")

    product_config = PRODUCTS.get(product)
    if not product_config:
        raise ValueError(f"Unknown product: {product}")

    try:
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price_data": {
                        "currency": product_config["currency"],
                        "unit_amount": product_config["price_cents"],
                        "product_data": {
                            "name": product_config["name"],
                            "description": product_config["description"],
                        },
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            customer_email=email,
            metadata={
                "product": product,
                "company_name": company_name,
                "company_email": email,
            },
            payment_intent_data={
                "metadata": {
                    "product": product,
                    "company_name": company_name,
                    "company_email": email,
                }
            },
        )

        # Create pending payment record
        payment = Payment(
            stripe_checkout_session_id=checkout_session.id,
            amount=product_config["price_cents"],
            currency=product_config["currency"],
            status="pending",
            customer_email=email,
            customer_name=company_name,
            metadata=str({
                "product": product,
                "company_name": company_name,
            }),
        )
        db.add(payment)
        db.commit()

        logger.info(
            f"Created checkout session {checkout_session.id} for {email} "
            f"(product: {product})"
        )

        return checkout_session.url, checkout_session.id

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error creating checkout: {e}")
        raise


def get_checkout_session_status(session_id: str) -> Dict:
    """
    Get status of a checkout session.

    Args:
        session_id: Stripe checkout session ID

    Returns:
        Dict with session status info
    """
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            "id": session.id,
            "status": session.status,
            "payment_status": session.payment_status,
            "customer_email": session.customer_email,
        }
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving session {session_id}: {e}")
        raise


# =============================================================================
# WEBHOOK HANDLING
# =============================================================================

def handle_checkout_complete(
    db: Session,
    *,
    stripe_session_id: str,
) -> Tuple[Optional[Voucher], Optional[ComplianceWizardSession]]:
    """
    Handle successful checkout completion.

    Called when checkout.session.completed webhook is received.
    Creates voucher and starts wizard session.

    Args:
        db: Database session
        stripe_session_id: Stripe checkout session ID

    Returns:
        Tuple of (voucher, wizard_session) or (None, None) if already processed
    """
    # Check if already processed (idempotency)
    existing_payment = (
        db.query(Payment)
        .filter(
            Payment.stripe_checkout_session_id == stripe_session_id,
            Payment.status == "succeeded",
        )
        .first()
    )
    if existing_payment:
        logger.info(f"Checkout {stripe_session_id} already processed")
        return None, None

    # Get session details from Stripe
    try:
        session = stripe.checkout.Session.retrieve(stripe_session_id)
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving session {stripe_session_id}: {e}")
        raise

    # Update payment record
    payment = (
        db.query(Payment)
        .filter(Payment.stripe_checkout_session_id == stripe_session_id)
        .first()
    )

    if not payment:
        # Create payment if webhook arrived before checkout endpoint returned
        payment = Payment(
            stripe_checkout_session_id=stripe_session_id,
            amount=session.amount_total,
            currency=session.currency,
            status="pending",
            customer_email=session.customer_email,
            customer_name=session.metadata.get("company_name", ""),
            metadata=str(session.metadata),
        )
        db.add(payment)

    payment.status = "succeeded"
    payment.stripe_payment_intent_id = session.payment_intent

    # Get or create tenant for this supplier
    tenant = _get_or_create_supplier_tenant(
        db,
        email=session.customer_email,
        company_name=session.metadata.get("company_name", ""),
    )

    # Generate voucher
    voucher_code = _generate_voucher_code()
    voucher = Voucher(
        tenant_id=tenant.id,
        code=voucher_code,
        payment_id=payment.id,
        company_email=session.customer_email,
        company_name=session.metadata.get("company_name", ""),
        valid_until=datetime.utcnow() + timedelta(days=365),
        is_used=True,  # Mark used immediately since we auto-start wizard
        used_at=datetime.utcnow(),
        status=VoucherStatus.USED,
    )
    db.add(voucher)
    db.flush()  # Get voucher ID

    # Auto-start wizard session
    wizard_session = ComplianceWizardSession(
        tenant_id=tenant.id,
        voucher_id=voucher.id,
        status=WizardStatus.DRAFT,
        current_step="company_profile",
        company_profile={
            "name": session.metadata.get("company_name", ""),
            "contact_email": session.customer_email,
        },
    )
    db.add(wizard_session)
    db.commit()
    db.refresh(voucher)
    db.refresh(wizard_session)

    logger.info(
        f"Checkout complete: created voucher {voucher.code} and "
        f"wizard session {wizard_session.id} for {session.customer_email}"
    )

    return voucher, wizard_session


def verify_webhook_signature(
    payload: bytes,
    sig_header: str,
) -> Dict:
    """
    Verify Stripe webhook signature and return event.

    Args:
        payload: Raw webhook payload
        sig_header: Stripe-Signature header value

    Returns:
        Parsed webhook event

    Raises:
        ValueError: If signature verification fails
    """
    if not settings.stripe_webhook_secret:
        raise ValueError("Stripe webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.stripe_webhook_secret,
        )
        return event
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {e}")
        raise
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        raise ValueError(f"Invalid signature: {e}")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _generate_voucher_code() -> str:
    """Generate unique voucher code."""
    return f"FT-{datetime.utcnow().year}-{secrets.token_urlsafe(8).upper()}"


def _get_or_create_supplier_tenant(
    db: Session,
    *,
    email: str,
    company_name: str,
) -> Tenant:
    """
    Get or create a tenant for a supplier.

    For self-serve suppliers, we create a tenant per company email domain.
    """
    # Try to find existing tenant by email
    # Simple approach: use email domain or create per-email tenant
    import uuid

    # Check if tenant exists for this email
    existing_voucher = (
        db.query(Voucher)
        .filter(Voucher.company_email == email)
        .first()
    )
    if existing_voucher:
        return existing_voucher.tenant

    # Create new tenant for this supplier
    tenant_id = str(uuid.uuid4())
    tenant = Tenant(
        id=tenant_id,
        name=company_name or f"Supplier: {email}",
        slug=email.split("@")[0][:50],  # Use email prefix as slug
        is_active=True,
    )
    db.add(tenant)
    db.flush()

    logger.info(f"Created new supplier tenant {tenant_id} for {email}")
    return tenant


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "create_checkout_session",
    "get_checkout_session_status",
    "handle_checkout_complete",
    "verify_webhook_signature",
    "PRODUCTS",
]
