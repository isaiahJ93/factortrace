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
        {"id": 2, "name": "Fuel Oil", "category": "stationary_combustion", "unit": "L", "factor": 2.753, "source": "EPA", "scope": 1},
        {"id": 3, "name": "Propane", "category": "stationary_combustion", "unit": "L", "factor": 1.51, "source": "EPA", "scope": 1},
        {"id": 4, "name": "Diesel - Vehicles", "category": "mobile_combustion", "unit": "L", "factor": 2.68, "source": "EPA", "scope": 1},
        {"id": 5, "name": "Gasoline - Vehicles", "category": "mobile_combustion", "unit": "L", "factor": 2.31, "source": "EPA", "scope": 1},
        {"id": 6, "name": "Jet Fuel", "category": "mobile_combustion", "unit": "L", "factor": 2.55, "source": "EPA", "scope": 1},
        {"id": 7, "name": "CO2 Process Emissions", "category": "process_emissions", "unit": "tCO2", "factor": 1.0, "source": "Direct", "scope": 1},
        {"id": 8, "name": "R-134a Refrigerant", "category": "refrigerants", "unit": "kg", "factor": 1430, "source": "IPCC", "scope": 1},
        {"id": 9, "name": "R-410A Refrigerant", "category": "refrigerants", "unit": "kg", "factor": 2088, "source": "IPCC", "scope": 1},
        
        # Scope 2 - Indirect Emissions
        {"id": 10, "name": "Electricity - Grid Average", "category": "electricity", "unit": "kWh", "factor": 0.233, "source": "EPA eGRID", "scope": 2},
        {"id": 11, "name": "Electricity - Renewable", "category": "electricity", "unit": "kWh", "factor": 0.0, "source": "EPA", "scope": 2},
        {"id": 12, "name": "District Heating", "category": "heating_cooling", "unit": "kWh", "factor": 0.215, "source": "EPA", "scope": 2},
        {"id": 13, "name": "District Cooling", "category": "heating_cooling", "unit": "kWh", "factor": 0.198, "source": "EPA", "scope": 2},
        {"id": 14, "name": "Steam", "category": "steam", "unit": "kg", "factor": 0.068, "source": "EPA", "scope": 2},
        
        # Scope 3 - Category 1: Purchased Goods and Services
        {"id": 15, "name": "Office Paper", "category": "purchased_goods_services", "unit": "kg", "factor": 0.92, "source": "EPA", "scope": 3},
        {"id": 16, "name": "Plastic Products", "category": "purchased_goods_services", "unit": "kg", "factor": 1.89, "source": "EPA", "scope": 3},
        {"id": 17, "name": "Steel", "category": "purchased_goods_services", "unit": "kg", "factor": 1.85, "source": "EPA", "scope": 3},
        {"id": 18, "name": "Aluminum", "category": "purchased_goods_services", "unit": "kg", "factor": 11.89, "source": "EPA", "scope": 3},
        {"id": 19, "name": "Concrete", "category": "purchased_goods_services", "unit": "m³", "factor": 385, "source": "EPA", "scope": 3},
        {"id": 20, "name": "Electronics", "category": "purchased_goods_services", "unit": "USD", "factor": 0.42, "source": "EPA", "scope": 3},
        {"id": 21, "name": "Textiles", "category": "purchased_goods_services", "unit": "kg", "factor": 8.1, "source": "EPA", "scope": 3},
        {"id": 22, "name": "Food & Beverages", "category": "purchased_goods_services", "unit": "USD", "factor": 0.89, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 2: Capital Goods
        {"id": 23, "name": "IT Equipment", "category": "capital_goods", "unit": "USD", "factor": 0.65, "source": "EPA", "scope": 3},
        {"id": 24, "name": "Office Furniture", "category": "capital_goods", "unit": "USD", "factor": 0.45, "source": "EPA", "scope": 3},
        {"id": 25, "name": "Vehicles", "category": "capital_goods", "unit": "USD", "factor": 0.89, "source": "EPA", "scope": 3},
        {"id": 26, "name": "Buildings", "category": "capital_goods", "unit": "m²", "factor": 125.0, "source": "EPA", "scope": 3},
        {"id": 27, "name": "Manufacturing Equipment", "category": "capital_goods", "unit": "USD", "factor": 0.78, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 3: Fuel and Energy Activities
        {"id": 28, "name": "Upstream Electricity", "category": "fuel_energy_activities", "unit": "kWh", "factor": 0.045, "source": "EPA", "scope": 3},
        {"id": 29, "name": "T&D Losses", "category": "fuel_energy_activities", "unit": "kWh", "factor": 0.023, "source": "EPA", "scope": 3},
        {"id": 30, "name": "WTT - Natural Gas", "category": "fuel_energy_activities", "unit": "m³", "factor": 0.031, "source": "EPA", "scope": 3},
        {"id": 31, "name": "WTT - Gasoline", "category": "fuel_energy_activities", "unit": "L", "factor": 0.62, "source": "EPA", "scope": 3},
        {"id": 32, "name": "WTT - Diesel", "category": "fuel_energy_activities", "unit": "L", "factor": 0.58, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 4: Upstream Transportation
        {"id": 33, "name": "Road Freight", "category": "upstream_transportation", "unit": "tonne-km", "factor": 0.105, "source": "EPA", "scope": 3},
        {"id": 34, "name": "Rail Freight", "category": "upstream_transportation", "unit": "tonne-km", "factor": 0.027, "source": "EPA", "scope": 3},
        {"id": 35, "name": "Air Freight", "category": "upstream_transportation", "unit": "tonne-km", "factor": 1.13, "source": "EPA", "scope": 3},
        {"id": 36, "name": "Sea Freight", "category": "upstream_transportation", "unit": "tonne-km", "factor": 0.016, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 5: Waste Operations
        {"id": 37, "name": "Landfill - Mixed Waste", "category": "waste_operations", "unit": "tonnes", "factor": 467.0, "source": "EPA", "scope": 3},
        {"id": 38, "name": "Recycling - Paper", "category": "waste_operations", "unit": "tonnes", "factor": 21.0, "source": "EPA", "scope": 3},
        {"id": 39, "name": "Recycling - Plastic", "category": "waste_operations", "unit": "tonnes", "factor": 32.0, "source": "EPA", "scope": 3},
        {"id": 40, "name": "Composting", "category": "waste_operations", "unit": "tonnes", "factor": 55.0, "source": "EPA", "scope": 3},
        {"id": 41, "name": "Incineration", "category": "waste_operations", "unit": "tonnes", "factor": 895.0, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 6: Business Travel
        {"id": 42, "name": "Air Travel - Short Haul", "category": "business_travel", "unit": "passenger-km", "factor": 0.215, "source": "EPA", "scope": 3},
        {"id": 43, "name": "Air Travel - Long Haul", "category": "business_travel", "unit": "passenger-km", "factor": 0.115, "source": "EPA", "scope": 3},
        {"id": 44, "name": "Rail Travel", "category": "business_travel", "unit": "passenger-km", "factor": 0.041, "source": "EPA", "scope": 3},
        {"id": 45, "name": "Taxi/Uber", "category": "business_travel", "unit": "km", "factor": 0.21, "source": "EPA", "scope": 3},
        {"id": 46, "name": "Hotel Stay", "category": "business_travel", "unit": "nights", "factor": 15.3, "source": "EPA", "scope": 3},
        {"id": 47, "name": "Rental Car", "category": "business_travel", "unit": "km", "factor": 0.171, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 7: Employee Commuting
        {"id": 48, "name": "Car - Average", "category": "employee_commuting", "unit": "km", "factor": 0.171, "source": "EPA", "scope": 3},
        {"id": 49, "name": "Bus", "category": "employee_commuting", "unit": "passenger-km", "factor": 0.089, "source": "EPA", "scope": 3},
        {"id": 50, "name": "Metro/Subway", "category": "employee_commuting", "unit": "passenger-km", "factor": 0.033, "source": "EPA", "scope": 3},
        {"id": 51, "name": "Motorcycle", "category": "employee_commuting", "unit": "km", "factor": 0.113, "source": "EPA", "scope": 3},
        {"id": 52, "name": "Bicycle", "category": "employee_commuting", "unit": "km", "factor": 0.0, "source": "EPA", "scope": 3},
        {"id": 53, "name": "Remote Work", "category": "employee_commuting", "unit": "days", "factor": 2.5, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 8: Upstream Leased Assets
        {"id": 54, "name": "Leased Buildings", "category": "upstream_leased_assets", "unit": "m²-year", "factor": 45.0, "source": "EPA", "scope": 3},
        {"id": 55, "name": "Leased Vehicles", "category": "upstream_leased_assets", "unit": "km", "factor": 0.171, "source": "EPA", "scope": 3},
        {"id": 56, "name": "Leased Equipment", "category": "upstream_leased_assets", "unit": "USD", "factor": 0.32, "source": "EPA", "scope": 3},
     
        
        # Scope 3 - Category 9: Downstream Transportation
        {"id": 57, "name": "Product Delivery - Road", "category": "downstream_transportation", "unit": "tonne-km", "factor": 0.105, "source": "EPA", "scope": 3},
        {"id": 58, "name": "Product Delivery - Rail", "category": "downstream_transportation", "unit": "tonne-km", "factor": 0.027, "source": "EPA", "scope": 3},
        {"id": 59, "name": "Product Delivery - Air", "category": "downstream_transportation", "unit": "tonne-km", "factor": 1.13, "source": "EPA", "scope": 3},
        {"id": 60, "name": "Product Delivery - Sea", "category": "downstream_transportation", "unit": "tonne-km", "factor": 0.016, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 10: Processing of Sold Products
        {"id": 61, "name": "Manufacturing Process", "category": "processing_sold_products", "unit": "kg", "factor": 0.85, "source": "EPA", "scope": 3},
        {"id": 62, "name": "Assembly Process", "category": "processing_sold_products", "unit": "unit", "factor": 12.5, "source": "EPA", "scope": 3},
        {"id": 63, "name": "Packaging Process", "category": "processing_sold_products", "unit": "kg", "factor": 0.45, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 11: Use of Sold Products
        {"id": 64, "name": "Electronics - Use Phase", "category": "use_of_sold_products", "unit": "unit-year", "factor": 125.0, "source": "EPA", "scope": 3},
        {"id": 65, "name": "Appliances - Use Phase", "category": "use_of_sold_products", "unit": "unit-year", "factor": 450.0, "source": "EPA", "scope": 3},
        {"id": 66, "name": "Vehicles - Use Phase", "category": "use_of_sold_products", "unit": "km", "factor": 0.171, "source": "EPA", "scope": 3},
        {"id": 67, "name": "Software - Use Phase", "category": "use_of_sold_products", "unit": "user-year", "factor": 8.5, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 12: End-of-Life Treatment
        {"id": 68, "name": "Landfill Disposal", "category": "end_of_life_treatment", "unit": "tonnes", "factor": 467.0, "source": "EPA", "scope": 3},
        {"id": 69, "name": "Recycling", "category": "end_of_life_treatment", "unit": "tonnes", "factor": 21.0, "source": "EPA", "scope": 3},
        {"id": 70, "name": "Incineration", "category": "end_of_life_treatment", "unit": "tonnes", "factor": 895.0, "source": "EPA", "scope": 3},
        {"id": 71, "name": "E-waste Treatment", "category": "end_of_life_treatment", "unit": "kg", "factor": 2.5, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 13: Downstream Leased Assets
        {"id": 72, "name": "Leased Real Estate", "category": "downstream_leased_assets", "unit": "m²-year", "factor": 45.0, "source": "EPA", "scope": 3},
        {"id": 73, "name": "Leased Equipment", "category": "downstream_leased_assets", "unit": "USD", "factor": 0.32, "source": "EPA", "scope": 3},
        {"id": 74, "name": "Leased Vehicles", "category": "downstream_leased_assets", "unit": "vehicle-year", "factor": 4500.0, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 14: Franchises
        {"id": 75, "name": "Franchise Operations", "category": "franchises", "unit": "m²-year", "factor": 55.0, "source": "EPA", "scope": 3},
        {"id": 76, "name": "Franchise Energy Use", "category": "franchises", "unit": "kWh", "factor": 0.233, "source": "EPA", "scope": 3},
        {"id": 77, "name": "Franchise Waste", "category": "franchises", "unit": "tonnes", "factor": 467.0, "source": "EPA", "scope": 3},
        
        # Scope 3 - Category 15: Investments
        {"id": 78, "name": "Equity Investments", "category": "investments", "unit": "USD", "factor": 0.00012, "source": "EPA", "scope": 3},
        {"id": 79, "name": "Debt Investments", "category": "investments", "unit": "USD", "factor": 0.00008, "source": "EPA", "scope": 3},
        {"id": 80, "name": "Project Finance", "category": "investments", "unit": "USD", "factor": 0.00015, "source": "EPA", "scope": 3},
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
    amount = request_body.get("amount", 0)
    
    # Get all factors to find the specific one
    all_factors = [
        # Just include a few for the calculation lookup
        {"id": 1, "name": "Natural Gas", "factor": 0.18454},
        {"id": 6, "name": "Air Travel (Economy)", "factor": 0.115},
        {"id": 43, "name": "Air Travel - Long Haul", "factor": 0.115},
        {"id": 44, "name": "Rail Travel", "factor": 0.041},
        {"id": 46, "name": "Hotel Stay", "factor": 15.3},
        # Add more as needed or fetch from a proper source
    ]
    
    # For now, just use a default factor if not found
    factor = next((f for f in all_factors if f["id"] == factor_id), {"factor": 0.233})
    
    # Calculate emission
    emission_value = amount * factor["factor"]
    
    return {
        "calculated_emissions": emission_value,
        "unit": "kgCO2e",
        "calculation_method": "activity_data * emission_factor",
        "data_quality_score": 85
    }
@router.get("/search")
def search_factors(
    query: str = Query(..., description="Search term"),
    db: Session = Depends(get_db)
):
    """Search emission factors by name"""
    all_factors = get_emission_factors(db=db)
    query_lower = query.lower()
    return [f for f in all_factors if query_lower in f["name"].lower()]
