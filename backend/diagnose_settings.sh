#!/bin/bash

echo "🔍 SETTINGS DIAGNOSTIC"
echo "====================="

# Check the actual error line
echo "📋 The error line (database.py:15):"
sed -n '15p' app/core/database.py

# Check settings class definition
echo -e "\n📋 Settings class in settings.py:"
grep -A 20 "class Settings" app/core/settings.py | head -25

# Look for any database URL definitions
echo -e "\n📋 All database-related settings:"
grep -n -E "(database|DATABASE|db_|DB_)" app/core/settings.py

# Try to import and check
echo -e "\n📋 Python diagnostic:"
python3 << 'EOF'
import sys
print("Python path check...")

try:
    from app.core.settings import Settings
    print("✅ Settings class imported")
    
    # Try to instantiate
    try:
        settings = Settings()
        print("✅ Settings instance created")
        
        # List all attributes
        print("\nAll settings attributes:")
        for attr in sorted(dir(settings)):
            if not attr.startswith('_'):
                try:
                    val = getattr(settings, attr)
                    if 'database' in attr.lower() or 'url' in attr.lower() or 'db' in attr.lower():
                        print(f"  🔹 {attr} = {repr(val)[:50]}...")
                except:
                    pass
                    
    except Exception as e:
        print(f"❌ Error creating settings instance: {e}")
        print("\nTrying to load from environment...")
        
        import os
        os.environ.setdefault("SQLALCHEMY_DATABASE_URL", "postgresql://user:pass@localhost/dbname")
        
        try:
            settings = Settings()
            print("✅ Settings created with default env vars")
        except Exception as e2:
            print(f"❌ Still failed: {e2}")
            
except ImportError as e:
    print(f"❌ Import error: {e}")
    
    # Try alternative import
    try:
        from app.core import settings
        print("✅ Alternative import worked")
        print(f"Settings type: {type(settings)}")
    except:
        print("❌ Alternative import also failed")
EOF

echo -e "\n🔧 Suggested fix:"
echo "sed -i '' 's/settings.DATABASE_URL/settings.SQLALCHEMY_DATABASE_URL/g' app/core/database.py"