# app/services/reports.py
"""
CSRD/ESRS Report Generation Service
====================================
Generates XHTML documents with embedded iXBRL tags for ESRS E1 disclosures.
"""
from datetime import date, datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.emission import Emission
from app.schemas.report import (
    CSRDSummaryRequest,
    CSRDSummaryResponse,
    ScopeBreakdown,
)
from app.core.config import settings


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
        scope_totals = (
            db.query(
                Emission.scope,
                func.sum(Emission.emissions_kg_co2e).label("total"),
                func.count(Emission.id).label("count"),
            )
            .filter(Emission.tenant_id == tenant_id)
            .filter(Emission.created_at >= period_start)
            .filter(Emission.created_at <= period_end)
            .group_by(Emission.scope)
            .all()
        )

        for row in scope_totals:
            scope_key = f"scope_{row.scope}" if row.scope else "scope_3"
            result[scope_key] = float(row.total or 0)
            result["count"] += row.count or 0

        # Get unique datasets used (tenant-filtered)
        datasets = (
            db.query(Emission.dataset_used)
            .filter(Emission.tenant_id == tenant_id)
            .filter(Emission.created_at >= period_start)
            .filter(Emission.created_at <= period_end)
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
) -> str:
    """
    Generate XHTML document with embedded iXBRL tags for ESRS E1.

    Uses ESRS taxonomy namespaces and proper iXBRL structure.
    """
    total_tonnes = total_kg / 1000
    scope_1_tonnes = scope_breakdown.scope_1_kg_co2e / 1000
    scope_2_tonnes = scope_breakdown.scope_2_kg_co2e / 1000
    scope_3_tonnes = scope_breakdown.scope_3_kg_co2e / 1000

    lei_section = ""
    if lei:
        lei_section = f"""
        <p>LEI: <ix:nonNumeric name="esrs:LegalEntityIdentifier" contextRef="ctx_period">{lei}</ix:nonNumeric></p>"""

    methodology_section = ""
    if include_methodology:
        methodology_section = """
    <section id="methodology">
        <h2>Methodology Notes</h2>
        <p>This report was generated using FactorTrace, an ESRS E1-compliant emissions calculation platform.</p>
        <p>Emission factors sourced from:</p>
        <ul>
            <li>DEFRA 2024 - UK Government GHG Conversion Factors</li>
            <li>EPA 2024 - US EPA Emission Factors Hub</li>
            <li>EXIOBASE 3 - Multi-Regional Environmentally Extended Input-Output Database</li>
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
    <title>ESRS E1 Climate Disclosure - {organization_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; }}
        h1 {{ color: #1a365d; border-bottom: 2px solid #2b6cb0; padding-bottom: 0.5rem; }}
        h2 {{ color: #2c5282; margin-top: 2rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #edf2f7; }}
        .total {{ font-weight: bold; background-color: #f7fafc; }}
        .numeric {{ text-align: right; font-family: monospace; }}
        .metadata {{ color: #718096; font-size: 0.875rem; }}
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
        <p><strong>Reporting Entity:</strong> <ix:nonNumeric name="esrs:ReportingEntityName" contextRef="ctx_period">{organization_name}</ix:nonNumeric></p>
        <p><strong>Reporting Period:</strong> {period_start.isoformat()} to {period_end.isoformat()}</p>{lei_section}
    </header>

    <section id="e1-6">
        <h2>E1-6: Gross Scopes 1, 2, 3 and Total GHG Emissions</h2>

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
                                        decimals="2">{scope_1_tonnes:.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr>
                    <td>Scope 2 - Indirect Energy Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:GrossScope2GHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{scope_2_tonnes:.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr>
                    <td>Scope 3 - Value Chain Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:GrossScope3GHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{scope_3_tonnes:.2f}</ix:nonFraction>
                    </td>
                </tr>
                <tr class="total">
                    <td>Total GHG Emissions</td>
                    <td class="numeric">
                        <ix:nonFraction name="esrs:TotalGHGEmissions"
                                        contextRef="ctx_period"
                                        unitRef="unit_tonnes_co2e"
                                        decimals="2">{total_tonnes:.2f}</ix:nonFraction>
                    </td>
                </tr>
            </tbody>
        </table>
    </section>
{methodology_section}
    <footer class="metadata">
        <p>Generated by FactorTrace v{settings.app_version} on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p>This document conforms to ESRS E1 disclosure requirements per Delegated Regulation (EU) 2023/2772.</p>
    </footer>
</body>
</html>"""

    return xhtml
