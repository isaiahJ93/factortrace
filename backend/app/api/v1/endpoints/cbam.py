# app/api/v1/endpoints/cbam.py
"""
CBAM (Carbon Border Adjustment Mechanism) API Endpoints.

Provides endpoints for managing CBAM declarations, products, installations,
and embedded emissions calculations.

Security:
- All tenant-owned data filtered by tenant_id from JWT
- Cross-tenant access returns 404 (not 403) to prevent enumeration
- tenant_id in request body is IGNORED - always set from authenticated user

Reference: docs/regimes/cbam.md
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

# CBAM Models
from app.models.cbam import (
    CBAMFactorSource,
    CBAMProduct,
    CBAMDeclaration,
    CBAMDeclarationLine,
    CBAMInstallation,
    CBAMDeclarationStatus,
    CBAMFactorDataset,
    CBAMProductSector,
)

# CBAM Schemas
from app.schemas.cbam import (
    # Factor Sources
    CBAMFactorSourceResponse,
    # Products
    CBAMProductCreate,
    CBAMProductUpdate,
    CBAMProductResponse,
    # Installations
    CBAMInstallationCreate,
    CBAMInstallationUpdate,
    CBAMInstallationResponse,
    # Declarations
    CBAMDeclarationCreate,
    CBAMDeclarationUpdate,
    CBAMDeclarationResponse,
    CBAMDeclarationSummary,
    # Lines
    CBAMDeclarationLineCreate,
    CBAMDeclarationLineUpdate,
    CBAMDeclarationLineResponse,
    # Calculation
    CBAMCalculateRequest,
    CBAMCalculateResponse,
    CBAMCalculationResult,
    # Aggregation
    CBAMDeclarationBreakdown,
    CBAMProductBreakdown,
    CBAMCountryBreakdown,
)

router = APIRouter(tags=["CBAM"])


# =============================================================================
# CBAM FACTOR SOURCES (Global Reference Data - No Tenant Filter)
# =============================================================================

@router.get(
    "/factor-sources",
    response_model=List[CBAMFactorSourceResponse],
    summary="List CBAM Factor Sources",
    description="Get available CBAM emission factor sources/datasets. This is global reference data.",
)
async def list_factor_sources(
    dataset: Optional[CBAMFactorDataset] = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List all CBAM factor sources (global reference data)."""
    query = db.query(CBAMFactorSource)

    if dataset:
        query = query.filter(CBAMFactorSource.dataset == dataset)

    return query.order_by(CBAMFactorSource.dataset, CBAMFactorSource.version).all()


@router.get(
    "/factor-sources/{source_id}",
    response_model=CBAMFactorSourceResponse,
    summary="Get CBAM Factor Source",
)
async def get_factor_source(
    source_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific CBAM factor source by ID."""
    source = db.query(CBAMFactorSource).filter(CBAMFactorSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Factor source not found")
    return source


# =============================================================================
# CBAM PRODUCTS (Global Reference Data - No Tenant Filter)
# =============================================================================

@router.get(
    "/products",
    response_model=List[CBAMProductResponse],
    summary="List CBAM Products",
    description="Get CBAM products by CN code. This is global reference data.",
)
async def list_products(
    sector: Optional[CBAMProductSector] = None,
    cn_code: Optional[str] = Query(None, description="Filter by CN code (partial match)"),
    hs_code: Optional[str] = Query(None, description="Filter by HS code"),
    is_active: bool = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List CBAM products (global reference data)."""
    query = db.query(CBAMProduct)

    if sector:
        query = query.filter(CBAMProduct.sector == sector)
    if cn_code:
        query = query.filter(CBAMProduct.cn_code.ilike(f"%{cn_code}%"))
    if hs_code:
        query = query.filter(CBAMProduct.hs_code == hs_code)
    if is_active is not None:
        query = query.filter(CBAMProduct.is_active == is_active)

    return query.order_by(CBAMProduct.cn_code).offset(skip).limit(limit).all()


@router.get(
    "/products/{product_id}",
    response_model=CBAMProductResponse,
    summary="Get CBAM Product",
)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific CBAM product by ID."""
    product = db.query(CBAMProduct).filter(CBAMProduct.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get(
    "/products/by-cn/{cn_code}",
    response_model=CBAMProductResponse,
    summary="Get CBAM Product by CN Code",
)
async def get_product_by_cn_code(
    cn_code: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a CBAM product by its CN code."""
    product = db.query(CBAMProduct).filter(CBAMProduct.cn_code == cn_code).first()
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with CN code {cn_code} not found")
    return product


# =============================================================================
# CBAM INSTALLATIONS (Tenant-Owned)
# =============================================================================

@router.get(
    "/installations",
    response_model=List[CBAMInstallationResponse],
    summary="List CBAM Installations",
    description="Get installations for the current tenant.",
)
async def list_installations(
    country: Optional[str] = Query(None, description="Filter by country code"),
    sector: Optional[CBAMProductSector] = None,
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List CBAM installations (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, CBAMInstallation, current_user.tenant_id)

    if country:
        query = query.filter(CBAMInstallation.country == country.upper())
    if sector:
        query = query.filter(CBAMInstallation.sector == sector)
    if is_active is not None:
        query = query.filter(CBAMInstallation.is_active == is_active)

    return query.order_by(CBAMInstallation.name).offset(skip).limit(limit).all()


@router.post(
    "/installations",
    response_model=CBAMInstallationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create CBAM Installation",
)
async def create_installation(
    installation: CBAMInstallationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new CBAM installation."""
    # MULTI-TENANT: Set tenant_id from authenticated user (ignore any in request)
    db_installation = create_tenant_record(
        db,
        CBAMInstallation,
        current_user.tenant_id,
        **installation.model_dump()
    )
    db.commit()
    db.refresh(db_installation)
    return db_installation


@router.get(
    "/installations/{installation_id}",
    response_model=CBAMInstallationResponse,
    summary="Get CBAM Installation",
)
async def get_installation(
    installation_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific CBAM installation."""
    # MULTI-TENANT: Filter by tenant_id, return 404 if not found/wrong tenant
    return get_tenant_record(db, CBAMInstallation, installation_id, current_user.tenant_id)


@router.put(
    "/installations/{installation_id}",
    response_model=CBAMInstallationResponse,
    summary="Update CBAM Installation",
)
async def update_installation(
    installation_id: int,
    installation: CBAMInstallationUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update a CBAM installation."""
    # MULTI-TENANT: Verify ownership and update
    update_data = installation.model_dump(exclude_unset=True)
    db_installation = update_tenant_record(
        db, CBAMInstallation, installation_id, current_user.tenant_id, update_data
    )
    db.commit()
    db.refresh(db_installation)
    return db_installation


@router.delete(
    "/installations/{installation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete CBAM Installation",
)
async def delete_installation(
    installation_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a CBAM installation."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, CBAMInstallation, installation_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# CBAM DECLARATIONS (Tenant-Owned)
# =============================================================================

@router.get(
    "/declarations",
    response_model=List[CBAMDeclarationSummary],
    summary="List CBAM Declarations",
    description="Get all declarations for the current tenant.",
)
async def list_declarations(
    status_filter: Optional[CBAMDeclarationStatus] = Query(None, alias="status"),
    period_start_from: Optional[datetime] = None,
    period_start_to: Optional[datetime] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List CBAM declarations (tenant-scoped)."""
    # MULTI-TENANT: Always filter by tenant_id
    query = tenant_query(db, CBAMDeclaration, current_user.tenant_id)

    if status_filter:
        query = query.filter(CBAMDeclaration.status == status_filter)
    if period_start_from:
        query = query.filter(CBAMDeclaration.period_start >= period_start_from)
    if period_start_to:
        query = query.filter(CBAMDeclaration.period_start <= period_start_to)

    declarations = query.order_by(CBAMDeclaration.period_start.desc()).offset(skip).limit(limit).all()

    # Build summary with line count
    results = []
    for decl in declarations:
        summary = CBAMDeclarationSummary(
            id=decl.id,
            tenant_id=decl.tenant_id,
            declaration_reference=decl.declaration_reference,
            period_start=decl.period_start,
            period_end=decl.period_end,
            status=decl.status,
            total_embedded_emissions_tco2e=decl.total_embedded_emissions_tco2e or 0.0,
            total_quantity=decl.total_quantity or 0.0,
            line_count=len(decl.lines) if decl.lines else 0,
            importer_name=decl.importer_name,
            created_at=decl.created_at,
        )
        results.append(summary)

    return results


@router.post(
    "/declarations",
    response_model=CBAMDeclarationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create CBAM Declaration",
)
async def create_declaration(
    declaration: CBAMDeclarationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Create a new CBAM declaration."""
    # Extract lines if provided
    lines_data = declaration.lines or []
    declaration_data = declaration.model_dump(exclude={"lines"})

    # MULTI-TENANT: Set tenant_id from authenticated user
    db_declaration = create_tenant_record(
        db,
        CBAMDeclaration,
        current_user.tenant_id,
        created_by_user_id=current_user.user_id,
        **declaration_data
    )
    db.flush()  # Get the ID

    # Add lines if provided
    for line_data in lines_data:
        # Verify product exists
        product = db.query(CBAMProduct).filter(
            CBAMProduct.id == line_data.cbam_product_id
        ).first()
        if not product:
            raise HTTPException(
                status_code=400,
                detail=f"Product with ID {line_data.cbam_product_id} not found"
            )

        db_line = CBAMDeclarationLine(
            declaration_id=db_declaration.id,
            **line_data.model_dump()
        )
        db.add(db_line)

    db.commit()
    db.refresh(db_declaration)

    # Build response with lines
    return _build_declaration_response(db_declaration)


@router.get(
    "/declarations/{declaration_id}",
    response_model=CBAMDeclarationResponse,
    summary="Get CBAM Declaration",
)
async def get_declaration(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific CBAM declaration with all lines."""
    # MULTI-TENANT: Filter by tenant_id
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )
    return _build_declaration_response(declaration)


@router.put(
    "/declarations/{declaration_id}",
    response_model=CBAMDeclarationResponse,
    summary="Update CBAM Declaration",
)
async def update_declaration(
    declaration_id: int,
    declaration: CBAMDeclarationUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update a CBAM declaration."""
    # MULTI-TENANT: Verify ownership and update
    update_data = declaration.model_dump(exclude_unset=True)
    db_declaration = update_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id, update_data
    )
    db.commit()
    db.refresh(db_declaration)
    return _build_declaration_response(db_declaration)


@router.delete(
    "/declarations/{declaration_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete CBAM Declaration",
)
async def delete_declaration(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a CBAM declaration and all its lines (CASCADE)."""
    # MULTI-TENANT: Verify ownership and delete
    delete_tenant_record(db, CBAMDeclaration, declaration_id, current_user.tenant_id)
    db.commit()


# =============================================================================
# CBAM DECLARATION LINES (Scoped via Parent Declaration)
# =============================================================================

@router.get(
    "/declarations/{declaration_id}/lines",
    response_model=List[CBAMDeclarationLineResponse],
    summary="List Declaration Lines",
)
async def list_declaration_lines(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get all lines for a declaration."""
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    lines = db.query(CBAMDeclarationLine).filter(
        CBAMDeclarationLine.declaration_id == declaration_id
    ).order_by(CBAMDeclarationLine.id).all()

    return [_build_line_response(line, db) for line in lines]


@router.post(
    "/declarations/{declaration_id}/lines",
    response_model=CBAMDeclarationLineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Declaration Line",
)
async def add_declaration_line(
    declaration_id: int,
    line: CBAMDeclarationLineCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Add a line to a declaration."""
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    # Verify product exists
    product = db.query(CBAMProduct).filter(
        CBAMProduct.id == line.cbam_product_id
    ).first()
    if not product:
        raise HTTPException(
            status_code=400,
            detail=f"Product with ID {line.cbam_product_id} not found"
        )

    db_line = CBAMDeclarationLine(
        declaration_id=declaration_id,
        **line.model_dump()
    )
    db.add(db_line)
    db.commit()
    db.refresh(db_line)

    # Update declaration totals
    _recalculate_declaration_totals(db, declaration)
    db.commit()

    return _build_line_response(db_line, db)


@router.get(
    "/declarations/{declaration_id}/lines/{line_id}",
    response_model=CBAMDeclarationLineResponse,
    summary="Get Declaration Line",
)
async def get_declaration_line(
    declaration_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific line from a declaration."""
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    line = db.query(CBAMDeclarationLine).filter(
        CBAMDeclarationLine.id == line_id,
        CBAMDeclarationLine.declaration_id == declaration_id
    ).first()

    if not line:
        raise HTTPException(status_code=404, detail="Declaration line not found")

    return _build_line_response(line, db)


@router.put(
    "/declarations/{declaration_id}/lines/{line_id}",
    response_model=CBAMDeclarationLineResponse,
    summary="Update Declaration Line",
)
async def update_declaration_line(
    declaration_id: int,
    line_id: int,
    line_update: CBAMDeclarationLineUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update a declaration line."""
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    db_line = db.query(CBAMDeclarationLine).filter(
        CBAMDeclarationLine.id == line_id,
        CBAMDeclarationLine.declaration_id == declaration_id
    ).first()

    if not db_line:
        raise HTTPException(status_code=404, detail="Declaration line not found")

    # Update fields
    update_data = line_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_line, key, value)

    db.commit()
    db.refresh(db_line)

    # Update declaration totals
    _recalculate_declaration_totals(db, declaration)
    db.commit()

    return _build_line_response(db_line, db)


@router.delete(
    "/declarations/{declaration_id}/lines/{line_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Declaration Line",
)
async def delete_declaration_line(
    declaration_id: int,
    line_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Delete a declaration line."""
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    result = db.query(CBAMDeclarationLine).filter(
        CBAMDeclarationLine.id == line_id,
        CBAMDeclarationLine.declaration_id == declaration_id
    ).delete()

    if result == 0:
        raise HTTPException(status_code=404, detail="Declaration line not found")

    db.commit()

    # Update declaration totals
    _recalculate_declaration_totals(db, declaration)
    db.commit()


# =============================================================================
# CALCULATION ENDPOINT
# =============================================================================

@router.post(
    "/declarations/{declaration_id}/calculate",
    response_model=CBAMCalculateResponse,
    summary="Calculate Embedded Emissions",
    description="Calculate embedded emissions for all lines in a declaration.",
)
async def calculate_declaration_emissions(
    declaration_id: int,
    recalculate_all: bool = Query(False, description="Recalculate all lines, not just uncalculated ones"),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Calculate embedded emissions for a CBAM declaration.

    For each line:
    1. Look up the emission factor (plant-specific or EU default)
    2. Calculate: embedded_emissions = quantity * factor
    3. Store the result
    """
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    lines = db.query(CBAMDeclarationLine).filter(
        CBAMDeclarationLine.declaration_id == declaration_id
    ).all()

    results = []
    errors = []
    lines_calculated = 0
    lines_skipped = 0

    for line in lines:
        # Skip if already calculated and not recalculating
        if not recalculate_all and line.embedded_emissions_tco2e is not None:
            lines_skipped += 1
            continue

        # Get the product
        product = db.query(CBAMProduct).filter(
            CBAMProduct.id == line.cbam_product_id
        ).first()

        if not product:
            errors.append(f"Line {line.id}: Product {line.cbam_product_id} not found")
            continue

        # Determine emission factor
        # Priority: 1. Manual override, 2. Installation-specific, 3. Product default
        factor_value = None
        factor_unit = "tCO2e/tonne"
        factor_dataset = CBAMFactorDataset.CBAM_DEFAULT
        is_default = True

        # Check for manual override on line
        if line.emission_factor_value is not None:
            factor_value = line.emission_factor_value
            factor_unit = line.emission_factor_unit or factor_unit
            factor_dataset = line.factor_dataset or CBAMFactorDataset.CBAM_PLANT_SPECIFIC
            is_default = False

        # Check for installation-specific factor
        elif line.facility_id:
            installation = tenant_query(
                db, CBAMInstallation, current_user.tenant_id
            ).filter(
                CBAMInstallation.installation_id == line.facility_id,
                CBAMInstallation.is_active == True
            ).first()

            if installation and installation.specific_emission_factor:
                factor_value = installation.specific_emission_factor
                factor_unit = installation.specific_factor_unit or factor_unit
                factor_dataset = CBAMFactorDataset.CBAM_PLANT_SPECIFIC
                is_default = False

        # Fall back to product default
        if factor_value is None:
            # For now, use a placeholder default factor
            # In production, this would look up from emission_factors table
            factor_value = _get_default_factor_for_product(product, db)
            if factor_value is None:
                errors.append(f"Line {line.id}: No emission factor available for product {product.cn_code}")
                continue

        # Calculate emissions
        embedded_emissions = line.quantity * factor_value

        # Update line
        line.embedded_emissions_tco2e = embedded_emissions
        line.emission_factor_value = factor_value
        line.emission_factor_unit = factor_unit
        line.factor_dataset = factor_dataset
        line.is_default_factor = is_default
        line.calculation_date = datetime.utcnow()

        lines_calculated += 1
        results.append(CBAMCalculationResult(
            line_id=line.id,
            cbam_product_id=line.cbam_product_id,
            quantity=line.quantity,
            embedded_emissions_tco2e=embedded_emissions,
            emission_factor_value=factor_value,
            emission_factor_unit=factor_unit,
            factor_dataset=factor_dataset,
            is_default_factor=is_default,
        ))

    db.commit()

    # Update declaration totals
    _recalculate_declaration_totals(db, declaration)
    db.commit()
    db.refresh(declaration)

    return CBAMCalculateResponse(
        declaration_id=declaration_id,
        total_embedded_emissions_tco2e=declaration.total_embedded_emissions_tco2e or 0.0,
        total_quantity=declaration.total_quantity or 0.0,
        lines_calculated=lines_calculated,
        lines_skipped=lines_skipped,
        results=results,
        errors=errors,
    )


# =============================================================================
# BREAKDOWN/AGGREGATION ENDPOINT
# =============================================================================

@router.get(
    "/declarations/{declaration_id}/breakdown",
    response_model=CBAMDeclarationBreakdown,
    summary="Get Declaration Breakdown",
    description="Get emissions breakdown by product, country, and factor dataset.",
)
async def get_declaration_breakdown(
    declaration_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get detailed breakdown of a CBAM declaration."""
    # MULTI-TENANT: Verify declaration belongs to tenant
    declaration = get_tenant_record(
        db, CBAMDeclaration, declaration_id, current_user.tenant_id
    )

    lines = db.query(CBAMDeclarationLine).filter(
        CBAMDeclarationLine.declaration_id == declaration_id
    ).all()

    # Aggregate by product
    by_product = {}
    for line in lines:
        product = db.query(CBAMProduct).filter(
            CBAMProduct.id == line.cbam_product_id
        ).first()

        if line.cbam_product_id not in by_product:
            by_product[line.cbam_product_id] = {
                "cbam_product_id": line.cbam_product_id,
                "cn_code": product.cn_code if product else "UNKNOWN",
                "sector": product.sector if product else CBAMProductSector.IRON_STEEL,
                "total_quantity": 0.0,
                "total_emissions_tco2e": 0.0,
                "line_count": 0,
                "default_count": 0,
            }

        by_product[line.cbam_product_id]["total_quantity"] += line.quantity or 0
        by_product[line.cbam_product_id]["total_emissions_tco2e"] += line.embedded_emissions_tco2e or 0
        by_product[line.cbam_product_id]["line_count"] += 1
        if line.is_default_factor:
            by_product[line.cbam_product_id]["default_count"] += 1

    product_breakdowns = []
    for p in by_product.values():
        default_pct = (p["default_count"] / p["line_count"] * 100) if p["line_count"] > 0 else 0
        product_breakdowns.append(CBAMProductBreakdown(
            cbam_product_id=p["cbam_product_id"],
            cn_code=p["cn_code"],
            sector=p["sector"],
            total_quantity=p["total_quantity"],
            total_emissions_tco2e=p["total_emissions_tco2e"],
            line_count=p["line_count"],
            default_factor_percentage=default_pct,
        ))

    # Aggregate by country
    by_country = {}
    for line in lines:
        country = line.country_of_origin
        if country not in by_country:
            by_country[country] = {
                "country_of_origin": country,
                "total_quantity": 0.0,
                "total_emissions_tco2e": 0.0,
                "line_count": 0,
                "products": set(),
            }

        by_country[country]["total_quantity"] += line.quantity or 0
        by_country[country]["total_emissions_tco2e"] += line.embedded_emissions_tco2e or 0
        by_country[country]["line_count"] += 1

        product = db.query(CBAMProduct).filter(
            CBAMProduct.id == line.cbam_product_id
        ).first()
        if product:
            by_country[country]["products"].add(product.cn_code)

    country_breakdowns = []
    for c in by_country.values():
        country_breakdowns.append(CBAMCountryBreakdown(
            country_of_origin=c["country_of_origin"],
            total_quantity=c["total_quantity"],
            total_emissions_tco2e=c["total_emissions_tco2e"],
            line_count=c["line_count"],
            products=list(c["products"]),
        ))

    # Aggregate by factor dataset
    by_dataset = {}
    for line in lines:
        dataset_name = line.factor_dataset.value if line.factor_dataset else "UNKNOWN"
        if dataset_name not in by_dataset:
            by_dataset[dataset_name] = 0.0
        by_dataset[dataset_name] += line.embedded_emissions_tco2e or 0

    return CBAMDeclarationBreakdown(
        declaration_id=declaration_id,
        total_embedded_emissions_tco2e=declaration.total_embedded_emissions_tco2e or 0.0,
        total_quantity=declaration.total_quantity or 0.0,
        by_product=product_breakdowns,
        by_country=country_breakdowns,
        by_factor_dataset=by_dataset,
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_declaration_response(declaration: CBAMDeclaration) -> CBAMDeclarationResponse:
    """Build a full declaration response with lines."""
    lines = []
    for line in declaration.lines:
        lines.append(CBAMDeclarationLineResponse(
            id=line.id,
            declaration_id=line.declaration_id,
            cbam_product_id=line.cbam_product_id,
            country_of_origin=line.country_of_origin,
            facility_id=line.facility_id,
            facility_name=line.facility_name,
            quantity=line.quantity,
            quantity_unit=line.quantity_unit,
            embedded_emissions_tco2e=line.embedded_emissions_tco2e,
            emission_factor_value=line.emission_factor_value,
            emission_factor_unit=line.emission_factor_unit,
            emission_factor_id=line.emission_factor_id,
            factor_dataset=line.factor_dataset,
            is_default_factor=line.is_default_factor or True,
            evidence_reference=line.evidence_reference,
            evidence_document_id=line.evidence_document_id,
            calculation_date=line.calculation_date,
            calculation_notes=line.calculation_notes,
            created_at=line.created_at,
            updated_at=line.updated_at,
            product=None,  # Could populate if needed
        ))

    return CBAMDeclarationResponse(
        id=declaration.id,
        tenant_id=declaration.tenant_id,
        declaration_reference=declaration.declaration_reference,
        period_start=declaration.period_start,
        period_end=declaration.period_end,
        status=declaration.status,
        total_embedded_emissions_tco2e=declaration.total_embedded_emissions_tco2e or 0.0,
        total_quantity=declaration.total_quantity or 0.0,
        importer_name=declaration.importer_name,
        importer_eori=declaration.importer_eori,
        importer_country=declaration.importer_country,
        is_verified=declaration.is_verified or False,
        verified_by=declaration.verified_by,
        verified_at=declaration.verified_at,
        verification_notes=declaration.verification_notes,
        submitted_at=declaration.submitted_at,
        submission_reference=declaration.submission_reference,
        created_at=declaration.created_at,
        updated_at=declaration.updated_at,
        created_by_user_id=declaration.created_by_user_id,
        lines=lines,
        line_count=len(lines),
    )


def _build_line_response(line: CBAMDeclarationLine, db: Session) -> CBAMDeclarationLineResponse:
    """Build a line response with product info."""
    product = None
    if line.cbam_product_id:
        db_product = db.query(CBAMProduct).filter(
            CBAMProduct.id == line.cbam_product_id
        ).first()
        if db_product:
            product = CBAMProductResponse(
                id=db_product.id,
                cn_code=db_product.cn_code,
                description=db_product.description,
                sector=db_product.sector,
                unit=db_product.unit,
                hs_code=db_product.hs_code,
                notes=db_product.notes,
                is_active=db_product.is_active,
                default_factor_id=db_product.default_factor_id,
                created_at=db_product.created_at,
                updated_at=db_product.updated_at,
            )

    return CBAMDeclarationLineResponse(
        id=line.id,
        declaration_id=line.declaration_id,
        cbam_product_id=line.cbam_product_id,
        country_of_origin=line.country_of_origin,
        facility_id=line.facility_id,
        facility_name=line.facility_name,
        quantity=line.quantity,
        quantity_unit=line.quantity_unit,
        embedded_emissions_tco2e=line.embedded_emissions_tco2e,
        emission_factor_value=line.emission_factor_value,
        emission_factor_unit=line.emission_factor_unit,
        emission_factor_id=line.emission_factor_id,
        factor_dataset=line.factor_dataset,
        is_default_factor=line.is_default_factor if line.is_default_factor is not None else True,
        evidence_reference=line.evidence_reference,
        evidence_document_id=line.evidence_document_id,
        calculation_date=line.calculation_date,
        calculation_notes=line.calculation_notes,
        created_at=line.created_at,
        updated_at=line.updated_at,
        product=product,
    )


def _recalculate_declaration_totals(db: Session, declaration: CBAMDeclaration) -> None:
    """Recalculate total emissions and quantity for a declaration."""
    totals = db.query(
        func.sum(CBAMDeclarationLine.embedded_emissions_tco2e).label("total_emissions"),
        func.sum(CBAMDeclarationLine.quantity).label("total_quantity"),
    ).filter(
        CBAMDeclarationLine.declaration_id == declaration.id
    ).first()

    declaration.total_embedded_emissions_tco2e = totals.total_emissions or 0.0
    declaration.total_quantity = totals.total_quantity or 0.0


def _get_default_factor_for_product(product: CBAMProduct, db: Session) -> Optional[float]:
    """
    Get the default emission factor for a CBAM product.

    In production, this would look up from the emission_factors table
    based on the product's sector and default_factor_id.

    For now, returns placeholder values based on sector.
    """
    # Placeholder default factors by sector (tCO2e per tonne)
    # These should come from the emission_factors table in production
    SECTOR_DEFAULT_FACTORS = {
        CBAMProductSector.IRON_STEEL: 1.9,      # Approximate EU default for steel
        CBAMProductSector.ALUMINIUM: 8.4,       # Approximate for primary aluminium
        CBAMProductSector.CEMENT: 0.9,          # Clinker-based estimate
        CBAMProductSector.FERTILISERS: 2.8,     # Nitrogen fertilisers
        CBAMProductSector.ELECTRICITY: 0.5,     # Per MWh equivalent
        CBAMProductSector.HYDROGEN: 9.0,        # Grey hydrogen estimate
    }

    # If product has a specific default factor, use that
    if product.default_factor_id:
        # Look up from emission_factors table
        from app.models.emission_factor import EmissionFactor
        factor = db.query(EmissionFactor).filter(
            EmissionFactor.id == product.default_factor_id
        ).first()
        if factor and factor.factor:
            return factor.factor

    # Fall back to sector default
    return SECTOR_DEFAULT_FACTORS.get(product.sector)
