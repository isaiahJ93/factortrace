# app/services/issb_report.py
"""
ISSB Disclosure Report Generation Service
==========================================
Generates comprehensive ISSB (IFRS S1/S2) disclosure reports with:
- Scope 1/2/3 emissions from linked data
- Scenario analysis results (1.5C, 2C, 3C)
- Double materiality scores
- Climate risk exposures by category
- Targets and progress tracking
- Export to PDF and JSON formats
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from io import BytesIO
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.issb import (
    ISSBDisclosureStatement,
    ISSBReportingUnit,
    ISSBFinancialMetric,
    ISSBClimateRiskExposure,
    ISSBTarget,
    ISSBScenario,
    ISSBScenarioResult,
    ISSBMaterialityAssessment,
    ISSBRiskType,
    ISSBTimeHorizon,
    ISSBTargetStatus,
    ISSBDisclosureSection,
    ISSBEmissionsScope,
)
from app.models.emission import Emission

logger = logging.getLogger(__name__)


class ISSBReportError(Exception):
    """Raised when ISSB report generation fails."""
    pass


def generate_issb_disclosure(
    db: Session,
    tenant_id: str,
    disclosure_id: int,
) -> Dict[str, Any]:
    """
    Generate a comprehensive ISSB disclosure report.

    Args:
        db: Database session
        tenant_id: Current tenant ID (for multi-tenant isolation)
        disclosure_id: ID of the disclosure statement

    Returns:
        Dict with full report data including:
        - disclosure: Basic disclosure info
        - emissions_summary: Scope 1/2/3 breakdown
        - scenario_analysis: Results by scenario (1.5C, 2C, 3C)
        - materiality: Double materiality scores
        - climate_risks: Risk exposures by category
        - targets: Targets and progress tracking

    Raises:
        ISSBReportError: If disclosure not found or generation fails
    """
    # Fetch disclosure with tenant isolation
    disclosure = (
        db.query(ISSBDisclosureStatement)
        .filter(
            ISSBDisclosureStatement.id == disclosure_id,
            ISSBDisclosureStatement.tenant_id == tenant_id,
        )
        .first()
    )

    if not disclosure:
        raise ISSBReportError(f"Disclosure {disclosure_id} not found")

    try:
        # Get the reporting unit
        reporting_unit = disclosure.reporting_unit

        # Build report sections
        report = {
            "report_type": "ISSB_DISCLOSURE",
            "generated_at": datetime.utcnow().isoformat(),
            "disclosure": _build_disclosure_summary(disclosure),
            "reporting_unit": _build_reporting_unit_info(reporting_unit),
            "emissions_summary": _build_emissions_summary(
                db, tenant_id, reporting_unit, disclosure
            ),
            "scenario_analysis": _build_scenario_analysis(
                db, tenant_id, reporting_unit, disclosure
            ),
            "materiality": _build_materiality_assessment(
                db, tenant_id, reporting_unit, disclosure
            ),
            "climate_risks": _build_climate_risks(
                db, tenant_id, reporting_unit, disclosure
            ),
            "targets": _build_targets_progress(
                db, tenant_id, reporting_unit
            ),
            "disclosure_sections": _build_disclosure_sections(
                db, tenant_id, reporting_unit, disclosure
            ),
        }

        return report

    except Exception as e:
        logger.error(f"ISSB report generation failed: {e}")
        raise ISSBReportError(f"Report generation failed: {e}")


def _build_disclosure_summary(disclosure: ISSBDisclosureStatement) -> Dict[str, Any]:
    """Build basic disclosure summary."""
    return {
        "id": disclosure.id,
        "standard": disclosure.standard.value if disclosure.standard else None,
        "section": disclosure.section.value if disclosure.section else None,
        "status": disclosure.status.value if disclosure.status else "draft",
        "period_start": disclosure.period_start.isoformat() if disclosure.period_start else None,
        "period_end": disclosure.period_end.isoformat() if disclosure.period_end else None,
        "headline_summary": disclosure.headline_summary,
        "generation_date": disclosure.generation_date.isoformat() if disclosure.generation_date else None,
        "approved_by": disclosure.approved_by,
        "approved_at": disclosure.approved_at.isoformat() if disclosure.approved_at else None,
    }


def _build_reporting_unit_info(unit: Optional[ISSBReportingUnit]) -> Dict[str, Any]:
    """Build reporting unit information."""
    if not unit:
        return {}
    return {
        "id": unit.id,
        "name": unit.name,
        "description": unit.description,
        "currency": unit.currency,
        "consolidation_method": unit.consolidation_method.value if unit.consolidation_method else None,
        "sector": unit.sector,
        "industry_code": unit.industry_code,
    }


def _build_emissions_summary(
    db: Session,
    tenant_id: str,
    reporting_unit: Optional[ISSBReportingUnit],
    disclosure: ISSBDisclosureStatement,
) -> Dict[str, Any]:
    """Build emissions summary by scope."""
    if not reporting_unit:
        return {
            "scope1": {"total_tco2e": 0.0, "categories": []},
            "scope2": {"total_tco2e": 0.0, "categories": []},
            "scope3": {"total_tco2e": 0.0, "categories": []},
            "total_tco2e": 0.0,
        }

    period_start = disclosure.period_start
    period_end = disclosure.period_end

    # Query emissions for the period, grouped by scope and category
    emissions_query = (
        db.query(
            Emission.scope,
            Emission.category,
            func.sum(Emission.total_emissions).label("total_tco2e"),
            func.count(Emission.id).label("record_count"),
        )
        .filter(
            Emission.tenant_id == tenant_id,
            Emission.date >= period_start,
            Emission.date <= period_end,
        )
        .group_by(Emission.scope, Emission.category)
    )

    emissions_data = emissions_query.all()

    # Organize by scope
    scope1_cats = []
    scope2_cats = []
    scope3_cats = []
    total_scope1 = 0.0
    total_scope2 = 0.0
    total_scope3 = 0.0

    for row in emissions_data:
        scope_val = row.scope.value if hasattr(row.scope, 'value') else str(row.scope)
        cat_data = {
            "category": row.category,
            "total_tco2e": float(row.total_tco2e or 0),
            "record_count": row.record_count,
        }

        if "1" in scope_val.lower() or scope_val == "SCOPE_1":
            scope1_cats.append(cat_data)
            total_scope1 += cat_data["total_tco2e"]
        elif "2" in scope_val.lower() or scope_val == "SCOPE_2":
            scope2_cats.append(cat_data)
            total_scope2 += cat_data["total_tco2e"]
        elif "3" in scope_val.lower() or scope_val == "SCOPE_3":
            scope3_cats.append(cat_data)
            total_scope3 += cat_data["total_tco2e"]

    return {
        "scope1": {
            "total_tco2e": total_scope1,
            "categories": sorted(scope1_cats, key=lambda x: x["total_tco2e"], reverse=True),
        },
        "scope2": {
            "total_tco2e": total_scope2,
            "categories": sorted(scope2_cats, key=lambda x: x["total_tco2e"], reverse=True),
        },
        "scope3": {
            "total_tco2e": total_scope3,
            "categories": sorted(scope3_cats, key=lambda x: x["total_tco2e"], reverse=True),
        },
        "total_tco2e": total_scope1 + total_scope2 + total_scope3,
        "period": {
            "start": period_start.isoformat() if period_start else None,
            "end": period_end.isoformat() if period_end else None,
        },
    }


def _build_scenario_analysis(
    db: Session,
    tenant_id: str,
    reporting_unit: Optional[ISSBReportingUnit],
    disclosure: ISSBDisclosureStatement,
) -> Dict[str, Any]:
    """Build scenario analysis results (1.5C, 2C, 3C pathways)."""
    if not reporting_unit:
        return {"scenarios": [], "summary": {}}

    # Get all scenarios for tenant
    scenarios = (
        db.query(ISSBScenario)
        .filter(
            ISSBScenario.tenant_id == tenant_id,
            ISSBScenario.is_active == True,
        )
        .all()
    )

    scenario_results = []

    for scenario in scenarios:
        # Get results for this scenario and reporting unit
        results = (
            db.query(ISSBScenarioResult)
            .filter(
                ISSBScenarioResult.tenant_id == tenant_id,
                ISSBScenarioResult.scenario_id == scenario.id,
                ISSBScenarioResult.reporting_unit_id == reporting_unit.id,
            )
            .all()
        )

        # Organize results by metric
        metrics_data = {}
        for result in results:
            metric_type = result.metric_type.value if result.metric_type else "unknown"
            if metric_type not in metrics_data:
                metrics_data[metric_type] = []
            metrics_data[metric_type].append({
                "projection_year": result.projection_year,
                "base_case_value": result.base_case_value,
                "scenario_value": result.scenario_value,
                "delta_value": result.delta_value,
                "delta_percentage": result.delta_percentage,
                "currency": result.currency,
                "carbon_price_used": result.carbon_price_used,
            })

        scenario_results.append({
            "scenario_id": scenario.id,
            "name": scenario.name,
            "temperature_pathway": scenario.temperature_pathway,
            "reference_source": scenario.reference_source,
            "carbon_price_path": scenario.carbon_price_path_json,
            "start_year": scenario.start_year,
            "end_year": scenario.end_year,
            "metrics": metrics_data,
            "is_default": scenario.is_default,
        })

    # Build summary comparing scenarios
    summary = {}
    pathways = set(s["temperature_pathway"] for s in scenario_results)
    for pathway in pathways:
        pathway_scenarios = [s for s in scenario_results if s["temperature_pathway"] == pathway]
        total_impact = 0.0
        for s in pathway_scenarios:
            for metric_results in s.get("metrics", {}).values():
                for r in metric_results:
                    if r.get("delta_value"):
                        total_impact += r["delta_value"]
        summary[pathway] = {
            "scenario_count": len(pathway_scenarios),
            "total_financial_impact": total_impact,
        }

    return {
        "scenarios": scenario_results,
        "summary": summary,
        "pathways_analyzed": list(pathways),
    }


def _build_materiality_assessment(
    db: Session,
    tenant_id: str,
    reporting_unit: Optional[ISSBReportingUnit],
    disclosure: ISSBDisclosureStatement,
) -> Dict[str, Any]:
    """Build double materiality assessment."""
    if not reporting_unit:
        return {
            "assessments": [],
            "is_climate_material": None,
            "summary": {},
        }

    # Get materiality assessments for the reporting unit
    assessments = (
        db.query(ISSBMaterialityAssessment)
        .filter(
            ISSBMaterialityAssessment.tenant_id == tenant_id,
            ISSBMaterialityAssessment.reporting_unit_id == reporting_unit.id,
        )
        .order_by(ISSBMaterialityAssessment.created_at.desc())
        .all()
    )

    assessment_data = []
    climate_materiality = None

    for assessment in assessments:
        topic = assessment.topic.value if assessment.topic else "unknown"
        data = {
            "id": assessment.id,
            "topic": topic,
            "impact_materiality_score": assessment.impact_materiality_score,
            "financial_materiality_score": assessment.financial_materiality_score,
            "is_material": assessment.material,
            "materiality_threshold": assessment.materiality_threshold,
            "justification": assessment.justification,
            "methodology": assessment.methodology_reference,
            "is_final": assessment.is_final,
            "period": {
                "start": assessment.period_start.isoformat() if assessment.period_start else None,
                "end": assessment.period_end.isoformat() if assessment.period_end else None,
            },
        }
        assessment_data.append(data)

        # Track climate materiality specifically
        if topic == "climate" and assessment.is_final:
            climate_materiality = assessment.material

    # Build summary
    material_topics = [a["topic"] for a in assessment_data if a.get("is_material")]
    avg_impact = sum(a.get("impact_materiality_score") or 0 for a in assessment_data) / len(assessment_data) if assessment_data else 0
    avg_financial = sum(a.get("financial_materiality_score") or 0 for a in assessment_data) / len(assessment_data) if assessment_data else 0

    return {
        "assessments": assessment_data,
        "is_climate_material": climate_materiality,
        "summary": {
            "total_topics_assessed": len(assessment_data),
            "material_topics": material_topics,
            "average_impact_score": round(avg_impact, 1),
            "average_financial_score": round(avg_financial, 1),
        },
    }


def _build_climate_risks(
    db: Session,
    tenant_id: str,
    reporting_unit: Optional[ISSBReportingUnit],
    disclosure: ISSBDisclosureStatement,
) -> Dict[str, Any]:
    """Build climate risk exposures by category."""
    if not reporting_unit:
        return {
            "physical_risks": [],
            "transition_risks": [],
            "summary": {},
        }

    # Get all active climate risks for the reporting unit
    risks = (
        db.query(ISSBClimateRiskExposure)
        .filter(
            ISSBClimateRiskExposure.tenant_id == tenant_id,
            ISSBClimateRiskExposure.reporting_unit_id == reporting_unit.id,
            ISSBClimateRiskExposure.is_active == True,
        )
        .all()
    )

    physical_risks = []
    transition_risks = []

    for risk in risks:
        risk_data = {
            "id": risk.id,
            "description": risk.description,
            "subtype": risk.subtype,
            "time_horizon": risk.time_horizon.value if risk.time_horizon else None,
            "financial_impact_type": risk.financial_impact_type.value if risk.financial_impact_type else None,
            "impact_range": {
                "low": risk.impact_range_low,
                "high": risk.impact_range_high,
                "currency": risk.currency,
            },
            "likelihood": risk.qualitative_likelihood.value if risk.qualitative_likelihood else None,
            "linked_scope": risk.linked_scope.value if risk.linked_scope else None,
            "mitigation_strategy": risk.mitigation_strategy,
            "is_mitigated": risk.is_mitigated,
        }

        if risk.risk_type == ISSBRiskType.PHYSICAL:
            physical_risks.append(risk_data)
        else:
            transition_risks.append(risk_data)

    # Build summary by time horizon
    by_horizon = {"short": 0, "medium": 0, "long": 0}
    total_low_impact = 0.0
    total_high_impact = 0.0

    for risk in risks:
        horizon = risk.time_horizon.value if risk.time_horizon else "unknown"
        if horizon in by_horizon:
            by_horizon[horizon] += 1
        if risk.impact_range_low:
            total_low_impact += risk.impact_range_low
        if risk.impact_range_high:
            total_high_impact += risk.impact_range_high

    return {
        "physical_risks": physical_risks,
        "transition_risks": transition_risks,
        "summary": {
            "total_risks": len(risks),
            "physical_risk_count": len(physical_risks),
            "transition_risk_count": len(transition_risks),
            "by_time_horizon": by_horizon,
            "total_impact_range": {
                "low": total_low_impact,
                "high": total_high_impact,
            },
            "mitigated_count": sum(1 for r in risks if r.is_mitigated),
        },
    }


def _build_targets_progress(
    db: Session,
    tenant_id: str,
    reporting_unit: Optional[ISSBReportingUnit],
) -> Dict[str, Any]:
    """Build targets and progress tracking."""
    if not reporting_unit:
        return {
            "targets": [],
            "summary": {},
        }

    # Get all targets for the reporting unit
    targets = (
        db.query(ISSBTarget)
        .filter(
            ISSBTarget.tenant_id == tenant_id,
            ISSBTarget.reporting_unit_id == reporting_unit.id,
            ISSBTarget.is_active == True,
        )
        .order_by(ISSBTarget.target_year)
        .all()
    )

    target_data = []
    for target in targets:
        # Calculate progress if we have current value
        progress = None
        if target.base_value and target.target_value and target.current_value is not None:
            total_change_needed = target.base_value - target.target_value
            if total_change_needed != 0:
                actual_change = target.base_value - target.current_value
                progress = (actual_change / total_change_needed) * 100

        target_data.append({
            "id": target.id,
            "name": target.name,
            "target_type": target.target_type.value if target.target_type else None,
            "scope": target.scope.value if target.scope else None,
            "base_year": target.base_year,
            "target_year": target.target_year,
            "base_value": target.base_value,
            "target_value": target.target_value,
            "current_value": target.current_value,
            "unit": target.unit,
            "status": target.status.value if target.status else None,
            "progress_percentage": target.progress_percentage or progress,
            "is_sbti_validated": target.is_sbti_validated,
            "validation_body": target.validation_body,
        })

    # Build summary
    on_track_count = sum(1 for t in targets if t.status == ISSBTargetStatus.ON_TRACK)
    achieved_count = sum(1 for t in targets if t.status == ISSBTargetStatus.ACHIEVED)
    sbti_count = sum(1 for t in targets if t.is_sbti_validated)

    return {
        "targets": target_data,
        "summary": {
            "total_targets": len(targets),
            "on_track": on_track_count,
            "achieved": achieved_count,
            "sbti_validated": sbti_count,
            "nearest_target_year": min((t.target_year for t in targets), default=None),
            "furthest_target_year": max((t.target_year for t in targets), default=None),
        },
    }


def _build_disclosure_sections(
    db: Session,
    tenant_id: str,
    reporting_unit: Optional[ISSBReportingUnit],
    disclosure: ISSBDisclosureStatement,
) -> Dict[str, Any]:
    """Build all disclosure sections (Governance, Strategy, Risk Management, Metrics & Targets)."""
    if not reporting_unit:
        return {}

    # Get all disclosure statements for this reporting unit and period
    statements = (
        db.query(ISSBDisclosureStatement)
        .filter(
            ISSBDisclosureStatement.tenant_id == tenant_id,
            ISSBDisclosureStatement.reporting_unit_id == reporting_unit.id,
            ISSBDisclosureStatement.period_start == disclosure.period_start,
            ISSBDisclosureStatement.period_end == disclosure.period_end,
        )
        .all()
    )

    sections = {}
    for stmt in statements:
        section_key = stmt.section.value if stmt.section else "unknown"
        sections[section_key] = {
            "id": stmt.id,
            "standard": stmt.standard.value if stmt.standard else None,
            "headline_summary": stmt.headline_summary,
            "body_markdown": stmt.body_markdown,
            "status": stmt.status.value if stmt.status else "draft",
            "approved_by": stmt.approved_by,
            "last_edited_by": stmt.last_edited_by,
            "last_edited_at": stmt.last_edited_at.isoformat() if stmt.last_edited_at else None,
        }

    return sections


# =============================================================================
# Export Functions
# =============================================================================

def export_issb_report_json(
    db: Session,
    tenant_id: str,
    disclosure_id: int,
) -> str:
    """
    Export ISSB disclosure report as JSON for investor portals.

    Returns JSON string formatted for external consumption.
    """
    report = generate_issb_disclosure(db, tenant_id, disclosure_id)

    # Format for investor portal (clean structure)
    export_data = {
        "meta": {
            "format": "ISSB_DISCLOSURE_V1",
            "generated_at": report["generated_at"],
            "standard": report["disclosure"].get("standard"),
        },
        "entity": report["reporting_unit"],
        "period": {
            "start": report["disclosure"].get("period_start"),
            "end": report["disclosure"].get("period_end"),
        },
        "emissions": report["emissions_summary"],
        "climate_scenarios": report["scenario_analysis"],
        "materiality": report["materiality"],
        "risks": report["climate_risks"],
        "targets": report["targets"],
    }

    return json.dumps(export_data, indent=2, default=str)


def generate_issb_pdf(
    db: Session,
    tenant_id: str,
    disclosure_id: int,
) -> bytes:
    """
    Generate ISSB disclosure report as PDF.

    Returns PDF as bytes.
    """
    from app.services.pdf_generator import PDFGenerator
    from xml.sax.saxutils import escape as xml_escape

    report = generate_issb_disclosure(db, tenant_id, disclosure_id)
    disclosure = report["disclosure"]
    unit = report["reporting_unit"]
    emissions = report["emissions_summary"]
    scenarios = report["scenario_analysis"]
    materiality = report["materiality"]
    risks = report["climate_risks"]
    targets = report["targets"]

    # Build emissions table rows
    emissions_rows = []
    for scope_key in ["scope1", "scope2", "scope3"]:
        scope_data = emissions.get(scope_key, {})
        scope_label = scope_key.upper().replace("SCOPE", "Scope ")
        emissions_rows.append(f"""
            <tr>
                <td><strong>{scope_label}</strong></td>
                <td class="numeric">{scope_data.get('total_tco2e', 0):,.2f}</td>
                <td>{len(scope_data.get('categories', []))} categories</td>
            </tr>
        """)

    # Build scenario rows
    scenario_rows = []
    for scenario in scenarios.get("scenarios", [])[:5]:
        pathway = scenario.get("temperature_pathway", "N/A")
        name = xml_escape(scenario.get("name", "Unnamed"))
        metrics_count = sum(len(v) for v in scenario.get("metrics", {}).values())
        scenario_rows.append(f"""
            <tr>
                <td>{name}</td>
                <td>{pathway}</td>
                <td class="numeric">{metrics_count}</td>
            </tr>
        """)

    # Build risks summary
    risks_summary = risks.get("summary", {})
    physical_count = risks_summary.get("physical_risk_count", 0)
    transition_count = risks_summary.get("transition_risk_count", 0)

    # Build targets rows
    target_rows = []
    for target in targets.get("targets", [])[:10]:
        status_class = f"status-{target.get('status', 'unknown')}"
        target_rows.append(f"""
            <tr class="{status_class}">
                <td>{xml_escape(target.get('name', 'N/A'))}</td>
                <td>{target.get('target_type', 'N/A')}</td>
                <td class="numeric">{target.get('target_year', 'N/A')}</td>
                <td class="numeric">{target.get('progress_percentage', 0) or 0:.1f}%</td>
                <td>{target.get('status', 'N/A')}</td>
            </tr>
        """)

    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>ISSB Disclosure Report - {xml_escape(unit.get('name', 'N/A'))}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; }}
        h1 {{ color: #1e3a5f; border-bottom: 2px solid #3b82f6; padding-bottom: 0.5rem; }}
        h2 {{ color: #1e3a5f; margin-top: 2rem; }}
        h3 {{ color: #475569; margin-top: 1.5rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #1e3a5f; color: white; }}
        .numeric {{ text-align: right; font-family: monospace; }}
        .summary-box {{ background-color: #eff6ff; border: 1px solid #93c5fd; padding: 1rem; margin: 1rem 0; border-radius: 4px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin: 1rem 0; }}
        .metric-card {{ background: #f8fafc; border: 1px solid #e2e8f0; padding: 1rem; border-radius: 4px; text-align: center; }}
        .metric-value {{ font-size: 1.5rem; font-weight: bold; color: #1e3a5f; }}
        .metric-label {{ color: #64748b; font-size: 0.875rem; }}
        .status-on_track {{ background-color: #d1fae5; }}
        .status-achieved {{ background-color: #bbf7d0; }}
        .status-off_track {{ background-color: #fee2e2; }}
        .status-in_progress {{ background-color: #fef3c7; }}
        .risk-badge {{ display: inline-block; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; }}
        .risk-physical {{ background-color: #fef3c7; color: #92400e; }}
        .risk-transition {{ background-color: #e0e7ff; color: #3730a3; }}
        .metadata {{ color: #718096; font-size: 0.875rem; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }}
    </style>
</head>
<body>
    <h1>ISSB Climate Disclosure Report</h1>
    <p style="color: #64748b;">IFRS S1/S2 Sustainability and Climate-Related Disclosures</p>

    <section class="summary-box">
        <p><strong>Entity:</strong> {xml_escape(unit.get('name', 'N/A'))}</p>
        <p><strong>Sector:</strong> {xml_escape(unit.get('sector', 'N/A') or 'Not specified')}</p>
        <p><strong>Standard:</strong> {disclosure.get('standard', 'IFRS_S2')}</p>
        <p><strong>Reporting Period:</strong> {disclosure.get('period_start', 'N/A')} to {disclosure.get('period_end', 'N/A')}</p>
        <p><strong>Status:</strong> {disclosure.get('status', 'draft').upper()}</p>
    </section>

    <h2>GHG Emissions Summary</h2>
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{emissions.get('scope1', {}).get('total_tco2e', 0):,.0f}</div>
            <div class="metric-label">Scope 1 (tCO2e)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{emissions.get('scope2', {}).get('total_tco2e', 0):,.0f}</div>
            <div class="metric-label">Scope 2 (tCO2e)</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{emissions.get('scope3', {}).get('total_tco2e', 0):,.0f}</div>
            <div class="metric-label">Scope 3 (tCO2e)</div>
        </div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Scope</th>
                <th class="numeric">Emissions (tCO2e)</th>
                <th>Categories</th>
            </tr>
        </thead>
        <tbody>
            {''.join(emissions_rows)}
            <tr style="font-weight: bold; background-color: #f1f5f9;">
                <td>Total</td>
                <td class="numeric">{emissions.get('total_tco2e', 0):,.2f}</td>
                <td>-</td>
            </tr>
        </tbody>
    </table>

    <h2>Climate Scenario Analysis</h2>
    <p>Scenarios analyzed: {', '.join(scenarios.get('pathways_analyzed', ['None']))}</p>
    <table>
        <thead>
            <tr>
                <th>Scenario</th>
                <th>Temperature Pathway</th>
                <th class="numeric">Metrics Computed</th>
            </tr>
        </thead>
        <tbody>
            {''.join(scenario_rows) if scenario_rows else '<tr><td colspan="3">No scenarios analyzed</td></tr>'}
        </tbody>
    </table>

    <h2>Double Materiality Assessment</h2>
    <p><strong>Climate Material:</strong> {'Yes' if materiality.get('is_climate_material') else 'No' if materiality.get('is_climate_material') is False else 'Not assessed'}</p>
    <p><strong>Topics Assessed:</strong> {materiality.get('summary', {}).get('total_topics_assessed', 0)}</p>
    <p><strong>Material Topics:</strong> {', '.join(materiality.get('summary', {}).get('material_topics', [])) or 'None identified'}</p>
    <p><strong>Average Impact Score:</strong> {materiality.get('summary', {}).get('average_impact_score', 0)}</p>
    <p><strong>Average Financial Score:</strong> {materiality.get('summary', {}).get('average_financial_score', 0)}</p>

    <h2>Climate Risk Exposures</h2>
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value">{physical_count}</div>
            <div class="metric-label">Physical Risks</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{transition_count}</div>
            <div class="metric-label">Transition Risks</div>
        </div>
        <div class="metric-card">
            <div class="metric-value">{risks_summary.get('mitigated_count', 0)}</div>
            <div class="metric-label">Mitigated</div>
        </div>
    </div>
    <p><strong>By Time Horizon:</strong></p>
    <ul>
        <li>Short-term (0-2 years): {risks_summary.get('by_time_horizon', {}).get('short', 0)}</li>
        <li>Medium-term (2-5 years): {risks_summary.get('by_time_horizon', {}).get('medium', 0)}</li>
        <li>Long-term (5+ years): {risks_summary.get('by_time_horizon', {}).get('long', 0)}</li>
    </ul>

    <h2>Climate Targets</h2>
    <p><strong>Total Targets:</strong> {targets.get('summary', {}).get('total_targets', 0)} |
       <strong>On Track:</strong> {targets.get('summary', {}).get('on_track', 0)} |
       <strong>Achieved:</strong> {targets.get('summary', {}).get('achieved', 0)} |
       <strong>SBTi Validated:</strong> {targets.get('summary', {}).get('sbti_validated', 0)}</p>
    <table>
        <thead>
            <tr>
                <th>Target</th>
                <th>Type</th>
                <th class="numeric">Year</th>
                <th class="numeric">Progress</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {''.join(target_rows) if target_rows else '<tr><td colspan="5">No targets defined</td></tr>'}
        </tbody>
    </table>

    <footer class="metadata">
        <p>Generated by FactorTrace on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p>This document is prepared in accordance with IFRS S1 and IFRS S2 sustainability disclosure standards.</p>
        <p>Disclosure ID: {disclosure.get('id', 'N/A')}</p>
    </footer>
</body>
</html>"""

    generator = PDFGenerator(
        company_name=unit.get("name", "FactorTrace"),
        include_page_numbers=True,
    )

    return generator.generate_pdf(xhtml, title=f"ISSB Disclosure - {unit.get('name', 'Report')}")
