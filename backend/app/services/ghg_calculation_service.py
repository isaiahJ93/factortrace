"""
GHG Protocol Calculation Service - Fixed for SQLite
Core business logic for Scope 3 calculations
IMPROVED VERSION - Dr. Chen-Nakamura enhancements
"""
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime
import numpy as np
from sqlalchemy.orm import Session

from app.models.ghg_tables import (
    GHGCalculationResult, GHGActivityData, GHGCategoryResult,
    GHGEmissionFactor, GHGOrganization
)
from app.schemas.ghg_schemas import (
    CalculationRequest, CalculationResponse, ActivityDataInput, Scope3Category
)

class GHGCalculationService:
    def __init__(self, db: Session):
        self.db = db
        
    async def create_calculation(self, request: CalculationRequest) -> CalculationResponse:
        """Create and execute a new GHG calculation"""
        
        # Create calculation record with string ID
        calculation_id = str(uuid4())
        calculation = GHGCalculationResult(
            id=calculation_id,
            organization_id=str(request.organization_id),
            reporting_period_start=request.reporting_period_start,
            reporting_period_end=request.reporting_period_end,
            calculation_method=request.calculation_method.value,
            status="processing"
        )
        self.db.add(calculation)
        self.db.flush()  # Flush to get the ID but don't commit yet
        
        # Process activity data
        category_results = []
        total_emissions = 0.0
        
        for activity in request.activity_data:
            # Store activity data with string IDs
            activity_db = GHGActivityData(
                id=str(uuid4()),
                organization_id=str(request.organization_id),
                calculation_id=calculation_id,
                category=activity.category.value,
                activity_type=activity.activity_type,
                amount=activity.amount,
                unit=activity.unit,
                data_quality_score=activity.data_quality_score
            )
            self.db.add(activity_db)
            
            # Calculate emissions
            emissions = await self._calculate_emissions(activity)
            
            # Store category result with string ID
            category_result = GHGCategoryResult(
                id=str(uuid4()),
                calculation_id=calculation_id,
                category=activity.category.value,
                emissions_co2e=emissions['co2e'],
                uncertainty_percentage=emissions.get('uncertainty', 10.0),
                data_quality_score=activity.data_quality_score or 3.0,
                calculation_details=emissions
            )
            self.db.add(category_result)
            
            # category_results.append(EmissionResultSchema(
#                 category=activity.category,
#                 emissions_co2e=emissions['co2e'],
#                 uncertainty_range=emissions.get('uncertainty_range'),
#                 data_quality_score=activity.data_quality_score,
#                 calculation_method=request.calculation_method
            
            total_emissions += emissions['co2e']
        
        # Update calculation with results
        calculation.total_emissions = total_emissions
        calculation.status = "completed"
        calculation.completed_at = datetime.utcnow()
        
        if request.include_uncertainty:
            calculation.uncertainty_min = total_emissions * 0.9
            calculation.uncertainty_max = total_emissions * 1.1
        
        self.db.commit()
        
        return CalculationResponse(
            calculation_id=calculation_id,
            status=calculation.status,
            total_emissions=total_emissions,
            category_results=category_results,
            uncertainty_analysis=self._generate_uncertainty_analysis(category_results) if request.include_uncertainty else None,
            created_at=calculation.created_at
        )
    
    async def _calculate_emissions(self, activity: ActivityDataInput) -> Dict:
        """Calculate emissions for a single activity"""
        
        # Get emission factor
        emission_factor = self.db.query(GHGEmissionFactor).filter(
            GHGEmissionFactor.category == activity.category.value
        ).first()
        
        if not emission_factor:
            # Use default factors
            default_factors = {
                Scope3Category.PURCHASED_GOODS: 2.5,  # kg CO2e per USD
                Scope3Category.BUSINESS_TRAVEL: 0.15,  # kg CO2e per km
                Scope3Category.WASTE: 0.5,  # kg CO2e per kg
                Scope3Category.UPSTREAM_TRANSPORT: 0.1,  # kg CO2e per ton-km
            }
            factor_value = default_factors.get(activity.category, 1.0)
        else:
            factor_value = emission_factor.factor_value
        
        # Calculate emissions
        emissions_co2e = activity.amount * factor_value
        
        # Add uncertainty
        uncertainty = 0.1 if emission_factor else 0.2
        
        return {
            'co2e': emissions_co2e,
            'factor_used': factor_value,
            'uncertainty': uncertainty * 100,
            'uncertainty_range': {
                'min': emissions_co2e * (1 - uncertainty),
                'max': emissions_co2e * (1 + uncertainty)
            }
        }
    
    def _generate_uncertainty_analysis(self, results: List[Dict]) -> Dict:
        """
        Generate uncertainty analysis using Monte Carlo simulation
        IMPROVED: Now uses IPCC-compliant methodology
        """
        
        # IMPROVEMENT: Increased iterations for better accuracy
        iterations = 10000  # Was 1000
        total_emissions = []
        
        # IMPROVEMENT: Track distribution types used
        distributions_used = {}
        
        for _ in range(iterations):
            iteration_total = 0
            for i, result in enumerate(results):
                if result.get('uncertainty_range'):
                    # IMPROVEMENT: Use proper distribution based on uncertainty level
                    uncertainty_percent = result.get('uncertainty', 20)
                    base_value = result.get('emissions_co2e', 0)
                    
                    # IMPROVEMENT: Select distribution per IPCC guidelines
                    if uncertainty_percent < 30:
                        # Normal distribution for low uncertainty
                        emission = np.random.normal(
                            base_value,
                            base_value * uncertainty_percent / 100
                        )
                        distributions_used[i] = 'normal'
                    elif uncertainty_percent < 100:
                        # Lognormal for medium uncertainty
                        cv = uncertainty_percent / 100
                        sigma = np.sqrt(np.log(1 + cv**2))
                        mu = np.log(base_value) - sigma**2 / 2
                        emission = np.random.lognormal(mu, sigma)
                        distributions_used[i] = 'lognormal'
                    else:
                        # Uniform for high uncertainty (conservative)
                        emission = np.random.uniform(
                            result['uncertainty_range']['min'],
                            result['uncertainty_range']['max']
                        )
                        distributions_used[i] = 'uniform'
                else:
                    emission = result.get('emissions_co2e', 0)
                
                # Ensure non-negative emissions
                iteration_total += max(0, emission)
            total_emissions.append(iteration_total)
        
        # IMPROVEMENT: Calculate more comprehensive statistics
        results_array = np.array(total_emissions)
        
        return {
            'method': 'IPCC Tier 2 Monte Carlo',
            'iterations': iterations,
            'mean': float(np.mean(results_array)),
            'median': float(np.median(results_array)),  # IMPROVEMENT: Added median
            'std': float(np.std(results_array)),
            'cv': float(np.std(results_array) / np.mean(results_array) * 100),  # IMPROVEMENT: Added CV
            'percentiles': {
                '5': float(np.percentile(results_array, 5)),
                '10': float(np.percentile(results_array, 10)),  # IMPROVEMENT: Added P10
                '25': float(np.percentile(results_array, 25)),  # IMPROVEMENT: Added P25
                '50': float(np.percentile(results_array, 50)),
                '75': float(np.percentile(results_array, 75)),  # IMPROVEMENT: Added P75
                '90': float(np.percentile(results_array, 90)),  # IMPROVEMENT: Added P90
                '95': float(np.percentile(results_array, 95))
            },
            'confidence_interval_95': [  # IMPROVEMENT: Added explicit CI
                float(np.percentile(results_array, 2.5)),
                float(np.percentile(results_array, 97.5))
            ],
            'distributions_used': list(set(distributions_used.values()))  # IMPROVEMENT: Track distributions
        }
    
    async def get_calculation(self, calculation_id: UUID) -> Optional[GHGCalculationResult]:
        """Get calculation by ID"""
        return self.db.query(GHGCalculationResult).filter(
            GHGCalculationResult.id == str(calculation_id)
        ).first()