# app/services/cbam_report.py
"""
CBAM Declaration Report Service
================================
Generates CBAM declaration reports with embedded emissions calculations,
product breakdowns, and export capabilities (CSV, PDF).

Security: All queries are filtered by tenant_id for multi-tenant isolation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import func
import csv
import io
import logging

from app.models.cbam import (
    CBAMDeclaration,
    CBAMDeclarationLine,
    CBAMProduct,
    CBAMDeclarationStatus,
    CBAMProductSector,
    CBAMFactorDataset,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class CBAMProductBreakdown:
    """Breakdown of emissions by product."""
    cn_code: str
    description: str
    sector: str
    quantity: float
    quantity_unit: str
    embedded_emissions_tco2e: float
    emission_factor_value: float
    emission_factor_unit: str
    is_default_factor: bool
    country_of_origin: str
    line_count: int = 1


@dataclass
class CBAMCountryBreakdown:
    """Breakdown of emissions by country of origin."""
    country_code: str
    country_name: str
    total_quantity: float
    total_emissions_tco2e: float
    line_count: int
    percentage: float = 0.0


@dataclass
class CBAMSectorBreakdown:
    """Breakdown of emissions by CBAM sector."""
    sector: str
    sector_name: str
    total_quantity: float
    total_emissions_tco2e: float
    line_count: int
    percentage: float = 0.0


@dataclass
class CBAMDeclarationReport:
    """Complete CBAM declaration report data structure."""
    # Declaration info
    declaration_id: int
    declaration_reference: Optional[str]
    tenant_id: str
    status: str
    period_start: datetime
    period_end: datetime

    # Importer info
    importer_name: Optional[str]
    importer_eori: Optional[str]
    importer_country: Optional[str]

    # Totals
    total_quantity: float
    total_embedded_emissions_tco2e: float
    line_count: int

    # Breakdowns
    product_breakdown: List[CBAMProductBreakdown] = field(default_factory=list)
    country_breakdown: List[CBAMCountryBreakdown] = field(default_factory=list)
    sector_breakdown: List[CBAMSectorBreakdown] = field(default_factory=list)

    # Factor source summary
    default_factor_count: int = 0
    plant_specific_factor_count: int = 0

    # Metadata
    generated_at: str = ""
    factortrace_version: str = ""


# =============================================================================
# MAIN REPORT GENERATION
# =============================================================================

def generate_cbam_declaration(
    db: Session,
    tenant_id: str,
    declaration_id: int,
) -> Dict[str, Any]:
    """
    Generate CBAM declaration report with full breakdown.

    Args:
        db: Database session
        tenant_id: Tenant ID (REQUIRED for multi-tenant isolation)
        declaration_id: ID of the CBAM declaration

    Returns:
        Dict with declaration data, breakdowns, and export formats

    Raises:
        ValueError: If declaration not found or not owned by tenant
    """
    # Query declaration with tenant filter (MULTI-TENANT)
    declaration = (
        db.query(CBAMDeclaration)
        .filter(CBAMDeclaration.id == declaration_id)
        .filter(CBAMDeclaration.tenant_id == tenant_id)
        .first()
    )

    if not declaration:
        raise ValueError(f"Declaration {declaration_id} not found or not authorized")

    # Query all line items with product info
    lines = (
        db.query(CBAMDeclarationLine)
        .filter(CBAMDeclarationLine.declaration_id == declaration_id)
        .all()
    )

    # Build report
    report = _build_declaration_report(declaration, lines)

    # Generate export formats
    csv_content = _generate_csv(report)

    return {
        "declaration": {
            "id": declaration.id,
            "reference": declaration.declaration_reference,
            "status": declaration.status.value if declaration.status else "draft",
            "period_start": declaration.period_start.isoformat() if declaration.period_start else None,
            "period_end": declaration.period_end.isoformat() if declaration.period_end else None,
            "importer_name": declaration.importer_name,
            "importer_eori": declaration.importer_eori,
            "importer_country": declaration.importer_country,
            "total_quantity": round(declaration.total_quantity or 0, 2),
            "total_embedded_emissions_tco2e": round(declaration.total_embedded_emissions_tco2e or 0, 4),
            "line_count": len(lines),
            "is_verified": declaration.is_verified,
            "verified_by": declaration.verified_by,
            "verified_at": declaration.verified_at.isoformat() if declaration.verified_at else None,
        },
        "breakdowns": {
            "by_product": [
                {
                    "cn_code": p.cn_code,
                    "description": p.description,
                    "sector": p.sector,
                    "quantity": round(p.quantity, 2),
                    "quantity_unit": p.quantity_unit,
                    "embedded_emissions_tco2e": round(p.embedded_emissions_tco2e, 4),
                    "emission_factor_value": round(p.emission_factor_value, 6) if p.emission_factor_value else None,
                    "is_default_factor": p.is_default_factor,
                    "country_of_origin": p.country_of_origin,
                }
                for p in report.product_breakdown
            ],
            "by_country": [
                {
                    "country_code": c.country_code,
                    "total_quantity": round(c.total_quantity, 2),
                    "total_emissions_tco2e": round(c.total_emissions_tco2e, 4),
                    "line_count": c.line_count,
                    "percentage": round(c.percentage, 1),
                }
                for c in report.country_breakdown
            ],
            "by_sector": [
                {
                    "sector": s.sector,
                    "sector_name": s.sector_name,
                    "total_quantity": round(s.total_quantity, 2),
                    "total_emissions_tco2e": round(s.total_emissions_tco2e, 4),
                    "line_count": s.line_count,
                    "percentage": round(s.percentage, 1),
                }
                for s in report.sector_breakdown
            ],
        },
        "factor_sources": {
            "default_factor_count": report.default_factor_count,
            "plant_specific_factor_count": report.plant_specific_factor_count,
            "default_factor_percentage": round(
                (report.default_factor_count / max(len(lines), 1)) * 100, 1
            ),
        },
        "csv_content": csv_content,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "factortrace_version": settings.app_version,
    }


def _build_declaration_report(
    declaration: CBAMDeclaration,
    lines: List[CBAMDeclarationLine],
) -> CBAMDeclarationReport:
    """Build complete declaration report from database objects."""
    report = CBAMDeclarationReport(
        declaration_id=declaration.id,
        declaration_reference=declaration.declaration_reference,
        tenant_id=declaration.tenant_id,
        status=declaration.status.value if declaration.status else "draft",
        period_start=declaration.period_start,
        period_end=declaration.period_end,
        importer_name=declaration.importer_name,
        importer_eori=declaration.importer_eori,
        importer_country=declaration.importer_country,
        total_quantity=declaration.total_quantity or 0,
        total_embedded_emissions_tco2e=declaration.total_embedded_emissions_tco2e or 0,
        line_count=len(lines),
        generated_at=datetime.utcnow().isoformat() + "Z",
        factortrace_version=settings.app_version,
    )

    # Aggregate by product
    product_map: Dict[str, CBAMProductBreakdown] = {}
    country_map: Dict[str, CBAMCountryBreakdown] = {}
    sector_map: Dict[str, CBAMSectorBreakdown] = {}

    for line in lines:
        # Get product info
        product = line.product
        cn_code = product.cn_code if product else "UNKNOWN"
        description = product.description if product else "Unknown Product"
        sector = product.sector.value if product and product.sector else "unknown"
        sector_name = _get_sector_name(sector)

        # Product breakdown
        if cn_code not in product_map:
            product_map[cn_code] = CBAMProductBreakdown(
                cn_code=cn_code,
                description=description,
                sector=sector,
                quantity=0,
                quantity_unit=line.quantity_unit or "tonne",
                embedded_emissions_tco2e=0,
                emission_factor_value=line.emission_factor_value or 0,
                emission_factor_unit=line.emission_factor_unit or "tCO2e/t",
                is_default_factor=line.is_default_factor if line.is_default_factor is not None else True,
                country_of_origin=line.country_of_origin or "XX",
                line_count=0,
            )
        product_map[cn_code].quantity += line.quantity or 0
        product_map[cn_code].embedded_emissions_tco2e += line.embedded_emissions_tco2e or 0
        product_map[cn_code].line_count += 1

        # Country breakdown
        country = line.country_of_origin or "XX"
        if country not in country_map:
            country_map[country] = CBAMCountryBreakdown(
                country_code=country,
                country_name=_get_country_name(country),
                total_quantity=0,
                total_emissions_tco2e=0,
                line_count=0,
            )
        country_map[country].total_quantity += line.quantity or 0
        country_map[country].total_emissions_tco2e += line.embedded_emissions_tco2e or 0
        country_map[country].line_count += 1

        # Sector breakdown
        if sector not in sector_map:
            sector_map[sector] = CBAMSectorBreakdown(
                sector=sector,
                sector_name=sector_name,
                total_quantity=0,
                total_emissions_tco2e=0,
                line_count=0,
            )
        sector_map[sector].total_quantity += line.quantity or 0
        sector_map[sector].total_emissions_tco2e += line.embedded_emissions_tco2e or 0
        sector_map[sector].line_count += 1

        # Factor source tracking
        if line.is_default_factor:
            report.default_factor_count += 1
        else:
            report.plant_specific_factor_count += 1

    # Calculate percentages
    total_emissions = report.total_embedded_emissions_tco2e
    if total_emissions > 0:
        for country in country_map.values():
            country.percentage = (country.total_emissions_tco2e / total_emissions) * 100
        for sector in sector_map.values():
            sector.percentage = (sector.total_emissions_tco2e / total_emissions) * 100

    # Sort and assign
    report.product_breakdown = sorted(
        product_map.values(),
        key=lambda x: x.embedded_emissions_tco2e,
        reverse=True
    )
    report.country_breakdown = sorted(
        country_map.values(),
        key=lambda x: x.total_emissions_tco2e,
        reverse=True
    )
    report.sector_breakdown = sorted(
        sector_map.values(),
        key=lambda x: x.total_emissions_tco2e,
        reverse=True
    )

    return report


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def _generate_csv(report: CBAMDeclarationReport) -> str:
    """Generate CSV export of CBAM declaration."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Header section
    writer.writerow(["CBAM Declaration Export"])
    writer.writerow([])
    writer.writerow(["Declaration Reference", report.declaration_reference or "N/A"])
    writer.writerow(["Status", report.status])
    writer.writerow(["Period Start", report.period_start.isoformat() if report.period_start else "N/A"])
    writer.writerow(["Period End", report.period_end.isoformat() if report.period_end else "N/A"])
    writer.writerow(["Importer", report.importer_name or "N/A"])
    writer.writerow(["EORI", report.importer_eori or "N/A"])
    writer.writerow([])

    # Summary
    writer.writerow(["Summary"])
    writer.writerow(["Total Quantity (tonnes)", round(report.total_quantity, 2)])
    writer.writerow(["Total Embedded Emissions (tCO2e)", round(report.total_embedded_emissions_tco2e, 4)])
    writer.writerow(["Line Items", report.line_count])
    writer.writerow([])

    # Product breakdown
    writer.writerow(["Product Breakdown"])
    writer.writerow([
        "CN Code", "Description", "Sector", "Country of Origin",
        "Quantity", "Unit", "Embedded Emissions (tCO2e)",
        "Emission Factor", "Factor Type"
    ])
    for product in report.product_breakdown:
        writer.writerow([
            product.cn_code,
            product.description[:100],  # Truncate long descriptions
            product.sector,
            product.country_of_origin,
            round(product.quantity, 2),
            product.quantity_unit,
            round(product.embedded_emissions_tco2e, 4),
            round(product.emission_factor_value, 6) if product.emission_factor_value else "N/A",
            "Default" if product.is_default_factor else "Plant-Specific",
        ])

    writer.writerow([])

    # Country breakdown
    writer.writerow(["Country Breakdown"])
    writer.writerow(["Country Code", "Total Quantity (tonnes)", "Total Emissions (tCO2e)", "Percentage"])
    for country in report.country_breakdown:
        writer.writerow([
            country.country_code,
            round(country.total_quantity, 2),
            round(country.total_emissions_tco2e, 4),
            f"{round(country.percentage, 1)}%",
        ])

    writer.writerow([])

    # Sector breakdown
    writer.writerow(["Sector Breakdown"])
    writer.writerow(["Sector", "Total Quantity (tonnes)", "Total Emissions (tCO2e)", "Percentage"])
    for sector in report.sector_breakdown:
        writer.writerow([
            sector.sector_name,
            round(sector.total_quantity, 2),
            round(sector.total_emissions_tco2e, 4),
            f"{round(sector.percentage, 1)}%",
        ])

    writer.writerow([])
    writer.writerow(["Generated", report.generated_at])
    writer.writerow(["FactorTrace Version", report.factortrace_version])

    return output.getvalue()


def export_cbam_declaration_csv(
    db: Session,
    tenant_id: str,
    declaration_id: int,
) -> str:
    """
    Export CBAM declaration as CSV string.

    Args:
        db: Database session
        tenant_id: Tenant ID
        declaration_id: Declaration ID

    Returns:
        CSV content as string
    """
    report_data = generate_cbam_declaration(db, tenant_id, declaration_id)
    return report_data["csv_content"]


def get_cbam_declaration_lines(
    db: Session,
    tenant_id: str,
    declaration_id: int,
) -> List[Dict[str, Any]]:
    """
    Get detailed line items for a CBAM declaration.

    Args:
        db: Database session
        tenant_id: Tenant ID
        declaration_id: Declaration ID

    Returns:
        List of line item dicts with product details
    """
    # Verify declaration ownership
    declaration = (
        db.query(CBAMDeclaration)
        .filter(CBAMDeclaration.id == declaration_id)
        .filter(CBAMDeclaration.tenant_id == tenant_id)
        .first()
    )

    if not declaration:
        raise ValueError(f"Declaration {declaration_id} not found or not authorized")

    lines = (
        db.query(CBAMDeclarationLine)
        .filter(CBAMDeclarationLine.declaration_id == declaration_id)
        .all()
    )

    return [
        {
            "id": line.id,
            "cn_code": line.product.cn_code if line.product else None,
            "product_description": line.product.description if line.product else None,
            "sector": line.product.sector.value if line.product and line.product.sector else None,
            "country_of_origin": line.country_of_origin,
            "facility_id": line.facility_id,
            "facility_name": line.facility_name,
            "quantity": line.quantity,
            "quantity_unit": line.quantity_unit,
            "embedded_emissions_tco2e": line.embedded_emissions_tco2e,
            "emission_factor_value": line.emission_factor_value,
            "emission_factor_unit": line.emission_factor_unit,
            "factor_dataset": line.factor_dataset.value if line.factor_dataset else None,
            "is_default_factor": line.is_default_factor,
            "calculation_date": line.calculation_date.isoformat() if line.calculation_date else None,
            "calculation_notes": line.calculation_notes,
        }
        for line in lines
    ]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_sector_name(sector: str) -> str:
    """Get human-readable sector name."""
    sector_names = {
        "iron_steel": "Iron & Steel",
        "aluminium": "Aluminium",
        "cement": "Cement",
        "fertilisers": "Fertilisers",
        "electricity": "Electricity",
        "hydrogen": "Hydrogen",
    }
    return sector_names.get(sector, sector.replace("_", " ").title())


def _get_country_name(country_code: str) -> str:
    """Get country name from ISO code (simplified mapping)."""
    # Common CBAM trade partners
    country_names = {
        "CN": "China",
        "RU": "Russia",
        "TR": "Turkey",
        "UA": "Ukraine",
        "IN": "India",
        "EG": "Egypt",
        "VN": "Vietnam",
        "TW": "Taiwan",
        "KR": "South Korea",
        "JP": "Japan",
        "US": "United States",
        "BR": "Brazil",
        "ZA": "South Africa",
        "AU": "Australia",
        "GB": "United Kingdom",
        "XX": "Unknown",
    }
    return country_names.get(country_code, country_code)
