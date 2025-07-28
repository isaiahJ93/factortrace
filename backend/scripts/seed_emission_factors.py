# backend/scripts/seed_emission_factors.py
"""
Seed real emission factors based on EPA, DEFRA, and GHG Protocol standards
Run this to populate your emission_factors table with real data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.emission_factor import EmissionFactor
from datetime import datetime

# Real emission factors (kg CO2e per unit)
# Sources: EPA (2024), DEFRA (2024), GHG Protocol
EMISSION_FACTORS = {
    # SCOPE 1 - Direct Emissions
    "scope_1": {
        "stationary_combustion": {
            "natural_gas": {"factor": 0.185, "unit": "kWh", "source": "EPA 2024"},
            "propane": {"factor": 1.51, "unit": "liter", "source": "EPA 2024"},
            "diesel": {"factor": 2.68, "unit": "liter", "source": "DEFRA 2024"},
            "gasoline": {"factor": 2.31, "unit": "liter", "source": "EPA 2024"},
            "coal_bituminous": {"factor": 2.86, "unit": "kg", "source": "IPCC 2024"},
            "fuel_oil": {"factor": 3.17, "unit": "liter", "source": "EPA 2024"},
        },
        "mobile_combustion": {
            "passenger_vehicle_gasoline": {"factor": 2.31, "unit": "liter", "source": "EPA 2024"},
            "passenger_vehicle_diesel": {"factor": 2.68, "unit": "liter", "source": "EPA 2024"},
            "light_duty_truck": {"factor": 2.65, "unit": "liter", "source": "EPA 2024"},
            "heavy_duty_truck": {"factor": 2.68, "unit": "liter", "source": "EPA 2024"},
            "bus_diesel": {"factor": 2.68, "unit": "liter", "source": "DEFRA 2024"},
            "motorcycle": {"factor": 2.31, "unit": "liter", "source": "EPA 2024"},
            # Alternative: per km factors
            "car_small_petrol": {"factor": 0.14, "unit": "km", "source": "DEFRA 2024"},
            "car_medium_petrol": {"factor": 0.18, "unit": "km", "source": "DEFRA 2024"},
            "car_large_petrol": {"factor": 0.28, "unit": "km", "source": "DEFRA 2024"},
            "car_small_diesel": {"factor": 0.13, "unit": "km", "source": "DEFRA 2024"},
            "car_medium_diesel": {"factor": 0.16, "unit": "km", "source": "DEFRA 2024"},
            "car_large_diesel": {"factor": 0.21, "unit": "km", "source": "DEFRA 2024"},
            "car_electric": {"factor": 0.053, "unit": "km", "source": "DEFRA 2024"},  # Based on avg grid
            "car_hybrid": {"factor": 0.11, "unit": "km", "source": "DEFRA 2024"},
        },
        "refrigerants": {
            "r134a": {"factor": 1430, "unit": "kg", "source": "IPCC AR5"},
            "r404a": {"factor": 3920, "unit": "kg", "source": "IPCC AR5"},
            "r410a": {"factor": 2088, "unit": "kg", "source": "IPCC AR5"},
            "r22": {"factor": 1810, "unit": "kg", "source": "IPCC AR5"},
            "r32": {"factor": 675, "unit": "kg", "source": "IPCC AR5"},
        },
    },
    
    # SCOPE 2 - Indirect Emissions (Electricity)
    "scope_2": {
        "electricity": {
            # Grid averages by country (2024 data)
            "grid_us_average": {"factor": 0.385, "unit": "kWh", "source": "EPA eGRID 2024"},
            "grid_uk": {"factor": 0.233, "unit": "kWh", "source": "DEFRA 2024"},
            "grid_eu_average": {"factor": 0.276, "unit": "kWh", "source": "EEA 2024"},
            "grid_china": {"factor": 0.581, "unit": "kWh", "source": "IEA 2024"},
            "grid_india": {"factor": 0.912, "unit": "kWh", "source": "CEA 2024"},
            "grid_brazil": {"factor": 0.074, "unit": "kWh", "source": "IEA 2024"},  # Hydro heavy
            "grid_germany": {"factor": 0.366, "unit": "kWh", "source": "UBA 2024"},
            "grid_france": {"factor": 0.056, "unit": "kWh", "source": "ADEME 2024"},  # Nuclear heavy
            "grid_japan": {"factor": 0.441, "unit": "kWh", "source": "METI 2024"},
            "grid_canada": {"factor": 0.119, "unit": "kWh", "source": "NIR 2024"},
            "grid_australia": {"factor": 0.656, "unit": "kWh", "source": "DCCEEW 2024"},
            # US State specific
            "grid_california": {"factor": 0.203, "unit": "kWh", "source": "CARB 2024"},
            "grid_texas": {"factor": 0.397, "unit": "kWh", "source": "ERCOT 2024"},
            "grid_new_york": {"factor": 0.289, "unit": "kWh", "source": "NYSERDA 2024"},
            # Renewable sources (lifecycle emissions)
            "renewable_solar": {"factor": 0.041, "unit": "kWh", "source": "IPCC 2024"},
            "renewable_wind": {"factor": 0.011, "unit": "kWh", "source": "IPCC 2024"},
            "renewable_hydro": {"factor": 0.024, "unit": "kWh", "source": "IPCC 2024"},
        },
        "heating_cooling": {
            "district_heating": {"factor": 0.215, "unit": "kWh", "source": "DEFRA 2024"},
            "district_cooling": {"factor": 0.195, "unit": "kWh", "source": "EPA 2024"},
            "steam": {"factor": 0.069, "unit": "kg", "source": "EPA 2024"},
        },
    },
    
    # SCOPE 3 - Value Chain Emissions
    "scope_3": {
        "business_travel": {
            "flight_domestic": {"factor": 0.246, "unit": "km", "source": "DEFRA 2024"},
            "flight_short_haul": {"factor": 0.151, "unit": "km", "source": "DEFRA 2024"},
            "flight_long_haul": {"factor": 0.147, "unit": "km", "source": "DEFRA 2024"},
            "flight_international_average": {"factor": 0.183, "unit": "km", "source": "DEFRA 2024"},
            "rail": {"factor": 0.037, "unit": "km", "source": "DEFRA 2024"},
            "bus": {"factor": 0.097, "unit": "km", "source": "DEFRA 2024"},
            "taxi": {"factor": 0.208, "unit": "km", "source": "DEFRA 2024"},
            "hotel_stay": {"factor": 10.3, "unit": "night", "source": "Cornell Hotel School 2024"},
        },
        "employee_commuting": {
            "car_average": {"factor": 0.171, "unit": "km", "source": "EPA 2024"},
            "bus": {"factor": 0.089, "unit": "km", "source": "DEFRA 2024"},
            "train": {"factor": 0.037, "unit": "km", "source": "DEFRA 2024"},
            "subway": {"factor": 0.028, "unit": "km", "source": "DEFRA 2024"},
            "walking": {"factor": 0, "unit": "km", "source": "Zero emissions"},
            "cycling": {"factor": 0, "unit": "km", "source": "Zero emissions"},
            "motorcycle": {"factor": 0.108, "unit": "km", "source": "DEFRA 2024"},
            "remote_work": {"factor": 0.14, "unit": "day", "source": "Microsoft Study 2024"},  # Home energy use
        },
        "purchased_goods": {
            "paper": {"factor": 0.919, "unit": "kg", "source": "EPA 2024"},
            "plastic": {"factor": 1.89, "unit": "kg", "source": "EPA 2024"},
            "glass": {"factor": 0.503, "unit": "kg", "source": "EPA 2024"},
            "aluminum": {"factor": 11.17, "unit": "kg", "source": "IAI 2024"},
            "steel": {"factor": 2.21, "unit": "kg", "source": "WSA 2024"},
            "concrete": {"factor": 0.107, "unit": "kg", "source": "GCCA 2024"},
            "laptop": {"factor": 331, "unit": "unit", "source": "Dell EPD 2024"},
            "monitor": {"factor": 485, "unit": "unit", "source": "HP EPD 2024"},
            "smartphone": {"factor": 72, "unit": "unit", "source": "Apple EPD 2024"},
            "office_chair": {"factor": 72, "unit": "unit", "source": "Herman Miller 2024"},
        },
        "waste": {
            "landfill_mixed": {"factor": 0.467, "unit": "kg", "source": "EPA WARM 2024"},
            "recycling_mixed": {"factor": -0.821, "unit": "kg", "source": "EPA WARM 2024"},  # Negative = avoided
            "composting_organic": {"factor": -0.183, "unit": "kg", "source": "EPA WARM 2024"},
            "incineration": {"factor": 0.932, "unit": "kg", "source": "DEFRA 2024"},
            "wastewater_treatment": {"factor": 0.272, "unit": "m3", "source": "IPCC 2024"},
        },
        "transportation_distribution": {
            "road_freight": {"factor": 0.089, "unit": "tonne.km", "source": "DEFRA 2024"},
            "rail_freight": {"factor": 0.028, "unit": "tonne.km", "source": "EPA 2024"},
            "air_freight": {"factor": 1.13, "unit": "tonne.km", "source": "DEFRA 2024"},
            "sea_freight": {"factor": 0.016, "unit": "tonne.km", "source": "IMO 2024"},
            "delivery_van": {"factor": 0.415, "unit": "km", "source": "DEFRA 2024"},
            "delivery_truck": {"factor": 0.897, "unit": "km", "source": "EPA 2024"},
        },
        "upstream_fuel": {
            "natural_gas_wtt": {"factor": 0.032, "unit": "kWh", "source": "DEFRA 2024"},  # Well-to-tank
            "gasoline_wtt": {"factor": 0.476, "unit": "liter", "source": "DEFRA 2024"},
            "diesel_wtt": {"factor": 0.545, "unit": "liter", "source": "DEFRA 2024"},
            "electricity_td_losses": {"factor": 0.038, "unit": "kWh", "source": "IEA 2024"},  # T&D losses
        },
    },
}

def seed_emission_factors():
    db = SessionLocal()
    
    try:
        # Check if we already have factors
        existing_count = db.query(EmissionFactor).count()
        if existing_count > 0:
            print(f"⚠️  Found {existing_count} existing emission factors")
            response = input("Do you want to clear and reseed? (y/N): ")
            if response.lower() != 'y':
                print("Skipping seed operation")
                return
            
            # Clear existing factors
            db.query(EmissionFactor).delete()
            db.commit()
            print("Cleared existing factors")
        
        # Insert new factors
        count = 0
        for scope, categories in EMISSION_FACTORS.items():
            for category, activities in categories.items():
                for activity, data in activities.items():
                    factor = EmissionFactor(
                        name=activity.replace('_', ' ').title(),
                        category=category,
                        scope=int(scope.split('_')[1]),  # Extract number from scope_1, scope_2, etc.
                        factor=data['factor'],
                        unit=data['unit'],
                        source=data.get('source', 'Unknown'),
                        description=f"{activity} - {category} ({scope})",
                        is_active=True,
                        valid_from=datetime.utcnow()
                    )
                    db.add(factor)
        
        db.commit()
        print(f"✅ Seeded {db.query(EmissionFactor).count()} emission factors")
        
        # Print summary
        for scope in [1, 2, 3]:
            count = db.query(EmissionFactor).filter(EmissionFactor.scope == scope).count()
            print(f"  Scope {scope}: {count} factors")
            
    except Exception as e:
        print(f"❌ Error seeding emission factors: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🌱 Seeding emission factors...")
    seed_emission_factors()


# backend/app/models/emission_factor.py
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, Index
from app.db.base import Base
from datetime import datetime

class EmissionFactor(Base):
    __tablename__ = "emission_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    scope = Column(Integer, nullable=False)  # 1, 2, or 3
    factor = Column(Float, nullable=False)  # kg CO2e per unit
    unit = Column(String(50), nullable=False)  # kWh, liter, km, etc.
    source = Column(String(255))  # EPA 2024, DEFRA 2024, etc.
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, default=datetime.utcnow)
    valid_to = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_factor_category_scope', 'category', 'scope'),
        Index('idx_factor_active', 'is_active'),
    )


# backend/app/schemas/emission_factor.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class EmissionFactorBase(BaseModel):
    name: str
    category: str
    scope: int
    factor: float
    unit: str
    source: Optional[str] = None
    description: Optional[str] = None

class EmissionFactorCreate(EmissionFactorBase):
    pass

class EmissionFactorUpdate(BaseModel):
    name: Optional[str] = None
    factor: Optional[float] = None
    is_active: Optional[bool] = None

class EmissionFactor(EmissionFactorBase):
    id: int
    is_active: bool
    valid_from: datetime
    valid_to: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# backend/app/api/v1/endpoints/emission_factors.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.emission_factor import EmissionFactor
from app.schemas.emission_factor import EmissionFactor as EmissionFactorSchema

router = APIRouter()

@router.get("/", response_model=List[EmissionFactorSchema])
def get_emission_factors(
    scope: Optional[int] = Query(None, ge=1, le=3),
    category: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get emission factors filtered by scope and category"""
    query = db.query(EmissionFactor)
    
    if scope:
        query = query.filter(EmissionFactor.scope == scope)
    if category:
        query = query.filter(EmissionFactor.category == category)
    if is_active is not None:
        query = query.filter(EmissionFactor.is_active == is_active)
    
    factors = query.offset(skip).limit(limit).all()
    return factors

@router.get("/categories", response_model=dict)
def get_categories(
    scope: Optional[int] = Query(None, ge=1, le=3),
    db: Session = Depends(get_db)
):
    """Get all unique categories grouped by scope"""
    query = db.query(EmissionFactor.scope, EmissionFactor.category).distinct()
    
    if scope:
        query = query.filter(EmissionFactor.scope == scope)
    
    results = query.all()
    
    # Group by scope
    categories_by_scope = {}
    for s, category in results:
        if s not in categories_by_scope:
            categories_by_scope[s] = []
        categories_by_scope[s].append(category)
    
    return categories_by_scope

@router.get("/{factor_id}", response_model=EmissionFactorSchema)
def get_emission_factor(factor_id: int, db: Session = Depends(get_db)):
    """Get a specific emission factor"""
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == factor_id).first()
    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    return factor

@router.post("/calculate")
def calculate_emission(
    factor_id: int,
    amount: float,
    db: Session = Depends(get_db)
):
    """Calculate emissions using a specific factor"""
    factor = db.query(EmissionFactor).filter(EmissionFactor.id == factor_id).first()
    if not factor:
        raise HTTPException(status_code=404, detail="Emission factor not found")
    
    calculated_emissions = amount * factor.factor
    
    return {
        "factor_id": factor.id,
        "factor_name": factor.name,
        "amount": amount,
        "unit": factor.unit,
        "emission_factor": factor.factor,
        "calculated_emissions": calculated_emissions,
        "scope": factor.scope,
        "category": factor.category,
        "source": factor.source
    }


# backend/app/api/v1/api.py
from fastapi import APIRouter
from app.api.v1.endpoints import emissions, emission_factors

api_router = APIRouter()

api_router.include_router(emissions.router, prefix="/emissions", tags=["emissions"])
api_router.include_router(emission_factors.router, prefix="/emission-factors", tags=["emission-factors"])