# app/api/v1/endpoints/issb.py
"""
ISSB (IFRS S1 + S2) API Endpoints.

Provides endpoints for managing ISSB reporting units, financial metrics,
climate risk exposures, targets, scenarios, scenario results, materiality
assessments, and disclosure statements.

Security:
- All ISSB data is tenant-owned and filtered by tenant_id from JWT
- Cross-tenant access returns 404 (not 403) to prevent enumeration
- tenant_id in request body is IGNORED - always set from authenticated user

Reference: docs/regimes/issb.md
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.core.auth import get_current_user
from app.core.tenant import (
    tenant_query,
    get_tenant_record,
    create_tenant_record,
    update_tenant_record,
    delete_tenant_record,
)
from app.schemas.auth_schemas import CurrentUser

# ISSB Models
from app.models.issb import (
    ISSBReportingUnit,
    ISSBFinancialMetric,
    ISSBClimateRiskExposure,
    ISSBTarget,
    ISSBScenario,
    ISSBScenarioResult,
    ISSBMaterialityAssessment,
    ISSBDisclosureStatement,
    ISSBConsolidationMethod,
    ISSBMetricType,
    ISSBRiskType,
    ISSBTimeHorizon,
    ISSBFinancialImpactType,
    ISSBLikelihood,
    ISSBEmissionsScope,
    ISSBTargetType,
    ISSBTargetStatus,
    ISSBScenarioResultMetric,
    ISSBMaterialityTopic,
    ISSBDisclosureStandard,
    ISSBDisclosureSection,
    ISSBDisclosureStatus,
)

# ISSB Schemas
from app.schemas.issb import (
    # Reporting Units
    ISSBReportingUnitCreate,
    ISSBReportingUnitUpdate,
    ISSBReportingUnitResponse,
    # Financial Metrics
    ISSBFinancialMetricCreate,
    ISSBFinancialMetricUpdate,
    ISSBFinancialMetricResponse,
    # Climate Risk Exposures
    ISSBClimateRiskExposureCreate,
    ISSBClimateRiskExposureUpdate,
    ISSBClimateRiskExposureResponse,
    # Targets
    ISSBTargetCreate,
    ISSBTargetUpdate,
    ISSBTargetResponse,
    # Scenarios
    ISSBScenarioCreate,
    ISSBScenarioUpdate,
    ISSBScenarioResponse,
    # Scenario Results
    ISSBScenarioResultCreate,
    ISSBScenarioResultUpdate,
    ISSBScenarioResultResponse,
    # Materiality Assessments
    ISSBMaterialityAssessmentCreate,
    ISSBMaterialityAssessmentUpdate,
    ISSBMaterialityAssessmentResponse,
    ISSBMaterialityEvaluationRequest,
    ISSBMaterialityEvaluationResponse,
    # Disclosure Statements
    ISSBDisclosureStatementCreate,
    ISSBDisclosureStatementUpdate,
    ISSBDisclosureStatementResponse,
    ISSBDisclosureGenerateRequest,
    ISSBDisclosureGenerateResponse,
    # Scenario Analysis
    ISSBScenarioAnalysisRequest,
    ISSBScenarioAnalysisResponse,
)

router = APIRouter(tags=["ISSB"])


# =============================================================================
# ISSB REPORTING UNITS (Tenant-Owned)
# =============================================================================

@router.get(
    "/reporting-units",
    response_model=List[ISSBReportingUnitResponse],
    summary="List ISSB Reporting Units",
    description="Get ISSB reporting units for the current tenant.",
)
async def list_reporting_units(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    parent_unit_id: Optional[int] = Query(None, description="Filter by parent unit"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB reporting units for current tenant."""
    query = tenant_query(db, ISSBReportingUnit, current_user.tenant_id)

    if is_active is not None:
        query = query.filter(ISSBReportingUnit.is_active == is_active)
    if sector:
        query = query.filter(ISSBReportingUnit.sector.ilike(f"%{sector}%"))
    if parent_unit_id is not None:
        query = query.filter(ISSBReportingUnit.parent_unit_id == parent_unit_id)

    return query.order_by(ISSBReportingUnit.name).offset(skip).limit(limit).all()


@router.get(
    "/reporting-units/{unit_id}",
    response_model=ISSBReportingUnitResponse,
    summary="Get ISSB Reporting Unit",
)
async def get_reporting_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB reporting unit by ID."""
    unit = get_tenant_record(db, ISSBReportingUnit, unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Reporting unit not found")
    return unit


@router.post(
    "/reporting-units",
    response_model=ISSBReportingUnitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Reporting Unit",
)
async def create_reporting_unit(
    data: ISSBReportingUnitCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB reporting unit."""
    # If parent_unit_id is provided, verify it exists and belongs to tenant
    if data.parent_unit_id:
        parent = get_tenant_record(db, ISSBReportingUnit, data.parent_unit_id, current_user.tenant_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent unit not found")

    return create_tenant_record(db, ISSBReportingUnit, data, current_user.tenant_id)


@router.patch(
    "/reporting-units/{unit_id}",
    response_model=ISSBReportingUnitResponse,
    summary="Update ISSB Reporting Unit",
)
async def update_reporting_unit(
    unit_id: int,
    data: ISSBReportingUnitUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB reporting unit."""
    # If parent_unit_id is being updated, verify it exists
    if data.parent_unit_id is not None:
        parent = get_tenant_record(db, ISSBReportingUnit, data.parent_unit_id, current_user.tenant_id)
        if not parent:
            raise HTTPException(status_code=400, detail="Parent unit not found")

    unit = update_tenant_record(db, ISSBReportingUnit, unit_id, data, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=404, detail="Reporting unit not found")
    return unit


@router.delete(
    "/reporting-units/{unit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Reporting Unit",
)
async def delete_reporting_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB reporting unit."""
    deleted = delete_tenant_record(db, ISSBReportingUnit, unit_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Reporting unit not found")
    return None


# =============================================================================
# ISSB FINANCIAL METRICS (Tenant-Owned)
# =============================================================================

@router.get(
    "/financial-metrics",
    response_model=List[ISSBFinancialMetricResponse],
    summary="List ISSB Financial Metrics",
)
async def list_financial_metrics(
    reporting_unit_id: Optional[int] = Query(None),
    metric_type: Optional[ISSBMetricType] = Query(None),
    is_audited: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB financial metrics for current tenant."""
    query = tenant_query(db, ISSBFinancialMetric, current_user.tenant_id)

    if reporting_unit_id:
        query = query.filter(ISSBFinancialMetric.reporting_unit_id == reporting_unit_id)
    if metric_type:
        query = query.filter(ISSBFinancialMetric.metric_type == metric_type)
    if is_audited is not None:
        query = query.filter(ISSBFinancialMetric.is_audited == is_audited)

    return query.order_by(ISSBFinancialMetric.period_start.desc()).offset(skip).limit(limit).all()


@router.get(
    "/financial-metrics/{metric_id}",
    response_model=ISSBFinancialMetricResponse,
    summary="Get ISSB Financial Metric",
)
async def get_financial_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB financial metric by ID."""
    metric = get_tenant_record(db, ISSBFinancialMetric, metric_id, current_user.tenant_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Financial metric not found")
    return metric


@router.post(
    "/financial-metrics",
    response_model=ISSBFinancialMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Financial Metric",
)
async def create_financial_metric(
    data: ISSBFinancialMetricCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB financial metric."""
    # Verify reporting unit exists and belongs to tenant
    unit = get_tenant_record(db, ISSBReportingUnit, data.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    return create_tenant_record(db, ISSBFinancialMetric, data, current_user.tenant_id)


@router.patch(
    "/financial-metrics/{metric_id}",
    response_model=ISSBFinancialMetricResponse,
    summary="Update ISSB Financial Metric",
)
async def update_financial_metric(
    metric_id: int,
    data: ISSBFinancialMetricUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB financial metric."""
    metric = update_tenant_record(db, ISSBFinancialMetric, metric_id, data, current_user.tenant_id)
    if not metric:
        raise HTTPException(status_code=404, detail="Financial metric not found")
    return metric


@router.delete(
    "/financial-metrics/{metric_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Financial Metric",
)
async def delete_financial_metric(
    metric_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB financial metric."""
    deleted = delete_tenant_record(db, ISSBFinancialMetric, metric_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Financial metric not found")
    return None


# =============================================================================
# ISSB CLIMATE RISK EXPOSURES (Tenant-Owned)
# =============================================================================

@router.get(
    "/climate-risks",
    response_model=List[ISSBClimateRiskExposureResponse],
    summary="List ISSB Climate Risk Exposures",
)
async def list_climate_risks(
    reporting_unit_id: Optional[int] = Query(None),
    risk_type: Optional[ISSBRiskType] = Query(None),
    time_horizon: Optional[ISSBTimeHorizon] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB climate risk exposures for current tenant."""
    query = tenant_query(db, ISSBClimateRiskExposure, current_user.tenant_id)

    if reporting_unit_id:
        query = query.filter(ISSBClimateRiskExposure.reporting_unit_id == reporting_unit_id)
    if risk_type:
        query = query.filter(ISSBClimateRiskExposure.risk_type == risk_type)
    if time_horizon:
        query = query.filter(ISSBClimateRiskExposure.time_horizon == time_horizon)
    if is_active is not None:
        query = query.filter(ISSBClimateRiskExposure.is_active == is_active)

    return query.order_by(ISSBClimateRiskExposure.id.desc()).offset(skip).limit(limit).all()


@router.get(
    "/climate-risks/{risk_id}",
    response_model=ISSBClimateRiskExposureResponse,
    summary="Get ISSB Climate Risk Exposure",
)
async def get_climate_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB climate risk exposure by ID."""
    risk = get_tenant_record(db, ISSBClimateRiskExposure, risk_id, current_user.tenant_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Climate risk exposure not found")
    return risk


@router.post(
    "/climate-risks",
    response_model=ISSBClimateRiskExposureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Climate Risk Exposure",
)
async def create_climate_risk(
    data: ISSBClimateRiskExposureCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB climate risk exposure."""
    # Verify reporting unit exists and belongs to tenant
    unit = get_tenant_record(db, ISSBReportingUnit, data.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    return create_tenant_record(db, ISSBClimateRiskExposure, data, current_user.tenant_id)


@router.patch(
    "/climate-risks/{risk_id}",
    response_model=ISSBClimateRiskExposureResponse,
    summary="Update ISSB Climate Risk Exposure",
)
async def update_climate_risk(
    risk_id: int,
    data: ISSBClimateRiskExposureUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB climate risk exposure."""
    risk = update_tenant_record(db, ISSBClimateRiskExposure, risk_id, data, current_user.tenant_id)
    if not risk:
        raise HTTPException(status_code=404, detail="Climate risk exposure not found")
    return risk


@router.delete(
    "/climate-risks/{risk_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Climate Risk Exposure",
)
async def delete_climate_risk(
    risk_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB climate risk exposure."""
    deleted = delete_tenant_record(db, ISSBClimateRiskExposure, risk_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Climate risk exposure not found")
    return None


# =============================================================================
# ISSB TARGETS (Tenant-Owned)
# =============================================================================

@router.get(
    "/targets",
    response_model=List[ISSBTargetResponse],
    summary="List ISSB Targets",
)
async def list_targets(
    reporting_unit_id: Optional[int] = Query(None),
    target_type: Optional[ISSBTargetType] = Query(None),
    target_status: Optional[ISSBTargetStatus] = Query(None),
    target_year: Optional[int] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB targets for current tenant."""
    query = tenant_query(db, ISSBTarget, current_user.tenant_id)

    if reporting_unit_id:
        query = query.filter(ISSBTarget.reporting_unit_id == reporting_unit_id)
    if target_type:
        query = query.filter(ISSBTarget.target_type == target_type)
    if target_status:
        query = query.filter(ISSBTarget.status == target_status)
    if target_year:
        query = query.filter(ISSBTarget.target_year == target_year)
    if is_active is not None:
        query = query.filter(ISSBTarget.is_active == is_active)

    return query.order_by(ISSBTarget.target_year).offset(skip).limit(limit).all()


@router.get(
    "/targets/{target_id}",
    response_model=ISSBTargetResponse,
    summary="Get ISSB Target",
)
async def get_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB target by ID."""
    target = get_tenant_record(db, ISSBTarget, target_id, current_user.tenant_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.post(
    "/targets",
    response_model=ISSBTargetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Target",
)
async def create_target(
    data: ISSBTargetCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB target."""
    # Verify reporting unit exists and belongs to tenant
    unit = get_tenant_record(db, ISSBReportingUnit, data.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    return create_tenant_record(db, ISSBTarget, data, current_user.tenant_id)


@router.patch(
    "/targets/{target_id}",
    response_model=ISSBTargetResponse,
    summary="Update ISSB Target",
)
async def update_target(
    target_id: int,
    data: ISSBTargetUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB target."""
    target = update_tenant_record(db, ISSBTarget, target_id, data, current_user.tenant_id)
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target


@router.delete(
    "/targets/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Target",
)
async def delete_target(
    target_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB target."""
    deleted = delete_tenant_record(db, ISSBTarget, target_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Target not found")
    return None


# =============================================================================
# ISSB SCENARIOS (Tenant-Owned)
# =============================================================================

@router.get(
    "/scenarios",
    response_model=List[ISSBScenarioResponse],
    summary="List ISSB Scenarios",
)
async def list_scenarios(
    temperature_pathway: Optional[str] = Query(None),
    is_default: Optional[bool] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB scenarios for current tenant."""
    query = tenant_query(db, ISSBScenario, current_user.tenant_id)

    if temperature_pathway:
        query = query.filter(ISSBScenario.temperature_pathway == temperature_pathway)
    if is_default is not None:
        query = query.filter(ISSBScenario.is_default == is_default)
    if is_active is not None:
        query = query.filter(ISSBScenario.is_active == is_active)

    return query.order_by(ISSBScenario.name).offset(skip).limit(limit).all()


@router.get(
    "/scenarios/{scenario_id}",
    response_model=ISSBScenarioResponse,
    summary="Get ISSB Scenario",
)
async def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB scenario by ID."""
    scenario = get_tenant_record(db, ISSBScenario, scenario_id, current_user.tenant_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post(
    "/scenarios",
    response_model=ISSBScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Scenario",
)
async def create_scenario(
    data: ISSBScenarioCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB scenario."""
    # If setting as default, unset other defaults
    if data.is_default:
        existing_defaults = tenant_query(db, ISSBScenario, current_user.tenant_id).filter(
            ISSBScenario.is_default == True
        ).all()
        for scenario in existing_defaults:
            scenario.is_default = False

    return create_tenant_record(db, ISSBScenario, data, current_user.tenant_id)


@router.patch(
    "/scenarios/{scenario_id}",
    response_model=ISSBScenarioResponse,
    summary="Update ISSB Scenario",
)
async def update_scenario(
    scenario_id: int,
    data: ISSBScenarioUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB scenario."""
    # If setting as default, unset other defaults
    if data.is_default:
        existing_defaults = tenant_query(db, ISSBScenario, current_user.tenant_id).filter(
            ISSBScenario.is_default == True,
            ISSBScenario.id != scenario_id
        ).all()
        for scenario in existing_defaults:
            scenario.is_default = False

    scenario = update_tenant_record(db, ISSBScenario, scenario_id, data, current_user.tenant_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete(
    "/scenarios/{scenario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Scenario",
)
async def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB scenario."""
    deleted = delete_tenant_record(db, ISSBScenario, scenario_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return None


# =============================================================================
# ISSB SCENARIO RESULTS (Tenant-Owned)
# =============================================================================

@router.get(
    "/scenario-results",
    response_model=List[ISSBScenarioResultResponse],
    summary="List ISSB Scenario Results",
)
async def list_scenario_results(
    scenario_id: Optional[int] = Query(None),
    reporting_unit_id: Optional[int] = Query(None),
    metric_type: Optional[ISSBScenarioResultMetric] = Query(None),
    projection_year: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB scenario results for current tenant."""
    query = tenant_query(db, ISSBScenarioResult, current_user.tenant_id)

    if scenario_id:
        query = query.filter(ISSBScenarioResult.scenario_id == scenario_id)
    if reporting_unit_id:
        query = query.filter(ISSBScenarioResult.reporting_unit_id == reporting_unit_id)
    if metric_type:
        query = query.filter(ISSBScenarioResult.metric_type == metric_type)
    if projection_year:
        query = query.filter(ISSBScenarioResult.projection_year == projection_year)

    return query.order_by(ISSBScenarioResult.id.desc()).offset(skip).limit(limit).all()


@router.get(
    "/scenario-results/{result_id}",
    response_model=ISSBScenarioResultResponse,
    summary="Get ISSB Scenario Result",
)
async def get_scenario_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB scenario result by ID."""
    result = get_tenant_record(db, ISSBScenarioResult, result_id, current_user.tenant_id)
    if not result:
        raise HTTPException(status_code=404, detail="Scenario result not found")
    return result


@router.post(
    "/scenario-results",
    response_model=ISSBScenarioResultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Scenario Result",
)
async def create_scenario_result(
    data: ISSBScenarioResultCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB scenario result."""
    # Verify scenario exists and belongs to tenant
    scenario = get_tenant_record(db, ISSBScenario, data.scenario_id, current_user.tenant_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="Scenario not found")

    # Verify reporting unit exists and belongs to tenant
    unit = get_tenant_record(db, ISSBReportingUnit, data.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    return create_tenant_record(db, ISSBScenarioResult, data, current_user.tenant_id)


@router.delete(
    "/scenario-results/{result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Scenario Result",
)
async def delete_scenario_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB scenario result."""
    deleted = delete_tenant_record(db, ISSBScenarioResult, result_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario result not found")
    return None


# =============================================================================
# ISSB SCENARIO ANALYSIS (Computed)
# =============================================================================

@router.post(
    "/scenario-analysis/run",
    response_model=ISSBScenarioAnalysisResponse,
    summary="Run ISSB Scenario Analysis",
    description="Run climate scenario analysis for a reporting unit using specified scenario.",
)
async def run_scenario_analysis(
    request: ISSBScenarioAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Run climate scenario analysis.

    Computes carbon cost exposure and financial impacts based on:
    - Scenario's carbon price path
    - Emissions provided
    - Base case financials (optional)
    """
    # Verify reporting unit
    unit = get_tenant_record(db, ISSBReportingUnit, request.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    # Verify scenario
    scenario = get_tenant_record(db, ISSBScenario, request.scenario_id, current_user.tenant_id)
    if not scenario:
        raise HTTPException(status_code=400, detail="Scenario not found")

    # Get carbon price for projection year
    carbon_price_path = scenario.carbon_price_path_json or {}
    year_str = str(request.projection_year)
    carbon_price = carbon_price_path.get(year_str, 0.0)

    # Calculate cost of carbon
    cost_of_carbon = request.emissions_tco2e * carbon_price

    # Build results
    results = []
    now = datetime.utcnow()

    # Cost of carbon result
    cost_result = ISSBScenarioResult(
        tenant_id=current_user.tenant_id,
        scenario_id=request.scenario_id,
        reporting_unit_id=request.reporting_unit_id,
        period_start=now,
        period_end=now,
        projection_year=request.projection_year,
        metric_type=ISSBScenarioResultMetric.COST_OF_CARBON,
        base_case_value=0.0,
        scenario_value=cost_of_carbon,
        delta_value=cost_of_carbon,
        delta_percentage=None,
        currency=unit.currency,
        calculation_date=now,
        carbon_price_used=carbon_price,
        emissions_used=request.emissions_tco2e,
    )
    db.add(cost_result)

    # EBITDA impact if base provided
    if request.base_ebitda:
        ebitda_scenario = request.base_ebitda - cost_of_carbon
        ebitda_delta_pct = (ebitda_scenario - request.base_ebitda) / request.base_ebitda * 100 if request.base_ebitda else None

        ebitda_result = ISSBScenarioResult(
            tenant_id=current_user.tenant_id,
            scenario_id=request.scenario_id,
            reporting_unit_id=request.reporting_unit_id,
            period_start=now,
            period_end=now,
            projection_year=request.projection_year,
            metric_type=ISSBScenarioResultMetric.EBITDA,
            base_case_value=request.base_ebitda,
            scenario_value=ebitda_scenario,
            delta_value=ebitda_scenario - request.base_ebitda,
            delta_percentage=ebitda_delta_pct,
            currency=unit.currency,
            calculation_date=now,
            carbon_price_used=carbon_price,
            emissions_used=request.emissions_tco2e,
        )
        db.add(ebitda_result)

    db.commit()
    db.refresh(cost_result)

    # Get all results for this analysis
    analysis_results = tenant_query(db, ISSBScenarioResult, current_user.tenant_id).filter(
        ISSBScenarioResult.scenario_id == request.scenario_id,
        ISSBScenarioResult.reporting_unit_id == request.reporting_unit_id,
        ISSBScenarioResult.projection_year == request.projection_year,
    ).all()

    return ISSBScenarioAnalysisResponse(
        scenario_id=request.scenario_id,
        scenario_name=scenario.name,
        temperature_pathway=scenario.temperature_pathway,
        projection_year=request.projection_year,
        carbon_price=carbon_price,
        cost_of_carbon=cost_of_carbon,
        results=[ISSBScenarioResultResponse.model_validate(r) for r in analysis_results],
    )


# =============================================================================
# ISSB MATERIALITY ASSESSMENTS (Tenant-Owned)
# =============================================================================

@router.get(
    "/materiality-assessments",
    response_model=List[ISSBMaterialityAssessmentResponse],
    summary="List ISSB Materiality Assessments",
)
async def list_materiality_assessments(
    reporting_unit_id: Optional[int] = Query(None),
    topic: Optional[ISSBMaterialityTopic] = Query(None),
    is_final: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB materiality assessments for current tenant."""
    query = tenant_query(db, ISSBMaterialityAssessment, current_user.tenant_id)

    if reporting_unit_id:
        query = query.filter(ISSBMaterialityAssessment.reporting_unit_id == reporting_unit_id)
    if topic:
        query = query.filter(ISSBMaterialityAssessment.topic == topic)
    if is_final is not None:
        query = query.filter(ISSBMaterialityAssessment.is_final == is_final)

    return query.order_by(ISSBMaterialityAssessment.id.desc()).offset(skip).limit(limit).all()


@router.get(
    "/materiality-assessments/{assessment_id}",
    response_model=ISSBMaterialityAssessmentResponse,
    summary="Get ISSB Materiality Assessment",
)
async def get_materiality_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB materiality assessment by ID."""
    assessment = get_tenant_record(db, ISSBMaterialityAssessment, assessment_id, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Materiality assessment not found")
    return assessment


@router.post(
    "/materiality-assessments",
    response_model=ISSBMaterialityAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Materiality Assessment",
)
async def create_materiality_assessment(
    data: ISSBMaterialityAssessmentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB materiality assessment."""
    # Verify reporting unit exists and belongs to tenant
    unit = get_tenant_record(db, ISSBReportingUnit, data.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    return create_tenant_record(db, ISSBMaterialityAssessment, data, current_user.tenant_id)


@router.patch(
    "/materiality-assessments/{assessment_id}",
    response_model=ISSBMaterialityAssessmentResponse,
    summary="Update ISSB Materiality Assessment",
)
async def update_materiality_assessment(
    assessment_id: int,
    data: ISSBMaterialityAssessmentUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB materiality assessment."""
    assessment = update_tenant_record(db, ISSBMaterialityAssessment, assessment_id, data, current_user.tenant_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Materiality assessment not found")
    return assessment


@router.delete(
    "/materiality-assessments/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Materiality Assessment",
)
async def delete_materiality_assessment(
    assessment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB materiality assessment."""
    deleted = delete_tenant_record(db, ISSBMaterialityAssessment, assessment_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Materiality assessment not found")
    return None


# =============================================================================
# ISSB MATERIALITY EVALUATION (Computed)
# =============================================================================

@router.post(
    "/materiality/evaluate",
    response_model=ISSBMaterialityEvaluationResponse,
    summary="Evaluate Materiality",
    description="Run double materiality evaluation for a reporting unit and topic.",
)
async def evaluate_materiality(
    request: ISSBMaterialityEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Evaluate double materiality.

    Computes impact and financial materiality scores based on:
    - Climate risk exposures
    - Financial metrics (revenue at risk)
    - Emissions data
    """
    # Verify reporting unit
    unit = get_tenant_record(db, ISSBReportingUnit, request.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    # Get climate risks for the unit
    risks = tenant_query(db, ISSBClimateRiskExposure, current_user.tenant_id).filter(
        ISSBClimateRiskExposure.reporting_unit_id == request.reporting_unit_id,
        ISSBClimateRiskExposure.is_active == True,
    ).all()

    # Get financial metrics for the period
    metrics = tenant_query(db, ISSBFinancialMetric, current_user.tenant_id).filter(
        ISSBFinancialMetric.reporting_unit_id == request.reporting_unit_id,
        ISSBFinancialMetric.period_start >= request.period_start,
        ISSBFinancialMetric.period_end <= request.period_end,
    ).all()

    # Simple scoring logic (placeholder - should be enhanced)
    # Impact materiality: based on risk count and severity
    high_risks = [r for r in risks if r.qualitative_likelihood in [ISSBLikelihood.HIGH, ISSBLikelihood.VERY_HIGH]]
    impact_score = min(100, len(high_risks) * 20 + len(risks) * 5)

    # Financial materiality: based on impact ranges
    total_impact = sum(
        (r.impact_range_high or 0) for r in risks if r.impact_range_high
    )
    revenue_metrics = [m for m in metrics if m.metric_type == ISSBMetricType.REVENUE]
    total_revenue = sum(m.value for m in revenue_metrics) if revenue_metrics else 1

    financial_score = min(100, (total_impact / total_revenue * 100) if total_revenue else 0)

    # Determine materiality
    overall_material = (
        impact_score >= request.threshold or
        financial_score >= request.threshold
    )

    # Build justification
    justification = (
        f"Impact score: {impact_score:.1f}/100 (based on {len(risks)} risks, {len(high_risks)} high/very high). "
        f"Financial score: {financial_score:.1f}/100 (based on {total_impact:,.0f} potential impact vs {total_revenue:,.0f} revenue). "
        f"Threshold: {request.threshold}. {'Material' if overall_material else 'Not material'}."
    )

    # Create assessment record
    assessment = ISSBMaterialityAssessment(
        tenant_id=current_user.tenant_id,
        reporting_unit_id=request.reporting_unit_id,
        period_start=request.period_start,
        period_end=request.period_end,
        topic=request.topic,
        impact_materiality_score=impact_score,
        financial_materiality_score=financial_score,
        material=overall_material,
        materiality_threshold=request.threshold,
        justification=justification,
        methodology_reference="automated_double_materiality_v1",
        revenue_total=total_revenue,
        revenue_exposed=total_impact,
        is_final=False,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    return ISSBMaterialityEvaluationResponse(
        reporting_unit_id=request.reporting_unit_id,
        topic=request.topic,
        impact_materiality_score=impact_score,
        financial_materiality_score=financial_score,
        overall_material=overall_material,
        threshold_used=request.threshold,
        justification=justification,
        assessment_id=assessment.id,
    )


# =============================================================================
# ISSB DISCLOSURE STATEMENTS (Tenant-Owned)
# =============================================================================

@router.get(
    "/disclosures",
    response_model=List[ISSBDisclosureStatementResponse],
    summary="List ISSB Disclosure Statements",
)
async def list_disclosures(
    reporting_unit_id: Optional[int] = Query(None),
    standard: Optional[ISSBDisclosureStandard] = Query(None),
    section: Optional[ISSBDisclosureSection] = Query(None),
    disclosure_status: Optional[ISSBDisclosureStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List ISSB disclosure statements for current tenant."""
    query = tenant_query(db, ISSBDisclosureStatement, current_user.tenant_id)

    if reporting_unit_id:
        query = query.filter(ISSBDisclosureStatement.reporting_unit_id == reporting_unit_id)
    if standard:
        query = query.filter(ISSBDisclosureStatement.standard == standard)
    if section:
        query = query.filter(ISSBDisclosureStatement.section == section)
    if disclosure_status:
        query = query.filter(ISSBDisclosureStatement.status == disclosure_status)

    return query.order_by(ISSBDisclosureStatement.id.desc()).offset(skip).limit(limit).all()


@router.get(
    "/disclosures/{disclosure_id}",
    response_model=ISSBDisclosureStatementResponse,
    summary="Get ISSB Disclosure Statement",
)
async def get_disclosure(
    disclosure_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific ISSB disclosure statement by ID."""
    disclosure = get_tenant_record(db, ISSBDisclosureStatement, disclosure_id, current_user.tenant_id)
    if not disclosure:
        raise HTTPException(status_code=404, detail="Disclosure statement not found")
    return disclosure


@router.post(
    "/disclosures",
    response_model=ISSBDisclosureStatementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create ISSB Disclosure Statement",
)
async def create_disclosure(
    data: ISSBDisclosureStatementCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new ISSB disclosure statement."""
    # Verify reporting unit exists and belongs to tenant
    unit = get_tenant_record(db, ISSBReportingUnit, data.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    return create_tenant_record(db, ISSBDisclosureStatement, data, current_user.tenant_id)


@router.patch(
    "/disclosures/{disclosure_id}",
    response_model=ISSBDisclosureStatementResponse,
    summary="Update ISSB Disclosure Statement",
)
async def update_disclosure(
    disclosure_id: int,
    data: ISSBDisclosureStatementUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an ISSB disclosure statement."""
    # Track edit count
    disclosure = get_tenant_record(db, ISSBDisclosureStatement, disclosure_id, current_user.tenant_id)
    if not disclosure:
        raise HTTPException(status_code=404, detail="Disclosure statement not found")

    if data.body_markdown is not None or data.body_html is not None:
        if data.edit_count is None:
            data.edit_count = (disclosure.edit_count or 0) + 1
        data.last_edited_at = datetime.utcnow()

    updated = update_tenant_record(db, ISSBDisclosureStatement, disclosure_id, data, current_user.tenant_id)
    return updated


@router.delete(
    "/disclosures/{disclosure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete ISSB Disclosure Statement",
)
async def delete_disclosure(
    disclosure_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an ISSB disclosure statement."""
    deleted = delete_tenant_record(db, ISSBDisclosureStatement, disclosure_id, current_user.tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Disclosure statement not found")
    return None


# =============================================================================
# ISSB DISCLOSURE GENERATION (Computed)
# =============================================================================

@router.post(
    "/disclosures/generate",
    response_model=ISSBDisclosureGenerateResponse,
    summary="Generate ISSB Disclosures",
    description="Auto-generate ISSB disclosure statements for a reporting unit.",
)
async def generate_disclosures(
    request: ISSBDisclosureGenerateRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate ISSB disclosure statements.

    Creates draft disclosures for each section (Governance, Strategy,
    Risk Management, Metrics & Targets) based on existing data.
    """
    # Verify reporting unit
    unit = get_tenant_record(db, ISSBReportingUnit, request.reporting_unit_id, current_user.tenant_id)
    if not unit:
        raise HTTPException(status_code=400, detail="Reporting unit not found")

    sections = request.sections or [
        ISSBDisclosureSection.GOVERNANCE,
        ISSBDisclosureSection.STRATEGY,
        ISSBDisclosureSection.RISK_MANAGEMENT,
        ISSBDisclosureSection.METRICS_TARGETS,
    ]

    now = datetime.utcnow()
    disclosures = []

    # Get data for disclosure generation
    risks = tenant_query(db, ISSBClimateRiskExposure, current_user.tenant_id).filter(
        ISSBClimateRiskExposure.reporting_unit_id == request.reporting_unit_id,
        ISSBClimateRiskExposure.is_active == True,
    ).all()

    targets = tenant_query(db, ISSBTarget, current_user.tenant_id).filter(
        ISSBTarget.reporting_unit_id == request.reporting_unit_id,
        ISSBTarget.is_active == True,
    ).all()

    scenarios = tenant_query(db, ISSBScenario, current_user.tenant_id).filter(
        ISSBScenario.is_active == True,
    ).all()

    for section in sections:
        # Generate content based on section
        if section == ISSBDisclosureSection.GOVERNANCE:
            headline = f"Climate governance for {unit.name}"
            body_md = (
                f"## Governance\n\n"
                f"The organization has established climate governance structures for {unit.name}.\n\n"
                f"### Board Oversight\n\n"
                f"[Board oversight of climate-related risks and opportunities to be documented]\n\n"
                f"### Management Role\n\n"
                f"[Management's role in assessing and managing climate-related risks to be documented]\n"
            )
        elif section == ISSBDisclosureSection.STRATEGY:
            headline = f"Climate strategy for {unit.name}"
            body_md = (
                f"## Strategy\n\n"
                f"### Climate Risks and Opportunities\n\n"
                f"Identified **{len(risks)}** climate-related risks.\n\n"
                f"### Scenario Analysis\n\n"
                f"**{len(scenarios)}** climate scenarios have been defined for analysis.\n\n"
                f"### Business Model Impacts\n\n"
                f"[Impact on business model and value chain to be documented]\n"
            )
        elif section == ISSBDisclosureSection.RISK_MANAGEMENT:
            physical_risks = [r for r in risks if r.risk_type == ISSBRiskType.PHYSICAL]
            transition_risks = [r for r in risks if r.risk_type == ISSBRiskType.TRANSITION]
            headline = f"Climate risk management for {unit.name}"
            body_md = (
                f"## Risk Management\n\n"
                f"### Physical Risks\n\n"
                f"Identified **{len(physical_risks)}** physical climate risks.\n\n"
                f"### Transition Risks\n\n"
                f"Identified **{len(transition_risks)}** transition risks.\n\n"
                f"### Integration with Enterprise Risk Management\n\n"
                f"[Integration details to be documented]\n"
            )
        else:  # METRICS_TARGETS
            sbti_targets = [t for t in targets if t.is_sbti_validated]
            headline = f"Climate metrics and targets for {unit.name}"
            body_md = (
                f"## Metrics and Targets\n\n"
                f"### Emissions Metrics\n\n"
                f"[Scope 1, 2, 3 emissions to be documented]\n\n"
                f"### Climate Targets\n\n"
                f"**{len(targets)}** climate targets defined ({len(sbti_targets)} SBTi validated).\n\n"
                f"### Target Progress\n\n"
                f"[Target progress to be documented]\n"
            )

        # Create disclosure
        disclosure = ISSBDisclosureStatement(
            tenant_id=current_user.tenant_id,
            reporting_unit_id=request.reporting_unit_id,
            period_start=request.period_start,
            period_end=request.period_end,
            standard=request.standard,
            section=section,
            headline_summary=headline[:500],
            body_markdown=body_md,
            generated_by_system=True,
            generation_date=now,
            template_version="v1.0",
            status=ISSBDisclosureStatus.DRAFT,
        )
        db.add(disclosure)
        disclosures.append(disclosure)

    db.commit()

    # Refresh all disclosures
    for d in disclosures:
        db.refresh(d)

    return ISSBDisclosureGenerateResponse(
        reporting_unit_id=request.reporting_unit_id,
        period_start=request.period_start,
        period_end=request.period_end,
        standard=request.standard,
        disclosures=[ISSBDisclosureStatementResponse.model_validate(d) for d in disclosures],
        generation_timestamp=now,
    )


@router.post(
    "/disclosures/{disclosure_id}/approve",
    response_model=ISSBDisclosureStatementResponse,
    summary="Approve ISSB Disclosure",
)
async def approve_disclosure(
    disclosure_id: int,
    approved_by: str = Query(..., description="Name of approver"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Approve an ISSB disclosure statement."""
    disclosure = get_tenant_record(db, ISSBDisclosureStatement, disclosure_id, current_user.tenant_id)
    if not disclosure:
        raise HTTPException(status_code=404, detail="Disclosure statement not found")

    disclosure.status = ISSBDisclosureStatus.APPROVED
    disclosure.approved_by = approved_by
    disclosure.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(disclosure)
    return disclosure


@router.post(
    "/disclosures/{disclosure_id}/archive",
    response_model=ISSBDisclosureStatementResponse,
    summary="Archive ISSB Disclosure",
)
async def archive_disclosure(
    disclosure_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Archive an ISSB disclosure statement."""
    disclosure = get_tenant_record(db, ISSBDisclosureStatement, disclosure_id, current_user.tenant_id)
    if not disclosure:
        raise HTTPException(status_code=404, detail="Disclosure statement not found")

    disclosure.status = ISSBDisclosureStatus.ARCHIVED

    db.commit()
    db.refresh(disclosure)
    return disclosure
