from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
print(f"ACTUAL DATABASE URL: {settings.database_url}")

print(f"DEBUG: Creating engine with URL: {settings.database_url}")
engine = create_engine(
    str(settings.database_url),
    connect_args={"check_same_thread": False} if str(settings.database_url).startswith("sqlite") else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()