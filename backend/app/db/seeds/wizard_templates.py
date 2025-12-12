# app/db/seeds/wizard_templates.py
"""
Industry Templates Seed Data for Compliance Wizard.

Pre-configured templates with smart defaults for common Tier 2 supplier types.
These templates help suppliers quickly complete the wizard with minimal input.

Usage:
    poetry run python -m app.db.seeds.wizard_templates
"""
import logging
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.wizard import IndustryTemplate

logger = logging.getLogger(__name__)

# =============================================================================
# INDUSTRY TEMPLATES
# =============================================================================

INDUSTRY_TEMPLATES = [
    # Manufacturing - General
    {
        "id": "manufacturing_small",
        "name": "Small Manufacturing Company",
        "nace_codes": ["C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18"],
        "description": "Suitable for small manufacturing facilities (10-49 employees)",
        "company_size": "small",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "diesel_l",
            "waste_kg",
            "water_m3",
            "purchased_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 75000,  # ~2,500 kWh/employee for 30 employees
            "natural_gas_m3": 5000,
            "diesel_l": 2000,
            "waste_kg": 15000,
            "water_m3": 500,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 10,
    },
    {
        "id": "manufacturing_medium",
        "name": "Medium Manufacturing Company",
        "nace_codes": ["C10", "C11", "C12", "C13", "C14", "C15", "C16", "C17", "C18"],
        "description": "Suitable for medium manufacturing facilities (50-249 employees)",
        "company_size": "medium",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "diesel_l",
            "petrol_l",
            "company_vehicles_km",
            "waste_kg",
            "waste_recycled_kg",
            "water_m3",
            "business_travel_km",
            "purchased_goods_eur",
            "upstream_transport_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 375000,  # ~2,500 kWh/employee for 150 employees
            "natural_gas_m3": 25000,
            "diesel_l": 10000,
            "petrol_l": 3000,
            "company_vehicles_km": 50000,
            "waste_kg": 75000,
            "waste_recycled_kg": 30000,
            "water_m3": 2500,
            "business_travel_km": 100000,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 11,
    },
    # Metals & Mining
    {
        "id": "metals_manufacturing",
        "name": "Metals & Machinery Manufacturing",
        "nace_codes": ["C24", "C25", "C26", "C27", "C28", "C29", "C30"],
        "description": "Metal products, machinery, and equipment manufacturing",
        "company_size": "medium",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "diesel_l",
            "company_vehicles_km",
            "waste_kg",
            "waste_recycled_kg",
            "water_m3",
            "purchased_goods_eur",
            "capital_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 500000,  # Higher for metals processing
            "natural_gas_m3": 50000,
            "diesel_l": 15000,
            "company_vehicles_km": 75000,
            "waste_kg": 100000,
            "waste_recycled_kg": 60000,  # Higher recycling in metals
            "water_m3": 5000,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 20,
    },
    # Chemicals
    {
        "id": "chemicals_manufacturing",
        "name": "Chemicals Manufacturing",
        "nace_codes": ["C20", "C21"],
        "description": "Chemical products and pharmaceuticals manufacturing",
        "company_size": "medium",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "diesel_l",
            "waste_kg",
            "water_m3",
            "purchased_goods_eur",
            "upstream_transport_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 600000,  # Energy-intensive
            "natural_gas_m3": 75000,
            "diesel_l": 8000,
            "waste_kg": 50000,
            "water_m3": 10000,  # High water use
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 30,
    },
    # Food & Beverage
    {
        "id": "food_beverage",
        "name": "Food & Beverage Manufacturing",
        "nace_codes": ["C10", "C11"],
        "description": "Food products and beverages manufacturing",
        "company_size": "small",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "diesel_l",
            "waste_kg",
            "water_m3",
            "purchased_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 150000,
            "natural_gas_m3": 20000,
            "diesel_l": 5000,
            "waste_kg": 30000,
            "water_m3": 8000,  # High water for food processing
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 40,
    },
    # Textiles
    {
        "id": "textiles",
        "name": "Textiles & Apparel Manufacturing",
        "nace_codes": ["C13", "C14", "C15"],
        "description": "Textiles, clothing, and leather products",
        "company_size": "small",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "waste_kg",
            "water_m3",
            "purchased_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 80000,
            "natural_gas_m3": 8000,
            "waste_kg": 10000,
            "water_m3": 5000,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 50,
    },
    # Logistics & Distribution
    {
        "id": "logistics",
        "name": "Logistics & Distribution",
        "nace_codes": ["H49", "H50", "H51", "H52"],
        "description": "Transportation, warehousing, and distribution services",
        "company_size": "small",
        "activity_categories": [
            "electricity_kwh",
            "diesel_l",
            "petrol_l",
            "company_vehicles_km",
            "waste_kg",
            "purchased_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 50000,  # Lower for logistics
            "diesel_l": 50000,  # Higher diesel for fleet
            "petrol_l": 10000,
            "company_vehicles_km": 500000,
            "waste_kg": 5000,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 60,
    },
    # Professional Services
    {
        "id": "professional_services",
        "name": "Professional Services Office",
        "nace_codes": ["M69", "M70", "M71", "M72", "M73", "M74", "M75"],
        "description": "Consulting, legal, accounting, and other professional services",
        "company_size": "small",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "business_travel_km",
            "business_travel_rail_km",
            "employee_commute_km",
            "purchased_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 30000,  # Lower for office
            "natural_gas_m3": 2000,
            "business_travel_km": 75000,
            "business_travel_rail_km": 25000,
            "employee_commute_km": 120000,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 70,
    },
    # Micro Enterprise (Generic)
    {
        "id": "micro_enterprise",
        "name": "Micro Enterprise (Any Sector)",
        "nace_codes": [],  # Applies to any
        "description": "Generic template for very small businesses (1-9 employees)",
        "company_size": "micro",
        "activity_categories": [
            "electricity_kwh",
            "natural_gas_m3",
            "business_travel_km",
            "employee_commute_km",
            "purchased_goods_eur",
        ],
        "smart_defaults": {
            "electricity_kwh": 15000,  # ~2,500 kWh x 6 employees
            "natural_gas_m3": 500,
            "business_travel_km": 10000,
            "employee_commute_km": 30000,
        },
        "recommended_datasets": {
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        "display_order": 100,
    },
]


def seed_industry_templates(db: Session) -> dict:
    """
    Seed industry templates into database.

    Returns dict with counts of created, updated, skipped templates.
    """
    stats = {"created": 0, "updated": 0, "skipped": 0}

    for template_data in INDUSTRY_TEMPLATES:
        existing = db.query(IndustryTemplate).filter(
            IndustryTemplate.id == template_data["id"]
        ).first()

        if existing:
            # Update existing template
            for key, value in template_data.items():
                setattr(existing, key, value)
            stats["updated"] += 1
            logger.info(f"Updated template: {template_data['id']}")
        else:
            # Create new template
            template = IndustryTemplate(**template_data)
            db.add(template)
            stats["created"] += 1
            logger.info(f"Created template: {template_data['id']}")

    db.commit()
    return stats


def run_seed():
    """Run the seed script."""
    logging.basicConfig(level=logging.INFO)
    logger.info("Seeding industry templates...")

    db = SessionLocal()
    try:
        stats = seed_industry_templates(db)
        logger.info(f"Seed complete: {stats}")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
