# setup_sqlite.py - Simple SQLite database setup
import os
import sys

# First, let's update the .env to use SQLite
print("🔧 Configuring for SQLite development...")

env_content = """# API Configuration
PROJECT_NAME=FactorTrace
VERSION=0.1.0
ENVIRONMENT=development
API_V1_STR=/api/v1
DEBUG=True

# Database - Using SQLite for development
DATABASE_URL=sqlite:///./factortrace.db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# Redis (already running locally)
REDIS_URL=redis://localhost:6379/0

# Security (generated secret key)
SECRET_KEY=dev-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Stripe (Get from https://dashboard.stripe.com/test/apikeys)
STRIPE_SECRET_KEY=sk_test_your_test_key_here
STRIPE_PUBLISHABLE_KEY=pk_test_your_test_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here
STRIPE_PRICE_ID=price_your_price_id_here

# Email Provider (SendGrid recommended over AWS SES for simplicity)
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.your_sendgrid_api_key_here
EMAIL_FROM=noreply@factortrace.com
EMAIL_FROM_NAME=FactorTrace

# AWS (optional - only if using SES)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-west-1

# Monitoring (optional)
SENTRY_DSN=

# CORS Settings
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","http://127.0.0.1:3000"]
ALLOWED_HOSTS=["localhost","127.0.0.1","0.0.0.0"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Frontend URL (for emails)
FRONTEND_URL=http://localhost:3000

# XSD/XBRL Configuration
XSD_BASE_PATH=./schemas/xsd
"""

# Write the .env file
with open('.env', 'w') as f:
    f.write(env_content)

print("✅ Created .env with SQLite configuration")

# Now set up the database
print("\n📦 Setting up SQLite database...")

try:
    from app.core.database import engine, Base
    from app.models import (
        user, voucher, payment, emission, emission_factor,
        evidence_document, data_quality
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created!")
    
    # Seed initial data
    from app.core.database import SessionLocal
    from app.models.user import User
    from app.models.emission_factor import EmissionFactor
    
    db = SessionLocal()
    
    # Check if admin exists
    admin = db.query(User).filter(User.email == "admin@factortrace.com").first()
    if not admin:
        # Create admin user
        admin = User(
            email="admin@factortrace.com",
            full_name="Admin User",
            is_active=True,
            is_admin=True,
            company_name="FactorTrace",
            has_emissions_access=True
        )
        admin.set_password("admin123")  # Change in production!
        db.add(admin)
        db.commit()
        print("✅ Created admin user: admin@factortrace.com / admin123")
    
    # Add basic emission factors if none exist
    if db.query(EmissionFactor).count() == 0:
        factors = [
            {
                "name": "Electricity - Grid Average",
                "category": "energy",
                "subcategory": "electricity",
                "unit": "kWh",
                "co2e_per_unit": 0.4,
                "source": "EPA",
                "scope": "scope2"
            },
            {
                "name": "Natural Gas",
                "category": "energy", 
                "subcategory": "natural_gas",
                "unit": "m3",
                "co2e_per_unit": 2.02,
                "source": "EPA",
                "scope": "scope1"
            },
            {
                "name": "Gasoline",
                "category": "transport",
                "subcategory": "fuel",
                "unit": "liter",
                "co2e_per_unit": 2.31,
                "source": "EPA",
                "scope": "scope1"
            }
        ]
        
        for factor_data in factors:
            factor = EmissionFactor(**factor_data)
            db.add(factor)
        
        db.commit()
        print("✅ Added sample emission factors")
    
    db.close()
    
    print("\n✅ Database setup complete!")
    print("\n📝 Next steps:")
    print("1. Start the API server:")
    print("   uvicorn app.main:app --reload --port 8000")
    print("\n2. Test the API:")
    print("   curl http://localhost:8000/health")
    print("\n3. View API docs:")
    print("   http://localhost:8000/docs")
    print("\n4. Login as admin:")
    print("   Email: admin@factortrace.com")
    print("   Password: admin123")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you're in the virtual environment")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Check that all model files exist in app/models/")
    sys.exit(1)