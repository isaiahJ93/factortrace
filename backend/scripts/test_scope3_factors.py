# backend/scripts/test_scope3_factors.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.emission_factor import EmissionFactor

engine = create_engine('sqlite:///factortrace.db')
Session = sessionmaker(bind=engine)
db = Session()

# Check Scope 3 factors
scope3_factors = db.query(EmissionFactor).filter(
    EmissionFactor.scope == 3
).all()

print(f"Total Scope 3 factors: {len(scope3_factors)}")

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for factor in scope3_factors:
    by_category[factor.scope3_category].append(factor)

print("\nScope 3 Categories:")
for category, factors in by_category.items():
    print(f"  {category}: {len(factors)} factors")
    print(f"    Methods: {set(f.calculation_method for f in factors)}")
    print(f"    Avg uncertainty: {sum(f.uncertainty_percentage for f in factors)/len(factors):.1f}%")