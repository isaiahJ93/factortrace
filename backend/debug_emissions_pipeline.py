#!/usr/bin/env python3
"""
Emergency diagnostic script to trace emissions data pipeline
Run this to find where calculations are failing
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
import traceback

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('emissions_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Emission factors (example - replace with your actual factors)
EMISSION_FACTORS = {
    'natural_gas': {
        'factor': 0.18254,  # kgCO2e/kWh
        'unit': 'kgCO2e/kWh'
    },
    'diesel': {
        'factor': 2.68787,  # kgCO2e/litre
        'unit': 'kgCO2e/litre'
    },
    'petrol': {
        'factor': 2.31049,  # kgCO2e/litre
        'unit': 'kgCO2e/litre'
    },
    'grid_electricity': {
        'factor': 0.23314,  # kgCO2e/kWh (location-based)
        'unit': 'kgCO2e/kWh'
    },
    'office_paper': {
        'factor': 0.91906,  # kgCO2e/kg
        'unit': 'kgCO2e/kg'
    },
    'road_freight': {
        'factor': 0.10456,  # kgCO2e/tonne.km
        'unit': 'kgCO2e/tonne.km'
    },
    'short_haul_flight': {
        'factor': 0.15553,  # kgCO2e/passenger.km
        'unit': 'kgCO2e/passenger.km'
    },
    'long_haul_flight': {
        'factor': 0.19309,  # kgCO2e/passenger.km
        'unit': 'kgCO2e/passenger.km'
    }
}

def find_calculation_functions():
    """Find all functions that should be calculating emissions"""
    logger.info("=== SEARCHING FOR CALCULATION FUNCTIONS ===")
    
    search_patterns = [
        "def.*calculate.*emission",
        "def.*compute.*co2",
        "def.*get.*emission",
        "class.*Calculator",
        "def.*scope.*calculation"
    ]
    
    for pattern in search_patterns:
        logger.info(f"Searching for pattern: {pattern}")
        # Add actual file search logic here

def trace_activity_data():
    """Trace where activity data from the form goes"""
    logger.info("=== TRACING ACTIVITY DATA FLOW ===")
    
    # Look for these specific values from your screenshot
    test_values = {
        'natural_gas': 234,  # kWh
        'diesel': 234,       # litres
        'petrol': 234,       # litres
        'grid_electricity': 345,  # kWh
        'district_heating': 342,  # kWh
        'office_paper': 234,      # kg
        'plastic_packaging': 234,  # kg
        'steel_products': 2,       # tonnes
        'machinery_equipment': 345344,  # EUR
        'upstream_electricity': 320,    # kWh
        'road_freight': 3454,          # tonne.km
        'rail_freight': 3421,          # tonne.km
        'landfill': 1,                 # tonnes
        'domestic_flights': 3432,       # passenger.km
        'long_haul_flights': 23434,     # passenger.km
        'car_average': 3454             # km
    }
    
    logger.info(f"Looking for activity values: {test_values}")
    
    # Calculate expected emissions
    logger.info("\n=== EXPECTED EMISSIONS CALCULATIONS ===")
    
    total_scope1 = 0
    total_scope2 = 0
    total_scope3 = 0
    
    # Scope 1 calculations
    scope1_calcs = {
        'natural_gas': test_values['natural_gas'] * EMISSION_FACTORS['natural_gas']['factor'] / 1000,
        'diesel_fleet': test_values['diesel'] * EMISSION_FACTORS['diesel']['factor'] / 1000,
        'petrol_fleet': test_values['petrol'] * EMISSION_FACTORS['petrol']['factor'] / 1000
    }
    
    for source, emissions in scope1_calcs.items():
        logger.info(f"Scope 1 - {source}: {emissions:.3f} tCO2e")
        total_scope1 += emissions
    
    logger.info(f"TOTAL SCOPE 1: {total_scope1:.3f} tCO2e (NOT 1000!)")
    
    # Scope 2 calculations  
    scope2_calcs = {
        'grid_electricity': test_values['grid_electricity'] * EMISSION_FACTORS['grid_electricity']['factor'] / 1000
    }
    
    for source, emissions in scope2_calcs.items():
        logger.info(f"Scope 2 - {source}: {emissions:.3f} tCO2e")
        total_scope2 += emissions
        
    logger.info(f"TOTAL SCOPE 2: {total_scope2:.3f} tCO2e (NOT 500!)")
    
    # Scope 3 calculations
    scope3_calcs = {
        'cat1_office_paper': test_values['office_paper'] * EMISSION_FACTORS['office_paper']['factor'] / 1000,
        'cat4_road_freight': test_values['road_freight'] * EMISSION_FACTORS['road_freight']['factor'] / 1000,
        'cat6_domestic_flights': test_values['domestic_flights'] * EMISSION_FACTORS['short_haul_flight']['factor'] / 1000,
        'cat6_long_haul_flights': test_values['long_haul_flights'] * EMISSION_FACTORS['long_haul_flight']['factor'] / 1000
    }
    
    for source, emissions in scope3_calcs.items():
        logger.info(f"Scope 3 - {source}: {emissions:.3f} tCO2e")
        total_scope3 += emissions
        
    logger.info(f"TOTAL SCOPE 3: {total_scope3:.3f} tCO2e (NOT 567!)")
    logger.info(f"GRAND TOTAL: {total_scope1 + total_scope2 + total_scope3:.3f} tCO2e (NOT 1967!)")

def check_xbrl_generation():
    """Find where XBRL facts are being generated with wrong values"""
    logger.info("\n=== CHECKING XBRL GENERATION ===")
    
    # Look for these specific XBRL generation patterns
    suspicious_patterns = [
        "1000</ix:nonFraction>",
        "500</ix:nonFraction>", 
        "567</ix:nonFraction>",
        "1967</ix:nonFraction>",
        "value=1000",
        "value=500",
        'emissions": 1000',
        'scope1": 1000'
    ]
    
    logger.info("Searching for hardcoded values in XBRL generation...")
    # Add file search logic here

def find_data_pipeline_break():
    """Identify where the calculation pipeline breaks"""
    logger.info("\n=== FINDING PIPELINE BREAK POINTS ===")
    
    checkpoints = [
        "1. Activity data input/parsing",
        "2. Emission factor application", 
        "3. Scope categorization",
        "4. Total calculation",
        "5. XBRL fact generation",
        "6. iXBRL template rendering"
    ]
    
    for checkpoint in checkpoints:
        logger.info(f"Checking: {checkpoint}")
        # Add specific checks for each stage

def generate_test_calculation():
    """Generate a test calculation to verify the pipeline"""
    logger.info("\n=== GENERATING TEST CALCULATION ===")
    
    test_data = {
        "company": "Test Company",
        "reporting_period": "2025",
        "activities": {
            "scope1": {
                "natural_gas": {"value": 234, "unit": "kWh"},
                "diesel_fleet": {"value": 234, "unit": "litres"}
            },
            "scope2": {
                "grid_electricity": {"value": 345, "unit": "kWh"}
            },
            "scope3": {
                "office_paper": {"value": 234, "unit": "kg"},
                "road_freight": {"value": 3454, "unit": "tonne.km"}
            }
        }
    }
    
    # Save test data
    with open('test_emissions_data.json', 'w') as f:
        json.dump(test_data, f, indent=2)
    
    logger.info("Test data saved to test_emissions_data.json")
    logger.info("Use this to test your calculation pipeline")

if __name__ == "__main__":
    logger.info("Starting emissions pipeline diagnostic...")
    
    try:
        find_calculation_functions()
        trace_activity_data()
        check_xbrl_generation()
        find_data_pipeline_break()
        generate_test_calculation()
        
        logger.info("\n=== DIAGNOSTIC COMPLETE ===")
        logger.info("Check emissions_debug.log for full details")
        logger.info("\nNEXT STEPS:")
        logger.info("1. Look for functions returning hardcoded values")
        logger.info("2. Check if emission factors are being applied")
        logger.info("3. Verify data flow from form -> calculations -> XBRL")
        logger.info("4. Replace ALL hardcoded values with calculations")
        
    except Exception as e:
        logger.error(f"Diagnostic failed: {str(e)}")
        logger.error(traceback.format_exc())