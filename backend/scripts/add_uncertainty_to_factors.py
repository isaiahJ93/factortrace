import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.emission_factor import EmissionFactor, UncertaintyAssessment

# Default uncertainty by category type
UNCERTAINTY_DEFAULTS = {
    # High certainty (5-10%)
    "stationary_combustion": 5.0,
    "purchased_electricity": 7.5,
    
    # Medium certainty (10-20%)
    "mobile_combustion": 15.0,
    "business_travel": 12.0,
    "employee_commuting": 20.0,
    
    # Lower certainty (20-30%)
    "waste_operations": 25.0,
    "purchased_goods_services": 30.0,
    "upstream_transportation": 20.0,
}

def add_uncertainty():
    db = SessionLocal()
    
    try:
        factors = db.query(EmissionFactor).filter(
            EmissionFactor.uncertainty_assessment_id.is_(None)
        ).all()
        
        print(f"Found {len(factors)} factors without uncertainty data")
        
        for factor in factors:
            # Get default uncertainty for category
            uncertainty_pct = UNCERTAINTY_DEFAULTS.get(factor.category, 15.0)
            
            # Create uncertainty assessment
            uncertainty = UncertaintyAssessment(
                uncertainty_percentage=uncertainty_pct,
                lower_bound=factor.factor * (1 - uncertainty_pct/100),
                upper_bound=factor.factor * (1 + uncertainty_pct/100),
                confidence_level=95.0,
                distribution='normal',
                method='monte_carlo'
            )
            db.add(uncertainty)
            db.flush()
            
            # Link to factor
            factor.uncertainty_assessment_id = uncertainty.id
            
            # Add data quality score based on source
            if 'EPA' in (factor.source or ''):
                factor.data_quality_score = 2  # Good
            elif 'DEFRA' in (factor.source or ''):
                factor.data_quality_score = 2  # Good
            elif 'IPCC' in (factor.source or ''):
                factor.data_quality_score = 1  # Excellent
            else:
                factor.data_quality_score = 3  # Fair
        
        db.commit()
        print(f"✅ Added uncertainty data to {len(factors)} factors")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_uncertainty()
