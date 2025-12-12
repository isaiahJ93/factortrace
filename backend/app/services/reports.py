# app/services/reports.py
"""
CSRD/ESRS Report Generation Service
====================================
Generates XHTML documents with embedded iXBRL tags for ESRS E1 disclosures.
Includes data quality scoring and methodology disclosure per ESRS requirements.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from sqlalchemy.orm import Session
from sqlalchemy import func, case
import logging

from app.models.emission import Emission, EmissionScope, DataSourceType
from app.schemas.report import (
    CSRDSummaryRequest,
    CSRDSummaryResponse,
    ScopeBreakdown,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DataQualityMetrics:
    """Data quality metrics for ESRS E1 disclosure."""
    overall_score: int = 0  # 1-100
    measured_percentage: float = 0.0
    calculated_percentage: float = 0.0
    estimated_percentage: float = 0.0
    default_percentage: float = 0.0
    uncertainty_percentage: float = 0.0
    verified_count: int = 0
    total_count: int = 0


@dataclass
class Scope3Breakdown:
    """Scope 3 emissions breakdown by GHG Protocol category."""
    purchased_goods_services: float = 0.0
    capital_goods: float = 0.0
    fuel_energy_activities: float = 0.0
    upstream_transportation: float = 0.0
    waste_generated: float = 0.0
    business_travel: float = 0.0
    employee_commuting: float = 0.0
    upstream_leased_assets: float = 0.0
    downstream_transportation: float = 0.0
    processing_sold_products: float = 0.0
    use_sold_products: float = 0.0
    end_of_life_treatment: float = 0.0
    downstream_leased_assets: float = 0.0
    franchises: float = 0.0
    investments: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary, excluding zeros."""
        return {
            k: v for k, v in {
                "purchased_goods_services": self.purchased_goods_services,
                "capital_goods": self.capital_goods,
                "fuel_energy_activities": self.fuel_energy_activities,
                "upstream_transportation": self.upstream_transportation,
                "waste_generated": self.waste_generated,
                "business_travel": self.business_travel,
                "employee_commuting": self.employee_commuting,
                "upstream_leased_assets": self.upstream_leased_assets,
                "downstream_transportation": self.downstream_transportation,
                "processing_sold_products": self.processing_sold_products,
                "use_sold_products": self.use_sold_products,
                "end_of_life_treatment": self.end_of_life_treatment,
                "downstream_leased_assets": self.downstream_leased_assets,
                "franchises": self.franchises,
                "investments": self.investments,
            }.items() if v > 0
        }


@dataclass
class ESRSReportData:
    """Complete ESRS E1 report data structure."""
    # Organization info
    organization_name: str
    lei: Optional[str]
    reporting_year: int
    period_start: date
    period_end: date

    # Emissions data (in kg CO2e for schemas, tonnes for XBRL)
    scope_1_kg: float = 0.0
    scope_2_kg: float = 0.0
    scope_3_kg: float = 0.0
    scope_3_breakdown: Scope3Breakdown = field(default_factory=Scope3Breakdown)

    # Data quality
    data_quality: DataQualityMetrics = field(default_factory=DataQualityMetrics)

    # Metadata
    calculation_count: int = 0
    datasets_used: List[str] = field(default_factory=list)
    factor_sources: List[str] = field(default_factory=list)

    @property
    def total_kg(self) -> float:
        return self.scope_1_kg + self.scope_2_kg + self.scope_3_kg

    @property
    def total_tonnes(self) -> float:
        return self.total_kg / 1000


# =============================================================================
# MAIN REPORT GENERATION
# =============================================================================

def generate_esrs_e1_report(
    db: Session,
    tenant_id: str,
    organization_name: str,
    reporting_year: int,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    lei: Optional[str] = None,
    include_methodology: bool = True,
    revenue_eur: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive ESRS E1 report with data quality and methodology.

    Args:
        db: Database session
        tenant_id: Tenant ID (REQUIRED for multi-tenant isolation)
        organization_name: Legal name of reporting entity
        reporting_year: Reporting year
        period_start: Start of reporting period (defaults to Jan 1)
        period_end: End of reporting period (defaults to Dec 31)
        lei: Legal Entity Identifier (optional)
        include_methodology: Include methodology notes in output
        revenue_eur: Revenue in EUR for intensity calculations (optional)

    Returns:
        Dict with report_data, xhtml_content, data_quality, and metadata
    """
    # Set default period
    if period_start is None:
        period_start = date(reporting_year, 1, 1)
    if period_end is None:
        period_end = date(reporting_year, 12, 31)

    # Query and aggregate emissions
    report_data = _aggregate_emissions(
        db=db,
        tenant_id=tenant_id,
        period_start=period_start,
        period_end=period_end,
        organization_name=organization_name,
        lei=lei,
        reporting_year=reporting_year,
    )

    # Calculate GHG intensity if revenue provided
    ghg_intensity = None
    if revenue_eur and revenue_eur > 0:
        ghg_intensity = report_data.total_tonnes / (revenue_eur / 1_000_000)  # tCO2e per EUR million

    # Generate XHTML with iXBRL tags
    xhtml_content = _generate_xhtml(
        organization_name=organization_name,
        lei=lei,
        reporting_year=reporting_year,
        period_start=period_start,
        period_end=period_end,
        scope_breakdown=ScopeBreakdown(
            scope_1_kg_co2e=report_data.scope_1_kg,
            scope_2_kg_co2e=report_data.scope_2_kg,
            scope_3_kg_co2e=report_data.scope_3_kg,
        ),
        total_kg=report_data.total_kg,
        include_methodology=include_methodology,
        scope_3_breakdown=report_data.scope_3_breakdown,
        data_quality=report_data.data_quality,
        datasets_used=report_data.datasets_used,
        ghg_intensity=ghg_intensity,
    )

    return {
        "report_data": {
            "organization_name": organization_name,
            "reporting_year": reporting_year,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "lei": lei,
            "scope_1_kg_co2e": round(report_data.scope_1_kg, 2),
            "scope_2_kg_co2e": round(report_data.scope_2_kg, 2),
            "scope_3_kg_co2e": round(report_data.scope_3_kg, 2),
            "total_kg_co2e": round(report_data.total_kg, 2),
            "total_tonnes_co2e": round(report_data.total_tonnes, 4),
            "scope_3_categories": report_data.scope_3_breakdown.to_dict(),
            "ghg_intensity_tco2e_per_eur_million": round(ghg_intensity, 4) if ghg_intensity else None,
        },
        "data_quality": {
            "overall_score": report_data.data_quality.overall_score,
            "measured_percentage": round(report_data.data_quality.measured_percentage, 1),
            "calculated_percentage": round(report_data.data_quality.calculated_percentage, 1),
            "estimated_percentage": round(report_data.data_quality.estimated_percentage, 1),
            "default_percentage": round(report_data.data_quality.default_percentage, 1),
            "uncertainty_percentage": round(report_data.data_quality.uncertainty_percentage, 1),
            "verified_count": report_data.data_quality.verified_count,
            "total_count": report_data.data_quality.total_count,
        },
        "methodology": {
            "datasets_used": report_data.datasets_used,
            "factor_sources": report_data.factor_sources,
            "calculation_count": report_data.calculation_count,
        },
        "xhtml_content": xhtml_content,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "factortrace_version": settings.app_version,
    }


def generate_csrd_summary(
    db: Session,
    request: CSRDSummaryRequest,
    tenant_id: str,
) -> CSRDSummaryResponse:
    """
    Generate a CSRD-style summary report with embedded iXBRL tags.

    Args:
        db: Database session
        request: Report request parameters
        tenant_id: Tenant ID for multi-tenant filtering (REQUIRED)

    Returns:
        CSRDSummaryResponse with structured data and XHTML content
    """
    # Determine reporting period
    period_start = request.reporting_period_start or date(request.reporting_year, 1, 1)
    period_end = request.reporting_period_end or date(request.reporting_year, 12, 31)

    # Query emissions data from database (MULTI-TENANT: filtered by tenant_id)
    emissions_data = _query_emissions_by_scope(db, period_start, period_end, tenant_id)

    # Calculate totals
    scope_breakdown = ScopeBreakdown(
        scope_1_kg_co2e=emissions_data.get("scope_1", 0.0),
        scope_2_kg_co2e=emissions_data.get("scope_2", 0.0),
        scope_3_kg_co2e=emissions_data.get("scope_3", 0.0),
    )

    total_kg = (
        scope_breakdown.scope_1_kg_co2e +
        scope_breakdown.scope_2_kg_co2e +
        scope_breakdown.scope_3_kg_co2e
    )

    # Generate XHTML with iXBRL tags
    xhtml_content = _generate_xhtml(
        organization_name=request.organization_name,
        lei=request.lei,
        reporting_year=request.reporting_year,
        period_start=period_start,
        period_end=period_end,
        scope_breakdown=scope_breakdown,
        total_kg=total_kg,
        include_methodology=request.include_methodology_notes,
    )

    return CSRDSummaryResponse(
        organization_name=request.organization_name,
        reporting_year=request.reporting_year,
        reporting_period_start=period_start,
        reporting_period_end=period_end,
        lei=request.lei,
        total_emissions_kg_co2e=round(total_kg, 2),
        total_emissions_tonnes_co2e=round(total_kg / 1000, 2),
        scope_breakdown=scope_breakdown,
        calculation_count=emissions_data.get("count", 0),
        datasets_used=emissions_data.get("datasets", []),
        xhtml_content=xhtml_content,
        generated_at=datetime.utcnow().isoformat() + "Z",
        factortrace_version=settings.app_version,
    )


# =============================================================================
# DATA AGGREGATION
# =============================================================================

def _aggregate_emissions(
    db: Session,
    tenant_id: str,
    period_start: date,
    period_end: date,
    organization_name: str,
    lei: Optional[str],
    reporting_year: int,
) -> ESRSReportData:
    """
    Aggregate emissions data with quality metrics and Scope 3 breakdown.

    MULTI-TENANT: All queries filtered by tenant_id.
    """
    report = ESRSReportData(
        organization_name=organization_name,
        lei=lei,
        reporting_year=reporting_year,
        period_start=period_start,
        period_end=period_end,
    )

    try:
        # Base filter for all queries
        base_filter = [
            Emission.tenant_id == tenant_id,
            Emission.created_at >= period_start,
            Emission.created_at <= period_end,
            Emission.deleted_at.is_(None),  # Exclude soft-deleted
        ]

        # Query emissions by scope (amount is in tCO2e, convert to kg)
        scope_totals = (
            db.query(
                Emission.scope,
                func.sum(Emission.amount * 1000).label("total_kg"),  # tCO2e -> kg
                func.count(Emission.id).label("count"),
            )
            .filter(*base_filter)
            .group_by(Emission.scope)
            .all()
        )

        for row in scope_totals:
            if row.scope == EmissionScope.SCOPE_1 or row.scope == 1:
                report.scope_1_kg = float(row.total_kg or 0)
            elif row.scope == EmissionScope.SCOPE_2 or row.scope == 2:
                report.scope_2_kg = float(row.total_kg or 0)
            elif row.scope == EmissionScope.SCOPE_3 or row.scope == 3:
                report.scope_3_kg = float(row.total_kg or 0)
            report.calculation_count += row.count or 0

        # Query Scope 3 breakdown by category
        scope_3_categories = (
            db.query(
                Emission.category,
                func.sum(Emission.amount * 1000).label("total_kg"),
            )
            .filter(*base_filter)
            .filter(Emission.scope == EmissionScope.SCOPE_3)
            .group_by(Emission.category)
            .all()
        )

        category_map = {
            "purchased_goods_services": "purchased_goods_services",
            "purchased_goods": "purchased_goods_services",
            "capital_goods": "capital_goods",
            "fuel_energy_activities": "fuel_energy_activities",
            "fuel_energy": "fuel_energy_activities",
            "upstream_transportation": "upstream_transportation",
            "waste_generated": "waste_generated",
            "waste": "waste_generated",
            "business_travel": "business_travel",
            "employee_commuting": "employee_commuting",
            "commuting": "employee_commuting",
            "upstream_leased_assets": "upstream_leased_assets",
            "downstream_transportation": "downstream_transportation",
            "processing_sold_products": "processing_sold_products",
            "use_sold_products": "use_sold_products",
            "use_of_sold_products": "use_sold_products",
            "end_of_life_treatment": "end_of_life_treatment",
            "end_of_life": "end_of_life_treatment",
            "downstream_leased_assets": "downstream_leased_assets",
            "franchises": "franchises",
            "investments": "investments",
        }

        for row in scope_3_categories:
            normalized = category_map.get(row.category, row.category)
            if hasattr(report.scope_3_breakdown, normalized):
                setattr(report.scope_3_breakdown, normalized, float(row.total_kg or 0))

        # Query data quality metrics
        report.data_quality = _calculate_data_quality(db, base_filter)

        # Query unique datasets/sources used
        datasets = (
            db.query(Emission.emission_factor_source)
            .filter(*base_filter)
            .filter(Emission.emission_factor_source.isnot(None))
            .distinct()
            .all()
        )
        report.datasets_used = list(set(d[0] for d in datasets if d[0]))

    except Exception as e:
        logger.warning(f"Error aggregating emissions: {e}")
        # Return empty report on error

    return report


def _calculate_data_quality(
    db: Session,
    base_filter: List,
) -> DataQualityMetrics:
    """Calculate data quality metrics from emissions data."""
    metrics = DataQualityMetrics()

    try:
        # Count by data source type
        source_counts = (
            db.query(
                Emission.data_source,
                func.count(Emission.id).label("count"),
            )
            .filter(*base_filter)
            .group_by(Emission.data_source)
            .all()
        )

        total = sum(row.count for row in source_counts)
        metrics.total_count = total

        if total > 0:
            for row in source_counts:
                pct = (row.count / total) * 100
                if row.data_source == DataSourceType.MEASURED:
                    metrics.measured_percentage = pct
                elif row.data_source == DataSourceType.CALCULATED:
                    metrics.calculated_percentage = pct
                elif row.data_source == DataSourceType.ESTIMATED:
                    metrics.estimated_percentage = pct
                elif row.data_source == DataSourceType.DEFAULT:
                    metrics.default_percentage = pct

        # Count verified emissions
        verified = (
            db.query(func.count(Emission.id))
            .filter(*base_filter)
            .filter(Emission.is_verified == 1)
            .scalar()
        )
        metrics.verified_count = verified or 0

        # Calculate average uncertainty
        avg_uncertainty = (
            db.query(func.avg(Emission.uncertainty_percentage))
            .filter(*base_filter)
            .filter(Emission.uncertainty_percentage.isnot(None))
            .scalar()
        )
        metrics.uncertainty_percentage = float(avg_uncertainty or 30.0)  # Default 30%

        # Calculate overall quality score (0-100)
        # Higher is better: measured > calculated > estimated > default
        # Also factor in verification and uncertainty
        quality_weights = {
            "measured": 100,
            "calculated": 75,
            "estimated": 50,
            "default": 25,
        }

        weighted_sum = (
            metrics.measured_percentage * quality_weights["measured"] +
            metrics.calculated_percentage * quality_weights["calculated"] +
            metrics.estimated_percentage * quality_weights["estimated"] +
            metrics.default_percentage * quality_weights["default"]
        ) / 100

        # Verification bonus (up to 10 points)
        verification_bonus = (metrics.verified_count / max(total, 1)) * 10

        # Uncertainty penalty (lower uncertainty = higher score)
        uncertainty_penalty = max(0, (metrics.uncertainty_percentage - 10) / 2)

        metrics.overall_score = int(max(0, min(100,
            weighted_sum + verification_bonus - uncertainty_penalty
        )))

    except Exception as e:
        logger.warning(f"Error calculating data quality: {e}")
        metrics.overall_score = 50  # Default mid-range score

    return metrics


def _query_emissions_by_scope(
    db: Session,
    period_start: date,
    period_end: date,
    tenant_id: str,
) -> Dict[str, Any]:
    """
    Query emissions from database grouped by scope.

    MULTI-TENANT: Filters by tenant_id to ensure data isolation.

    Returns aggregated totals and metadata.
    """
    result = {
        "scope_1": 0.0,
        "scope_2": 0.0,
        "scope_3": 0.0,
        "count": 0,
        "datasets": [],
    }

    try:
        # Query aggregated emissions by scope
        # MULTI-TENANT: Always filter by tenant_id
        # Note: Emission.amount is in tCO2e, convert to kg for response
        scope_totals = (
            db.query(
                Emission.scope,
                func.sum(Emission.amount * 1000).label("total"),  # tCO2e -> kg
                func.count(Emission.id).label("count"),
            )
            .filter(Emission.tenant_id == tenant_id)
            .filter(Emission.created_at >= period_start)
            .filter(Emission.created_at <= period_end)
            .filter(Emission.deleted_at.is_(None))
            .group_by(Emission.scope)
            .all()
        )

        for row in scope_totals:
            scope_key = f"scope_{row.scope}" if row.scope else "scope_3"
            result[scope_key] = float(row.total or 0)
            result["count"] += row.count or 0

        # Get unique datasets used (tenant-filtered)
        datasets = (
            db.query(Emission.emission_factor_source)
            .filter(Emission.tenant_id == tenant_id)
            .filter(Emission.created_at >= period_start)
            .filter(Emission.created_at <= period_end)
            .filter(Emission.deleted_at.is_(None))
            .distinct()
            .all()
        )
        result["datasets"] = [d[0] for d in datasets if d[0]]

    except Exception:
        # If no emissions table or data, return zeros
        pass

    return result


def _generate_xhtml(
    organization_name: str,
    lei: Optional[str],
    reporting_year: int,
    period_start: date,
    period_end: date,
    scope_breakdown: ScopeBreakdown,
    total_kg: float,
    include_methodology: bool = True,
    scope_3_breakdown: Optional[Scope3Breakdown] = None,
    data_quality: Optional[DataQualityMetrics] = None,
    datasets_used: Optional[List[str]] = None,
    ghg_intensity: Optional[float] = None,
) -> str:
    """
    Generate XHTML document with embedded iXBRL tags for ESRS E1.

    Uses ESRS taxonomy namespaces and proper iXBRL structure.
    """
    from xml.sax.saxutils import escape as xml_escape

    total_tonnes = total_kg / 1000
    scope_1_tonnes = scope_breakdown.scope_1_kg_co2e / 1000
    scope_2_tonnes = scope_breakdown.scope_2_kg_co2e / 1000
    scope_3_tonnes = scope_breakdown.scope_3_kg_co2e / 1000

    lei_section = ""
    if lei:
        lei_section = f"""
        <p><strong>LEI:</strong> <ix:nonNumeric name="esrs:LegalEntityIdentifier" contextRef="ctx_period">{xml_escape(lei)}</ix:nonNumeric></p>"""

    # Scope 3 breakdown section
    scope_3_detail_section = ""
    if scope_3_breakdown and scope_3_tonnes > 0:
        categories = scope_3_breakdown.to_dict()
        if categories:
            rows = []
            category_labels = {
                "purchased_goods_services": "Cat 1: Purchased Goods & Services",
                "capital_goods": "Cat 2: Capital Goods",
                "fuel_energy_activities": "Cat 3: Fuel & Energy Activities",
                "upstream_transportation": "Cat 4: Upstream Transportation",
                "waste_generated": "Cat 5: Waste Generated",
                "business_travel": "Cat 6: Business Travel",
                "employee_commuting": "Cat 7: Employee Commuting",
                "upstream_leased_assets": "Cat 8: Upstream Leased Assets",
                "downstream_transportation": "Cat 9: Downstream Transportation",
                "processing_sold_products": "Cat 10: Processing of Sold Products",
                "use_sold_products": "Cat 11: Use of Sold Products",
                "end_of_life_treatment": "Cat 12: End-of-Life Treatment",
                "downstream_leased_assets": "Cat 13: Downstream Leased Assets",
                "franchises": "Cat 14: Franchises",
                "investments": "Cat 15: Investments",
            }
            for cat_key, kg_value in categories.items():
                label = category_labels.get(cat_key, cat_key.replace("_", " ").title())
                tonnes = kg_value / 1000
                rows.append(f"""                <tr>
                    <td>{xml_escape(label)}</td>
                    <td class="numeric">{tonnes:,.2f}</td>
                </tr>""")

            scope_3_detail_section = f"""
    <section id="scope3-breakdown">
        <h3>Scope 3 Category Breakdown</h3>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th class="numeric">tonnes CO2e</th>
                </tr>
            </thead>
            <tbody>
{chr(10).join(rows)}
            </tbody>
        </table>
    </section>"""

    # Data quality section
    data_quality_section = ""
    if data_quality and data_quality.total_count > 0:
        data_quality_section = f"""
    <section id="data-quality">
        <h2>Data Quality Assessment</h2>
        <table>
            <tbody>
                <tr>
                    <td>Overall Quality Score</td>
                    <td class="numeric"><strong>{data_quality.overall_score}/100</strong></td>
                </tr>
                <tr>
                    <td>Measured Data</td>
                    <td class="numeric">{data_quality.measured_percentage:.1f}%</td>
                </tr>
                <tr>
                    <td>Calculated Data</td>
                    <td class="numeric">{data_quality.calculated_percentage:.1f}%</td>
                </tr>
                <tr>
                    <td>Estimated Data</td>
                    <td class="numeric">{data_quality.estimated_percentage:.1f}%</td>
                </tr>
                <tr>
                    <td>Default Factors Used</td>
                    <td class="numeric">{data_quality.default_percentage:.1f}%</td>
                </tr>
                <tr>
                    <td>Verified Calculations</td>
                    <td class="numeric">{data_quality.verified_count} of {data_quality.total_count}</td>
                </tr>
                <tr>
                    <td>Uncertainty</td>
                    <td class="numeric">&plusmn;{data_quality.uncertainty_percentage:.1f}%</td>
                </tr>
            </tbody>
        </table>
    </section>"""

    # GHG Intensity section
    intensity_section = ""
    if ghg_intensity is not None:
        intensity_section = f"""
    <section id="ghg-intensity">
        <h2>GHG Intensity</h2>
        <p>GHG intensity (total emissions / revenue): <strong>{ghg_intensity:.4f} tCO2e per EUR million</strong></p>
    </section>"""

    # Methodology section
    methodology_section = ""
    if include_methodology:
        datasets_list = ""
        if datasets_used:
            datasets_list = "\n".join(f"            <li>{xml_escape(ds)}</li>" for ds in datasets_used)
        else:
            datasets_list = """            <li>DEFRA 2024 - UK Government GHG Conversion Factors</li>
            <li>EPA 2024 - US EPA Emission Factors Hub</li>
            <li>EXIOBASE 3 - Multi-Regional Environmentally Extended Input-Output Database</li>"""

        methodology_section = f"""
    <section id="methodology">
        <h2>Methodology Notes</h2>
        <p>This report was generated using FactorTrace, an ESRS E1-compliant emissions calculation platform.</p>
        <h3>Emission Factor Sources</h3>
        <ul>
{datasets_list}
        </ul>
        <h3>Standards & Guidelines</h3>
        <ul>
            <li>GHG Protocol Corporate Standard for Scope 1 and 2</li>
            <li>GHG Protocol Corporate Value Chain (Scope 3) Standard</li>
            <li>ESRS E1 Climate Change Disclosure Requirements</li>
        </ul>
        <p>All calculations follow GHG Protocol guidelines for Scope 1, 2, and 3 emissions.</p>
    </section>"""

    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2020-02-12"
      xmlns:esrs="http://www.efrag.org/esrs/2024"
      xmlns:xbrli="http://www.xbrl.org/2003/instance"
      xml:lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>ESRS E1 Climate Disclosure - {xml_escape(organization_name)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; line-height: 1.6; }}
        h1 {{ color: #1a365d; border-bottom: 2px solid #2b6cb0; padding-bottom: 0.5rem; }}
        h2 {{ color: #2c5282; margin-top: 2rem; border-bottom: 1px solid #e2e8f0; padding-bottom: 0.25rem; }}
        h3 {{ color: #3182ce; margin-top: 1.5rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #2c5282; color: white; }}
        tr:nth-child(even) {{ background-color: #f7fafc; }}
        .total {{ font-weight: bold; background-color: #ebf8ff; border-top: 2px solid #2b6cb0; }}
        .numeric {{ text-align: right; font-family: monospace; }}
        .metadata {{ color: #718096; font-size: 0.875rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }}
        ul {{ margin: 0.5rem 0; }}
        li {{ margin: 0.25rem 0; }}
    </style>
</head>
<body>
    <ix:header>
        <ix:hidden>
            <ix:context id="ctx_period">
                <xbrli:entity>
                    <xbrli:identifier scheme="http://standards.iso.org/iso/17442">{lei or 'NOT_PROVIDED'}</xbrli:identifier>
                </xbrli:entity>
                <xbrli:period>
                    <xbrli:startDate>{period_start.isoformat()}</xbrli:startDate>
                    <xbrli:endDate>{period_end.isoformat()}</xbrli:endDate>
                </xbrli:period>
            </ix:context>
            <ix:unit id="unit_tonnes_co2e">
                <xbrli:measure>esrs:tonnes_CO2e</xbrli:measure>
            </ix:unit>
        </ix:hidden>
    </ix:header>

    <header>
        <h1>ESRS E1 Climate-Related Disclosure</h1>
        <p><strong>Reporting Entity:</strong> <ix:nonNumeric name="esrs:ReportingEntityName" contextRef="ctx_period">{xml_escape(organization_name)}</ix:nonNumeric></p>
        <p><strong>Reporting Period:</strong> {period_start.isoformat()} to {period_end.isoformat()}</p>
        <p><strong>Reporting Year:</strong> {reporting_year}</p>{lei_section}
    </header>

    <section id="e1-6">
        <h2>E1-6: Gross Scopes 1, 2, 3 and Total GHG Emissions</h2>
        <p>Greenhouse gas emissions for the reporting period, measured in tonnes of CO2 equivalent (tCO2e).</p>

        <table>
            <thead>
                <tr>
                    <th>Emission Category</th>
                    <th class="numeric">tonnes CO2e</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Scope 1 - Direct Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:GrossScope1GHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{scope_1_tonnes:,.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr>
                    <td>Scope 2 - Indirect Energy Emissions (Location-based)</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:GrossScope2GHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{scope_2_tonnes:,.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr>
                    <td>Scope 3 - Value Chain Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:GrossScope3GHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{scope_3_tonnes:,.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr class="total">
                    <td>Total GHG Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:TotalGHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{total_tonnes:,.2f}</ix:nonFraction>
                    </td>
                </tr>
            </tbody>
        </table>
    </section>
{scope_3_detail_section}
{intensity_section}
{data_quality_section}
{methodology_section}
    <footer class="metadata">
        <p>Generated by FactorTrace v{settings.app_version} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p>This document conforms to ESRS E1 disclosure requirements per Delegated Regulation (EU) 2023/2772.</p>
    </footer>
</body>
</html>"""

    return xhtml
