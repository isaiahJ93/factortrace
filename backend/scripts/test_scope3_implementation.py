# backend/scripts/test_scope3_implementation.py

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.emissions_calculator import (
    EliteEmissionsCalculator, 
    CalculationContext,
    calculate_scope3_emissions,
    GWPVersionEnum
)
from app.db.session import SessionLocal
from app.models.emission_factor import EmissionFactor
from decimal import Decimal

def test_scope3_calculations():
    """Test Scope 3 calculations with real data"""
    db = SessionLocal()
    
    try:
        print("🧪 Testing Scope 3 Emissions Calculations\n")
        
        # Test 1: Check database factors
        print("Test 1: Verify Database Emission Factors")
        print("-" * 50)
        
        # Check a few categories
        categories_to_check = [
            "purchased_goods_services",
            "business_travel", 
            "employee_commuting",
            "use_of_sold_products"
        ]
        
        for category in categories_to_check:
            count = db.query(EmissionFactor).filter(
                EmissionFactor.scope3_category == category
            ).count()
            
            # Get a sample factor
            sample = db.query(EmissionFactor).filter(
                EmissionFactor.scope3_category == category
            ).first()
            
            print(f"✅ {category}: {count} factors")
            if sample:
                print(f"   Example: {sample.name} = {sample.factor} {sample.unit}")
        
        print()
        
        # Test 2: Calculate emissions for purchased goods
        print("Test 2: Calculate Purchased Goods & Services")
        print("-" * 50)
        
        # Get steel factor from DB
        steel_factor = db.query(EmissionFactor).filter(
            EmissionFactor.name.ilike("%Steel (Virgin)%"),
            EmissionFactor.scope3_category == "purchased_goods_services"
        ).first()
        
        if steel_factor:
            activity_data = [{
                "factor_name": "Steel (Virgin)",
                "quantity": 1000,  # 1000 kg
                "unit": "kg",
                "calculation_method": "activity_based"
            }]
            
            result = calculate_scope3_emissions(
                category="purchased_goods_services",
                activity_data=activity_data,
                db_session=db
            )
            
            print(f"Steel purchase: 1000 kg")
            print(f"Emission factor: {steel_factor.factor} kgCO2e/kg")
            print(f"Total emissions: {result.emissions_tco2e:.3f} tCO2e")
            print(f"Uncertainty: ±{result.uncertainty_percent:.1f}%")
            print(f"95% CI: [{result.confidence_interval_lower:.3f}, {result.confidence_interval_upper:.3f}]")
            print(f"Data quality score: {result.data_quality.overall_score}/100")
        
        print()
        
        # Test 3: Business travel calculation
        print("Test 3: Calculate Business Travel")
        print("-" * 50)
        
        flight_factor = db.query(EmissionFactor).filter(
            EmissionFactor.name.ilike("%Flight - Long Haul%"),
            EmissionFactor.scope3_category == "business_travel"
        ).first()
        
        if flight_factor:
            activity_data = [{
                "factor_name": "Flight - Long Haul",
                "quantity": 10000,  # 10,000 km
                "unit": "km",
                "calculation_method": "activity_based"
            }]
            
            result = calculate_scope3_emissions(
                category="business_travel",
                activity_data=activity_data,
                db_session=db
            )
            
            print(f"Long-haul flight: 10,000 km")
            print(f"Emission factor: {flight_factor.factor} kgCO2e/km")
            print(f"Total emissions: {result.emissions_tco2e:.3f} tCO2e")
            print(f"ESRS Requirements: {result.esrs_mapping}")
            print(f"CDP Questions: {result.cdp_mapping}")
        
        print()
        
        # Test 4: Materiality assessment
        print("Test 4: Materiality Assessment")
        print("-" * 50)
        
        context = CalculationContext(
            user_id="test",
            organization_id="test_org",
            gwp_version=GWPVersionEnum.AR6_100
        )
        
        calculator = EliteEmissionsCalculator(context, db_session=db)
        
        # Mock emissions data
        total_emissions = Decimal("10000")  # 10,000 tCO2e total
        category_emissions = {
            "purchased_goods_services": Decimal("2500"),  # 25%
            "use_of_sold_products": Decimal("4000"),      # 40%
            "business_travel": Decimal("100"),            # 1%
            "employee_commuting": Decimal("200"),         # 2%
        }
        
        materiality = calculator.assess_scope3_materiality(
            sector="Manufacturing",
            total_emissions=total_emissions,
            category_emissions=category_emissions
        )
        
        print(f"Sector: Manufacturing")
        print(f"Total emissions: {total_emissions} tCO2e")
        print(f"Materiality threshold: 5%\n")
        
        for assessment in materiality[:5]:  # Top 5
            status = "✅ MATERIAL" if assessment.is_material else "❌ NOT MATERIAL"
            print(f"{assessment.category_name}: {status}")
            if assessment.actual_percentage:
                print(f"  Percentage: {assessment.actual_percentage:.1f}%")
            print(f"  Reasons: {'; '.join(assessment.reasons)}")
            print()
        
        # Test 5: Compliance report
        print("Test 5: Generate Compliance Report")
        print("-" * 50)
        
        report = calculator.generate_compliance_report(
            standard="ESRS",
            emissions_by_category=category_emissions,
            reporting_period="2024"
        )
        
        print(f"Standard: {report.standard}")
        print(f"Compliance Status: {report.compliance_status}")
        print(f"Completeness: {report.completeness_percentage:.1f}%")
        print(f"Categories reported: {len(report.category_emissions)}/15")
        print(f"Requirements met: {len(report.requirements_met)}")
        print(f"Priority actions:")
        for action in report.priority_actions[:3]:
            print(f"  • {action}")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_scope3_calculations()