"""
Calculation Service for GHG Protocol Scope 3 Calculator
Manages emission calculations and inventory generation
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4
import json
import logging

import redis.asyncio as redis

from app.models.ghg_protocol_models import (
    Scope3Category, MethodologyType, EmissionFactorSource,
    Organization, EmissionFactor, ActivityData,
    CategoryCalculationResult, Scope3Inventory,
    CalculationParameters
)
from app.services.ghg_calculation_engine import CalculationEngineFactory
from app.repositories import (
    EmissionFactorRepository, ActivityDataRepository,
    CalculationResultRepository, AuditLogRepository,
    OrganizationRepository
)
from app.schemas.calculation_schemas import CalculationRequest

logger = logging.getLogger(__name__)


class CalculationService:
    """Service for managing emission calculations"""
    
    def __init__(
        self,
        ef_repo: EmissionFactorRepository,
        ad_repo: ActivityDataRepository,
        calc_repo: CalculationResultRepository,
        audit_repo: AuditLogRepository,
        cache: redis.Redis
    ):
        self.ef_repo = ef_repo
        self.ad_repo = ad_repo
        self.calc_repo = calc_repo
        self.audit_repo = audit_repo
        self.cache = cache
        self.engine_factory = CalculationEngineFactory()
        
    async def submit_calculation(
        self,
        organization_id: UUID,
        request: CalculationRequest
    ) -> UUID:
        """Submit calculation for async processing"""
        # Create calculation job
        job_id = uuid4()
        
        # Store request in cache for worker
        await self.cache.setex(
            f"calc_job:{job_id}",
            3600,  # 1 hour TTL
            json.dumps({
                "organization_id": str(organization_id),
                "request": request.dict()
            })
        )
        
        # Import here to avoid circular imports
        from app.tasks.calculation_tasks import calculate_emissions_task
        
        # Submit to Celery
        task = calculate_emissions_task.delay(str(job_id))
        
        # Store task ID for status tracking
        await self.cache.setex(
            f"calc_task:{job_id}",
            3600,
            task.id
        )
        
        return job_id
        
    async def get_calculation_status(
        self,
        job_id: UUID
    ) -> Dict[str, Any]:
        """Get status of calculation job"""
        from celery.result import AsyncResult
        from app.tasks.celery_app import celery_app
        
        # Get Celery task ID
        task_id = await self.cache.get(f"calc_task:{job_id}")
        if not task_id:
            return {"status": "not_found"}
            
        # Get task result
        result = AsyncResult(task_id, app=celery_app)
        
        return {
            "status": result.status,
            "progress": result.info.get("progress", 0) if result.info else 0,
            "current_step": result.info.get("current_step") if result.info else None,
            "result_id": result.info.get("result_id") if result.status == "SUCCESS" else None
        }
        
    async def calculate_category(
        self,
        organization_id: UUID,
        category: Scope3Category,
        activity_data: List[ActivityData],
        parameters: CalculationParameters,
        user: str
    ) -> CategoryCalculationResult:
        """Calculate emissions for a single category"""
        
        # Get appropriate emission factors
        emission_factors = await self._get_emission_factors(
            category=category,
            activity_data=activity_data,
            source_preference=parameters.emission_factor_source if hasattr(parameters, 'emission_factor_source') else None
        )
        
        # Get calculator for category
        calculator = self.engine_factory.get_calculator(category)
        
        # Perform calculation
        result = calculator.calculate(
            activity_data=activity_data,
            emission_factors=emission_factors,
            parameters=parameters
        )
        
        # Save result
        result.organization_id = organization_id
        saved_result = await self.calc_repo.save_result(result)
        
        # Audit log
        await self.audit_repo.log_action(
            organization_id=organization_id,
            user=user,
            action="calculation_completed",
            category=category,
            calculation_id=saved_result.id,
            new_value={"emissions": float(saved_result.emissions.value)}
        )
        
        return saved_result
        
    async def update_calculation(
        self,
        calculation_id: UUID,
        organization_id: UUID,
        update_data: Dict[str, Any],
        user: str
    ) -> CategoryCalculationResult:
        """Update calculation with better data"""
        
        # Get existing calculation
        existing = await self.calc_repo.get_result(calculation_id)
        if not existing or existing.organization_id != organization_id:
            raise ValueError("Calculation not found")
            
        # Create new version
        new_result = existing.copy(deep=True)
        new_result.id = uuid4()
        new_result.version = existing.version + 1
        new_result.supersedes_id = existing.id
        new_result.calculation_date = datetime.utcnow()
        
        # Apply updates
        if "activity_data" in update_data:
            # Recalculate with new data
            new_activity_data = update_data["activity_data"]
            parameters = existing.calculation_parameters
            
            new_result = await self.calculate_category(
                organization_id=organization_id,
                category=existing.category,
                activity_data=new_activity_data,
                parameters=parameters,
                user=user
            )
            
        # Save and audit
        saved_result = await self.calc_repo.save_result(new_result)
        
        await self.audit_repo.log_action(
            organization_id=organization_id,
            user=user,
            action="calculation_updated",
            category=existing.category,
            calculation_id=saved_result.id,
            previous_value={"emissions": float(existing.emissions.value)},
            new_value={"emissions": float(saved_result.emissions.value)},
            reason=update_data.get("reason")
        )
        
        return saved_result
    
    async def delete_calculation(
        self,
        calculation_id: UUID,
        user: str,
        reason: str
    ) -> None:
        """Delete a calculation (soft delete with audit trail)"""
        # Implementation would mark as deleted and log the action
        pass
        
    async def get_inventory(
        self,
        organization_id: UUID,
        year: int
    ) -> Optional[Scope3Inventory]:
        """Get or calculate complete inventory for a year"""
        
        # Check cache first
        cache_key = f"inventory:{organization_id}:{year}"
        cached = await self.cache.get(cache_key)
        if cached:
            return Scope3Inventory(**json.loads(cached))
            
        # Get all calculations for the year
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        
        category_results = {}
        for category in Scope3Category:
            result = await self.calc_repo.get_latest_result(
                organization_id=organization_id,
                category=category,
                reporting_period=start_date
            )
            if result:
                category_results[category] = result
                
        if not category_results:
            return None
            
        # Create inventory
        organization = await self._get_organization(organization_id)
        inventory = Scope3Inventory(
            organization=organization,
            reporting_year=year,
            category_results=category_results
        )
        
        # Cache for 1 hour
        await self.cache.setex(
            cache_key,
            3600,
            json.dumps(inventory.dict())
        )
        
        return inventory
        
    async def _get_emission_factors(
        self,
        category: Scope3Category,
        activity_data: List[ActivityData],
        source_preference: Optional[EmissionFactorSource] = None
    ) -> List[EmissionFactor]:
        """Get best matching emission factors for activity data"""
        
        emission_factors = []
        
        for activity in activity_data:
            # Determine search criteria from activity data
            region = activity.location
            year = activity.time_period.year
            
            # Try to get specific factor
            factor = await self.ef_repo.get_factor(
                category=category,
                region=region,
                year=year,
                activity_type=activity.metadata.get("type")
            )
            
            if factor:
                emission_factors.append(factor)
            else:
                # Get default factor
                default = await self.ef_repo.get_factor(
                    category=category,
                    year=year
                )
                if default:
                    emission_factors.append(default)
                    
        return emission_factors
        
    async def _get_organization(self, organization_id: UUID) -> Organization:
        """Get organization details"""
        # Simplified - would use OrganizationRepository
        return Organization(
            id=organization_id,
            name="Example Corp",
            industry="Manufacturing",
            reporting_year=2024,
            locations=["US", "EU", "CN"]
        )
