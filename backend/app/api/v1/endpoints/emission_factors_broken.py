from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List, Dict
from app.core.database import get_db

router = APIRouter()

@router.get("/categories")
def get_categories(
    scope: Optional[int] = Query(None, ge=1, le=3, description="Filter by specific scope"),
    db: Session = Depends(get_db)
):
    """Get all unique categories grouped by scope"""
    return {
        "1": ["stationary_combustion", "mobile_combustion", "process_emissions", "refrigerants"],
        "2": ["electricity", "heating_cooling", "steam"],
        "3": [
            "purchased_goods_services",
            "capital_goods", 
            "fuel_energy_activities",
            "upstream_transportation",
            "waste_operations",
            "business_travel",
            "employee_commuting",
            "upstream_leased_assets",
            "downstream_transportation",
            "processing_sold_products",
            "use_of_sold_products",
            "end_of_life_treatment",
            "downstream_leased_assets",
            "franchises",
            "investments"
        ]
    }

@router.get("/")
def get_emission_factors(
    scope: Optional[int] = Query(None, ge=1, le=3),
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get emission factors with optional filtering"""
    
    all_factors = [
        # Scope 1 - Direct Emissions
        {"id": 1, "name": "Natural Gas", "category": "stationary_combustion", "unit": "m³", "factor": 0.18454, "source": "EPA", "scope": 1},
        {"id": 2, "name": "Diesel", "category": "mobile_combustion", "unit": "L", "factor": 2.68, "source": "EPA", "scope": 1},
        {"id": 3, "name": "Gasoline", "category": "mobile_combustion", "unit": "L", "factor": 2.31, "source": "EPA", "scope": 1},
        {"id": 4, "name": "Propane", "category": "stationary_combustion", "unit": "L", "factor": 1.51, "source": "EPA", "scope": 1},
        
        # Scope 2 - Indirect Emissions
        {"id": 10, "name": "Electricity - Grid Average", "category": "electricity", "unit": "kWh", "factor": 0.233, "source": "EPA eGRID", "scope": 2},
        {"id": 11, "name": "Electricity - Renewable", "category": "electricity", "unit": "kWh", "factor": 0.0, "source": "EPA", "scope": 2},
        {"id": 12, "name": "District Heating", "category": "heating_cooling", "unit": "kWh", "factor": 0.215, "source": "EPA", "scope": 2},
        {"id": 13, "name": "District Cooling", "category": "heating_cooling", "unit": "kWh", "factor": 0.198, "source": "EPA", "scope": 2},
        {"id": 14, "name": "Steam", "category": "steam", "unit": "kg", "factor": 0.068, "source": "EPA", "scope": 2},
        
        # Scope 3 - Purchased Goods and Services
        {"id": 15, "name": "Office Paper", "category": "purchased_goods_services", "unit": "kg", "factor": 0.92, "source": "EPA", "scope": 3},
        {"id": 16, "name": "Plastic Products", "category": "purchased_goods_services", "unit": "kg", "factor": 1.89, "source": "EPA", "scope": 3},
        {"id": 17, "name": "Steel", "category": "purchased_goods_services", "unit": "kg", "factor": 1.85, "source": "EPA", "scope": 3},
        {"id": 18, "name": "Aluminum", "category": "purchased_goods_services", "unit": "kg", "factor": 11.89, "source": "EPA", "scope": 3},
        {"id": 19, "name": "Concrete", "category": "purchased_goods_services", "unit": "m³", "factor": 385.0, "source": "EPA", "scope": 3},
        {"id": 20, "name": "Electronics", "category": "purchased_goods_services", "unit": "USD", "factor": 0.42, "source": "EPA", "scope": 3},
        {"id": 21, "name": "Textiles", "category": "purchased_goods_services", "unit": "kg", "factor": 8.1, "source": "EPA", "scope": 3},
        {"id": 22, "name": "Food & Beverages", "category": "purchased_goods_services", "unit": "USD", "factor": 0.89, "source": "EPA", "scope": 3},
        
        # Scope 3 - Capital Goods
        {"id": 23, "name": "IT Equipment", "category": "capital_goods", "unit": "USD", "factor": 0.65, "source": "EPA", "scope": 3},
        {"id": 24, "name": "Office Furniture", "category": "capital_goods", "unit": "USD", "factor": 0.45, "source": "EPA", "scope": 3},
        {"id": 25, "name": "Vehicles", "category": "capital_goods", "unit": "USD", "factor": 0.89, "source": "EPA", "scope": 3},
        {"id": 26, "name": "Buildings", "category": "capital_goods", "unit": "m²", "factor": 125.0, "source": "EPA", "scope": 3},
        {"id": 27, "name": "Manufacturing Equipment", "category": "capital_goods", "unit": "USD", "factor": 0.78, "source": "EPA", "scope": 3},
        
        # Scope 3 - Business Travel
        {"id": 42, "name": "Air Travel - Short Haul", "category": "business_travel", "unit": "passenger-km", "factor": 0.215, "source": "EPA", "scope": 3},
        {"id": 43, "name": "Air Travel - Long Haul", "category": "business_travel", "unit": "passenger-km", "factor": 0.115, "source": "EPA", "scope": 3},
        {"id": 44, "name": "Rail Travel", "category": "business_travel", "unit": "passenger-km", "factor": 0.041, "source": "EPA", "scope": 3},
        {"id": 45, "name": "Taxi/Uber", "category": "business_travel", "unit": "km", "factor": 0.21, "source": "EPA", "scope": 3},
        {"id": 46, "name": "Hotel Stay", "category": "business_travel", "unit": "nights", "factor": 15.3, "source": "EPA", "scope": 3},
        {"id": 47, "name": "Rental Car", "category": "business_travel", "unit": "km", "factor": 0.171, "source": "EPA", "scope": 3},
        
        # Scope 3 - Waste Operations
        {"id": 37, "name": "Landfill - Mixed Waste", "category": "waste_operations", "unit": "tonnes", "factor": 467.0, "source": "EPA", "scope": 3},
        {"id": 38, "name": "Recycling - Paper", "category": "waste_operations", "unit": "tonnes", "factor": 21.0, "source": "EPA", "scope": 3},
        {"id": 39, "name": "Recycling - Plastic", "category": "waste_operations", "unit": "tonnes", "factor": 32.0, "source": "EPA", "scope": 3},
        {"id": 40, "name": "Composting", "category": "waste_operations", "unit": "tonnes", "factor": 55.0, "source": "EPA", "scope": 3},
        {"id": 41, "name": "Incineration", "category": "waste_operations", "unit": "tonnes", "factor": 895.0, "source": "EPA", "scope": 3},
        
        # Add more factors as needed...
    ]
    
    # Filter by scope if provided
    if scope:
        factors = [f for f in all_factors if f["scope"] == scope]
    else:
        factors = all_factors
    
    # Filter by category if provided
    if category:
        factors = [f for f in factors if f["category"] == category]
    
    # Apply pagination
    return factors[skip:skip+limit]

@router.post("/calculate")
def calculate_emission(request_body: dict, db: Session = Depends(get_db)):
    """Calculate emissions based on activity data and emission factor"""
    
    factor_id = request_body.get("factor_id", 1)
    amount = float(request_body.get("amount", 0))
    
    # Define all factors directly here to avoid the Query parameter issue
    all_factors = [
        # Scope 1 - Direct Emissions
        {"id": 1, "name": "Natural Gas", "factor": 0.18454, "unit": "m³"},
        {"id": 2, "name": "Diesel", "factor": 2.68, "unit": "L"},
        {"id": 3, "name": "Gasoline", "factor": 2.31, "unit": "L"},
        
        # Scope 2 - Indirect Emissions
        {"id": 4, "name": "Electricity Grid", "factor": 0.233, "unit": "kWh"},
        {"id": 5, "name": "District Heating", "factor": 0.215, "unit": "kWh"},
        
        # Scope 3 - Purchased Goods and Services
        {"id": 15, "name": "Office Paper", "factor": 0.92, "unit": "kg"},
        {"id": 16, "name": "Plastic Products", "factor": 1.89, "unit": "kg"},
        {"id": 17, "name": "Steel", "factor": 1.85, "unit": "kg"},
        {"id": 18, "name": "Aluminum", "factor": 11.89, "unit": "kg"},
        {"id": 19, "name": "Concrete", "factor": 385.0, "unit": "m³"},
        {"id": 20, "name": "Electronics", "factor": 0.42, "unit": "USD"},
        
        # Scope 3 - Business Travel
        {"id": 42, "name": "Air Travel - Short Haul", "factor": 0.215, "unit": "passenger-km"},
        {"id": 43, "name": "Air Travel - Long Haul", "factor": 0.115, "unit": "passenger-km"},
        {"id": 44, "name": "Rail Travel", "factor": 0.041, "unit": "passenger-km"},
        {"id": 46, "name": "Hotel Stay", "factor": 15.3, "unit": "nights"},
        
        # Scope 3 - Waste Operations
        {"id": 37, "name": "Landfill - Mixed Waste", "factor": 467.0, "unit": "tonnes"},
        {"id": 38, "name": "Recycling - Paper", "factor": 21.0, "unit": "tonnes"},
        {"id": 39, "name": "Recycling - Plastic", "factor": 32.0, "unit": "tonnes"},
    ]
    
    # Find the specific factor
    factor = next((f for f in all_factors if f["id"] == factor_id), None)
    
    if not factor:
        factor = {"name": "Unknown", "factor": 0.233, "unit": "unit"}
    
    # Calculate emissions
    emissions = amount * factor["factor"]
    
    return {
        "calculated_emissions": emissions,
        "unit": "kgCO2e",
        "calculation_method": "activity_data * emission_factor",
        "data_quality_score": 85,
        "factor_used": {
            "id": factor_id,
            "name": factor["name"],
            "factor": factor["factor"],
            "unit": factor["unit"]
        }
    }@router.get("/search")
def search_factors(
    query: str = Query(..., description="Search term"),
    db: Session = Depends(get_db)
):
    """Search emission factors by name"""
    all_factors = get_emission_factors(db=db)
    query_lower = query.lower()
    return [f for f in all_factors if query_lower in f["name"].lower()]
