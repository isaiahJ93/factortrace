#!/usr/bin/env python3
"""Debug what's actually in settings"""

try:
    from app.core.config import settings
    
    print("✅ Settings loaded successfully!")
    print("\nAll attributes containing 'database' or 'url':")
    for attr in sorted(dir(settings)):
        if not attr.startswith('_') and ('database' in attr.lower() or 'url' in attr.lower()):
            try:
                value = getattr(settings, attr)
                print(f"  - {attr}: {type(value).__name__}")
                if 'database_url' in attr:
                    print(f"    Value: {value}")
            except:
                pass
    
    print("\n🎯 The correct attribute is: database_url")
    print("🎯 Type is PostgresDsn, so use: str(settings.database_url)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nTrying to set environment variable...")
    import os
    os.environ['DATABASE_URL'] = 'postgresql://user:pass@localhost/db'
    
    try:
        from app.core.config import settings
        print("✅ Settings loaded with default DATABASE_URL")
    except Exception as e2:
        print(f"❌ Still failed: {e2}")