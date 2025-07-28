#!/bin/bash

echo "🚨 EMERGENCY FIX - FINDING AND FIXING SETTINGS"
echo "============================================="

# Step 1: Find where settings actually is
echo "📋 Finding settings file..."
SETTINGS_FILE=$(find app -name "settings.py" -type f 2>/dev/null | head -1)

if [ -z "$SETTINGS_FILE" ]; then
    echo "   Settings.py not found, checking for config.py..."
    SETTINGS_FILE=$(find app -name "config.py" -type f 2>/dev/null | head -1)
fi

if [ -n "$SETTINGS_FILE" ]; then
    echo "   ✅ Found settings at: $SETTINGS_FILE"
else
    echo "   ❌ No settings file found!"
fi

# Step 2: Check where settings is imported from in database.py
echo -e "\n📋 Checking database.py imports..."
head -20 app/core/database.py | grep -n "import"

# Step 3: Look for the settings object
echo -e "\n📋 Finding settings import..."
grep -n "settings" app/core/database.py | head -5

# Step 4: Apply the immediate fix
echo -e "\n🔧 Applying DATABASE_URL fix..."
sed -i '' 's/settings\.DATABASE_URL/settings.SQLALCHEMY_DATABASE_URL/g' app/core/database.py

# Step 5: If settings is in config.py, check it
if [ -f "app/core/config.py" ]; then
    echo -e "\n📋 Found app/core/config.py, checking for database URL..."
    grep -i "database" app/core/config.py | head -10
fi

# Step 6: If settings is imported differently, find it
echo -e "\n📋 Checking how settings is defined in database.py..."
grep -B5 "settings" app/core/database.py | head -10

# Step 7: Nuclear option - check if we need to create settings instance
echo -e "\n🔧 Checking if settings needs to be instantiated..."
if grep -q "from app.core.config import Settings" app/core/database.py; then
    echo "   Settings class needs to be instantiated!"
    # Add settings = Settings() after the import
    sed -i '' '/from app.core.config import Settings/a\
settings = Settings()
' app/core/database.py
fi

# Step 8: Create a minimal settings/config file if needed
if [ ! -f "app/core/config.py" ] && [ ! -f "app/core/settings.py" ]; then
    echo -e "\n📋 Creating minimal config.py..."
    cat > app/core/config.py << 'EOF'
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str = os.getenv(
        "SQLALCHEMY_DATABASE_URL", 
        "sqlite:///./factortrace.db"
    )
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
EOF
    echo "   ✅ Created config.py with settings"
fi

# Step 9: Final verification
echo -e "\n✅ Verification:"
echo "DATABASE_URL line in database.py:"
grep -n "DATABASE_URL" app/core/database.py || echo "   ✅ DATABASE_URL reference fixed!"

echo -e "\n🚀 Starting server..."
uvicorn app.main:app --reload --port 8000