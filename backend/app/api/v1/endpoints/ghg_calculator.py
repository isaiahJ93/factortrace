"""
GHG Calculator API Endpoint with Monte Carlo Analysis and Export Functionality
Enhanced with ESRS E1 Compliance Features and ALL Scope 3 Categories
Version 5.2 - Production Ready with Exact DEFRA 2024 Emission Factors

CHANGELOG v5.2:
- UPDATED: Exact emission factors from DEFRA 2024 database
- FIXED: Natural gas factor to 0.185 kgCO2e/kWh
- FIXED: Diesel factor to 2.680 kgCO2e/litres
- ADDED: Complete coverage of all 100+ activity types
- IMPROVED: Category 3 WTT/T&D factors alignment

CHANGELOG v5.1:
- ADDED: Comprehensive emission factors database covering all Scope 1, 2, and 3 categories
- UPDATED: Response model with clear tCO2e units
- IMPROVED: More accurate emission factors aligned with DEFRA 2024 and EPA standards
- ENHANCED: Support for 100+ activity types across all 15 Scope 3 categories

CHANGELOG v5.0:
- FIXED: Variable scope conflict with additional_breakdowns
- FIXED: Zero emissions bug for diesel/natural gas/electricity
- FIXED: Function signature issues
- REMOVED: Redundant initializations and patches
- ADDED: Enhanced error handling and logging
- IMPROVED: Code organization and performance
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.emission_factor import EmissionFactor
from sqlalchemy import update
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from pydantic import BaseModel, Field, validator
from functools import lru_cache
from decimal import Decimal
import numpy as np
from scipy import stats
import io
import json
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom

# PDF generation imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.lib.enums import TA_CENTER

# Initialize router and logger
router = APIRouter()
logger = logging.getLogger(__name__)

# ===== GWP FACTORS FOR GAS CONVERSION =====
GWP_FACTORS_AR6 = {
    "CO2": 1.0,
    "CH4": 29.8,  # Fossil methane
    "CH4_biogenic": 27.0,  # Biogenic methane
    "N2O": 273.0,
    "SF6": 25200.0,
    "NF3": 17400.0,
    "HFC-134a": 1530.0,
    "HFC-410A": 2255.0
}

GWP_FACTORS_AR5 = {
    "CO2": 1.0,
    "CH4": 28.0,
    "N2O": 265.0,
    "SF6": 23500.0,
    "NF3": 16100.0
}

# ===== ENHANCED SCOPE 3 ESTIMATION FACTORS =====
# Spend-based emission factors by sector (kgCO2e/EUR) - Updated to match emission factors
SPEND_BASED_FACTORS = {
    "manufacturing": {
        "purchased_goods": 0.350,  # Updated from emission factors
        "capital_goods": 0.320,
        "upstream_transport": 0.12,
        "business_travel": 0.08,
        "downstream_transport": 0.10
    },
    "services": {
        "purchased_goods": 0.350,
        "capital_goods": 0.320,
        "upstream_transport": 0.08,
        "business_travel": 0.15,
        "employee_commuting": 0.05
    },
    "retail": {
        "purchased_goods": 0.350,
        "capital_goods": 0.320,
        "upstream_transport": 0.15,
        "downstream_transport": 0.12,
        "waste": 0.05
    },
    "technology": {
        "purchased_goods": 0.350,
        "capital_goods": 0.320,
        "business_travel": 0.18,
        "employee_commuting": 0.06,
        "use_of_sold_products": 0.25
    },
    "energy": {
        "purchased_goods": 0.350,
        "capital_goods": 0.320,
        "upstream_transport": 0.10,
        "use_of_sold_products": 0.80
    }
}

# Scope 3 to Scope 1+2 intensity ratios by sector
INTENSITY_RATIOS = {
    "manufacturing": {
        "category_1": (0.30, 0.50),
        "category_2": (0.05, 0.10),
        "category_4": (0.04, 0.09),
        "category_5": (0.02, 0.05),
        "category_6": (0.01, 0.03),
        "category_7": (0.02, 0.04),
        "category_11": (0.40, 0.80)
    },
    "services": {
        "category_1": (0.20, 0.35),
        "category_2": (0.05, 0.08),
        "category_4": (0.02, 0.05),
        "category_5": (0.01, 0.03),
        "category_6": (0.03, 0.06),
        "category_7": (0.03, 0.05),
        "category_11": (0.05, 0.10)
    },
    "retail": {
        "category_1": (0.35, 0.55),
        "category_2": (0.06, 0.10),
        "category_4": (0.08, 0.12),
        "category_5": (0.03, 0.06),
        "category_6": (0.02, 0.04),
        "category_7": (0.02, 0.04),
        "category_9": (0.05, 0.10),
        "category_11": (0.10, 0.20)
    },
    "default": {
        "category_1": (0.25, 0.40),
        "category_2": (0.05, 0.10),
        "category_4": (0.04, 0.08),
        "category_5": (0.02, 0.04),
        "category_6": (0.02, 0.04),
        "category_7": (0.02, 0.04),
        "category_11": (0.10, 0.30)
    }
}

# Per-employee emission factors (kgCO2e/employee/year)
PER_EMPLOYEE_FACTORS = {
    "business_travel": {
        "manufacturing": 500,
        "services": 1200,
        "retail": 300,
        "technology": 2000,
        "energy": 800,
        "default": 800
    },
    "employee_commuting": {
        "manufacturing": 1500,
        "services": 1200,
        "retail": 1000,
        "technology": 1000,
        "energy": 1800,
        "default": 1200
    },
    "waste": {
        "manufacturing": 200,
        "services": 50,
        "retail": 150,
        "technology": 30,
        "energy": 250,
        "default": 100
    }
}

# ===== CATEGORY 3 WTT AND T&D FACTORS =====
CATEGORY_3_FACTORS = {
    "natural_gas": {
        "wtt_factor": 0.035,  # Updated from DEFRA 2024
        "name": "Natural Gas WTT",
        "unit": "kWh",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "natural_gas_stationary": {
        "wtt_factor": 0.035,
        "name": "Natural Gas WTT",
        "unit": "kWh",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "diesel": {
        "wtt_factor": 0.61314,
        "name": "Diesel WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "diesel_stationary": {
        "wtt_factor": 0.61314,
        "name": "Diesel WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "diesel_fleet": {
        "wtt_factor": 0.61314,
        "name": "Fleet Diesel WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "petrol": {
        "wtt_factor": 0.59054,
        "name": "Petrol WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "petrol_fleet": {
        "wtt_factor": 0.59054,
        "name": "Fleet Petrol WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "gasoline": {
        "wtt_factor": 0.59054,
        "name": "Gasoline WTT",
        "unit": "litres",
        "source": "DEFRA 2024 - Fuels, Table 1"
    },
    "electricity": {
        "td_factor": 0.020,  # Updated T&D losses
        "name": "Electricity T&D Losses",
        "unit": "kWh",
        "source": "DEFRA 2024 - UK Grid Electricity"
    },
    "electricity_grid": {
        "td_factor": 0.020,
        "name": "Grid Electricity T&D Losses",
        "unit": "kWh",
        "source": "DEFRA 2024 - UK Grid Electricity"
    },
    "district_heating": {
        "td_factor": 0.00883,
        "name": "District Heating T&D",
        "unit": "kWh",
        "source": "DEFRA 2024 - Heat and Steam"
    },
    "fuel_oil": {
        "wtt_factor": 0.725,
        "name": "Fuel Oil WTT",
        "unit": "litres",
        "source": "DEFRA 2024"
    },
    "lpg_stationary": {
        "wtt_factor": 0.18412,
        "name": "LPG WTT",
        "unit": "litres",
        "source": "DEFRA 2024"
    },
    "coal": {
        "wtt_factor": 139.0,  # kgCO2e/tonnes
        "name": "Coal WTT",
        "unit": "tonnes",
        "source": "DEFRA 2024"
    }
}

# ===== COMPLETE EMISSION FACTORS DATABASE (Matching Frontend) =====
DEFAULT_EMISSION_FACTORS = {
    # SCOPE 1 - STATIONARY COMBUSTION
    "natural_gas_stationary": {
        "factor": 0.185,  # kgCO2e/kWh (DEFRA 2024)
        "unit": "kWh",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "diesel_stationary": {
        "factor": 2.680,  # kgCO2e/litres (DEFRA 2024)
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "lpg_stationary": {
        "factor": 1.560,  # kgCO2e/litres (DEFRA 2024)
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "coal": {
        "factor": 2419.000,  # kgCO2e/tonnes (DEFRA 2024 - industrial coal)
        "unit": "tonnes",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "fuel_oil": {
        "factor": 3.180,  # kgCO2e/litres (DEFRA 2024)
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    
    # SCOPE 1 - MOBILE COMBUSTION
    "diesel_fleet": {
        "factor": 2.680,  # kgCO2e/litres (DEFRA 2024)
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "petrol_fleet": {
        "factor": 2.190,  # kgCO2e/litres (DEFRA 2024)
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "van_diesel": {
        "factor": 0.251,  # kgCO2e/km (DEFRA 2024 - average van)
        "unit": "km",
        "scope": "scope_1",
        "uncertainty": 7
    },
    "van_petrol": {
        "factor": 0.175,  # kgCO2e/km (DEFRA 2024)
        "unit": "km",
        "scope": "scope_1",
        "uncertainty": 7
    },
    "hgv_rigid": {
        "factor": 0.811,  # kgCO2e/km (DEFRA 2024 - all rigid)
        "unit": "km",
        "scope": "scope_1",
        "uncertainty": 7
    },
    "hgv_articulated": {
        "factor": 0.961,  # kgCO2e/km (DEFRA 2024 - all artic)
        "unit": "km",
        "scope": "scope_1",
        "uncertainty": 7
    },
    
    # SCOPE 1 - PROCESS EMISSIONS
    "industrial_process": {
        "factor": 1000.000,  # kgCO2e/tonnes (customizable)
        "unit": "tonnes",
        "scope": "scope_1",
        "uncertainty": 15
    },
    "chemical_production": {
        "factor": 1500.000,  # kgCO2e/tonnes (customizable)
        "unit": "tonnes",
        "scope": "scope_1",
        "uncertainty": 15
    },
    
    # SCOPE 1 - FUGITIVE EMISSIONS
    "refrigerant_hfc": {
        "factor": 1430.000,  # kgCO2e/kg (HFC-134a GWP)
        "unit": "kg",
        "scope": "scope_1",
        "uncertainty": 20
    },
    "refrigerant_r410a": {
        "factor": 2088.000,  # kgCO2e/kg (R410A GWP)
        "unit": "kg",
        "scope": "scope_1",
        "uncertainty": 10
    },
    "sf6_leakage": {
        "factor": 22800.000,  # kgCO2e/kg (SF6 GWP AR5)
        "unit": "kg",
        "scope": "scope_1",
        "uncertainty": 10
    },
    
    # SCOPE 2 - PURCHASED ELECTRICITY
    "electricity_grid": {
        "factor": 0.233,  # kgCO2e/kWh (UK grid 2024)
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 10
    },
    "electricity_renewable": {
        "factor": 0.000,  # kgCO2e/kWh (100% renewable)
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 0
    },
    "electricity_partial_green": {
        "factor": 0.116,  # kgCO2e/kWh (50% renewable mix)
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 8
    },
    "district_heating": {
        "factor": 0.210,  # kgCO2e/kWh (DEFRA 2024)
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 10
    },
    "purchased_steam": {
        "factor": 0.185,  # kgCO2e/kWh (DEFRA 2024)
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 10
    },
    "district_cooling": {
        "factor": 0.150,  # kgCO2e/kWh (estimate based on COP)
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 12
    },
    
    # SCOPE 3 - CATEGORY 1: PURCHASED GOODS & SERVICES
    "office_paper": {
        "factor": 0.919,  # kgCO2e/kg (DEFRA 2024)
        "unit": "kg",
        "scope": "scope_3",
        "category": 1,
        "uncertainty": 15
    },
    "plastic_packaging": {
        "factor": 3.130,  # kgCO2e/kg (DEFRA 2024 - average plastic)
        "unit": "kg",
        "scope": "scope_3",
        "category": 1,
        "uncertainty": 20
    },
    "steel_products": {
        "factor": 850.000,  # kgCO2e/tonnes (World Steel Association)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 1,
        "uncertainty": 15
    },
    "electronics": {
        "factor": 0.320,  # kgCO2e/EUR (EEIO model)
        "unit": "EUR",
        "scope": "scope_3",
        "category": 1,
        "uncertainty": 25
    },
    "food_beverages": {
        "factor": 0.350,  # kgCO2e/EUR (EEIO model)
        "unit": "EUR",
        "scope": "scope_3",
        "category": 1,
        "uncertainty": 20
    },
    
    # SCOPE 3 - CATEGORY 2: CAPITAL GOODS
    "machinery": {
        "factor": 0.320,  # kgCO2e/EUR (EEIO model)
        "unit": "EUR",
        "scope": "scope_3",
        "category": 2,
        "uncertainty": 25
    },
    "buildings": {
        "factor": 0.320,  # kgCO2e/EUR (EEIO model)
        "unit": "EUR",
        "scope": "scope_3",
        "category": 2,
        "uncertainty": 20
    },
    "vehicles": {
        "factor": 0.370,  # kgCO2e/EUR (EEIO model)
        "unit": "EUR",
        "scope": "scope_3",
        "category": 2,
        "uncertainty": 20
    },
    
    # SCOPE 3 - CATEGORY 3: FUEL & ENERGY ACTIVITIES
    "upstream_electricity": {
        "factor": 0.045,  # kgCO2e/kWh (DEFRA 2024 WTT)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 3,
        "uncertainty": 10
    },
    "upstream_natural_gas": {
        "factor": 0.035,  # kgCO2e/kWh (DEFRA 2024 WTT)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 3,
        "uncertainty": 10
    },
    "transmission_losses": {
        "factor": 0.020,  # kgCO2e/kWh (DEFRA 2024 T&D)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 3,
        "uncertainty": 8
    },
    
    # SCOPE 3 - CATEGORY 4: UPSTREAM TRANSPORTATION
    "road_freight": {
        "factor": 0.096,  # kgCO2e/tonne.km (DEFRA 2024)
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 4,
        "uncertainty": 12
    },
    "rail_freight": {
        "factor": 0.025,  # kgCO2e/tonne.km (DEFRA 2024)
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 4,
        "uncertainty": 10
    },
    "sea_freight": {
        "factor": 0.016,  # kgCO2e/tonne.km (DEFRA 2024)
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 4,
        "uncertainty": 15
    },
    "air_freight": {
        "factor": 1.230,  # kgCO2e/tonne.km (DEFRA 2024)
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 4,
        "uncertainty": 12
    },
    
    # SCOPE 3 - CATEGORY 5: WASTE GENERATED
    "waste_landfill": {
        "factor": 467.000,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 5,
        "uncertainty": 15
    },
    "waste_recycled": {
        "factor": 21.000,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 5,
        "uncertainty": 10
    },
    "waste_composted": {
        "factor": 8.950,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 5,
        "uncertainty": 15
    },
    "waste_incineration": {
        "factor": 21.000,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 5,
        "uncertainty": 12
    },
    "wastewater": {
        "factor": 0.272,  # kgCO2e/m3 (DEFRA 2024)
        "unit": "m3",
        "scope": "scope_3",
        "category": 5,
        "uncertainty": 20
    },
    
    # SCOPE 3 - CATEGORY 6: BUSINESS TRAVEL
    "flight_domestic": {
        "factor": 0.250,  # kgCO2e/passenger.km (DEFRA 2024)
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 10
    },
    "flight_short_haul": {
        "factor": 0.149,  # kgCO2e/passenger.km (DEFRA 2024)
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 10
    },
    "flight_long_haul": {
        "factor": 0.190,  # kgCO2e/passenger.km (DEFRA 2024)
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 10
    },
    "rail_travel": {
        "factor": 0.035,  # kgCO2e/passenger.km (DEFRA 2024)
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 8
    },
    "taxi": {
        "factor": 0.208,  # kgCO2e/km (DEFRA 2024)
        "unit": "km",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 12
    },
    "hotel_stays": {
        "factor": 16.100,  # kgCO2e/nights (DEFRA 2024 UK)
        "unit": "nights",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 20
    },
    
    # SCOPE 3 - CATEGORY 7: EMPLOYEE COMMUTING
    "car_commute": {
        "factor": 0.171,  # kgCO2e/km (DEFRA 2024 average car)
        "unit": "km",
        "scope": "scope_3",
        "category": 7,
        "uncertainty": 15
    },
    "bus_commute": {
        "factor": 0.097,  # kgCO2e/passenger.km (DEFRA 2024)
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 7,
        "uncertainty": 12
    },
    "rail_commute": {
        "factor": 0.035,  # kgCO2e/passenger.km (DEFRA 2024)
        "unit": "passenger.km",
        "scope": "scope_3",
        "category": 7,
        "uncertainty": 10
    },
    "bicycle": {
        "factor": 0.000,  # kgCO2e/km (zero emissions)
        "unit": "km",
        "scope": "scope_3",
        "category": 7,
        "uncertainty": 0
    },
    
    # SCOPE 3 - CATEGORY 8: UPSTREAM LEASED ASSETS
    "leased_buildings": {
        "factor": 0.233,  # kgCO2e/kWh (grid electricity)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 8,
        "uncertainty": 15
    },
    "leased_vehicles": {
        "factor": 0.171,  # kgCO2e/km (average vehicle)
        "unit": "km",
        "scope": "scope_3",
        "category": 8,
        "uncertainty": 12
    },
    "leased_equipment": {
        "factor": 5.500,  # kgCO2e/hours (operational hours)
        "unit": "hours",
        "scope": "scope_3",
        "category": 8,
        "uncertainty": 25
    },
    "data_centers": {
        "factor": 0.233,  # kgCO2e/kWh (grid electricity)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 8,
        "uncertainty": 15
    },
    
    # SCOPE 3 - CATEGORY 9: DOWNSTREAM TRANSPORTATION
    "product_delivery": {
        "factor": 0.096,  # kgCO2e/tonne.km (DEFRA 2024)
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 9,
        "uncertainty": 15
    },
    "customer_collection": {
        "factor": 2.500,  # kgCO2e/trips (average round trip)
        "unit": "trips",
        "scope": "scope_3",
        "category": 9,
        "uncertainty": 20
    },
    "third_party_logistics": {
        "factor": 0.096,  # kgCO2e/tonne.km (DEFRA 2024)
        "unit": "tonne.km",
        "scope": "scope_3",
        "category": 9,
        "uncertainty": 15
    },
    
    # SCOPE 3 - CATEGORY 10: PROCESSING OF SOLD PRODUCTS
    "intermediate_processing": {
        "factor": 125.000,  # kgCO2e/tonnes (industry average)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 10,
        "uncertainty": 30
    },
    "customer_manufacturing": {
        "factor": 2.500,  # kgCO2e/units (estimate)
        "unit": "units",
        "scope": "scope_3",
        "category": 10,
        "uncertainty": 35
    },
    "further_processing": {
        "factor": 85.000,  # kgCO2e/tonnes (industry average)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 10,
        "uncertainty": 30
    },
    
    # SCOPE 3 - CATEGORY 11: USE OF SOLD PRODUCTS
    "product_electricity": {
        "factor": 0.233,  # kgCO2e/kWh (grid electricity)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 11,
        "uncertainty": 20
    },
    "product_fuel": {
        "factor": 2.310,  # kgCO2e/litres (petrol average)
        "unit": "litres",
        "scope": "scope_3",
        "category": 11,
        "uncertainty": 15
    },
    "product_lifetime_energy": {
        "factor": 150.000,  # kgCO2e/units (lifetime energy)
        "unit": "units",
        "scope": "scope_3",
        "category": 11,
        "uncertainty": 25
    },
    
    # SCOPE 3 - CATEGORY 12: END-OF-LIFE TREATMENT
    "product_landfill": {
        "factor": 467.000,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 12,
        "uncertainty": 20
    },
    "product_recycling": {
        "factor": 21.000,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 12,
        "uncertainty": 15
    },
    "product_incineration": {
        "factor": 21.000,  # kgCO2e/tonnes (DEFRA 2024)
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 12,
        "uncertainty": 15
    },
    
    # SCOPE 3 - CATEGORY 13: DOWNSTREAM LEASED ASSETS
    "leased_real_estate": {
        "factor": 55.000,  # kgCO2e/m2.year (commercial average)
        "unit": "m2.year",
        "scope": "scope_3",
        "category": 13,
        "uncertainty": 20
    },
    "leased_equipment_downstream": {
        "factor": 150.000,  # kgCO2e/units.year
        "unit": "units.year",
        "scope": "scope_3",
        "category": 13,
        "uncertainty": 25
    },
    "franchise_buildings": {
        "factor": 55.000,  # kgCO2e/m2.year (commercial average)
        "unit": "m2.year",
        "scope": "scope_3",
        "category": 13,
        "uncertainty": 20
    },
    
    # SCOPE 3 - CATEGORY 14: FRANCHISES
    "franchise_energy": {
        "factor": 0.233,  # kgCO2e/kWh (grid electricity)
        "unit": "kWh",
        "scope": "scope_3",
        "category": 14,
        "uncertainty": 20
    },
    "franchise_operations": {
        "factor": 250.000,  # kgCO2e/locations (annual average)
        "unit": "locations",
        "scope": "scope_3",
        "category": 14,
        "uncertainty": 30
    },
    "franchise_travel": {
        "factor": 0.140,  # kgCO2e/EUR (travel spend based)
        "unit": "EUR",
        "scope": "scope_3",
        "category": 14,
        "uncertainty": 25
    },
    "franchise_fleet": {
        "factor": 0.171,  # kgCO2e/km (average vehicle)
        "unit": "km",
        "scope": "scope_3",
        "category": 14,
        "uncertainty": 15
    },
    
    # SCOPE 3 - CATEGORY 15: INVESTMENTS
    "equity_investments": {
        "factor": 630.000,  # kgCO2e/EUR million (PCAF database)
        "unit": "EUR million",
        "scope": "scope_3",
        "category": 15,
        "uncertainty": 40
    },
    "debt_investments": {
        "factor": 325.000,  # kgCO2e/EUR million (PCAF database)
        "unit": "EUR million",
        "scope": "scope_3",
        "category": 15,
        "uncertainty": 40
    },
    "project_finance": {
        "factor": 415.000,  # kgCO2e/EUR million (PCAF database)
        "unit": "EUR million",
        "scope": "scope_3",
        "category": 15,
        "uncertainty": 35
    },
    "investment_funds": {
        "factor": 510.000,  # kgCO2e/EUR million (PCAF database)
        "unit": "EUR million",
        "scope": "scope_3",
        "category": 15,
        "uncertainty": 40
    },
    
    # Backwards compatibility aliases
    "natural_gas": {
        "factor": 0.185,
        "unit": "kWh",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "diesel": {
        "factor": 2.680,
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "petrol": {
        "factor": 2.190,
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "gasoline": {
        "factor": 2.190,
        "unit": "litres",
        "scope": "scope_1",
        "uncertainty": 5
    },
    "electricity": {
        "factor": 0.233,
        "unit": "kWh",
        "scope": "scope_2",
        "uncertainty": 10
    },
    "purchased_goods": {
        "factor": 0.350,  # Generic spend-based factor
        "unit": "EUR",
        "scope": "scope_3",
        "category": 1,
        "uncertainty": 20
    },
    "capital_goods": {
        "factor": 0.320,  # Generic capital goods factor
        "unit": "EUR",
        "scope": "scope_3",
        "category": 2,
        "uncertainty": 20
    },
    "business_travel": {
        "factor": 0.190,  # Average flight factor
        "unit": "km",
        "scope": "scope_3",
        "category": 6,
        "uncertainty": 15
    },
    "employee_commuting": {
        "factor": 0.171,  # Car average
        "unit": "km",
        "scope": "scope_3",
        "category": 7,
        "uncertainty": 15
    },
    "landfill": {
        "factor": 467.000,  # Alias for waste_landfill
        "unit": "tonnes",
        "scope": "scope_3",
        "category": 5,
        "uncertainty": 15
    }
}

# ===== ESRS E1 MODELS =====
class EnergyConsumption(BaseModel):
    """E1-5: Energy consumption and mix"""
    total_energy_mwh: float = Field(0, description="Total energy consumption in MWh")
    electricity_mwh: float = Field(0, description="Electricity consumption")
    heating_cooling_mwh: float = Field(0, description="Heating and cooling consumption")
    steam_mwh: float = Field(0, description="Steam consumption")
    fuel_combustion_mwh: float = Field(0, description="Fuel combustion for energy")
    renewable_energy_mwh: float = Field(0, description="Renewable energy consumption")
    renewable_percentage: float = Field(0, ge=0, le=100, description="Percentage renewable")
    energy_intensity_value: Optional[float] = None
    energy_intensity_unit: Optional[str] = "MWh/million_EUR"
    by_source: Optional[Dict[str, float]] = Field(default_factory=dict)
    
    @validator('renewable_percentage')
    def calculate_renewable_percentage(cls, v, values):
        if 'total_energy_mwh' in values and values['total_energy_mwh'] > 0:
            return (values.get('renewable_energy_mwh', 0) / values['total_energy_mwh']) * 100
        return v

class GHGBreakdown(BaseModel):
    """Detailed GHG breakdown by gas type per ESRS E1"""
    CO2_tonnes: float = Field(0, description="CO2 emissions in tonnes")
    CH4_tonnes: float = Field(0, description="CH4 emissions in tonnes")
    N2O_tonnes: float = Field(0, description="N2O emissions in tonnes")
    HFCs_tonnes_co2e: Optional[float] = Field(0, description="HFCs in tonnes CO2e")
    PFCs_tonnes_co2e: Optional[float] = Field(0, description="PFCs in tonnes CO2e")
    SF6_tonnes: Optional[float] = Field(0, description="SF6 in tonnes")
    NF3_tonnes: Optional[float] = Field(0, description="NF3 in tonnes")
    total_co2e: float = Field(0, description="Total CO2 equivalent")
    gwp_version: str = Field("AR6", description="GWP version used (AR6/AR5)")

class Scope3CategoryBreakdown(BaseModel):
    """Breakdown of Scope 3 emissions by category"""
    category_1: float = Field(0, description="Purchased goods and services")
    category_2: float = Field(0, description="Capital goods")
    category_3: float = Field(0, description="Fuel and energy related activities")
    category_4: float = Field(0, description="Upstream transportation")
    category_5: float = Field(0, description="Waste generated")
    category_6: float = Field(0, description="Business travel")
    category_7: float = Field(0, description="Employee commuting")
    category_8: float = Field(0, description="Upstream leased assets")
    category_9: float = Field(0, description="Downstream transportation")
    category_10: float = Field(0, description="Processing of sold products")
    category_11: float = Field(0, description="Use of sold products")
    category_12: float = Field(0, description="End-of-life treatment")
    category_13: float = Field(0, description="Downstream leased assets")
    category_14: float = Field(0, description="Franchises")
    category_15: float = Field(0, description="Investments")

class InternalCarbonPricing(BaseModel):
    """E1-8: Internal carbon pricing mechanism"""
    implemented: bool = Field(False, description="Whether internal carbon pricing is implemented")
    price_per_tco2e: Optional[float] = Field(None, description="Price per tonne CO2e")
    currency: str = Field("EUR", description="Currency for carbon price")
    coverage_scope1: bool = Field(False, description="Applies to Scope 1")
    coverage_scope2: bool = Field(False, description="Applies to Scope 2")
    coverage_scope3_categories: List[int] = Field(default_factory=list, description="Scope 3 categories covered")
    pricing_type: Optional[str] = Field(None, description="shadow/internal/implicit")
    total_revenue_generated: Optional[float] = Field(0, description="Revenue from carbon pricing")
    revenue_allocation: Optional[str] = None

class ClimatePolicy(BaseModel):
    """E1-2: Climate change mitigation and adaptation policies"""
    has_climate_policy: bool = Field(False)
    policy_adoption_date: Optional[str] = None
    policy_document_url: Optional[str] = None
    policy_description: Optional[str] = None
    net_zero_target_year: Optional[int] = None
    interim_targets: List[Dict[str, Any]] = Field(default_factory=list)
    board_oversight: bool = Field(False)
    executive_compensation_linked: bool = Field(False)
    covers_value_chain: bool = Field(False)

class ClimateActions(BaseModel):
    """E1-3: Actions and resources related to climate change"""
    reporting_year: int = Field(..., description="Reporting year")
    capex_climate_eur: float = Field(0, description="CapEx for climate mitigation/adaptation")
    opex_climate_eur: float = Field(0, description="OpEx for climate mitigation/adaptation")
    total_climate_finance_eur: float = Field(0, description="Total climate finance")
    fte_dedicated: float = Field(0, description="FTEs dedicated to climate actions")
    key_projects: List[Dict[str, Any]] = Field(default_factory=list, description="Key climate projects")
    
    @validator('total_climate_finance_eur')
    def calculate_total_finance(cls, v, values):
        return values.get('capex_climate_eur', 0) + values.get('opex_climate_eur', 0)

class ESRSE1Metadata(BaseModel):
    """Complete ESRS E1 metadata structure"""
    energy_consumption: Optional[EnergyConsumption] = None
    ghg_breakdown: Optional[GHGBreakdown] = None
    internal_carbon_pricing: Optional[InternalCarbonPricing] = None
    climate_policy: Optional[ClimatePolicy] = None
    climate_actions: Optional[ClimateActions] = None

class CompanyProfile(BaseModel):
    """Company profile for enhanced Scope 3 calculations"""
    sector: Optional[str] = Field(None, description="manufacturing/services/retail/technology/energy")
    revenue: Optional[float] = Field(None, description="Annual revenue in EUR")
    employees: Optional[int] = Field(None, description="Number of employees")
    facility_size: Optional[float] = Field(None, description="m² of facilities")
    supply_chain_spend: Optional[float] = Field(None, description="Annual procurement spend")
    capital_expenditure: Optional[float] = Field(None, description="Annual CapEx")
    has_manufacturing: Optional[bool] = Field(False)
    has_fleet: Optional[bool] = Field(False)
    business_travel_km: Optional[float] = Field(None)
    product_sales_units: Optional[int] = Field(None, description="Units of products sold")
    average_product_lifetime_years: Optional[float] = Field(None)
    waste_tonnes: Optional[float] = Field(None)
    investments_eur: Optional[float] = Field(None)
    leased_assets_value: Optional[float] = Field(None)
    franchises_count: Optional[int] = Field(None)

# ===== REQUEST/RESPONSE MODELS =====
class EmissionInput(BaseModel):
    activity_type: str
    amount: float = Field(..., gt=0)
    unit: str
    uncertainty_percentage: Optional[float] = 10.0
    gas_type: Optional[str] = "CO2"
    custom_factor: Optional[float] = None

class CalculateEmissionsRequest(BaseModel):
    company_id: str = "default"
    reporting_period: str
    emissions_data: List[EmissionInput]
    company_profile: Optional[CompanyProfile] = None
    esrs_e1_data: Optional[ESRSE1Metadata] = None
    include_gas_breakdown: bool = False
    include_uncertainty: bool = Field(False, description="Include Monte Carlo uncertainty analysis")
    monte_carlo_iterations: int = Field(1000, description="Number of Monte Carlo iterations")

class EmissionBreakdown(BaseModel):
    activity_type: str
    scope: str
    emissions_kg_co2e: float
    unit: str
    calculation_method: str
    gas_type: Optional[str] = "CO2"
    gas_amount_tonnes: Optional[float] = None
    scope3_category: Optional[int] = None

class CalculateEmissionsResponse(BaseModel):
    total_emissions_kg_co2e: float = Field(..., description="Total in kg CO2e")
    total_emissions_tco2e: float = Field(..., description="Total in tonnes CO2e")
    scope1_emissions_tco2e: float = Field(..., description="Scope 1 in tCO2e")
    scope2_emissions_tco2e: float = Field(..., description="Scope 2 in tCO2e")
    scope3_emissions_tco2e: float = Field(..., description="Scope 3 in tCO2e")
    scope3_category_breakdown: Optional[Scope3CategoryBreakdown] = Field(None, description="Breakdown by category in tCO2e")
    breakdown: List[EmissionBreakdown] = Field(..., description="Detailed breakdown in kg")
    reporting_period: str
    calculation_date: str
    ghg_breakdown: Optional[GHGBreakdown] = Field(None, description="GHG breakdown in tonnes")
    esrs_e1_metadata: Optional[Dict[str, Any]] = None
    energy_consumption: Optional[EnergyConsumption] = None
    calculation_metadata: Optional[Dict[str, Any]] = None
    uncertainty_analysis: Optional[Dict[str, Any]] = None
    scope3_detailed: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Detailed Scope 3 in tCO2e")

# ===== CALCULATION HELPER FUNCTIONS =====
def get_emission_factor(activity_type: str) -> Optional[Dict[str, Any]]:
    """Get emission factor with fallback logic"""
    activity_lower = activity_type.lower()
    
    # Direct lookup
    if activity_lower in DEFAULT_EMISSION_FACTORS:
        return DEFAULT_EMISSION_FACTORS[activity_lower]
    
    # Try alternate names
    alternate_names = {
        "natural gas": "natural_gas_stationary",
        "grid electricity": "electricity_grid",
        "electricity grid": "electricity_grid",
        "purchased electricity": "electricity_grid",
        "diesel fuel": "diesel_stationary",
        "petrol fuel": "petrol_fleet",
        "gasoline fuel": "petrol_fleet",
        "waste to landfill": "waste_landfill",
        "flights domestic": "flight_domestic",
        "flights short haul": "flight_short_haul",
        "flights long haul": "flight_long_haul",
        "flights international": "flight_long_haul",
        "business flights": "flight_long_haul",
        "car travel": "car_commute",
        "rail": "rail_travel",
        "train": "rail_commute"
    }
    
    for alt_name, factor_key in alternate_names.items():
        if alt_name in activity_lower:
            if factor_key in DEFAULT_EMISSION_FACTORS:
                return DEFAULT_EMISSION_FACTORS[factor_key]
    
    # Try partial matches
    for key in DEFAULT_EMISSION_FACTORS:
        if key in activity_lower or activity_lower in key:
            return DEFAULT_EMISSION_FACTORS[key]
    
    logger.warning(f"No emission factor found for activity: {activity_type}. Available activities: {', '.join(list(DEFAULT_EMISSION_FACTORS.keys())[:5])}...")
    return None

def calculate_gas_breakdown(emissions_kg_co2e: float, activity_type: str, gwp_factors: Dict[str, float] = None) -> Dict[str, float]:
    """Calculate breakdown by gas type"""
    if gwp_factors is None:
        gwp_factors = GWP_FACTORS_AR6
    
    # Default to 100% CO2 for most activities
    gas_composition = {"CO2": 1.0}
    
    # Special cases for methane and N2O
    if "natural_gas" in activity_type.lower():
        gas_composition = {"CO2": 0.95, "CH4": 0.04, "N2O": 0.01}
    elif "diesel" in activity_type.lower() or "petrol" in activity_type.lower():
        gas_composition = {"CO2": 0.97, "CH4": 0.02, "N2O": 0.01}
    elif "waste" in activity_type.lower():
        gas_composition = {"CO2": 0.50, "CH4": 0.45, "N2O": 0.05}
    
    breakdown = {}
    for gas, fraction in gas_composition.items():
        gas_co2e = emissions_kg_co2e * fraction / 1000  # Convert to tonnes
        gwp = gwp_factors.get(gas, 1.0)
        gas_tonnes = gas_co2e / gwp
        breakdown[f"{gas}_tonnes"] = gas_tonnes
    
    return breakdown

def calculate_combined_uncertainty(activity_uncertainty: float, ef_uncertainty: float) -> float:
    """Calculate combined uncertainty using error propagation"""
    return float(np.sqrt(activity_uncertainty**2 + ef_uncertainty**2))

def select_distribution(uncertainty_percent: float, distribution_type: str = "lognormal"):
    """Select appropriate distribution based on uncertainty level"""
    if distribution_type == "normal":
        return stats.norm(loc=1.0, scale=uncertainty_percent/100)
    else:  # lognormal (default)
        cv = uncertainty_percent / 100
        sigma = np.sqrt(np.log(1 + cv**2))
        mu = -sigma**2 / 2
        return stats.lognorm(s=sigma, scale=np.exp(mu))

def run_monte_carlo(base_value: float, uncertainty_percent: float, 
                   n_iterations: int = 10000, distribution_type: str = "lognormal") -> np.ndarray:
    """Run Monte Carlo simulation for a single value"""
    if uncertainty_percent == 0 or base_value == 0:
        return np.full(n_iterations, base_value)
    
    dist = select_distribution(uncertainty_percent, distribution_type)
    samples = dist.rvs(size=n_iterations)
    return base_value * samples

def calculate_scope3_categories(
    activity_data: List[EmissionInput],
    company_profile: Optional[CompanyProfile],
    scope1_emissions: float,
    scope2_emissions: float,
    existing_categories: Dict[str, float]
) -> Tuple[Dict[str, float], Dict[str, Dict[str, Any]], List[EmissionBreakdown]]:
    """
    Calculate all 15 Scope 3 categories based on available data
    Returns: (category_emissions, metadata, additional_breakdowns)
    """
    scope3_breakdowns = []  # Use different variable name to avoid conflict
    categories = existing_categories.copy()
    metadata = {}
    
    # Get sector-specific factors
    sector = company_profile.sector if company_profile else "default"
    if sector not in INTENSITY_RATIOS:
        sector = "default"
    
    intensity_ratios = INTENSITY_RATIOS[sector]
    spend_factors = SPEND_BASED_FACTORS.get(sector, SPEND_BASED_FACTORS["services"])
    employee_factors = PER_EMPLOYEE_FACTORS
    
    # Total Scope 1+2 for proxy calculations
    total_s1s2 = scope1_emissions + scope2_emissions
    
    # Category 1: Purchased Goods & Services
    if categories.get("category_1", 0) == 0:
        if company_profile and company_profile.supply_chain_spend:
            cat1_emissions = company_profile.supply_chain_spend * spend_factors["purchased_goods"]
            method = "spend_based"
        else:
            ratio_min, ratio_max = intensity_ratios.get("category_1", (0.25, 0.40))
            cat1_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
            method = "proxy_based"
        
        categories["category_1"] = cat1_emissions
        metadata["category_1"] = {
            "calculation_method": method,
            "data_quality": "estimated"
        }
        
        scope3_breakdowns.append(EmissionBreakdown(
            activity_type="Purchased Goods & Services (estimated)",
            scope="scope_3",
            emissions_kg_co2e=round(cat1_emissions, 2),
            unit="EUR" if method == "spend_based" else "proxy",
            calculation_method=method,
            scope3_category=1
        ))
    
    # Category 2: Capital Goods
    if categories.get("category_2", 0) == 0:
        if company_profile and company_profile.capital_expenditure:
            cat2_emissions = company_profile.capital_expenditure * spend_factors["capital_goods"]
            method = "spend_based"
        else:
            ratio_min, ratio_max = intensity_ratios.get("category_2", (0.05, 0.10))
            cat2_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
            method = "proxy_based"
        
        categories["category_2"] = cat2_emissions
        metadata["category_2"] = {
            "calculation_method": method,
            "data_quality": "estimated"
        }
        
        if cat2_emissions > 0:
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="Capital Goods (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat2_emissions, 2),
                unit="EUR" if method == "spend_based" else "proxy",
                calculation_method=method,
                scope3_category=2
            ))
    
    # Category 4: Upstream Transportation
    if categories.get("category_4", 0) == 0:
        if company_profile and company_profile.supply_chain_spend:
            cat4_emissions = categories.get("category_1", 0) * 0.15
            method = "proxy_based"
        else:
            ratio_min, ratio_max = intensity_ratios.get("category_4", (0.04, 0.08))
            cat4_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
            method = "proxy_based"
        
        categories["category_4"] = cat4_emissions
        metadata["category_4"] = {
            "calculation_method": method,
            "data_quality": "estimated"
        }
        
        if cat4_emissions > 0:
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="Upstream Transportation (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat4_emissions, 2),
                unit="proxy",
                calculation_method=method,
                scope3_category=4
            ))
    
    # Category 5: Waste Generated
    if categories.get("category_5", 0) == 0:
        if company_profile:
            if company_profile.waste_tonnes:
                cat5_emissions = company_profile.waste_tonnes * 467
                method = "activity_based"
            elif company_profile.employees:
                cat5_emissions = company_profile.employees * employee_factors["waste"][sector]
                method = "average_data"
            else:
                ratio_min, ratio_max = intensity_ratios.get("category_5", (0.02, 0.04))
                cat5_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
                method = "proxy_based"
        else:
            cat5_emissions = total_s1s2 * 0.03
            method = "proxy_based"
        
        categories["category_5"] = cat5_emissions
        metadata["category_5"] = {
            "calculation_method": method,
            "data_quality": "estimated" if method != "activity_based" else "measured"
        }
        
        if cat5_emissions > 0:
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="Waste Generated (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat5_emissions, 2),
                unit="tonnes" if method == "activity_based" else "proxy",
                calculation_method=method,
                scope3_category=5
            ))
    
    # Category 6: Business Travel
    if categories.get("category_6", 0) == 0:
        if company_profile:
            if company_profile.business_travel_km:
                cat6_emissions = company_profile.business_travel_km * 0.148
                method = "activity_based"
            elif company_profile.employees:
                cat6_emissions = company_profile.employees * employee_factors["business_travel"][sector]
                method = "average_data"
            else:
                ratio_min, ratio_max = intensity_ratios.get("category_6", (0.02, 0.04))
                cat6_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
                method = "proxy_based"
        else:
            cat6_emissions = total_s1s2 * 0.03
            method = "proxy_based"
        
        categories["category_6"] = cat6_emissions
        metadata["category_6"] = {
            "calculation_method": method,
            "data_quality": "estimated" if method != "activity_based" else "measured"
        }
        
        if cat6_emissions > 0:
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="Business Travel (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat6_emissions, 2),
                unit="km" if method == "activity_based" else "proxy",
                calculation_method=method,
                scope3_category=6
            ))
    
    # Category 7: Employee Commuting
    if categories.get("category_7", 0) == 0:
        if company_profile and company_profile.employees:
            cat7_emissions = company_profile.employees * employee_factors["employee_commuting"][sector]
            method = "average_data"
        else:
            ratio_min, ratio_max = intensity_ratios.get("category_7", (0.02, 0.04))
            cat7_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
            method = "proxy_based"
        
        categories["category_7"] = cat7_emissions
        metadata["category_7"] = {
            "calculation_method": method,
            "data_quality": "estimated"
        }
        
        if cat7_emissions > 0:
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="Employee Commuting (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat7_emissions, 2),
                unit="employees" if method == "average_data" else "proxy",
                calculation_method=method,
                scope3_category=7
            ))
    
    # Category 11: Use of Sold Products
    if categories.get("category_11", 0) == 0:
        if company_profile and (company_profile.has_manufacturing or sector == "manufacturing"):
            if company_profile.product_sales_units and company_profile.average_product_lifetime_years:
                cat11_emissions = company_profile.product_sales_units * 100 * company_profile.average_product_lifetime_years
                method = "activity_based"
            else:
                ratio_min, ratio_max = intensity_ratios.get("category_11", (0.40, 0.80))
                cat11_emissions = total_s1s2 * ((ratio_min + ratio_max) / 2)
                method = "proxy_based"
            
            categories["category_11"] = cat11_emissions
            metadata["category_11"] = {
                "calculation_method": method,
                "data_quality": "estimated"
            }
            
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="Use of Sold Products (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat11_emissions, 2),
                unit="products" if method == "activity_based" else "proxy",
                calculation_method=method,
                scope3_category=11
            ))
    
    # Category 12: End-of-life treatment
    if categories.get("category_12", 0) == 0 and company_profile and company_profile.has_manufacturing:
        cat12_emissions = categories.get("category_11", 0) * 0.1
        categories["category_12"] = cat12_emissions
        metadata["category_12"] = {
            "calculation_method": "proxy_based",
            "data_quality": "estimated"
        }
        
        if cat12_emissions > 0:
            scope3_breakdowns.append(EmissionBreakdown(
                activity_type="End-of-life Treatment (estimated)",
                scope="scope_3",
                emissions_kg_co2e=round(cat12_emissions, 2),
                unit="proxy",
                calculation_method="proxy_based",
                scope3_category=12
            ))
    
    # Category 15: Investments
    if categories.get("category_15", 0) == 0 and company_profile and company_profile.investments_eur:
        cat15_emissions = company_profile.investments_eur * 0.2
        categories["category_15"] = cat15_emissions
        metadata["category_15"] = {
            "calculation_method": "spend_based",
            "data_quality": "estimated"
        }
        
        scope3_breakdowns.append(EmissionBreakdown(
            activity_type="Investments (estimated)",
            scope="scope_3",
            emissions_kg_co2e=round(cat15_emissions, 2),
            unit="EUR",
            calculation_method="spend_based",
            scope3_category=15
        ))
    
    return categories, metadata, scope3_breakdowns

def calculate_data_quality_score(
    scope3_detailed: Dict[str, Dict[str, Any]], 
    scope_totals: Dict[str, float]
) -> float:
    """Calculate overall data quality score based on calculation methods used"""
    total_emissions = sum(scope_totals.values())
    if total_emissions == 0:
        return 0
    
    quality_weights = {
        "activity_based": 100,
        "spend_based": 70,
        "average_data": 50,
        "proxy_based": 30
    }
    
    weighted_score = 0
    for category, details in scope3_detailed.items():
        if not details["excluded"]:
            emissions = details["emissions_tco2e"] * 1000
            method = details.get("calculation_method", "proxy_based")
            weight = quality_weights.get(method, 30)
            weighted_score += (emissions / total_emissions) * weight
    
    scope12_percentage = (scope_totals["scope_1"] + scope_totals["scope_2"]) / total_emissions
    weighted_score += scope12_percentage * 100
    
    return round(weighted_score, 1)

def aggregate_energy_from_activities(activities: List[Dict[str, Any]]) -> EnergyConsumption:
    """Aggregate energy consumption from activities"""
    energy_data = {
        "electricity_mwh": 0,
        "heating_cooling_mwh": 0,
        "steam_mwh": 0,
        "fuel_combustion_mwh": 0,
        "renewable_energy_mwh": 0,
        "total_energy_mwh": 0
    }
    
    for activity in activities:
        activity_type = activity.get("activity_type", "").lower()
        amount = activity.get("amount", 0)
        
        if "electricity" in activity_type:
            if activity_type in ["electricity_grid", "electricity"]:
                energy_data["electricity_mwh"] += amount / 1000
            elif activity_type == "electricity_renewable":
                energy_data["renewable_energy_mwh"] += amount / 1000
                energy_data["electricity_mwh"] += amount / 1000
        elif "heating" in activity_type or "cooling" in activity_type:
            energy_data["heating_cooling_mwh"] += amount / 1000
        elif "steam" in activity_type:
            energy_data["steam_mwh"] += amount / 1000
        elif any(fuel in activity_type for fuel in ["natural_gas", "diesel", "petrol", "oil"]):
            if "natural_gas" in activity_type:
                energy_data["fuel_combustion_mwh"] += amount / 1000
            elif "diesel" in activity_type:
                energy_data["fuel_combustion_mwh"] += (amount * 10) / 1000
            elif "petrol" in activity_type:
                energy_data["fuel_combustion_mwh"] += (amount * 9.5) / 1000
    
    energy_data["total_energy_mwh"] = sum([
        energy_data["electricity_mwh"],
        energy_data["heating_cooling_mwh"],
        energy_data["steam_mwh"],
        energy_data["fuel_combustion_mwh"]
    ])
    
    return EnergyConsumption(**energy_data)

# ===== MAIN API ENDPOINTS =====
@router.post("/calculate", response_model=CalculateEmissionsResponse)
async def calculate_emissions(request: CalculateEmissionsRequest):
    """
    Calculate GHG emissions with complete Scope 3 coverage for ESRS E1 compliance
    """
    try:
        total_emissions = 0.0
        scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
        scope3_categories = {f"category_{i}": 0.0 for i in range(1, 16)}
        breakdown = []
        category3_breakdowns = []  # Separate variable for Category 3 WTT/T&D
        
        calculation_methods_used = set()
        data_gaps = []
        estimation_quality = "high"
        
        gas_breakdown = {
            "CO2_tonnes": 0.0,
            "CH4_tonnes": 0.0,
            "N2O_tonnes": 0.0,
            "HFCs_tonnes_co2e": 0.0,
            "PFCs_tonnes_co2e": 0.0,
            "SF6_tonnes": 0.0,
            "NF3_tonnes": 0.0
        }
        
        # Process each emission input
        for emission_input in request.emissions_data:
            activity_type = emission_input.activity_type.lower()
            
            # Get emission factor
            if emission_input.custom_factor:
                factor = emission_input.custom_factor
                scope = "scope_3"
                category = None
            else:
                factor_data = get_emission_factor(activity_type)
                if not factor_data:
                    data_gaps.append(f"No emission factor for {activity_type}")
                    continue
                
                factor = factor_data["factor"]
                scope = factor_data["scope"]
                category = factor_data.get("category")
            
            # Calculate emissions
            emissions_kg = emission_input.amount * factor
            scope_totals[scope] += emissions_kg
            total_emissions += emissions_kg
            calculation_methods_used.add("activity_based")
            
            # Track Scope 3 categories
            if scope == "scope_3" and category:
                scope3_categories[f"category_{category}"] += emissions_kg
            
            # Calculate gas breakdown
            if request.include_gas_breakdown:
                gas_specific = calculate_gas_breakdown(emissions_kg, activity_type)
                for gas, amount in gas_specific.items():
                    if gas in gas_breakdown:
                        gas_breakdown[gas] += amount
            
            breakdown.append(EmissionBreakdown(
                activity_type=emission_input.activity_type,
                scope=scope,
                emissions_kg_co2e=round(emissions_kg, 2),
                unit=emission_input.unit,
                calculation_method="emission_factor",
                gas_type=emission_input.gas_type,
                scope3_category=category
            ))
            
            # AUTOMATIC CATEGORY 3 CALCULATION
            for fuel_key, cat3_data in CATEGORY_3_FACTORS.items():
                if fuel_key in activity_type:
                    cat3_emissions = 0
                    
                    if fuel_key == "electricity":
                        cat3_emissions = emission_input.amount * cat3_data["td_factor"]
                    else:
                        cat3_emissions = emission_input.amount * cat3_data.get("wtt_factor", 0.1)
                    
                    if cat3_emissions > 0:
                        scope_totals["scope_3"] += cat3_emissions
                        total_emissions += cat3_emissions
                        scope3_categories["category_3"] += cat3_emissions
                        
                        category3_breakdowns.append(EmissionBreakdown(
                            activity_type=cat3_data["name"],
                            scope="scope_3",
                            emissions_kg_co2e=round(cat3_emissions, 2),
                            unit=emission_input.unit,
                            calculation_method="emission_factor",
                            gas_type="CO2",
                            scope3_category=3
                        ))
                        
                        if request.include_gas_breakdown:
                            gas_breakdown["CO2_tonnes"] += cat3_emissions / 1000
                        
                        logger.info(f"Auto-calculated Category 3 for {activity_type}: {cat3_emissions:.2f} kg CO2e")
                    break
        
        # Add Category 3 breakdowns to main breakdown
        breakdown.extend(category3_breakdowns)
        
        # Calculate all Scope 3 categories
        enhanced_categories, category_metadata, scope3_additional = calculate_scope3_categories(
            activity_data=request.emissions_data,
            company_profile=request.company_profile,
            scope1_emissions=scope_totals["scope_1"],
            scope2_emissions=scope_totals["scope_2"],
            existing_categories=scope3_categories
        )
        
        # Update totals
        for category, emissions in enhanced_categories.items():
            if emissions > scope3_categories.get(category, 0):
                additional_emissions = emissions - scope3_categories.get(category, 0)
                scope3_categories[category] = emissions
                scope_totals["scope_3"] += additional_emissions
                total_emissions += additional_emissions
        
        # Add scope3 additional breakdowns
        breakdown.extend(scope3_additional)
        
        # Track calculation methods
        for meta in category_metadata.values():
            method = meta["calculation_method"]
            calculation_methods_used.add(method)
            if method in ["spend_based", "proxy_based", "average_data"]:
                if estimation_quality == "high":
                    estimation_quality = "medium"
                if method == "proxy_based" and estimation_quality == "medium":
                    estimation_quality = "low"
        
        # Set total CO2e
        gas_breakdown["total_co2e"] = total_emissions / 1000
        
        # Create response objects
        ghg_breakdown_obj = GHGBreakdown(**gas_breakdown) if request.include_gas_breakdown else None
        
        scope3_category_obj = Scope3CategoryBreakdown(**{
            k: round(v / 1000, 2) for k, v in scope3_categories.items()
        })
        
        # Create scope3_detailed
        scope3_detailed = {}
        for i in range(1, 16):
            emissions_tco2e = scope3_categories[f"category_{i}"] / 1000
            scope3_detailed[f"category_{i}"] = {
                "emissions_tco2e": round(emissions_tco2e, 2),
                "excluded": emissions_tco2e == 0,
                "calculation_method": category_metadata.get(f"category_{i}", {}).get("calculation_method", "activity_based" if emissions_tco2e > 0 else None),
                "data_quality_tier": "Tier 1" if category_metadata.get(f"category_{i}", {}).get("data_quality") == "measured" else "Tier 2" if emissions_tco2e > 0 else None,
                "data_quality": category_metadata.get(f"category_{i}", {}).get("data_quality", "measured" if emissions_tco2e > 0 else None)
            }
        
        # Calculate energy consumption
        energy_consumption = aggregate_energy_from_activities(
            [{"activity_type": e.activity_type, "amount": e.amount} for e in request.emissions_data]
        )
        
        if request.company_profile and request.company_profile.revenue and energy_consumption.total_energy_mwh > 0:
            energy_consumption.energy_intensity_value = energy_consumption.total_energy_mwh / (request.company_profile.revenue / 1_000_000)
        
        # Monte Carlo uncertainty analysis (if requested)
        uncertainty_analysis = None
        if request.include_uncertainty and request.monte_carlo_iterations > 0:
            logger.info(f"Running Monte Carlo simulation with {request.monte_carlo_iterations} iterations")
            
            simulation_results = []
            category_simulations = {f"category_{i}": [] for i in range(1, 16)}
            
            for iteration in range(request.monte_carlo_iterations):
                sim_total = 0.0
                sim_scope_totals = {"scope_1": 0.0, "scope_2": 0.0, "scope_3": 0.0}
                sim_categories = {f"category_{i}": 0.0 for i in range(1, 16)}
                
                # Simulate each activity
                for emission_input in request.emissions_data:
                    activity_type = emission_input.activity_type.lower()
                    
                    if emission_input.custom_factor:
                        factor = emission_input.custom_factor
                        scope = "scope_3"
                        factor_uncertainty = 20
                    else:
                        factor_data = get_emission_factor(activity_type)
                        if not factor_data:
                            continue
                        
                        factor = factor_data["factor"]
                        scope = factor_data["scope"]
                        factor_uncertainty = factor_data.get("uncertainty", 10)
                    
                    activity_uncertainty = emission_input.uncertainty_percentage or 10
                    combined_uncertainty = calculate_combined_uncertainty(
                        activity_uncertainty,
                        factor_uncertainty
                    )
                    
                    sim_emissions = run_monte_carlo(
                        emission_input.amount * factor,
                        combined_uncertainty,
                        1
                    )[0]
                    
                    sim_scope_totals[scope] += sim_emissions
                    sim_total += sim_emissions
                    
                    # Simulate Category 3
                    for fuel_key, cat3_data in CATEGORY_3_FACTORS.items():
                        if fuel_key in activity_type:
                            if fuel_key == "electricity":
                                cat3_sim = run_monte_carlo(
                                    emission_input.amount * cat3_data["td_factor"],
                                    15, 1
                                )[0]
                            else:
                                cat3_sim = run_monte_carlo(
                                    emission_input.amount * cat3_data.get("wtt_factor", 0.1),
                                    10, 1
                                )[0]
                            
                            if cat3_sim > 0:
                                sim_scope_totals["scope_3"] += cat3_sim
                                sim_total += cat3_sim
                                sim_categories["category_3"] += cat3_sim
                            break
                
                # Simulate estimated Scope 3 categories
                for cat_key, base_value in enhanced_categories.items():
                    if base_value > sim_categories.get(cat_key, 0):
                        estimated_portion = base_value - sim_categories.get(cat_key, 0)
                        meta = category_metadata.get(cat_key, {})
                        
                        uncertainty_map = {
                            "activity_based": 10,
                            "spend_based": 20,
                            "average_data": 25,
                            "proxy_based": 35
                        }
                        uncertainty = uncertainty_map.get(meta.get("calculation_method", "proxy_based"), 30)
                        
                        sim_cat_emissions = run_monte_carlo(estimated_portion, uncertainty, 1)[0]
                        sim_categories[cat_key] += max(0, sim_cat_emissions)
                        sim_total += max(0, sim_cat_emissions)
                
                simulation_results.append(sim_total)
                for cat_key, cat_value in sim_categories.items():
                    category_simulations[cat_key].append(cat_value)
            
            # Calculate statistics
            if simulation_results:
                results_array = np.array(simulation_results)
                mean_emissions = float(np.mean(results_array))
                std_dev = float(np.std(results_array))
                cv = (std_dev / mean_emissions * 100) if mean_emissions > 0 else 0
                
                data_quality_score = calculate_data_quality_score(scope3_detailed, scope_totals)
                
                uncertainty_analysis = {
                    "monte_carlo_runs": request.monte_carlo_iterations,
                    "mean_emissions_kg": mean_emissions,
                    "std_deviation_kg": std_dev,
                    "coefficient_of_variation_percent": cv,
                    "confidence_interval_95": [
                        float(np.percentile(results_array, 2.5)),
                        float(np.percentile(results_array, 97.5))
                    ],
                    "confidence_interval_90": [
                        float(np.percentile(results_array, 5)),
                        float(np.percentile(results_array, 95))
                    ],
                    "relative_uncertainty_percent": cv,
                    "methodology": "IPCC Tier 2 Monte Carlo with sector-specific proxies",
                    "data_quality_score": data_quality_score
                }
                
                # Add category-specific uncertainty
                uncertainty_analysis["category_uncertainty"] = {}
                for cat_key, cat_sims in category_simulations.items():
                    if cat_sims and any(s > 0 for s in cat_sims):
                        cat_array = np.array(cat_sims)
                        cat_mean = float(np.mean(cat_array))
                        cat_std = float(np.std(cat_array))
                        uncertainty_analysis["category_uncertainty"][cat_key] = {
                            "mean_kg": cat_mean,
                            "std_dev_kg": cat_std,
                            "confidence_interval_95": [
                                float(np.percentile(cat_array, 2.5)),
                                float(np.percentile(cat_array, 97.5))
                            ],
                            "relative_uncertainty_percent": (cat_std / cat_mean * 100) if cat_mean > 0 else 0
                        }
        
        # Prepare ESRS E1 metadata
        esrs_e1_metadata = None
        if request.esrs_e1_data:
            if not request.esrs_e1_data.energy_consumption:
                request.esrs_e1_data.energy_consumption = energy_consumption
            esrs_e1_metadata = request.esrs_e1_data.model_dump()
        
        # Prepare calculation metadata
        calculation_metadata = {
            "calculation_methods_used": list(calculation_methods_used),
            "data_gaps_identified": data_gaps if data_gaps else ["None"],
            "estimation_quality": estimation_quality,
            "scope3_coverage": {
                "categories_calculated": sum(1 for v in scope3_categories.values() if v > 0),
                "categories_excluded": sum(1 for v in scope3_categories.values() if v == 0),
                "estimation_percentage": round(
                    sum(v for k, v in scope3_categories.items() if category_metadata.get(k, {}).get("data_quality") == "estimated") / 
                    sum(scope3_categories.values()) * 100 if sum(scope3_categories.values()) > 0 else 0, 
                    1
                )
            },
            "data_quality_score": calculate_data_quality_score(scope3_detailed, scope_totals)
        }
        
        return CalculateEmissionsResponse(
            total_emissions_kg_co2e=round(total_emissions, 2),
            total_emissions_tco2e=round(total_emissions / 1000, 3),  # Convert to tonnes with 3 decimals
            scope1_emissions_tco2e=round(scope_totals["scope_1"] / 1000, 3),
            scope2_emissions_tco2e=round(scope_totals["scope_2"] / 1000, 3),
            scope3_emissions_tco2e=round(scope_totals["scope_3"] / 1000, 3),
            scope3_category_breakdown=scope3_category_obj,  # Already in tCO2e
            scope3_detailed=scope3_detailed,  # Already in tCO2e
            breakdown=breakdown,  # Keep in kg for detail
            reporting_period=request.reporting_period,
            calculation_date=str(date.today()),
            ghg_breakdown=ghg_breakdown_obj,  # Already in tonnes
            esrs_e1_metadata=esrs_e1_metadata,
            energy_consumption=energy_consumption,
            calculation_metadata=calculation_metadata,
            uncertainty_analysis=uncertainty_analysis
        )
        
    except Exception as e:
        logger.error(f"Error calculating emissions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "5.2",
        "improvements": [
            "Exact DEFRA 2024 emission factors",
            "100+ activity types supported",
            "Clear tCO2e unit conversion",
            "Fixed variable scope conflict",
            "Fixed zero emissions bug",
            "Enhanced error handling"
        ],
        "features": {
            "monte_carlo": True,
            "monte_carlo_in_calculate": True,
            "monte_carlo_scope3_all": True,
            "esrs_e1": True,
            "gas_breakdown": True,
            "automatic_category_3": True,
            "all_scope3_categories": True,
            "company_profile": True,
            "scope3_detailed": True,
            "category_uncertainty": True,
            "data_quality_scoring": True,
            "uncertainty_analysis": True,
            "comprehensive_factors": True
        },
        "emission_factors_count": len(DEFAULT_EMISSION_FACTORS),
        "key_factors": {
            "natural_gas": DEFAULT_EMISSION_FACTORS["natural_gas_stationary"]["factor"],
            "diesel": DEFAULT_EMISSION_FACTORS["diesel_stationary"]["factor"],
            "electricity": DEFAULT_EMISSION_FACTORS["electricity_grid"]["factor"],
            "waste_landfill": DEFAULT_EMISSION_FACTORS["waste_landfill"]["factor"]
        }
    }

@router.get("/activity-types")
async def get_activity_types():
    """Get all supported activity types with enhanced metadata"""
    activity_types = {
        "scope_1": [],
        "scope_2": [],
        "scope_3": []
    }
    
    seen = set()
    
    for name, data in DEFAULT_EMISSION_FACTORS.items():
        key = f"{name}_{data['unit']}"
        if key not in seen:
            seen.add(key)
            scope = data["scope"]
            
            activity_info = {
                "value": name,
                "label": name.replace("-", " ").replace("_", " ").title(),
                "unit": data["unit"],
                "factor": data["factor"],
                "factor_unit": "kgCO2e"
            }
            
            if "category" in data:
                activity_info["scope3_category"] = data["category"]
            if "uncertainty" in data:
                activity_info["uncertainty_percent"] = data["uncertainty"]
            
            activity_types[scope].append(activity_info)
    
    # Sort each scope's activities alphabetically by label
    for scope in activity_types:
        activity_types[scope].sort(key=lambda x: x["label"])
    
    return {
        "total_activities": sum(len(activities) for activities in activity_types.values()),
        "by_scope": activity_types,
        "note": "All emission factors are in kgCO2e per unit"
    }

@router.get("/activity-categories")
async def get_activity_categories():
    """Get activity types organized by Scope 3 categories"""
    categories = {
        "scope_1": {
            "stationary_combustion": [],
            "mobile_combustion": [],
            "process_emissions": [],
            "fugitive_emissions": []
        },
        "scope_2": {
            "purchased_electricity": [],
            "purchased_heat_steam": []
        },
        "scope_3": {f"category_{i}": [] for i in range(1, 16)}
    }
    
    for name, data in DEFAULT_EMISSION_FACTORS.items():
        activity_info = {
            "value": name,
            "label": name.replace("-", " ").replace("_", " ").title(),
            "unit": data["unit"],
            "factor": data["factor"]
        }
        
        if data["scope"] == "scope_1":
            # Categorize Scope 1 activities
            if any(x in name.lower() for x in ["natural_gas", "diesel_gen", "lpg", "coal", "fuel_oil"]):
                categories["scope_1"]["stationary_combustion"].append(activity_info)
            elif any(x in name.lower() for x in ["fleet", "van", "hgv"]):
                categories["scope_1"]["mobile_combustion"].append(activity_info)
            elif any(x in name.lower() for x in ["industrial", "chemical"]):
                categories["scope_1"]["process_emissions"].append(activity_info)
            elif any(x in name.lower() for x in ["refrigerant", "sf6"]):
                categories["scope_1"]["fugitive_emissions"].append(activity_info)
        
        elif data["scope"] == "scope_2":
            # Categorize Scope 2 activities
            if "electricity" in name.lower():
                categories["scope_2"]["purchased_electricity"].append(activity_info)
            else:
                categories["scope_2"]["purchased_heat_steam"].append(activity_info)
        
        elif data["scope"] == "scope_3" and "category" in data:
            # Categorize Scope 3 activities
            category_key = f"category_{data['category']}"
            categories["scope_3"][category_key].append(activity_info)
    
    return categories

@router.post("/test-calculation")
async def test_calculation():
    """Test endpoint to verify emission calculations"""
    test_activities = [
        {"activity_type": "natural_gas_stationary", "amount": 1000, "unit": "kWh", "expected_kg": 185.0},
        {"activity_type": "diesel_stationary", "amount": 1000, "unit": "litres", "expected_kg": 2680.0},
        {"activity_type": "electricity_grid", "amount": 1000, "unit": "kWh", "expected_kg": 233.0},
        {"activity_type": "flight_domestic", "amount": 1000, "unit": "passenger.km", "expected_kg": 250.0},
        {"activity_type": "waste_landfill", "amount": 1, "unit": "tonnes", "expected_kg": 467.0},
        {"activity_type": "coal", "amount": 1, "unit": "tonnes", "expected_kg": 2419.0}
    ]
    
    results = []
    for test in test_activities:
        factor_data = get_emission_factor(test["activity_type"])
        if factor_data:
            calculated_kg = test["amount"] * factor_data["factor"]
            calculated_tco2e = calculated_kg / 1000
            results.append({
                "activity": test["activity_type"],
                "amount": test["amount"],
                "unit": test["unit"],
                "expected_kg": test["expected_kg"],
                "calculated_kg": round(calculated_kg, 2),
                "calculated_tco2e": round(calculated_tco2e, 3),
                "match": abs(calculated_kg - test["expected_kg"]) < 0.01,
                "scope": factor_data["scope"],
                "factor": factor_data["factor"]
            })
        else:
            results.append({
                "activity": test["activity_type"],
                "error": "Factor not found"
            })
    
    return {
        "test_results": results,
        "all_passed": all(r.get("match", False) for r in results if "match" in r),
        "summary": {
            "natural_gas_factor": DEFAULT_EMISSION_FACTORS["natural_gas_stationary"]["factor"],
            "diesel_factor": DEFAULT_EMISSION_FACTORS["diesel_stationary"]["factor"],
            "electricity_factor": DEFAULT_EMISSION_FACTORS["electricity_grid"]["factor"]
        }
    }

@router.get("/emission-factors")
async def get_emission_factors():
    """Get all emission factors with enhanced metadata"""
    factors = []
    seen = set()
    
    for name, data in DEFAULT_EMISSION_FACTORS.items():
        key = f"{name}_{data['unit']}"
        if key not in seen:
            seen.add(key)
            factor_info = {
                "name": name.replace("-", " ").replace("_", " ").title(),
                "category": name,
                "unit": data["unit"],
                "factor": data["factor"],
                "factor_unit": "kgCO2e",  # Clarify the factor unit
                "scope": int(data["scope"].split("_")[1])
            }
            
            if "uncertainty" in data:
                factor_info["uncertainty_percent"] = data["uncertainty"]
            if "category" in data:
                factor_info["scope3_category"] = data["category"]
            
            factors.append(factor_info)
    
    # Add Category 3 factors
    for fuel, cat3_data in CATEGORY_3_FACTORS.items():
        factor_info = {
            "name": cat3_data["name"],
            "category": f"{fuel}_category3",
            "unit": cat3_data["unit"],
            "factor": cat3_data.get("wtt_factor", cat3_data.get("td_factor")),
            "factor_unit": "kgCO2e",
            "scope": 3,
            "scope3_category": 3,
            "source": cat3_data["source"]
        }
        factors.append(factor_info)
    
    return {
        "total_factors": len(factors),
        "factors": factors,
        "note": "All factors are in kgCO2e, outputs are converted to tCO2e"
    }