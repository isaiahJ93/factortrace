from app.core.config import settings
print(f"DATABASE_URL from settings: {settings.DATABASE_URL}")
print(f"Database type: {'PostgreSQL' if 'postgresql' in settings.DATABASE_URL else 'SQLite' if 'sqlite' in settings.DATABASE_URL else 'Unknown'}")
