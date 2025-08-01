import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

try:
    # Test the connection
    balance = stripe.Balance.retrieve()
    print(f"✅ Stripe connected! Balance: {balance}")
except Exception as e:
    print(f"❌ Stripe error: {e}")
    print(f"Make sure to set STRIPE_SECRET_KEY in .env")
