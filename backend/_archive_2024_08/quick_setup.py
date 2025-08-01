# quick_setup.py - Quick setup for development
import os
import sys

print("🚀 FactorTrace Quick Setup\n")

# Step 1: Ensure we have a clean .env file
print("1️⃣ Creating clean .env file...")

env_content = """# FactorTrace Configuration
PROJECT_NAME=FactorTrace
VERSION=0.1.0
ENVIRONMENT=development
API_V1_STR=/api/v1
DEBUG=true

# Database - SQLite for development
DATABASE_URL=sqlite:///./factortrace.db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_TIMEOUT=30

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=dev-secret-key-for-development-only
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Stripe (Update with your test keys)
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_PRICE_ID=

# Email
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=
EMAIL_FROM=noreply@factortrace.com
EMAIL_FROM_NAME=FactorTrace

# AWS (Optional)
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=eu-west-1

# Monitoring
SENTRY_DSN=

# CORS
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]
ALLOWED_HOSTS=["localhost","127.0.0.1"]

# Rate Limiting  
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Frontend
FRONTEND_URL=http://localhost:3000

# XBRL
XSD_BASE_PATH=./schemas/xsd
"""

with open('.env', 'w') as f:
    f.write(env_content)
print("✅ Created .env file\n")

# Step 2: Test imports and create database
print("2️⃣ Setting up database...")

try:
    # Import models first to ensure they're available
    print("   Loading models...")
    from app.db.base import Base  # This should import all models
    from app.core.database import engine, SessionLocal
    
    # Create tables
    print("   Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created\n")
    
    # Step 3: Add initial data
    print("3️⃣ Adding initial data...")
    
    from app.models.user import User
    
    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.email == "admin@factortrace.com").first()
        if not admin:
            admin = User(
                email="admin@factortrace.com",
                full_name="Admin User",
                is_active=True,
                is_admin=True,
                company_name="FactorTrace"
            )
            # Set password
            admin.set_password("admin123")
            db.add(admin)
            db.commit()
            print("✅ Created admin user\n")
        else:
            print("✅ Admin user already exists\n")
            
    finally:
        db.close()
    
    print("🎉 Setup complete!\n")
    print("📝 Next steps:\n")
    print("1. Start Redis (if not running):")
    print("   redis-server\n")
    print("2. Start the API:")
    print("   uvicorn app.main:app --reload --port 8000\n")
    print("3. View API docs:")
    print("   http://localhost:8000/docs\n")
    print("4. Login credentials:")
    print("   Email: admin@factortrace.com")
    print("   Password: admin123\n")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\nMake sure you have all dependencies installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)