#!/bin/bash
# startup.sh - Run this from your backend directory

echo "🚀 Starting GHG Calculator Backend Setup..."

# 1. Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
}

# 2. Install/update dependencies
echo "📚 Installing dependencies..."
pip install fastapi uvicorn sqlalchemy asyncpg pydantic python-dotenv pytest pytest-asyncio

# 3. Create necessary files if they don't exist
echo "📝 Creating missing module files..."

# Create the calculation_engine.py symlink/wrapper
if [ ! -f "app/calculation_engine.py" ]; then
    echo "Creating app/calculation_engine.py..."
    cat > app/calculation_engine.py << 'EOF'
"""Export calculation engine for compatibility"""
from .services.ghg_calculation_engine import *
EOF
fi

# Create domain_models wrapper
if [ ! -f "app/domain_models.py" ]; then
    echo "Creating app/domain_models.py..."
    cat > app/domain_models.py << 'EOF'
"""Export domain models for compatibility"""
from .models.ghg_domain import *
from .models.ghg_protocol_models import *
EOF
fi

# Create database_models wrapper
if [ ! -f "app/database_models.py" ]; then
    echo "Creating app/database_models.py..."
    cat > app/database_models.py << 'EOF'
"""Export database models for compatibility"""
from .models.ghg_database_models import *
from .db.base_class import Base
EOF
fi

# Create api_models wrapper
if [ ! -f "app/api_models.py" ]; then
    echo "Creating app/api_models.py..."
    cat > app/api_models.py << 'EOF'
"""Export API models for compatibility"""
from .schemas.ghg_schemas import *
from .models.ghg_protocol_models import EmissionScope, ActivityType, CalculationMethod, DataQuality
EOF
fi

# 4. Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./factortrace.db
TESTING=false
API_V1_STR=/api/v1
PROJECT_NAME=GHG Protocol Calculator
ENV=development
EOF
fi

# 5. Create the new endpoint file
echo "📝 Creating GHG calculator endpoint..."
mkdir -p app/api/v1/endpoints
cat > app/api/v1/endpoints/ghg_calculator.py << 'EOF'
"""
GHG Calculator API Endpoint
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from datetime import date
from pydantic import BaseModel, Field

router = APIRouter()

class EmissionInput(BaseModel):
    activity_type: str
    amount: float = Field(..., gt=0)
    unit: str

class CalculateEmissionsRequest(BaseModel):
    company_id: str = "default"
    reporting_period: str
    emissions_data: List[EmissionInput]

class EmissionBreakdown(BaseModel):
    activity_type: str
    scope: str
    emissions_kg_co2e: float
    unit: str
    calculation_method: str

class CalculateEmissionsResponse(BaseModel):
    total_emissions_kg_co2e: float
    total_emissions_tons_co2e: float
    scope1_emissions: float
    scope2_emissions: float
    scope3_emissions: float
    breakdown: List[EmissionBreakdown]
    reporting_period: str
    calculation_date: str

# Default emission factors
DEFAULT_EMISSION_FACTORS = {
    "electricity": {"factor": 0.0007, "unit": "kWh", "scope": "scope_2"},
    "natural_gas": {"factor": 0.00185, "unit": "m3", "scope": "scope_1"},
    "vehicle_fuel": {"factor": 0.00235, "unit": "liters", "scope": "scope_1"},
    "business_travel": {"factor": 0.00021, "unit": "km", "scope": "scope_3"},
}

@router.post("/calculate", response_model=CalculateEmissionsResponse)
async def calculate_emissions(request: CalculateEmissionsRequest):
    """Calculate GHG emissions"""
    total_emissions = 0.0
    scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
    breakdown = []
    
    for emission_input in request.emissions_data:
        activity_type = emission_input.activity_type.lower()
        
        if activity_type not in DEFAULT_EMISSION_FACTORS:
            continue
            
        factor_data = DEFAULT_EMISSION_FACTORS[activity_type]
        emissions_kg = emission_input.amount * factor_data["factor"] * 1000
        
        scope = factor_data["scope"]
        scope_totals[scope] += emissions_kg
        total_emissions += emissions_kg
        
        breakdown.append(EmissionBreakdown(
            activity_type=emission_input.activity_type,
            scope=scope,
            emissions_kg_co2e=round(emissions_kg, 2),
            unit=emission_input.unit,
            calculation_method="emission_factor"
        ))
    
    return CalculateEmissionsResponse(
        total_emissions_kg_co2e=round(total_emissions, 2),
        total_emissions_tons_co2e=round(total_emissions / 1000, 2),
        scope1_emissions=round(scope_totals["scope_1"], 2),
        scope2_emissions=round(scope_totals["scope_2"], 2),
        scope3_emissions=round(scope_totals["scope_3"], 2),
        breakdown=breakdown,
        reporting_period=request.reporting_period,
        calculation_date=date.today().isoformat()
    )

@router.get("/activity-types")
async def get_activity_types():
    """Get supported activity types"""
    return {
        "scope_1": [
            {"value": "natural_gas", "label": "Natural Gas", "unit": "m3"},
            {"value": "vehicle_fuel", "label": "Vehicle Fuel", "unit": "liters"},
        ],
        "scope_2": [
            {"value": "electricity", "label": "Electricity", "unit": "kWh"},
        ],
        "scope_3": [
            {"value": "business_travel", "label": "Business Travel", "unit": "km"},
        ]
    }
EOF

# 6. Update the API router
echo "📝 Updating API router..."
if [ -f "app/api/v1/api.py" ]; then
    # Check if ghg_calculator is already imported
    if ! grep -q "ghg_calculator" app/api/v1/api.py; then
        echo "Adding ghg_calculator to API router..."
        # This is a simplified approach - in production you'd want more robust file editing
        echo """
# Add to imports
from app.api.v1.endpoints import ghg_calculator

# Add to router
api_router.include_router(
    ghg_calculator.router,
    prefix='/ghg-calculator',
    tags=['ghg-calculator']
)
""" >> app/api/v1/api_update_instructions.txt
        echo "⚠️  Please manually add ghg_calculator to your app/api/v1/api.py file"
        echo "   See app/api/v1/api_update_instructions.txt for details"
    fi
fi

# 7. Start the server
echo "🚀 Starting FastAPI server..."
echo ""
echo "==================================="
echo "Backend is starting on http://localhost:8000"
echo "API docs: http://localhost:8000/docs"
echo "==================================="
echo ""

# Run the server
uvicorn app.main:app --reload --port 8000