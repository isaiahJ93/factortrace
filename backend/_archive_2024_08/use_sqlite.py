# use_sqlite.py - Switch to SQLite for easier development
import os

print("🔄 Switching to SQLite database...")

# Update .env to use SQLite
env_content = """# FactorTrace Configuration
PROJECT_NAME=FactorTrace
VERSION=0.1.0
ENVIRONMENT=development
API_V1_STR=/api/v1
DEBUG=true

# Database - Using SQLite for development (no setup required!)
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

# Backup current .env
if os.path.exists('.env'):
    os.rename('.env', '.env.postgresql.backup')
    print("✅ Backed up current .env to .env.postgresql.backup")

# Write new .env
with open('.env', 'w') as f:
    f.write(env_content)

print("✅ Created new .env with SQLite configuration")

# Delete old SQLite database if exists
if os.path.exists('factortrace.db'):
    os.remove('factortrace.db')
    print("✅ Removed old SQLite database")

print("\n✅ Switched to SQLite!")
print("\nNow run:")
print("  python final_setup.py")
print("\nThis will create a fresh SQLite database with all tables.")