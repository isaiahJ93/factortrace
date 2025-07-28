"""
Analytics Service for GHG Protocol Scope 3 Calculator
Generates insights and analytics from emission data
"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID
from collections import defaultdict

import numpy as np

from app.models.ghg_protocol_models import CategoryCalculationResult
from app.repositories import CalculationResultRepository

import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for analytics and insights"""
    
    def __init__(self, calc_repo: CalculationResultRepository):
        self.calc_repo = calc_repo
        
    async def get_analytics(
        self,
        organization_id: UUID,
        start_date: date,
        end_date: date,
        metrics: List[str],
        group_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate analytics for the period"""
        
        # Get all calculations in period
        results = await self.calc_repo.get_results(
            organization_id=organization_id,
            start_date=start_date,
            end_date=end_date
        )
        
        analytics = {
            "period_start": start_date,
            "period_end": end_date,
            "metrics": [],
            "insights": []
        }
        
        # Calculate requested metrics
        if "total_emissions" in metrics:
            total = sum(r.emissions.value for r in results)
            analytics["metrics"].append({
                "name": "total_emissions",
                "value": float(total),
                "unit": "kgCO2e"
            })
            
        if "emissions_by_category" in metrics:
            by_category = defaultdict(Decimal)
            for r in results:
                by_category[r.category] += r.emissions.value
                
            analytics["emissions_by_category"] = {
                cat.value: float(val) for cat, val in by_category.items()
            }
            
        if "data_quality" in metrics:
            if results:
                avg_quality = np.mean([r.data_quality_score for r in results])
                analytics["metrics"].append({
                    "name": "average_data_quality",
                    "value": float(avg_quality),
                    "unit": "score"
                })
                
        # Time series if requested
        if group_by == "month":
            time_series = defaultdict(lambda: defaultdict(Decimal))
            for r in results:
                month_key = r.reporting_period.strftime("%Y-%m")
                time_series[month_key][r.category] += r.emissions.value
                
            analytics["time_series"] = {
                month: {cat.value: float(val) for cat, val in cats.items()}
                for month, cats in time_series.items()
            }
            
        # Generate insights
        analytics["insights"] = self._generate_insights(results, analytics)
        
        # Generate recommendations
        analytics["recommendations"] = self._generate_recommendations(results, analytics)
        
        return analytics
        
    def _generate_insights(
        self,
        results: List[CategoryCalculationResult],
        analytics: Dict
    ) -> List[str]:
        """Generate actionable insights from data"""
        insights = []
        
        # Find largest emission sources
        if "emissions_by_category" in analytics:
            sorted_cats = sorted(
                analytics["emissions_by_category"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            if sorted_cats:
                top_cat = sorted_cats[0]
                insights.append(
                    f"{top_cat[0].replace('_', ' ').title()} represents your largest "
                    f"emission source at {top_cat[1]/1000:.1f} tCO2e"
                )
                
        # Data quality insights
        low_quality = [r for r in results if r.data_quality_score > 3.5]
        if low_quality:
            categories = list(set(r.category.value for r in low_quality))
            insights.append(
                f"Consider improving data quality for: {', '.join(categories)}"
            )
            
        # Trend insights
        if "time_series" in analytics and len(analytics["time_series"]) > 1:
            months = sorted(analytics["time_series"].keys())
            first_month_total = sum(analytics["time_series"][months[0]].values())
            last_month_total = sum(analytics["time_series"][months[-1]].values())
            
            if first_month_total > 0:
                change = ((last_month_total - first_month_total) / first_month_total) * 100
                if abs(change) > 5:
                    direction = "increased" if change > 0 else "decreased"
                    insights.append(
                        f"Emissions {direction} by {abs(change):.1f}% over the period"
                    )
                
        # Coverage insights
        calculated_categories = set(r.category for r in results)
        missing_categories = set(Scope3Category) - calculated_categories
        if missing_categories:
            insights.append(
                f"Consider calculating emissions for: "
                f"{', '.join(cat.value.replace('_', ' ').title() for cat in list(missing_categories)[:3])}"
            )
                
        return insights
    
    def _generate_recommendations(
        self,
        results: List[CategoryCalculationResult],
        analytics: Dict
    ) -> List[str]:
        """Generate recommendations based on analytics"""
        recommendations = []
        
        # High emission categories
        if "emissions_by_category" in analytics:
            for cat, emissions in analytics["emissions_by_category"].items():
                if emissions > 100000:  # 100 tCO2e
                    recommendations.append(
                        f"Develop reduction strategy for {cat.replace('_', ' ').title()} emissions"
                    )
                    
        # Data quality recommendations
        avg_quality = np.mean([r.data_quality_score for r in results]) if results else 5.0
        if avg_quality > 3.0:
            recommendations.append(
                "Invest in primary data collection to improve calculation accuracy"
            )
            
        # Uncertainty recommendations
        high_uncertainty = [
            r for r in results 
            if r.emissions.uncertainty_upper and r.emissions.uncertainty_lower
            and (float(r.emissions.uncertainty_upper - r.emissions.uncertainty_lower) / float(r.emissions.value)) > 0.5
        ]
        if high_uncertainty:
            recommendations.append(
                "Focus on reducing uncertainty in high-impact categories through better data"
            )
            
        return recommendations
    
    async def get_benchmarks(
        self,
        organization_id: UUID,
        industry: str,
        year: int
    ) -> Dict[str, Any]:
        """Get industry benchmarks for comparison"""
        # Implementation would fetch industry-specific benchmarks
        # This is a placeholder
        return {
            "industry": industry,
            "year": year,
            "average_intensity": 0.5,  # tCO2e per unit
            "percentile_25": 0.3,
            "percentile_75": 0.7,
            "best_in_class": 0.1
        }
