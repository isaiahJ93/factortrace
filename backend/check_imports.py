#!/usr/bin/env python3
import sys
sys.path.append('.')

print("Checking imports...")

try:
    from app.models.user import User
    print("✅ User model imported successfully")
except Exception as e:
    print(f"❌ User model import failed: {e}")

try:
    from app.models.emission import Emission
    print("✅ Emission model imported successfully")
except Exception as e:
    print(f"❌ Emission model import failed: {e}")

try:
    from app.models.emission_factor import EmissionFactor
    print("✅ EmissionFactor model imported successfully")
except Exception as e:
    print(f"❌ EmissionFactor model import failed: {e}")

try:
    from app.api.v1.endpoints import emissions
    print("✅ Emissions endpoint imported successfully")
except Exception as e:
    print(f"❌ Emissions endpoint import failed: {e}")

try:
    from app.api.v1.endpoints import emission_factors
    print("✅ EmissionFactors endpoint imported successfully")
except Exception as e:
    print(f"❌ EmissionFactors endpoint import failed: {e}")

print("\nAll checks complete!")
