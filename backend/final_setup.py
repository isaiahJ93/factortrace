# final_setup.py - Complete setup script
import os
import sys

print("🚀 FactorTrace Final Setup\n")

# Step 1: Install missing dependency
print("1️⃣ Installing bcrypt...")
os.system("pip install bcrypt")

# Step 2: Create clean .env
print("\n2️⃣ Creating .env file...")
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
print("✅ Created .env file")

# Step 3: Create models directory if it doesn't exist
print("\n3️⃣ Checking models directory...")
os.makedirs("app/models", exist_ok=True)

# Create __init__.py if it doesn't exist
init_file = "app/models/__init__.py"
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        f.write('# Models package\n')
    print("✅ Created models __init__.py")

# Step 4: Test database setup
print("\n4️⃣ Setting up database...")
try:
    # Import after ensuring models exist
    from app.db.base import Base, import_all_models
    from app.core.database import engine, SessionLocal
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Add admin user
    from app.models.user import User
    
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@factortrace.com").first()
        if not admin:
            admin = User(
                email="admin@factortrace.com",
                full_name="Admin User",
                is_active=True,
                is_admin=True,
                company_name="FactorTrace",
                has_emissions_access=True
            )
            admin.set_password("admin123")
            db.add(admin)
            db.commit()
            print("✅ Created admin user")
        else:
            print("✅ Admin user already exists")
    finally:
        db.close()
    
    print("\n🎉 Setup complete!\n")
    print("=" * 50)
    print("📋 QUICK START GUIDE")
    print("=" * 50)
    print("\n1️⃣ Start Redis (if not running):")
    print("   redis-server\n")
    print("2️⃣ Start the API:")
    print("   uvicorn app.main:app --reload --port 8000\n")
    print("3️⃣ View API documentation:")
    print("   http://localhost:8000/docs\n")
    print("4️⃣ Test the API:")
    print("   curl http://localhost:8000/health\n")
    print("5️⃣ Login as admin:")
    print("   Email: admin@factortrace.com")
    print("   Password: admin123\n")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Troubleshooting tips:")
    print("1. Make sure you're in the virtual environment")
    print("2. Check if all model files exist in app/models/")
    print("3. Try running: pip install -r requirements.txt")
    sys.exit(1)