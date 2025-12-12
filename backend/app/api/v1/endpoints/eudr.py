# app/api/v1/endpoints/eudr.py
"""
EUDR (EU Deforestation Regulation) API Endpoints.

Provides endpoints for managing EUDR commodities, operators, supply sites,
batches, supply chain links, geo risk snapshots, and due diligence assessments.

Security:
- All tenant-owned data filtered by tenant_id from JWT
- Cross-tenant access returns 404 (not 403) to prevent enumeration
- tenant_id in request body is IGNORED - always set from authenticated user
- EUDRCommodity is global reference data (no tenant filter)

Reference: docs/regimes/eudr.md
"""
from datetime import datetime
from typing import List, Optional, Dict, Set
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

# EUDR Models
from app.models.eudr import (
    EUDRCommodity,
    EUDROperator,
    EUDRSupplySite,
    EUDRBatch,
    EUDRSupplyChainLink,
    EUDRGeoRiskSnapshot,
    EUDRDueDiligence,
    EUDRDueDiligenceBatchLink,
    EUDRCommodityType,
    EUDROperatorRole,
    EUDRSupplyChainLinkType,
    EUDRRiskLevel,
    EUDRDueDiligenceStatus,
    EUDRGeoRiskSource,
)

# EUDR Schemas
from app.schemas.eudr import (
    # Commodities
    EUDRCommodityCreate,
    EUDRCommodityUpdate,
    EUDRCommodityResponse,
    # Operators
    EUDROperatorCreate,
    EUDROperatorUpdate,
    EUDROperatorResponse,
    # Supply Sites
    EUDRSupplySiteCreate,
    EUDRSupplySiteUpdate,
    EUDRSupplySiteResponse,
    EUDRSupplySiteSummary,
    # Batches
    EUDRBatchCreate,
    EUDRBatchUpdate,
    EUDRBatchResponse,
    EUDRBatchSummary,
    # Supply Chain Links
    EUDRSupplyChainLinkCreate,
    EUDRSupplyChainLinkResponse,
    # Geo Risk Snapshots
    EUDRGeoRiskSnapshotCreate,
    EUDRGeoRiskSnapshotResponse,
    EUDRGeoRiskRefreshRequest,
    EUDRGeoRiskRefreshResponse,
    # Due Diligence
    EUDRDueDiligenceCreate,
    EUDRDueDiligenceUpdate,
    EUDRDueDiligenceResponse,
    EUDRDueDiligenceSummary,
    EUDRDueDiligenceBatchLinkCreate,
    EUDRDueDiligenceBatchLinkResponse,
    # Risk Evaluation
    EUDRRiskEvaluateRequest,
    EUDRRiskEvaluateResponse,
    EUDRBatchRiskResult,
)

router = APIRouter(tags=["EUDR"])


# =============================================================================
# EUDR COMMODITIES (Global Reference Data - No Tenant Filter)
# =============================================================================

@router.get(
    "/commodities",
    response_model=List[EUDRCommodityResponse],
    summary="List EUDR Commodities",
    description="Get available EUDR commodities. This is global reference data.",
)
async def list_commodities(
    commodity_type: Optional[EUDRCommodityType] = None,
    name: Optional[str] = Query(None, description="Filter by name (partial match)"),
    is_active: bool = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List EUDR commodities (global reference data)."""
    query = db.query(EUDRCommodity)

    if commodity_type:
        query = query.filter(EUDRCommodity.commodity_type == commodity_type)
    if name:
        query = query.filter(EUDRCommodity.name.ilike(f"%{name}%"))
    if is_active is not None:
        query = query.filter(EUDRCommodity.is_active == is_active)

    return query.order_by(EUDRCommodity.name).offset(skip).limit(limit).all()


@router.get(
    "/commodities/{commodity_id}",
    response_model=EUDRCommodityResponse,
    summary="Get EUDR Commodity",
)
async def get_commodity(
    commodity_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific EUDR commodity by ID."""
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == commodity_id).first()
    if not commodity:
        raise HTTPException(status_code=404, detail="Commodity not found")
    return commodity


# =============================================================================
# EUDR OPERATORS (Tenant-Owned)
# =============================================================================

@router.get(
    "/operators",
    response_model=List[EUDROperatorResponse],
    summary="List EUDR Operators",
    description="Get operators for the current tenant.",
)
async def list_operators(
    role: Optional[EUDROperatorRole] = None,
    country: Optional[str] = Query(None, description="Filter by country code"),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List EUDR operators (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, EUDROperator, current_user.tenant_id)

    if role:
        query = query.filter(EUDROperator.role == role)
    if country:
        query = query.filter(EUDROperator.country == country.upper())
    if is_active is not None:
        query = query.filter(EUDROperator.is_active == is_active)

    return query.order_by(EUDROperator.name).offset(skip).limit(limit).all()


@router.post(
    "/operators",
    response_model=EUDROperatorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create EUDR Operator",
)
async def create_operator(
    operator: EUDROperatorCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new EUDR operator."""
    # MULTI-TENANT: Set tenant_id from authenticated user (ignore any in request)
    db_operator = create_tenant_record(
        db,
        EUDROperator,
        current_user.tenant_id,
        **operator.model_dump()
    )
    db.commit()
    db.refresh(db_operator)
    return db_operator


@router.get(
    "/operators/{operator_id}",
    response_model=EUDROperatorResponse,
    summary="Get EUDR Operator",
)
async def get_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific EUDR operator."""
    # MULTI-TENANT: Filter by tenant_id, return 404 if not found/wrong tenant
    return get_tenant_record(db, EUDROperator, operator_id, current_user.tenant_id)


@router.put(
    "/operators/{operator_id}",
    response_model=EUDROperatorResponse,
    summary="Update EUDR Operator",
)
async def update_operator(
    operator_id: int,
    operator: EUDROperatorUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an EUDR operator."""
    # MULTI-TENANT: Verify ownership and update
    update_data = operator.model_dump(exclude_unset=True)
    db_operator = update_tenant_record(
        db, EUDROperator, operator_id, current_user.tenant_id, update_data
    )
    db.commit()
    db.refresh(db_operator)
    return db_operator


@router.delete(
    "/operators/{operator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete EUDR Operator",
)
async def delete_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an EUDR operator."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, EUDROperator, operator_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# EUDR SUPPLY SITES (Tenant-Owned)
# =============================================================================

@router.get(
    "/supply-sites",
    response_model=List[EUDRSupplySiteResponse],
    summary="List EUDR Supply Sites",
    description="Get supply sites for the current tenant.",
)
async def list_supply_sites(
    operator_id: Optional[int] = None,
    commodity_id: Optional[int] = None,
    country: Optional[str] = Query(None, description="Filter by country code"),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List EUDR supply sites (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, EUDRSupplySite, current_user.tenant_id)

    if operator_id:
        query = query.filter(EUDRSupplySite.operator_id == operator_id)
    if commodity_id:
        query = query.filter(EUDRSupplySite.commodity_id == commodity_id)
    if country:
        query = query.filter(EUDRSupplySite.country == country.upper())
    if is_active is not None:
        query = query.filter(EUDRSupplySite.is_active == is_active)

    sites = query.order_by(EUDRSupplySite.name).offset(skip).limit(limit).all()

    # Build responses with computed properties
    return [_build_supply_site_response(site, db) for site in sites]


@router.post(
    "/supply-sites",
    response_model=EUDRSupplySiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create EUDR Supply Site",
)
async def create_supply_site(
    site: EUDRSupplySiteCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new EUDR supply site."""
    # Verify operator belongs to tenant
    operator = get_tenant_record(db, EUDROperator, site.operator_id, current_user.tenant_id)

    # Verify commodity exists
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == site.commodity_id).first()
    if not commodity:
        raise HTTPException(status_code=400, detail=f"Commodity {site.commodity_id} not found")

    # MULTI-TENANT: Set tenant_id from authenticated user
    db_site = create_tenant_record(
        db,
        EUDRSupplySite,
        current_user.tenant_id,
        **site.model_dump()
    )
    db.commit()
    db.refresh(db_site)
    return _build_supply_site_response(db_site, db)


@router.get(
    "/supply-sites/{site_id}",
    response_model=EUDRSupplySiteResponse,
    summary="Get EUDR Supply Site",
)
async def get_supply_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific EUDR supply site."""
    # MULTI-TENANT: Filter by tenant_id
    site = get_tenant_record(db, EUDRSupplySite, site_id, current_user.tenant_id)
    return _build_supply_site_response(site, db)


@router.put(
    "/supply-sites/{site_id}",
    response_model=EUDRSupplySiteResponse,
    summary="Update EUDR Supply Site",
)
async def update_supply_site(
    site_id: int,
    site: EUDRSupplySiteUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an EUDR supply site."""
    # MULTI-TENANT: Verify ownership and update
    update_data = site.model_dump(exclude_unset=True)
    db_site = update_tenant_record(
        db, EUDRSupplySite, site_id, current_user.tenant_id, update_data
    )
    db.commit()
    db.refresh(db_site)
    return _build_supply_site_response(db_site, db)


@router.delete(
    "/supply-sites/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete EUDR Supply Site",
)
async def delete_supply_site(
    site_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an EUDR supply site."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, EUDRSupplySite, site_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# EUDR SUPPLY SITE RISK ENDPOINTS
# =============================================================================

@router.post(
    "/supply-sites/{site_id}/refresh-risk",
    response_model=EUDRGeoRiskRefreshResponse,
    summary="Refresh Geo Risk for Supply Site",
    description="Fetch fresh geospatial risk data for a supply site.",
)
async def refresh_site_risk(
    site_id: int,
    request: EUDRGeoRiskRefreshRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Refresh geospatial risk data for a supply site."""
    # MULTI-TENANT: Verify site belongs to tenant
    site = get_tenant_record(db, EUDRSupplySite, site_id, current_user.tenant_id)

    # Check for recent snapshot if not forcing refresh
    was_cached = False
    if not request.force_refresh:
        recent_snapshot = db.query(EUDRGeoRiskSnapshot).filter(
            EUDRGeoRiskSnapshot.supply_site_id == site_id,
            EUDRGeoRiskSnapshot.tenant_id == current_user.tenant_id,
            EUDRGeoRiskSnapshot.source == request.source,
        ).order_by(EUDRGeoRiskSnapshot.snapshot_date.desc()).first()

        if recent_snapshot:
            # Return cached if less than 24 hours old
            age_hours = (datetime.utcnow() - recent_snapshot.snapshot_date.replace(tzinfo=None)).total_seconds() / 3600
            if age_hours < 24:
                was_cached = True
                return EUDRGeoRiskRefreshResponse(
                    supply_site_id=site_id,
                    snapshot=_build_georisk_response(recent_snapshot),
                    was_cached=True,
                )

    # Generate new risk snapshot using mock provider
    snapshot = _generate_mock_georisk(site, request.source, current_user.tenant_id)
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return EUDRGeoRiskRefreshResponse(
        supply_site_id=site_id,
        snapshot=_build_georisk_response(snapshot),
        was_cached=False,
    )


@router.get(
    "/supply-sites/{site_id}/risk",
    response_model=List[EUDRGeoRiskSnapshotResponse],
    summary="Get Risk History for Supply Site",
    description="Get historical geospatial risk snapshots for a supply site.",
)
async def get_site_risk_history(
    site_id: int,
    source: Optional[EUDRGeoRiskSource] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get geo risk history for a supply site."""
    # MULTI-TENANT: Verify site belongs to tenant
    site = get_tenant_record(db, EUDRSupplySite, site_id, current_user.tenant_id)

    query = db.query(EUDRGeoRiskSnapshot).filter(
        EUDRGeoRiskSnapshot.supply_site_id == site_id,
        EUDRGeoRiskSnapshot.tenant_id == current_user.tenant_id,
    )

    if source:
        query = query.filter(EUDRGeoRiskSnapshot.source == source)

    snapshots = query.order_by(EUDRGeoRiskSnapshot.snapshot_date.desc()).limit(limit).all()
    return [_build_georisk_response(s) for s in snapshots]


# =============================================================================
# EUDR BATCHES (Tenant-Owned)
# =============================================================================

@router.get(
    "/batches",
    response_model=List[EUDRBatchResponse],
    summary="List EUDR Batches",
    description="Get batches for the current tenant.",
)
async def list_batches(
    commodity_id: Optional[int] = None,
    origin_site_id: Optional[int] = None,
    origin_country: Optional[str] = Query(None, description="Filter by origin country"),
    harvest_year: Optional[int] = None,
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List EUDR batches (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, EUDRBatch, current_user.tenant_id)

    if commodity_id:
        query = query.filter(EUDRBatch.commodity_id == commodity_id)
    if origin_site_id:
        query = query.filter(EUDRBatch.origin_site_id == origin_site_id)
    if origin_country:
        query = query.filter(EUDRBatch.origin_country == origin_country.upper())
    if harvest_year:
        query = query.filter(EUDRBatch.harvest_year == harvest_year)
    if is_active is not None:
        query = query.filter(EUDRBatch.is_active == is_active)

    batches = query.order_by(EUDRBatch.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_batch_response(batch, db) for batch in batches]


@router.post(
    "/batches",
    response_model=EUDRBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create EUDR Batch",
)
async def create_batch(
    batch: EUDRBatchCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new EUDR batch."""
    # Verify commodity exists
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == batch.commodity_id).first()
    if not commodity:
        raise HTTPException(status_code=400, detail=f"Commodity {batch.commodity_id} not found")

    # Verify origin site if provided
    if batch.origin_site_id:
        site = get_tenant_record(db, EUDRSupplySite, batch.origin_site_id, current_user.tenant_id)

    # MULTI-TENANT: Set tenant_id from authenticated user
    db_batch = create_tenant_record(
        db,
        EUDRBatch,
        current_user.tenant_id,
        **batch.model_dump()
    )
    db.commit()
    db.refresh(db_batch)
    return _build_batch_response(db_batch, db)


@router.get(
    "/batches/{batch_id}",
    response_model=EUDRBatchResponse,
    summary="Get EUDR Batch",
)
async def get_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific EUDR batch."""
    # MULTI-TENANT: Filter by tenant_id
    batch = get_tenant_record(db, EUDRBatch, batch_id, current_user.tenant_id)
    return _build_batch_response(batch, db)


@router.put(
    "/batches/{batch_id}",
    response_model=EUDRBatchResponse,
    summary="Update EUDR Batch",
)
async def update_batch(
    batch_id: int,
    batch: EUDRBatchUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update an EUDR batch."""
    # Verify origin site if being updated
    if batch.origin_site_id:
        site = get_tenant_record(db, EUDRSupplySite, batch.origin_site_id, current_user.tenant_id)

    # MULTI-TENANT: Verify ownership and update
    update_data = batch.model_dump(exclude_unset=True)
    db_batch = update_tenant_record(
        db, EUDRBatch, batch_id, current_user.tenant_id, update_data
    )
    db.commit()
    db.refresh(db_batch)
    return _build_batch_response(db_batch, db)


@router.delete(
    "/batches/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete EUDR Batch",
)
async def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete an EUDR batch."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, EUDRBatch, batch_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# EUDR SUPPLY CHAIN LINKS (Tenant-Owned)
# =============================================================================

@router.get(
    "/supply-chain-links",
    response_model=List[EUDRSupplyChainLinkResponse],
    summary="List Supply Chain Links",
    description="Get supply chain links for the current tenant.",
)
async def list_supply_chain_links(
    from_batch_id: Optional[int] = None,
    to_batch_id: Optional[int] = None,
    from_operator_id: Optional[int] = None,
    to_operator_id: Optional[int] = None,
    link_type: Optional[EUDRSupplyChainLinkType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List supply chain links (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, EUDRSupplyChainLink, current_user.tenant_id)

    if from_batch_id:
        query = query.filter(EUDRSupplyChainLink.from_batch_id == from_batch_id)
    if to_batch_id:
        query = query.filter(EUDRSupplyChainLink.to_batch_id == to_batch_id)
    if from_operator_id:
        query = query.filter(EUDRSupplyChainLink.from_operator_id == from_operator_id)
    if to_operator_id:
        query = query.filter(EUDRSupplyChainLink.to_operator_id == to_operator_id)
    if link_type:
        query = query.filter(EUDRSupplyChainLink.link_type == link_type)

    links = query.order_by(EUDRSupplyChainLink.created_at.desc()).offset(skip).limit(limit).all()
    return [_build_link_response(link, db) for link in links]


@router.post(
    "/supply-chain-links",
    response_model=EUDRSupplyChainLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Supply Chain Link",
)
async def create_supply_chain_link(
    link: EUDRSupplyChainLinkCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new supply chain link."""
    # Verify operators belong to tenant
    from_op = get_tenant_record(db, EUDROperator, link.from_operator_id, current_user.tenant_id)
    to_op = get_tenant_record(db, EUDROperator, link.to_operator_id, current_user.tenant_id)

    # Verify batches if provided
    if link.from_batch_id:
        from_batch = get_tenant_record(db, EUDRBatch, link.from_batch_id, current_user.tenant_id)
    if link.to_batch_id:
        to_batch = get_tenant_record(db, EUDRBatch, link.to_batch_id, current_user.tenant_id)

    # Check for circular links (simple check)
    if link.from_batch_id and link.to_batch_id and link.from_batch_id == link.to_batch_id:
        raise HTTPException(status_code=400, detail="Cannot create self-referencing link")

    # MULTI-TENANT: Set tenant_id from authenticated user
    db_link = create_tenant_record(
        db,
        EUDRSupplyChainLink,
        current_user.tenant_id,
        **link.model_dump()
    )
    db.commit()
    db.refresh(db_link)
    return _build_link_response(db_link, db)


@router.get(
    "/supply-chain-links/{link_id}",
    response_model=EUDRSupplyChainLinkResponse,
    summary="Get Supply Chain Link",
)
async def get_supply_chain_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific supply chain link."""
    # MULTI-TENANT: Filter by tenant_id
    link = get_tenant_record(db, EUDRSupplyChainLink, link_id, current_user.tenant_id)
    return _build_link_response(link, db)


@router.delete(
    "/supply-chain-links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Supply Chain Link",
)
async def delete_supply_chain_link(
    link_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a supply chain link."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, EUDRSupplyChainLink, link_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# SUPPLY CHAIN TRAVERSAL
# =============================================================================

@router.get(
    "/batches/{batch_id}/trace-origins",
    response_model=Dict,
    summary="Trace Batch Origins",
    description="Traverse supply chain backwards to find all origin batches and sites.",
)
async def trace_batch_origins(
    batch_id: int,
    max_depth: int = Query(10, ge=1, le=50, description="Maximum traversal depth"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Trace a batch back through the supply chain to find origins."""
    # MULTI-TENANT: Verify batch belongs to tenant
    batch = get_tenant_record(db, EUDRBatch, batch_id, current_user.tenant_id)

    # BFS traversal with cycle detection
    visited_batches: Set[int] = set()
    visited_links: Set[int] = set()
    queue = [batch_id]
    depth = 0
    origins = []
    path_links = []

    while queue and depth < max_depth:
        next_queue = []
        for current_batch_id in queue:
            if current_batch_id in visited_batches:
                continue
            visited_batches.add(current_batch_id)

            # Get incoming links to this batch
            incoming = tenant_query(db, EUDRSupplyChainLink, current_user.tenant_id).filter(
                EUDRSupplyChainLink.to_batch_id == current_batch_id
            ).all()

            if not incoming:
                # This is an origin batch
                origin_batch = db.query(EUDRBatch).filter(EUDRBatch.id == current_batch_id).first()
                if origin_batch:
                    origin_data = {
                        "batch_id": origin_batch.id,
                        "batch_reference": origin_batch.batch_reference,
                        "origin_country": origin_batch.origin_country,
                        "origin_site_id": origin_batch.origin_site_id,
                        "commodity_id": origin_batch.commodity_id,
                        "volume": origin_batch.volume,
                        "volume_unit": origin_batch.volume_unit,
                        "depth": depth,
                    }
                    if origin_batch.origin_site_id:
                        site = db.query(EUDRSupplySite).filter(
                            EUDRSupplySite.id == origin_batch.origin_site_id
                        ).first()
                        if site:
                            origin_data["origin_site"] = {
                                "id": site.id,
                                "name": site.name,
                                "country": site.country,
                                "latitude": site.latitude,
                                "longitude": site.longitude,
                            }
                    origins.append(origin_data)
            else:
                for link in incoming:
                    if link.id not in visited_links:
                        visited_links.add(link.id)
                        path_links.append({
                            "link_id": link.id,
                            "from_batch_id": link.from_batch_id,
                            "to_batch_id": link.to_batch_id,
                            "link_type": link.link_type.value,
                            "depth": depth,
                        })
                        if link.from_batch_id and link.from_batch_id not in visited_batches:
                            next_queue.append(link.from_batch_id)

        queue = next_queue
        depth += 1

    return {
        "batch_id": batch_id,
        "origins": origins,
        "supply_chain_links": path_links,
        "total_origins": len(origins),
        "max_depth_reached": depth,
        "unique_countries": list(set(o["origin_country"] for o in origins)),
    }


# =============================================================================
# EUDR GEO RISK SNAPSHOTS (Tenant-Owned)
# =============================================================================

@router.get(
    "/georisk-snapshots",
    response_model=List[EUDRGeoRiskSnapshotResponse],
    summary="List Geo Risk Snapshots",
    description="Get all geo risk snapshots for the current tenant.",
)
async def list_georisk_snapshots(
    supply_site_id: Optional[int] = None,
    source: Optional[EUDRGeoRiskSource] = None,
    risk_level: Optional[EUDRRiskLevel] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List geo risk snapshots (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, EUDRGeoRiskSnapshot, current_user.tenant_id)

    if supply_site_id:
        query = query.filter(EUDRGeoRiskSnapshot.supply_site_id == supply_site_id)
    if source:
        query = query.filter(EUDRGeoRiskSnapshot.source == source)
    if risk_level:
        query = query.filter(EUDRGeoRiskSnapshot.risk_level == risk_level)

    snapshots = query.order_by(EUDRGeoRiskSnapshot.snapshot_date.desc()).offset(skip).limit(limit).all()
    return [_build_georisk_response(s) for s in snapshots]


@router.post(
    "/georisk-snapshots",
    response_model=EUDRGeoRiskSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Geo Risk Snapshot",
    description="Manually create a geo risk snapshot (for manual assessments).",
)
async def create_georisk_snapshot(
    snapshot: EUDRGeoRiskSnapshotCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a manual geo risk snapshot."""
    # Verify supply site belongs to tenant
    site = get_tenant_record(db, EUDRSupplySite, snapshot.supply_site_id, current_user.tenant_id)

    # MULTI-TENANT: Set tenant_id from authenticated user
    db_snapshot = create_tenant_record(
        db,
        EUDRGeoRiskSnapshot,
        current_user.tenant_id,
        **snapshot.model_dump()
    )
    db.commit()
    db.refresh(db_snapshot)
    return _build_georisk_response(db_snapshot)


@router.get(
    "/georisk-snapshots/{snapshot_id}",
    response_model=EUDRGeoRiskSnapshotResponse,
    summary="Get Geo Risk Snapshot",
)
async def get_georisk_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific geo risk snapshot."""
    # MULTI-TENANT: Filter by tenant_id
    snapshot = get_tenant_record(db, EUDRGeoRiskSnapshot, snapshot_id, current_user.tenant_id)
    return _build_georisk_response(snapshot)


@router.delete(
    "/georisk-snapshots/{snapshot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Geo Risk Snapshot",
)
async def delete_georisk_snapshot(
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a geo risk snapshot."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, EUDRGeoRiskSnapshot, snapshot_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# EUDR DUE DILIGENCE (Tenant-Owned)
# =============================================================================

@router.get(
    "/due-diligence",
    response_model=List[EUDRDueDiligenceSummary],
    summary="List Due Diligence Assessments",
    description="Get due diligence assessments for the current tenant.",
)
async def list_due_diligence(
    status_filter: Optional[EUDRDueDiligenceStatus] = Query(None, alias="status"),
    operator_id: Optional[int] = None,
    commodity_id: Optional[int] = None,
    risk_level: Optional[EUDRRiskLevel] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List due diligence assessments (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, EUDRDueDiligence, current_user.tenant_id)

    if status_filter:
        query = query.filter(EUDRDueDiligence.status == status_filter)
    if operator_id:
        query = query.filter(EUDRDueDiligence.operator_id == operator_id)
    if commodity_id:
        query = query.filter(EUDRDueDiligence.commodity_id == commodity_id)
    if risk_level:
        query = query.filter(EUDRDueDiligence.overall_risk_level == risk_level)

    dds = query.order_by(EUDRDueDiligence.created_at.desc()).offset(skip).limit(limit).all()

    return [EUDRDueDiligenceSummary(
        id=dd.id,
        tenant_id=dd.tenant_id,
        reference=dd.reference,
        operator_id=dd.operator_id,
        commodity_id=dd.commodity_id,
        period_start=dd.period_start,
        period_end=dd.period_end,
        status=dd.status,
        overall_risk_level=dd.overall_risk_level,
        overall_risk_score=dd.overall_risk_score,
        batch_count=dd.batch_count,
        total_volume=dd.total_volume or 0.0,
        created_at=dd.created_at,
    ) for dd in dds]


@router.post(
    "/due-diligence",
    response_model=EUDRDueDiligenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Due Diligence Assessment",
)
async def create_due_diligence(
    dd: EUDRDueDiligenceCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new due diligence assessment."""
    # Verify operator belongs to tenant
    operator = get_tenant_record(db, EUDROperator, dd.operator_id, current_user.tenant_id)

    # Verify commodity exists
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == dd.commodity_id).first()
    if not commodity:
        raise HTTPException(status_code=400, detail=f"Commodity {dd.commodity_id} not found")

    # Verify batches if provided
    batch_ids = dd.batch_ids or []
    for batch_id in batch_ids:
        get_tenant_record(db, EUDRBatch, batch_id, current_user.tenant_id)

    # Create DD
    dd_data = dd.model_dump(exclude={"batch_ids"})
    db_dd = create_tenant_record(
        db,
        EUDRDueDiligence,
        current_user.tenant_id,
        created_by_user_id=current_user.user_id,
        **dd_data
    )
    db.flush()

    # Link batches
    total_volume = 0.0
    for batch_id in batch_ids:
        batch = db.query(EUDRBatch).filter(EUDRBatch.id == batch_id).first()
        link = EUDRDueDiligenceBatchLink(
            due_diligence_id=db_dd.id,
            batch_id=batch_id,
            included_volume=batch.volume if batch else None,
            included_volume_unit=batch.volume_unit if batch else "tonne",
        )
        db.add(link)
        if batch:
            total_volume += batch.volume

    # Update aggregates
    db_dd.batch_count = len(batch_ids)
    db_dd.total_volume = total_volume

    db.commit()
    db.refresh(db_dd)
    return _build_dd_response(db_dd, db)


@router.get(
    "/due-diligence/{dd_id}",
    response_model=EUDRDueDiligenceResponse,
    summary="Get Due Diligence Assessment",
)
async def get_due_diligence(
    dd_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific due diligence assessment."""
    # MULTI-TENANT: Filter by tenant_id
    dd = get_tenant_record(db, EUDRDueDiligence, dd_id, current_user.tenant_id)
    return _build_dd_response(dd, db)


@router.put(
    "/due-diligence/{dd_id}",
    response_model=EUDRDueDiligenceResponse,
    summary="Update Due Diligence Assessment",
)
async def update_due_diligence(
    dd_id: int,
    dd_update: EUDRDueDiligenceUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update a due diligence assessment."""
    # MULTI-TENANT: Verify ownership and update
    update_data = dd_update.model_dump(exclude_unset=True)
    db_dd = update_tenant_record(
        db, EUDRDueDiligence, dd_id, current_user.tenant_id, update_data
    )
    db.commit()
    db.refresh(db_dd)
    return _build_dd_response(db_dd, db)


@router.delete(
    "/due-diligence/{dd_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Due Diligence Assessment",
)
async def delete_due_diligence(
    dd_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a due diligence assessment."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, EUDRDueDiligence, dd_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# DUE DILIGENCE BATCH LINKS
# =============================================================================

@router.get(
    "/due-diligence/{dd_id}/batches",
    response_model=List[EUDRDueDiligenceBatchLinkResponse],
    summary="List Batches in Due Diligence",
)
async def list_dd_batches(
    dd_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get all batches linked to a due diligence assessment."""
    # MULTI-TENANT: Verify DD belongs to tenant
    dd = get_tenant_record(db, EUDRDueDiligence, dd_id, current_user.tenant_id)

    links = db.query(EUDRDueDiligenceBatchLink).filter(
        EUDRDueDiligenceBatchLink.due_diligence_id == dd_id
    ).all()

    return [_build_dd_batch_link_response(link, db) for link in links]


@router.post(
    "/due-diligence/{dd_id}/batches",
    response_model=EUDRDueDiligenceBatchLinkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Batch to Due Diligence",
)
async def add_batch_to_dd(
    dd_id: int,
    batch_link: EUDRDueDiligenceBatchLinkCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a batch to a due diligence assessment."""
    # MULTI-TENANT: Verify DD belongs to tenant
    dd = get_tenant_record(db, EUDRDueDiligence, dd_id, current_user.tenant_id)

    # Verify batch belongs to tenant
    batch = get_tenant_record(db, EUDRBatch, batch_link.batch_id, current_user.tenant_id)

    # Check if already linked
    existing = db.query(EUDRDueDiligenceBatchLink).filter(
        EUDRDueDiligenceBatchLink.due_diligence_id == dd_id,
        EUDRDueDiligenceBatchLink.batch_id == batch_link.batch_id,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Batch already linked to this due diligence")

    db_link = EUDRDueDiligenceBatchLink(
        due_diligence_id=dd_id,
        batch_id=batch_link.batch_id,
        included_volume=batch_link.included_volume or batch.volume,
        included_volume_unit=batch_link.included_volume_unit or batch.volume_unit,
        assessment_notes=batch_link.assessment_notes,
    )
    db.add(db_link)

    # Update DD aggregates
    dd.batch_count = (dd.batch_count or 0) + 1
    dd.total_volume = (dd.total_volume or 0) + (db_link.included_volume or 0)

    db.commit()
    db.refresh(db_link)
    return _build_dd_batch_link_response(db_link, db)


@router.delete(
    "/due-diligence/{dd_id}/batches/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Batch from Due Diligence",
)
async def remove_batch_from_dd(
    dd_id: int,
    batch_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Remove a batch from a due diligence assessment."""
    # MULTI-TENANT: Verify DD belongs to tenant
    dd = get_tenant_record(db, EUDRDueDiligence, dd_id, current_user.tenant_id)

    link = db.query(EUDRDueDiligenceBatchLink).filter(
        EUDRDueDiligenceBatchLink.due_diligence_id == dd_id,
        EUDRDueDiligenceBatchLink.batch_id == batch_id,
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Batch link not found")

    # Update DD aggregates
    dd.batch_count = max(0, (dd.batch_count or 0) - 1)
    dd.total_volume = max(0, (dd.total_volume or 0) - (link.included_volume or 0))

    db.delete(link)
    db.commit()


# =============================================================================
# RISK EVALUATION
# =============================================================================

@router.post(
    "/due-diligence/{dd_id}/evaluate",
    response_model=EUDRRiskEvaluateResponse,
    summary="Evaluate Due Diligence Risk",
    description="Calculate risk scores for all batches in a due diligence assessment.",
)
async def evaluate_dd_risk(
    dd_id: int,
    recalculate_all: bool = Query(False, description="Recalculate all batch risks"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Evaluate risk for a due diligence assessment."""
    # MULTI-TENANT: Verify DD belongs to tenant
    dd = get_tenant_record(db, EUDRDueDiligence, dd_id, current_user.tenant_id)

    # Get all batch links
    batch_links = db.query(EUDRDueDiligenceBatchLink).filter(
        EUDRDueDiligenceBatchLink.due_diligence_id == dd_id
    ).all()

    if not batch_links:
        raise HTTPException(status_code=400, detail="No batches linked to this due diligence")

    # Get commodity for baseline risk
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == dd.commodity_id).first()

    results = []
    errors = []
    batches_evaluated = 0
    batches_skipped = 0
    risk_breakdown = {"low": 0, "medium": 0, "high": 0}

    for link in batch_links:
        # Skip if already calculated and not recalculating
        if not recalculate_all and link.batch_risk_score is not None:
            batches_skipped += 1
            if link.batch_risk_level:
                risk_breakdown[link.batch_risk_level.value] += 1
            continue

        batch = db.query(EUDRBatch).filter(EUDRBatch.id == link.batch_id).first()
        if not batch:
            errors.append(f"Batch {link.batch_id} not found")
            continue

        # Calculate risk using weighted model
        risk_result = _calculate_batch_risk(batch, commodity, db, current_user.tenant_id)

        # Update link
        link.batch_risk_score = risk_result["score"]
        link.batch_risk_level = risk_result["level"]

        batches_evaluated += 1
        risk_breakdown[risk_result["level"].value] += 1

        results.append(EUDRBatchRiskResult(
            batch_id=batch.id,
            batch_reference=batch.batch_reference,
            risk_score=risk_result["score"],
            risk_level=risk_result["level"],
            commodity_risk=risk_result["commodity_risk"],
            geo_risk=risk_result["geo_risk"],
            supply_chain_risk=risk_result["supply_chain_risk"],
            documentation_risk=risk_result["documentation_risk"],
        ))

    # Calculate overall risk (weighted average by volume)
    total_volume = sum(link.included_volume or 0 for link in batch_links if link.batch_risk_score is not None)
    if total_volume > 0:
        weighted_score = sum(
            (link.batch_risk_score or 0) * (link.included_volume or 0)
            for link in batch_links if link.batch_risk_score is not None
        ) / total_volume
    else:
        weighted_score = sum(link.batch_risk_score or 0 for link in batch_links if link.batch_risk_score is not None) / max(1, len([l for l in batch_links if l.batch_risk_score is not None]))

    overall_level = _score_to_level(weighted_score)

    # Update DD
    dd.overall_risk_score = weighted_score
    dd.overall_risk_level = overall_level

    db.commit()
    db.refresh(dd)

    return EUDRRiskEvaluateResponse(
        due_diligence_id=dd_id,
        overall_risk_score=weighted_score,
        overall_risk_level=overall_level,
        batches_evaluated=batches_evaluated,
        batches_skipped=batches_skipped,
        batch_results=results,
        risk_breakdown=risk_breakdown,
        errors=errors,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_supply_site_response(site: EUDRSupplySite, db: Session) -> EUDRSupplySiteResponse:
    """Build supply site response with related data."""
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == site.commodity_id).first()
    operator = db.query(EUDROperator).filter(EUDROperator.id == site.operator_id).first()

    return EUDRSupplySiteResponse(
        id=site.id,
        tenant_id=site.tenant_id,
        operator_id=site.operator_id,
        commodity_id=site.commodity_id,
        name=site.name,
        site_reference=site.site_reference,
        country=site.country,
        region=site.region,
        latitude=site.latitude,
        longitude=site.longitude,
        geometry_geojson=site.geometry_geojson,
        area_ha=site.area_ha,
        legal_title_reference=site.legal_title_reference,
        is_active=site.is_active,
        notes=site.notes,
        has_coordinates=site.has_coordinates,
        has_polygon=site.has_polygon,
        created_at=site.created_at,
        updated_at=site.updated_at,
        commodity=EUDRCommodityResponse.model_validate(commodity) if commodity else None,
        operator=EUDROperatorResponse.model_validate(operator) if operator else None,
    )


def _build_batch_response(batch: EUDRBatch, db: Session) -> EUDRBatchResponse:
    """Build batch response with related data."""
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == batch.commodity_id).first()
    origin_site = None
    if batch.origin_site_id:
        site = db.query(EUDRSupplySite).filter(EUDRSupplySite.id == batch.origin_site_id).first()
        if site:
            origin_site = EUDRSupplySiteSummary(
                id=site.id,
                tenant_id=site.tenant_id,
                name=site.name,
                country=site.country,
                commodity_id=site.commodity_id,
                operator_id=site.operator_id,
                latitude=site.latitude,
                longitude=site.longitude,
                area_ha=site.area_ha,
                is_active=site.is_active,
            )

    return EUDRBatchResponse(
        id=batch.id,
        tenant_id=batch.tenant_id,
        batch_reference=batch.batch_reference,
        commodity_id=batch.commodity_id,
        volume=batch.volume,
        volume_unit=batch.volume_unit,
        harvest_year=batch.harvest_year,
        origin_site_id=batch.origin_site_id,
        origin_country=batch.origin_country,
        is_active=batch.is_active,
        notes=batch.notes,
        created_at=batch.created_at,
        updated_at=batch.updated_at,
        commodity=EUDRCommodityResponse.model_validate(commodity) if commodity else None,
        origin_site=origin_site,
    )


def _build_link_response(link: EUDRSupplyChainLink, db: Session) -> EUDRSupplyChainLinkResponse:
    """Build supply chain link response with related data."""
    from_batch = None
    to_batch = None

    if link.from_batch_id:
        b = db.query(EUDRBatch).filter(EUDRBatch.id == link.from_batch_id).first()
        if b:
            from_batch = EUDRBatchSummary(
                id=b.id,
                tenant_id=b.tenant_id,
                batch_reference=b.batch_reference,
                commodity_id=b.commodity_id,
                volume=b.volume,
                volume_unit=b.volume_unit,
                harvest_year=b.harvest_year,
                origin_country=b.origin_country,
                is_active=b.is_active,
            )

    if link.to_batch_id:
        b = db.query(EUDRBatch).filter(EUDRBatch.id == link.to_batch_id).first()
        if b:
            to_batch = EUDRBatchSummary(
                id=b.id,
                tenant_id=b.tenant_id,
                batch_reference=b.batch_reference,
                commodity_id=b.commodity_id,
                volume=b.volume,
                volume_unit=b.volume_unit,
                harvest_year=b.harvest_year,
                origin_country=b.origin_country,
                is_active=b.is_active,
            )

    from_operator = db.query(EUDROperator).filter(EUDROperator.id == link.from_operator_id).first()
    to_operator = db.query(EUDROperator).filter(EUDROperator.id == link.to_operator_id).first()

    return EUDRSupplyChainLinkResponse(
        id=link.id,
        tenant_id=link.tenant_id,
        from_batch_id=link.from_batch_id,
        from_operator_id=link.from_operator_id,
        to_batch_id=link.to_batch_id,
        to_operator_id=link.to_operator_id,
        link_type=link.link_type,
        documentation_reference=link.documentation_reference,
        created_at=link.created_at,
        from_batch=from_batch,
        to_batch=to_batch,
        from_operator=EUDROperatorResponse.model_validate(from_operator) if from_operator else None,
        to_operator=EUDROperatorResponse.model_validate(to_operator) if to_operator else None,
    )


def _build_georisk_response(snapshot: EUDRGeoRiskSnapshot) -> EUDRGeoRiskSnapshotResponse:
    """Build geo risk snapshot response."""
    return EUDRGeoRiskSnapshotResponse(
        id=snapshot.id,
        tenant_id=snapshot.tenant_id,
        supply_site_id=snapshot.supply_site_id,
        source=snapshot.source,
        snapshot_date=snapshot.snapshot_date,
        deforestation_flag=snapshot.deforestation_flag,
        tree_cover_loss_ha=snapshot.tree_cover_loss_ha,
        protected_area_overlap=snapshot.protected_area_overlap,
        risk_score_raw=snapshot.risk_score_raw,
        risk_level=snapshot.risk_level,
        details_json=snapshot.details_json,
        created_at=snapshot.created_at,
    )


def _build_dd_response(dd: EUDRDueDiligence, db: Session) -> EUDRDueDiligenceResponse:
    """Build due diligence response with related data."""
    operator = db.query(EUDROperator).filter(EUDROperator.id == dd.operator_id).first()
    commodity = db.query(EUDRCommodity).filter(EUDRCommodity.id == dd.commodity_id).first()

    batch_links = db.query(EUDRDueDiligenceBatchLink).filter(
        EUDRDueDiligenceBatchLink.due_diligence_id == dd.id
    ).all()

    return EUDRDueDiligenceResponse(
        id=dd.id,
        tenant_id=dd.tenant_id,
        operator_id=dd.operator_id,
        reference=dd.reference,
        commodity_id=dd.commodity_id,
        period_start=dd.period_start,
        period_end=dd.period_end,
        status=dd.status,
        overall_risk_level=dd.overall_risk_level,
        overall_risk_score=dd.overall_risk_score,
        justification_summary=dd.justification_summary,
        total_volume=dd.total_volume or 0.0,
        total_volume_unit=dd.total_volume_unit or "tonne",
        batch_count=dd.batch_count or 0,
        created_at=dd.created_at,
        updated_at=dd.updated_at,
        created_by_user_id=dd.created_by_user_id,
        operator=EUDROperatorResponse.model_validate(operator) if operator else None,
        commodity=EUDRCommodityResponse.model_validate(commodity) if commodity else None,
        batch_links=[_build_dd_batch_link_response(link, db) for link in batch_links],
    )


def _build_dd_batch_link_response(link: EUDRDueDiligenceBatchLink, db: Session) -> EUDRDueDiligenceBatchLinkResponse:
    """Build DD batch link response."""
    batch = db.query(EUDRBatch).filter(EUDRBatch.id == link.batch_id).first()
    batch_summary = None
    if batch:
        batch_summary = EUDRBatchSummary(
            id=batch.id,
            tenant_id=batch.tenant_id,
            batch_reference=batch.batch_reference,
            commodity_id=batch.commodity_id,
            volume=batch.volume,
            volume_unit=batch.volume_unit,
            harvest_year=batch.harvest_year,
            origin_country=batch.origin_country,
            is_active=batch.is_active,
        )

    return EUDRDueDiligenceBatchLinkResponse(
        id=link.id,
        due_diligence_id=link.due_diligence_id,
        batch_id=link.batch_id,
        batch_risk_score=link.batch_risk_score,
        batch_risk_level=link.batch_risk_level,
        included_volume=link.included_volume,
        included_volume_unit=link.included_volume_unit,
        assessment_notes=link.assessment_notes,
        created_at=link.created_at,
        batch=batch_summary,
    )


def _generate_mock_georisk(site: EUDRSupplySite, source: EUDRGeoRiskSource, tenant_id: str) -> EUDRGeoRiskSnapshot:
    """
    Generate a mock geo risk snapshot for development/testing.

    In production, this would call real geospatial APIs (GFW, etc.).
    """
    import random

    # Mock risk based on country (higher risk for known deforestation hotspots)
    HIGH_RISK_COUNTRIES = {"BR", "ID", "MY", "CO", "CD"}
    MEDIUM_RISK_COUNTRIES = {"PE", "BO", "EC", "NG", "CM", "GH", "CI"}

    base_risk = 15  # Low baseline
    if site.country in HIGH_RISK_COUNTRIES:
        base_risk = 45
    elif site.country in MEDIUM_RISK_COUNTRIES:
        base_risk = 30

    # Add some randomness
    risk_score = min(100, max(0, base_risk + random.randint(-10, 20)))

    # Determine flags based on score
    deforestation_flag = risk_score > 50 or random.random() < 0.1
    protected_area_overlap = random.random() < 0.15
    tree_cover_loss = random.uniform(0, 50) if deforestation_flag else random.uniform(0, 5)

    if deforestation_flag:
        risk_score = min(100, risk_score + 20)
    if protected_area_overlap:
        risk_score = min(100, risk_score + 15)

    risk_level = _score_to_level(risk_score)

    return EUDRGeoRiskSnapshot(
        tenant_id=tenant_id,
        supply_site_id=site.id,
        source=source,
        snapshot_date=datetime.utcnow(),
        deforestation_flag=deforestation_flag,
        tree_cover_loss_ha=round(tree_cover_loss, 2),
        protected_area_overlap=protected_area_overlap,
        risk_score_raw=round(risk_score, 1),
        risk_level=risk_level,
        details_json={
            "mock": True,
            "country_baseline": base_risk,
            "coordinates_available": site.has_coordinates,
        },
    )


def _calculate_batch_risk(
    batch: EUDRBatch,
    commodity: Optional[EUDRCommodity],
    db: Session,
    tenant_id: str
) -> Dict:
    """
    Calculate risk score for a batch using weighted model.

    Per docs/regimes/eudr.md section 5.2:
    - Commodity baseline: low=10, medium=25, high=40
    - Geospatial: deforestation_flag=+40, protected_area=+30, tree_loss>threshold=+20
    - Supply chain: each hop beyond 2=+5, each additional country=+5
    - Documentation: missing=+10-20

    Score clamped to 0-100, mapped to level:
    - 0-30 = low
    - 31-60 = medium
    - 61-100 = high
    """
    score = 0.0
    commodity_risk = 0.0
    geo_risk = 0.0
    supply_chain_risk = 0.0
    documentation_risk = 0.0

    # Commodity baseline
    if commodity:
        if commodity.risk_profile_default == EUDRRiskLevel.LOW:
            commodity_risk = 10.0
        elif commodity.risk_profile_default == EUDRRiskLevel.MEDIUM:
            commodity_risk = 25.0
        else:
            commodity_risk = 40.0
    else:
        commodity_risk = 25.0  # Default to medium if unknown

    score += commodity_risk

    # Geospatial risk from origin site
    if batch.origin_site_id:
        latest_snapshot = db.query(EUDRGeoRiskSnapshot).filter(
            EUDRGeoRiskSnapshot.supply_site_id == batch.origin_site_id,
            EUDRGeoRiskSnapshot.tenant_id == tenant_id,
        ).order_by(EUDRGeoRiskSnapshot.snapshot_date.desc()).first()

        if latest_snapshot:
            if latest_snapshot.deforestation_flag:
                geo_risk += 40.0
            if latest_snapshot.protected_area_overlap:
                geo_risk += 30.0
            if latest_snapshot.tree_cover_loss_ha and latest_snapshot.tree_cover_loss_ha > 10:
                geo_risk += 20.0
        else:
            # No geo risk data = add some uncertainty risk
            geo_risk += 15.0

    score += geo_risk

    # Supply chain complexity
    # Count incoming links to this batch
    link_count = db.query(EUDRSupplyChainLink).filter(
        EUDRSupplyChainLink.to_batch_id == batch.id,
        EUDRSupplyChainLink.tenant_id == tenant_id,
    ).count()

    if link_count > 2:
        supply_chain_risk += min(25.0, (link_count - 2) * 5.0)

    score += supply_chain_risk

    # Documentation risk (simplified - based on presence of origin site)
    if not batch.origin_site_id:
        documentation_risk += 15.0  # Missing origin site
    if not batch.harvest_year:
        documentation_risk += 5.0  # Missing harvest year

    score += documentation_risk

    # Clamp to 0-100
    score = min(100.0, max(0.0, score))
    level = _score_to_level(score)

    return {
        "score": round(score, 1),
        "level": level,
        "commodity_risk": commodity_risk,
        "geo_risk": geo_risk,
        "supply_chain_risk": supply_chain_risk,
        "documentation_risk": documentation_risk,
    }


def _score_to_level(score: float) -> EUDRRiskLevel:
    """Convert numeric score to risk level."""
    if score <= 30:
        return EUDRRiskLevel.LOW
    elif score <= 60:
        return EUDRRiskLevel.MEDIUM
    else:
        return EUDRRiskLevel.HIGH


# =============================================================================
# EUDR REPORT GENERATION ENDPOINTS
# =============================================================================

@router.get(
    "/due-diligence/{dd_id}/report",
    response_model=Dict,
    summary="Get Due Diligence Report",
    description="Generate a comprehensive EUDR due diligence report.",
)
async def get_due_diligence_report(
    dd_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Generate a comprehensive EUDR due diligence report.

    Returns structured data including:
    - Due diligence summary
    - Commodity breakdown by country/year
    - Supply chain summary (operators, sites)
    - Risk assessment by site
    - Supply chain graph (nodes + edges)
    - Compliance checklist
    """
    from app.services.eudr_report import generate_eudr_due_diligence_report, EUDRReportError

    try:
        report = generate_eudr_due_diligence_report(
            db=db,
            tenant_id=current_user.tenant_id,
            due_diligence_id=dd_id,
        )
        return report
    except EUDRReportError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/due-diligence/{dd_id}/export",
    summary="Export Due Diligence Report",
    description="Export EUDR due diligence report in PDF or CSV format.",
)
async def export_due_diligence_report(
    dd_id: int,
    format: str = Query("pdf", regex="^(pdf|csv)$", description="Export format: pdf or csv"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Export EUDR due diligence report.

    Supported formats:
    - pdf: Full formatted PDF report
    - csv: Tabular data export
    """
    from fastapi.responses import Response
    from app.services.eudr_report import (
        generate_eudr_pdf,
        export_eudr_report_csv,
        EUDRReportError,
    )

    try:
        if format == "pdf":
            pdf_bytes = generate_eudr_pdf(
                db=db,
                tenant_id=current_user.tenant_id,
                due_diligence_id=dd_id,
            )
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename=eudr_due_diligence_{dd_id}.pdf"
                },
            )
        else:  # csv
            csv_content = export_eudr_report_csv(
                db=db,
                tenant_id=current_user.tenant_id,
                due_diligence_id=dd_id,
            )
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=eudr_due_diligence_{dd_id}.csv"
                },
            )
    except EUDRReportError as e:
        raise HTTPException(status_code=404, detail=str(e))
