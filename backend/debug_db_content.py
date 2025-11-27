import sys
import os

# Ensure we can import app modules
sys.path.append(os.getcwd())

from app.core.database import SessionLocal
# Import the base to trigger model registration
from app.db.base import import_all_models
from app.models.emission_factor import EmissionFactor

# CRITICAL: Register all models first
import_all_models()

db = SessionLocal()
print(f"\n{'ID':<4} {'SCOPE':<10} {'CATEGORY':<25} {'ACTIVITY':<20} {'COUNTRY':<8} {'FACTOR':<8}")
print("-" * 90)

# Query all factors
factors = db.query(EmissionFactor).all()
for f in factors:
    # Handle None values safely
    scope = str(f.scope or "")[:10]
    cat = str(f.category or "")[:25]
    act = str(f.activity_type or "")[:20]
    cntry = str(f.country_code or "")[:8]
    fact = str(f.factor)
    
    print(f"{f.id:<4} {scope:<10} {cat:<25} {act:<20} {cntry:<8} {fact:<8}")

db.close()
