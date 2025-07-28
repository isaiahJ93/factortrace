# backend/scripts/seed_complete_emission_factors.py
from sqlalchemy import func
"""
Complete emission factors seeder with all factors for all 15 Scope 3 categories
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.session import SessionLocal
from app.models.emission_factor import EmissionFactor
from datetime import datetime

# Complete emission factors dataset
EMISSION_FACTORS = {
    # SCOPE 1 - Direct Emissions
    "scope_1": {
        "stationary_combustion": [
            # Natural Gas
            {"name": "Natural Gas", "factor": 0.185, "unit": "kWh", "source": "EPA 2024", "description": "Commercial/Industrial natural gas combustion", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            {"name": "Natural Gas (Therms)", "factor": 5.3, "unit": "therm", "source": "EPA 2024", "description": "Natural gas by therms", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            {"name": "Natural Gas (Cubic Meters)", "factor": 2.02, "unit": "m3", "source": "DEFRA 2024", "description": "Natural gas by volume", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            
            # Propane & LPG
            {"name": "Propane", "factor": 1.51, "unit": "liter", "source": "EPA 2024", "description": "Propane/LPG combustion", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            {"name": "Propane (kg)", "factor": 2.94, "unit": "kg", "source": "DEFRA 2024", "description": "Propane by weight", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            
            # Diesel
            {"name": "Diesel", "factor": 2.68, "unit": "liter", "source": "EPA 2024", "description": "Diesel fuel combustion", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            {"name": "Diesel (US Gallon)", "factor": 10.21, "unit": "gallon", "source": "EPA 2024", "description": "Diesel by US gallon", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            
            # Gasoline/Petrol
            {"name": "Gasoline", "factor": 2.31, "unit": "liter", "source": "EPA 2024", "description": "Gasoline/petrol combustion", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
            {"name": "Gasoline (US Gallon)", "factor": 8.78, "unit": "gallon", "source": "EPA 2024", "description": "Gasoline by US gallon", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Direct measurement", "region": None},
        ],
        
        "mobile_combustion": [
            # Passenger Vehicles
            {"name": "Passenger Car - Gasoline", "factor": 2.31, "unit": "liter", "source": "EPA 2024", "description": "Average gasoline passenger vehicle", "uncertainty_percentage": 5, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "Fleet average", "region": None},
            {"name": "Passenger Car - Diesel", "factor": 2.68, "unit": "liter", "source": "EPA 2024", "description": "Average diesel passenger vehicle", "uncertainty_percentage": 5, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "Fleet average", "region": None},
            {"name": "Small Car - Petrol", "factor": 0.14, "unit": "km", "source": "DEFRA 2024", "description": "Small petrol car (<1.4L)", "uncertainty_percentage": 5, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "Fleet average", "region": None},
            {"name": "Medium Car - Petrol", "factor": 0.18, "unit": "km", "source": "DEFRA 2024", "description": "Medium petrol car (1.4-2.0L)", "uncertainty_percentage": 5, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "Fleet average", "region": None},
            {"name": "Large Car - Petrol", "factor": 0.28, "unit": "km", "source": "DEFRA 2024", "description": "Large petrol car (>2.0L)", "uncertainty_percentage": 5, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "Fleet average", "region": None},
        ],
        
        "refrigerants": [
            {"name": "R-134a (HFC)", "factor": 1430, "unit": "kg", "source": "IPCC AR6", "description": "Common in vehicle AC", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "IPCC methodology", "region": None},
            {"name": "R-404A", "factor": 3920, "unit": "kg", "source": "IPCC AR6", "description": "Commercial refrigeration", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "IPCC methodology", "region": None},
            {"name": "R-410A", "factor": 2088, "unit": "kg", "source": "IPCC AR6", "description": "Common in AC systems", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "IPCC methodology", "region": None},
        ],
    },
    
    # SCOPE 2 - Indirect Emissions
    "scope_2": {
        "electricity": [
            # Grid averages
            {"name": "US Grid Average", "factor": 0.385, "unit": "kWh", "source": "EPA eGRID 2024", "description": "US national average", "uncertainty_percentage": 10, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Grid measurement", "region": "US"},
            {"name": "California Grid", "factor": 0.203, "unit": "kWh", "source": "CARB 2024", "description": "California state grid", "uncertainty_percentage": 8, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Grid measurement", "region": "US-CA"},
            {"name": "UK Grid", "factor": 0.233, "unit": "kWh", "source": "DEFRA 2024", "description": "UK grid average", "uncertainty_percentage": 8, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Grid measurement", "region": "UK"},
            {"name": "EU Average", "factor": 0.276, "unit": "kWh", "source": "EEA 2024", "description": "EU average", "uncertainty_percentage": 10, "data_quality_score": 1, "tier_level": "TIER_3", "methodology": "Grid measurement", "region": "EU"},
            {"name": "China Grid", "factor": 0.581, "unit": "kWh", "source": "MEE 2024", "description": "China national grid", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "Grid measurement", "region": "CN"},
        ],
        
        "heating_cooling": [
            {"name": "District Heating", "factor": 0.215, "unit": "kWh", "source": "DEFRA 2024", "description": "Average district heating", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "methodology": "System average", "region": None},
            {"name": "Steam", "factor": 0.069, "unit": "kg", "source": "EPA 2024", "description": "Purchased steam", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "methodology": "System average", "region": None},
        ],
    },
    
    # SCOPE 3 - All 15 Categories
    "scope_3": {
        # Category 1: Purchased Goods and Services
        "purchased_goods_services": [
            # Spend-based factors
            {"name": "Steel Products (Spend)", "factor": 3.71, "unit": "USD", "source": "EPA EEIO 2024", "description": "Steel products spend-based", "uncertainty_percentage": 15, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Steel Products (Spend) - EU", "factor": 3.45, "unit": "USD", "source": "EPA EEIO 2024", "description": "Steel products EU spend-based", "uncertainty_percentage": 15, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": "EU"},
            {"name": "Aluminum Products (Spend)", "factor": 8.24, "unit": "USD", "source": "EPA EEIO 2024", "description": "Aluminum products spend-based", "uncertainty_percentage": 18, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Plastic Products (Spend)", "factor": 2.48, "unit": "USD", "source": "EPA EEIO 2024", "description": "Plastic products spend-based", "uncertainty_percentage": 12, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Paper Products (Spend)", "factor": 1.35, "unit": "USD", "source": "EPA EEIO 2024", "description": "Paper products spend-based", "uncertainty_percentage": 10, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Electronic Components (Spend)", "factor": 0.65, "unit": "USD", "source": "EPA EEIO 2024", "description": "Electronic components spend-based", "uncertainty_percentage": 20, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "IT Services (Spend)", "factor": 0.18, "unit": "USD", "source": "EPA EEIO 2024", "description": "IT services spend-based", "uncertainty_percentage": 22, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Professional Services (Spend)", "factor": 0.31, "unit": "USD", "source": "EPA EEIO 2024", "description": "Professional services spend-based", "uncertainty_percentage": 25, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "purchased_goods_services", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            
            # Activity-based factors
            {"name": "Steel (Virgin)", "factor": 2.32, "unit": "kg", "source": "Ecoinvent 3.9", "description": "Virgin steel production", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Life cycle assessment", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Steel (Virgin) - EU", "factor": 2.21, "unit": "kg", "source": "Ecoinvent 3.9", "description": "Virgin steel EU", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Life cycle assessment", "lifecycle_stage": "cradle-to-gate", "region": "EU"},
            {"name": "Steel (Recycled)", "factor": 0.43, "unit": "kg", "source": "Worldsteel 2024", "description": "Recycled steel production", "uncertainty_percentage": 6, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Aluminum (Primary)", "factor": 11.89, "unit": "kg", "source": "IAI 2024", "description": "Primary aluminum production", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Aluminum (Recycled)", "factor": 0.53, "unit": "kg", "source": "IAI 2024", "description": "Recycled aluminum", "uncertainty_percentage": 5, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Plastic (PET)", "factor": 2.15, "unit": "kg", "source": "PlasticsEurope 2023", "description": "PET plastic production", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Plastic (HDPE)", "factor": 1.93, "unit": "kg", "source": "PlasticsEurope 2023", "description": "HDPE plastic production", "uncertainty_percentage": 9, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Paper (Virgin)", "factor": 0.92, "unit": "kg", "source": "CEPI 2024", "description": "Virgin paper production", "uncertainty_percentage": 7, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Paper (Recycled)", "factor": 0.48, "unit": "kg", "source": "CEPI 2024", "description": "Recycled paper production", "uncertainty_percentage": 6, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Cement", "factor": 0.91, "unit": "kg", "source": "GCCA 2024", "description": "Cement production", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Concrete", "factor": 0.107, "unit": "kg", "source": "GCCA 2024", "description": "Ready-mix concrete", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Glass", "factor": 0.503, "unit": "kg", "source": "EPA 2024", "description": "Glass production", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Wood", "factor": 0.072, "unit": "kg", "source": "EPA 2024", "description": "Lumber/timber", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "purchased_goods_services", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "cradle-to-gate", "region": None},
        ],
        
        # Category 2: Capital Goods
        "capital_goods": [
            # Spend-based
            {"name": "Buildings Commercial (Spend)", "factor": 0.38, "unit": "USD", "source": "EPA EEIO 2024", "description": "Commercial buildings depreciated", "uncertainty_percentage": 20, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "capital_goods", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Machinery Industrial (Spend)", "factor": 0.89, "unit": "USD", "source": "EPA EEIO 2024", "description": "Industrial machinery depreciated", "uncertainty_percentage": 18, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "capital_goods", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Vehicles Commercial (Spend)", "factor": 1.12, "unit": "USD", "source": "EPA EEIO 2024", "description": "Commercial vehicles depreciated", "uncertainty_percentage": 15, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "capital_goods", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "IT Equipment (Spend)", "factor": 0.73, "unit": "USD", "source": "EPA EEIO 2024", "description": "IT equipment depreciated", "uncertainty_percentage": 22, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "capital_goods", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "cradle-to-gate", "region": None},
            
            # Activity-based
            {"name": "Office Building Construction", "factor": 435, "unit": "m2", "source": "RICS 2024", "description": "Office building construction", "uncertainty_percentage": 15, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Building LCA", "lifecycle_stage": "cradle-to-practical-completion", "region": None},
            {"name": "Warehouse Construction", "factor": 295, "unit": "m2", "source": "RICS 2024", "description": "Warehouse construction", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Building LCA", "lifecycle_stage": "cradle-to-practical-completion", "region": None},
            {"name": "Passenger Vehicle", "factor": 5800, "unit": "unit", "source": "Argonne GREET 2024", "description": "Passenger vehicle manufacturing", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Vehicle LCA", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Delivery Truck", "factor": 18500, "unit": "unit", "source": "Argonne GREET 2024", "description": "Delivery truck manufacturing", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Vehicle LCA", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Laptop Computer", "factor": 316, "unit": "unit", "source": "Dell EPD 2024", "description": "Laptop manufacturing", "uncertainty_percentage": 8, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Product EPD", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Desktop Computer", "factor": 485, "unit": "unit", "source": "HP EPD 2024", "description": "Desktop with monitor", "uncertainty_percentage": 10, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Product EPD", "lifecycle_stage": "cradle-to-gate", "region": None},
            {"name": "Server Rack", "factor": 6250, "unit": "unit", "source": "HPE EPD 2024", "description": "Server rack manufacturing", "uncertainty_percentage": 10, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "capital_goods", "calculation_method": "activity_based", "methodology": "Product EPD", "lifecycle_stage": "cradle-to-gate", "region": None},
        ],
        
        # Category 3: Fuel and Energy Related Activities
        "fuel_energy_activities": [
            {"name": "Natural Gas WTT", "factor": 0.18453, "unit": "kWh", "source": "DEFRA 2024", "description": "Well-to-tank emissions for natural gas", "uncertainty_percentage": 5, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "WTT analysis", "lifecycle_stage": "well-to-tank", "region": None},
            {"name": "Diesel WTT", "factor": 0.61314, "unit": "liter", "source": "DEFRA 2024", "description": "Well-to-tank emissions for diesel", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "WTT analysis", "lifecycle_stage": "well-to-tank", "region": None},
            {"name": "Gasoline WTT", "factor": 0.59054, "unit": "liter", "source": "DEFRA 2024", "description": "Well-to-tank emissions for gasoline", "uncertainty_percentage": 6, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "WTT analysis", "lifecycle_stage": "well-to-tank", "region": None},
            {"name": "Electricity T&D Losses (US)", "factor": 0.048, "unit": "kWh", "source": "EPA eGRID 2024", "description": "US grid T&D losses 4.8%", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "Grid loss calculation", "lifecycle_stage": "use-phase", "region": "US"},
            {"name": "Electricity T&D Losses (EU)", "factor": 0.038, "unit": "kWh", "source": "EU Statistics 2024", "description": "EU grid T&D losses", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "Grid loss calculation", "lifecycle_stage": "use-phase", "region": "EU"},
            {"name": "Jet Fuel WTT", "factor": 0.519, "unit": "liter", "source": "DEFRA 2024", "description": "Aviation fuel upstream", "uncertainty_percentage": 8, "data_quality_score": 1, "tier_level": "TIER_3", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "WTT analysis", "lifecycle_stage": "well-to-tank", "region": None},
            {"name": "Marine Fuel WTT", "factor": 0.416, "unit": "liter", "source": "IMO 2024", "description": "Marine fuel upstream", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "fuel_energy_activities", "calculation_method": "activity_based", "methodology": "WTT analysis", "lifecycle_stage": "well-to-tank", "region": None},
        ],
        
        # Category 4: Upstream Transportation and Distribution
        "upstream_transportation": [
            {"name": "Road Truck (per tonne.km)", "factor": 0.10417, "unit": "tonne.km", "source": "GLEC 2023", "description": "Average articulated truck", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "GLEC Framework", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Road Truck - EU", "factor": 0.09821, "unit": "tonne.km", "source": "GLEC 2023", "description": "EU articulated truck", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "GLEC Framework", "lifecycle_stage": "use-phase", "region": "EU"},
            {"name": "Rail Freight", "factor": 0.02214, "unit": "tonne.km", "source": "GLEC 2023", "description": "Rail freight average", "uncertainty_percentage": 6, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "GLEC Framework", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Sea Container", "factor": 0.01222, "unit": "tonne.km", "source": "GLEC 2023", "description": "Container shipping", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "GLEC Framework", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Air Freight", "factor": 1.2164, "unit": "tonne.km", "source": "GLEC 2023", "description": "Air freight average", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "GLEC Framework", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Van Delivery", "factor": 0.748, "unit": "tonne.km", "source": "DEFRA 2024", "description": "Delivery van per tonne.km", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "Fleet average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Warehousing (Ambient)", "factor": 15.3, "unit": "pallet.month", "source": "WBCSD 2024", "description": "Ambient warehouse per pallet-month", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "Facility average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Warehousing (Refrigerated)", "factor": 42.7, "unit": "pallet.month", "source": "WBCSD 2024", "description": "Refrigerated warehouse per pallet-month", "uncertainty_percentage": 18, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_transportation", "calculation_method": "activity_based", "methodology": "Facility average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Logistics Services (Spend)", "factor": 1.89, "unit": "USD", "source": "EPA EEIO 2024", "description": "Logistics services spend-based", "uncertainty_percentage": 20, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "upstream_transportation", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 5: Waste Generated in Operations
        "waste_operations": [
            {"name": "Landfill Mixed Waste", "factor": 467.9, "unit": "tonne", "source": "EPA WARM 2024", "description": "Mixed waste to landfill with CH4 collection", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "EPA WARM model", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Landfill Organic Waste", "factor": 819.4, "unit": "tonne", "source": "EPA WARM 2024", "description": "Organic waste to landfill", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "EPA WARM model", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Incineration Mixed Waste", "factor": 1016.8, "unit": "tonne", "source": "EPA WARM 2024", "description": "Mixed waste incineration", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "Combustion calculation", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Recycling Mixed Materials", "factor": 21.3, "unit": "tonne", "source": "EPA WARM 2024", "description": "Mixed recycling processing", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "Process-based LCA", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Composting Organic", "factor": -182.7, "unit": "tonne", "source": "EPA WARM 2024", "description": "Organic composting with carbon sequestration", "uncertainty_percentage": 30, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "Carbon sequestration model", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Wastewater Treatment", "factor": 0.689, "unit": "m3", "source": "IPCC 2019", "description": "Municipal wastewater treatment", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "IPCC methodology", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Paper Recycling", "factor": -3893, "unit": "tonne", "source": "EPA WARM 2024", "description": "Paper recycling avoided emissions", "uncertainty_percentage": 15, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "Avoided emissions", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Plastic Recycling", "factor": -1486, "unit": "tonne", "source": "EPA WARM 2024", "description": "Plastic recycling avoided emissions", "uncertainty_percentage": 18, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "Avoided emissions", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Metal Recycling", "factor": -4921, "unit": "tonne", "source": "EPA WARM 2024", "description": "Metal recycling avoided emissions", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "waste_operations", "calculation_method": "activity_based", "methodology": "Avoided emissions", "lifecycle_stage": "end-of-life", "region": None},
        ],
        
        # Category 6: Business Travel
        "business_travel": [
            # Air Travel
            {"name": "Flight - Domestic", "factor": 0.246, "unit": "km", "source": "DEFRA 2024", "description": "Domestic flights average", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Distance-based", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Flight - Short Haul", "factor": 0.151, "unit": "km", "source": "DEFRA 2024", "description": "Flights <3,700km", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Distance-based", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Flight - Long Haul", "factor": 0.147, "unit": "km", "source": "DEFRA 2024", "description": "Flights >3,700km", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Distance-based", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Flight - Economy Class", "factor": 0.146, "unit": "km", "source": "DEFRA 2024", "description": "Economy class specific", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Class-specific", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Flight - Business Class", "factor": 0.419, "unit": "km", "source": "DEFRA 2024", "description": "Business class specific", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Class-specific", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Flight - First Class", "factor": 0.583, "unit": "km", "source": "DEFRA 2024", "description": "First class specific", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Class-specific", "lifecycle_stage": "use-phase", "region": None},
            
            # Ground Transportation
            {"name": "Taxi", "factor": 0.208, "unit": "km", "source": "DEFRA 2024", "description": "Average taxi/rideshare", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Fleet average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Rail - National", "factor": 0.037, "unit": "km", "source": "DEFRA 2024", "description": "National rail average", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Network average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Bus - Long Distance", "factor": 0.027, "unit": "km", "source": "DEFRA 2024", "description": "Coach/long-distance bus", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Fleet average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Rental Car - Average", "factor": 0.171, "unit": "km", "source": "EPA 2024", "description": "Average rental car", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Fleet average", "lifecycle_stage": "use-phase", "region": None},
            
            # Accommodation
            {"name": "Hotel Stay - Average", "factor": 10.3, "unit": "night", "source": "Cornell Hotel School 2024", "description": "Average hotel per room-night", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Industry study", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Hotel Stay - Luxury", "factor": 15.8, "unit": "night", "source": "Cornell Hotel School 2024", "description": "Luxury hotel per room-night", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "business_travel", "calculation_method": "activity_based", "methodology": "Industry study", "lifecycle_stage": "use-phase", "region": None},
            
            # Spend-based
            {"name": "Travel Expenses (Spend)", "factor": 0.52, "unit": "USD", "source": "EPA EEIO 2024", "description": "Travel expenses spend-based", "uncertainty_percentage": 30, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "business_travel", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 7: Employee Commuting
        "employee_commuting": [
            {"name": "Car - Average", "factor": 0.171, "unit": "km", "source": "EPA 2024", "description": "Average passenger car", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Fleet average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Car - Small", "factor": 0.14, "unit": "km", "source": "DEFRA 2024", "description": "Small car commute", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Vehicle class", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Car - Large/SUV", "factor": 0.28, "unit": "km", "source": "DEFRA 2024", "description": "Large car/SUV commute", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Vehicle class", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Carpool (2 people)", "factor": 0.086, "unit": "km", "source": "EPA 2024", "description": "Carpooling with one other person", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Occupancy-based", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Bus", "factor": 0.089, "unit": "km", "source": "DEFRA 2024", "description": "Public bus commute", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Transit average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Train/Subway", "factor": 0.037, "unit": "km", "source": "DEFRA 2024", "description": "Commuter rail/subway", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Transit average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Motorcycle", "factor": 0.108, "unit": "km", "source": "DEFRA 2024", "description": "Motorcycle commute", "uncertainty_percentage": 8, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Vehicle type", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Remote Work", "factor": 0.14, "unit": "day", "source": "Microsoft 2024", "description": "Home office energy use per day", "uncertainty_percentage": 30, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Energy modeling", "lifecycle_stage": "use-phase", "region": None},
            {"name": "E-bike", "factor": 0.003, "unit": "km", "source": "ECF 2024", "description": "Electric bicycle", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Energy consumption", "lifecycle_stage": "use-phase", "region": None},
            {"name": "E-scooter", "factor": 0.019, "unit": "km", "source": "ITF 2024", "description": "Electric scooter", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "employee_commuting", "calculation_method": "activity_based", "methodology": "Energy consumption", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 8: Upstream Leased Assets
        "upstream_leased_assets": [
            {"name": "Office Space Energy", "factor": 53.2, "unit": "m2.year", "source": "CIBSE 2024", "description": "Office space annual energy use", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_leased_assets", "calculation_method": "activity_based", "methodology": "Building energy model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Warehouse Energy", "factor": 35.7, "unit": "m2.year", "source": "CIBSE 2024", "description": "Warehouse annual energy use", "uncertainty_percentage": 18, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_leased_assets", "calculation_method": "activity_based", "methodology": "Building energy model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Retail Space Energy", "factor": 89.4, "unit": "m2.year", "source": "CIBSE 2024", "description": "Retail space annual energy use", "uncertainty_percentage": 22, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_leased_assets", "calculation_method": "activity_based", "methodology": "Building energy model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Data Center Energy", "factor": 1824, "unit": "m2.year", "source": "Uptime Institute 2024", "description": "Data center annual energy use", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_leased_assets", "calculation_method": "activity_based", "methodology": "PUE-based calculation", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Vehicle Lease - Passenger", "factor": 4123, "unit": "vehicle.year", "source": "EPA 2024", "description": "Leased passenger vehicle annual", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "upstream_leased_assets", "calculation_method": "activity_based", "methodology": "Vehicle use model", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 9: Downstream Transportation and Distribution
        "downstream_transportation": [
            {"name": "Last Mile Delivery - Van", "factor": 0.849, "unit": "delivery", "source": "MIT CTL 2024", "description": "Urban delivery average 8km", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "downstream_transportation", "calculation_method": "activity_based", "methodology": "Route analysis", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Parcel Delivery - National", "factor": 0.415, "unit": "parcel", "source": "UPS Sustainability 2024", "description": "Average parcel delivery", "uncertainty_percentage": 15, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "downstream_transportation", "calculation_method": "activity_based", "methodology": "Network model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Retail Customer Transport", "factor": 2.31, "unit": "trip", "source": "WBCSD 2024", "description": "Average 13.5km round trip", "uncertainty_percentage": 35, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "downstream_transportation", "calculation_method": "activity_based", "methodology": "Survey-based", "lifecycle_stage": "use-phase", "region": None},
            {"name": "E-commerce Delivery", "factor": 0.215, "unit": "package", "source": "MIT CTL 2024", "description": "Average e-commerce package", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "downstream_transportation", "calculation_method": "activity_based", "methodology": "Network model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Container Shipping - Ocean", "factor": 0.01222, "unit": "tonne.km", "source": "GLEC 2023", "description": "Ocean freight downstream", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "downstream_transportation", "calculation_method": "activity_based", "methodology": "GLEC Framework", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 10: Processing of Sold Products
        "processing_sold_products": [
            {"name": "Steel Processing - Forming", "factor": 0.326, "unit": "kg", "source": "Worldsteel 2024", "description": "Steel forming and shaping", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "processing_sold_products", "calculation_method": "activity_based", "methodology": "Process LCA", "lifecycle_stage": "processing", "region": None},
            {"name": "Plastic Injection Molding", "factor": 1.82, "unit": "kg", "source": "PlasticsEurope 2023", "description": "Plastic injection molding", "uncertainty_percentage": 15, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "processing_sold_products", "calculation_method": "activity_based", "methodology": "Process LCA", "lifecycle_stage": "processing", "region": None},
            {"name": "Chemical Processing - Generic", "factor": 1.45, "unit": "kg", "source": "CEFIC 2024", "description": "Generic chemical processing", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "processing_sold_products", "calculation_method": "activity_based", "methodology": "Industry average", "lifecycle_stage": "processing", "region": None},
            {"name": "Food Processing - Cooking", "factor": 0.234, "unit": "kg", "source": "FAO 2024", "description": "Food cooking and processing", "uncertainty_percentage": 18, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "processing_sold_products", "calculation_method": "activity_based", "methodology": "Process study", "lifecycle_stage": "processing", "region": None},
            {"name": "Metal Machining", "factor": 0.412, "unit": "kg", "source": "Industry Average 2024", "description": "Metal machining and finishing", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "processing_sold_products", "calculation_method": "activity_based", "methodology": "Process LCA", "lifecycle_stage": "processing", "region": None},
        ],
        
        # Category 11: Use of Sold Products
        "use_of_sold_products": [
            {"name": "Passenger Vehicle - Lifetime", "factor": 33000, "unit": "vehicle", "source": "EPA 2024", "description": "150,000 miles lifetime", "uncertainty_percentage": 20, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Use phase model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Refrigerator - Annual", "factor": 225, "unit": "unit.year", "source": "Energy Star 2024", "description": "Annual refrigerator emissions", "uncertainty_percentage": 15, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Energy consumption", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Laptop Computer - Annual", "factor": 52, "unit": "unit.year", "source": "Energy Star 2024", "description": "Annual laptop emissions", "uncertainty_percentage": 20, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Energy consumption", "lifecycle_stage": "use-phase", "region": None},
            {"name": "LED Bulb - Lifetime", "factor": 21.3, "unit": "bulb", "source": "DOE 2024", "description": "25,000 hour lifetime", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Energy consumption", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Washing Machine - Annual", "factor": 143, "unit": "unit.year", "source": "Energy Star 2024", "description": "Annual washing machine emissions", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Energy consumption", "lifecycle_stage": "use-phase", "region": None},
            {"name": "HVAC System - Annual", "factor": 1850, "unit": "unit.year", "source": "ASHRAE 2024", "description": "Annual HVAC emissions", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Energy modeling", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Electric Vehicle - Lifetime", "factor": 12500, "unit": "vehicle", "source": "EPA 2024", "description": "150,000 miles EV lifetime", "uncertainty_percentage": 25, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "use_of_sold_products", "calculation_method": "activity_based", "methodology": "Grid-based charging", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 12: End-of-Life Treatment of Sold Products  
        "end_of_life_treatment": [
            {"name": "Plastic - Landfill", "factor": 32.1, "unit": "tonne", "source": "EPA WARM 2024", "description": "Plastic to landfill", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Waste model", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Plastic - Incineration", "factor": 2754, "unit": "tonne", "source": "EPA WARM 2024", "description": "Plastic incineration", "uncertainty_percentage": 10, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Combustion calculation", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Plastic - Recycling", "factor": -1486, "unit": "tonne", "source": "EPA WARM 2024", "description": "Plastic recycling credit", "uncertainty_percentage": 18, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Avoided emissions", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Paper - Landfill", "factor": 923, "unit": "tonne", "source": "EPA WARM 2024", "description": "Paper to landfill", "uncertainty_percentage": 12, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Waste model", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Electronics - Recycling", "factor": -2341, "unit": "tonne", "source": "EPA WARM 2024", "description": "Electronics recycling credit", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Material recovery", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Metal - Recycling", "factor": -4921, "unit": "tonne", "source": "EPA WARM 2024", "description": "Metal recycling credit", "uncertainty_percentage": 12, "data_quality_score": 2, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Avoided emissions", "lifecycle_stage": "end-of-life", "region": None},
            {"name": "Textiles - Landfill", "factor": 678, "unit": "tonne", "source": "EPA WARM 2024", "description": "Textiles to landfill", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "end_of_life_treatment", "calculation_method": "activity_based", "methodology": "Waste model", "lifecycle_stage": "end-of-life", "region": None},
        ],
        
        # Category 13: Downstream Leased Assets
        "downstream_leased_assets": [
            {"name": "Leased Building Operations", "factor": 53.2, "unit": "m2.year", "source": "CIBSE 2024", "description": "Leased building annual emissions", "uncertainty_percentage": 20, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "downstream_leased_assets", "calculation_method": "activity_based", "methodology": "Building energy model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Leased Equipment Energy", "factor": 0.35, "unit": "hour", "source": "Industry Average 2024", "description": "Leased equipment per hour", "uncertainty_percentage": 30, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "downstream_leased_assets", "calculation_method": "activity_based", "methodology": "Equipment average", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Leased Vehicle Operations", "factor": 4123, "unit": "vehicle.year", "source": "EPA 2024", "description": "Leased vehicle annual emissions", "uncertainty_percentage": 15, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "downstream_leased_assets", "calculation_method": "activity_based", "methodology": "Vehicle use model", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Leased Retail Space", "factor": 89.4, "unit": "m2.year", "source": "CIBSE 2024", "description": "Leased retail space emissions", "uncertainty_percentage": 22, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "downstream_leased_assets", "calculation_method": "activity_based", "methodology": "Building energy model", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 14: Franchises
        "franchises": [
            {"name": "Restaurant Franchise", "factor": 125000, "unit": "location.year", "source": "Restaurant Industry 2024", "description": "Average restaurant franchise annual", "uncertainty_percentage": 25, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "franchises", "calculation_method": "activity_based", "methodology": "Industry survey", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Retail Franchise", "factor": 45000, "unit": "location.year", "source": "Retail Federation 2024", "description": "Average retail franchise annual", "uncertainty_percentage": 30, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "franchises", "calculation_method": "activity_based", "methodology": "Industry survey", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Service Franchise", "factor": 18000, "unit": "location.year", "source": "IFA 2024", "description": "Average service franchise annual", "uncertainty_percentage": 35, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "franchises", "calculation_method": "activity_based", "methodology": "Industry survey", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Hotel Franchise", "factor": 215000, "unit": "location.year", "source": "Hotel Association 2024", "description": "Average hotel franchise", "uncertainty_percentage": 25, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "franchises", "calculation_method": "activity_based", "methodology": "Industry survey", "lifecycle_stage": "use-phase", "region": None},
            {"name": "Franchise Fees (Spend)", "factor": 0.42, "unit": "USD", "source": "EPA EEIO 2024", "description": "Franchise fees spend-based", "uncertainty_percentage": 40, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "franchises", "calculation_method": "spend_based", "methodology": "Input-output analysis", "lifecycle_stage": "use-phase", "region": None},
        ],
        
        # Category 15: Investments
        "investments": [
            {"name": "Listed Equity - Developed", "factor": 0.42, "unit": "thousand_USD", "source": "PCAF 2024", "description": "Listed equity developed markets", "uncertainty_percentage": 30, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "investments", "calculation_method": "spend_based", "methodology": "PCAF methodology", "lifecycle_stage": "operational", "region": None},
            {"name": "Listed Equity - Emerging", "factor": 0.67, "unit": "thousand_USD", "source": "PCAF 2024", "description": "Listed equity emerging markets", "uncertainty_percentage": 35, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "investments", "calculation_method": "spend_based", "methodology": "PCAF methodology", "lifecycle_stage": "operational", "region": None},
            {"name": "Corporate Bonds", "factor": 0.38, "unit": "thousand_USD", "source": "PCAF 2024", "description": "Corporate bonds emissions", "uncertainty_percentage": 28, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "investments", "calculation_method": "spend_based", "methodology": "PCAF methodology", "lifecycle_stage": "operational", "region": None},
            {"name": "Commercial Real Estate", "factor": 125, "unit": "m2.year", "source": "PCAF 2024", "description": "Commercial real estate", "uncertainty_percentage": 25, "data_quality_score": 3, "tier_level": "TIER_2", "scope3_category": "investments", "calculation_method": "activity_based", "methodology": "PCAF methodology", "lifecycle_stage": "operational", "region": None},
            {"name": "Private Equity", "factor": 0.55, "unit": "thousand_USD", "source": "PCAF 2024", "description": "Private equity investments", "uncertainty_percentage": 40, "data_quality_score": 4, "tier_level": "TIER_1", "scope3_category": "investments", "calculation_method": "spend_based", "methodology": "PCAF methodology", "lifecycle_stage": "operational", "region": None},
        ],
    },
}

def seed_emission_factors():
    """Seed the database with emission factors including all compliance metadata"""
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
            scope_num = int(scope.split('_')[1])
            
            for category, factors_list in categories.items():
                for factor_data in factors_list:
                    # Parse dates
                    last_verified = datetime.now()
                    
                    # Create emission factor with all compliance fields
                    factor = EmissionFactor(
                        name=factor_data['name'],
                        category=category,
                        scope=scope_num,
                        factor=factor_data['factor'],
                        unit=factor_data['unit'],
                        source=factor_data.get('source', 'Unknown'),
                        description=factor_data.get('description', ''),
                        is_active=True,
                        valid_from=datetime.now(),
                        # Compliance fields
                        uncertainty_percentage=factor_data.get('uncertainty_percentage'),
                        data_quality_score=factor_data.get('data_quality_score'),
                        tier_level=factor_data.get('tier_level'),
                        scope3_category=factor_data.get('scope3_category'),
                        calculation_method=factor_data.get('calculation_method'),
                        methodology=factor_data.get('methodology'),
                        lifecycle_stage=factor_data.get('lifecycle_stage'),
                        region=factor_data.get('region'),
                        temporal_representativeness="2024 data",
                        geographical_representativeness="Global average" if not factor_data.get('region') else f"Regional - {factor_data['region']}",
                        last_verified=last_verified
                    )
                    db.add(factor)
                    count += 1
        
        db.commit()
        print(f"✅ Successfully seeded {count} emission factors with compliance metadata")
        
        # Print detailed summary
        print_seeding_summary(db)
        
    except Exception as e:
        print(f"❌ Error seeding emission factors: {e}")
        db.rollback()
    finally:
        db.close()

def print_seeding_summary(db: Session):
    """Print detailed summary of seeded emission factors"""
    
    # Overall summary
    for scope in [1, 2, 3]:
        scope_count = db.query(EmissionFactor).filter(EmissionFactor.scope == scope).count()
        print(f"  Scope {scope}: {scope_count} factors")
    
    # Scope 3 detailed summary
    print("\n🎯 Scope 3 Categories Summary (GHG Protocol):")
    scope3_categories = [
        ("purchased_goods_services", "Category 1: Purchased Goods and Services"),
        ("capital_goods", "Category 2: Capital Goods"),
        ("fuel_energy_activities", "Category 3: Fuel- and Energy-Related Activities"),
        ("upstream_transportation", "Category 4: Upstream Transportation and Distribution"),
        ("waste_operations", "Category 5: Waste Generated in Operations"),
        ("business_travel", "Category 6: Business Travel"),
        ("employee_commuting", "Category 7: Employee Commuting"),
        ("upstream_leased_assets", "Category 8: Upstream Leased Assets"),
        ("downstream_transportation", "Category 9: Downstream Transportation and Distribution"),
        ("processing_sold_products", "Category 10: Processing of Sold Products"),
        ("use_of_sold_products", "Category 11: Use of Sold Products"),
        ("end_of_life_treatment", "Category 12: End-of-Life Treatment of Sold Products"),
        ("downstream_leased_assets", "Category 13: Downstream Leased Assets"),
        ("franchises", "Category 14: Franchises"),
        ("investments", "Category 15: Investments")
    ]
    
    for cat_key, cat_name in scope3_categories:
        # Count factors by calculation method
        spend_count = db.query(EmissionFactor).filter(
            EmissionFactor.scope3_category == cat_key,
            EmissionFactor.calculation_method == "spend_based"
        ).count()
        activity_count = db.query(EmissionFactor).filter(
            EmissionFactor.scope3_category == cat_key,
            EmissionFactor.calculation_method == "activity_based"
        ).count()
        total_count = spend_count + activity_count
        
        if total_count > 0:
            print(f"  {cat_name}")
            print(f"    ✅ Total: {total_count} factors")
            if spend_count > 0:
                print(f"       - Spend-based: {spend_count}")
            if activity_count > 0:
                print(f"       - Activity-based: {activity_count}")
        else:
            print(f"  {cat_name}")
            print(f"    ❌ No factors found")
    
    # Data quality summary
    print("\n📊 Data Quality Summary:")
    quality_counts = db.query(
        EmissionFactor.data_quality_score,
        func.count(EmissionFactor.id)
    ).filter(
        EmissionFactor.data_quality_score.isnot(None)
    ).group_by(
        EmissionFactor.data_quality_score
    ).all()
    
    quality_labels = {1: "Excellent", 2: "Good", 3: "Fair", 4: "Poor", 5: "Very Poor"}
    for score, count in sorted(quality_counts):
        print(f"  Score {score} ({quality_labels.get(score, 'Unknown')}): {count} factors")
    
    # Tier level summary
    print("\n📈 Tier Level Summary:")
    tier_counts = db.query(
        EmissionFactor.tier_level,
        func.count(EmissionFactor.id)
    ).filter(
        EmissionFactor.tier_level.isnot(None)
    ).group_by(
        EmissionFactor.tier_level
    ).all()
    
    for tier, count in sorted(tier_counts):
        print(f"  {tier}: {count} factors")

if __name__ == "__main__":
    print("🌱 Seeding comprehensive emission factors with all 15 Scope 3 categories...")
    print("   Including full compliance metadata (data quality, uncertainty, tiers)")
    seed_emission_factors()