# backend/scripts/test_scope3_calculations.py

from app.services.emissions_calculator import (
    EliteEmissionsCalculator, 
    CalculationContext,
    calculate_scope3_emissions,
    GWPVersionEnum
)
from app.db.session import SessionLocal
from decimal import Decimal

# Test 1: Calculate purchased goods emissions
print("Test 1: Purchased Goods & Services")
activity_data = [
    {
        "factor_name": "Steel (Virgin)",
        "quantity": 1000,  # 1000 kg
        "unit": "kg",
        "calculation_method": "activity_based",
        "region": "EU"
    },
    {
        "factor_name": "Aluminum (Primary)",
        "quantity": 500,  # 500 kg
        "unit": "kg",
        "calculation_method": "activity_based"
    }
]

db = SessionLocal()
result = calculate_scope3_emissions(
    category="purchased_goods_services",
    activity_data=activity_data,
    db_session=db
)

print(f"Emissions: {result.emissions_tco2e:.2f} tCO2e")
print(f"Uncertainty: ±{result.uncertainty_percent:.1f}%")
print(f"Range: {result.confidence_interval_lower:.2f} - {result.confidence_interval_upper:.2f}")
print(f"ESRS Requirements: {result.esrs_mapping}")
print()

# Test 2: Materiality Assessment
print("Test 2: Materiality Assessment")
context = CalculationContext(
    user_id="test",
    organization_id="test_org",
    gwp_version=GWPVersionEnum.AR6_100
)

calculator = EliteEmissionsCalculator(context, db_session=db)
materiality = calculator.assess_scope3_materiality(
    sector="Manufacturing",
    total_emissions=Decimal("10000"),
    category_emissions={
        "purchased_goods_services": Decimal("2500"),
        "use_of_sold_products": Decimal("4000"),
        "business_travel": Decimal("100")
    }
)

for assessment in materiality[:5]:  # Top 5
    print(f"{assessment.category_name}: {'MATERIAL' if assessment.is_material else 'NOT MATERIAL'}")
    print(f"  Reasons: {', '.join(assessment.reasons)}")
    print(f"  Data availability: {assessment.data_availability}")
    print()

# Test 3: Compliance Report
print("Test 3: ESRS Compliance Report")
emissions_by_category = {
    "purchased_goods_services": Decimal("2500"),
    "capital_goods": Decimal("500"),
    "fuel_energy_activities": Decimal("300"),
    "upstream_transportation": Decimal("400"),
    "waste_operations": Decimal("100"),
    "business_travel": Decimal("150"),
    "employee_commuting": Decimal("200"),
    "use_of_sold_products": Decimal("4000"),
    "end_of_life_treatment": Decimal("350")
}

report = calculator.generate_compliance_report(
    standard="ESRS",
    emissions_by_category=emissions_by_category,
    reporting_period="2024"
)

print(f"Compliance Status: {report.compliance_status}")
print(f"Completeness: {report.completeness_percentage:.1f}%")
print(f"Requirements Met: {len(report.requirements_met)}")
print(f"Requirements Pending: {len(report.requirements_pending)}")
print(f"Priority Actions: {report.priority_actions[0]}")

db.close()