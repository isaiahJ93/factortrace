# app/services/eudr_report.py
"""
EUDR Due Diligence Report Generation Service
=============================================
Generates comprehensive EUDR due diligence reports with:
- Commodity breakdown and volumes
- Supply chain summary and visualization data
- Risk scores by site (georisk snapshots)
- Export to PDF and CSV formats
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from io import BytesIO, StringIO
import csv
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.eudr import (
    EUDRDueDiligence,
    EUDRDueDiligenceBatchLink,
    EUDRBatch,
    EUDRSupplySite,
    EUDRGeoRiskSnapshot,
    EUDROperator,
    EUDRCommodity,
    EUDRSupplyChainLink,
    EUDRRiskLevel,
)

logger = logging.getLogger(__name__)


class EUDRReportError(Exception):
    """Raised when EUDR report generation fails."""
    pass


def generate_eudr_due_diligence_report(
    db: Session,
    tenant_id: str,
    due_diligence_id: int,
) -> Dict[str, Any]:
    """
    Generate a comprehensive EUDR due diligence report.

    Args:
        db: Database session
        tenant_id: Current tenant ID (for multi-tenant isolation)
        due_diligence_id: ID of the due diligence statement

    Returns:
        Dict with full report data including:
        - due_diligence: Basic DD info
        - commodity_breakdown: Volumes by commodity
        - supply_chain_summary: Operators and sites overview
        - risk_by_site: Georisk scores per site
        - supply_chain_graph: Nodes and edges for visualization

    Raises:
        EUDRReportError: If due diligence not found or generation fails
    """
    # Fetch due diligence with tenant isolation
    dd = (
        db.query(EUDRDueDiligence)
        .filter(
            EUDRDueDiligence.id == due_diligence_id,
            EUDRDueDiligence.tenant_id == tenant_id,
        )
        .first()
    )

    if not dd:
        raise EUDRReportError(f"Due diligence {due_diligence_id} not found")

    try:
        # Build report sections
        report = {
            "report_type": "EUDR_DUE_DILIGENCE",
            "generated_at": datetime.utcnow().isoformat(),
            "due_diligence": _build_dd_summary(dd),
            "commodity_breakdown": _build_commodity_breakdown(db, tenant_id, dd),
            "supply_chain_summary": _build_supply_chain_summary(db, tenant_id, dd),
            "risk_by_site": _build_risk_by_site(db, tenant_id, dd),
            "supply_chain_graph": _build_supply_chain_graph(db, tenant_id, dd),
            "compliance_checklist": _build_compliance_checklist(dd),
        }

        return report

    except Exception as e:
        logger.error(f"EUDR report generation failed: {e}")
        raise EUDRReportError(f"Report generation failed: {e}")


def _build_dd_summary(dd: EUDRDueDiligence) -> Dict[str, Any]:
    """Build basic due diligence summary."""
    return {
        "id": dd.id,
        "reference": dd.reference,
        "status": dd.status.value if dd.status else "draft",
        "period_start": dd.period_start.isoformat() if dd.period_start else None,
        "period_end": dd.period_end.isoformat() if dd.period_end else None,
        "overall_risk_level": dd.overall_risk_level.value if dd.overall_risk_level else None,
        "overall_risk_score": dd.overall_risk_score,
        "total_volume": dd.total_volume,
        "total_volume_unit": dd.total_volume_unit,
        "batch_count": dd.batch_count,
        "justification_summary": dd.justification_summary,
        "operator": {
            "id": dd.operator.id,
            "name": dd.operator.name,
            "role": dd.operator.role.value,
            "country": dd.operator.country,
        } if dd.operator else None,
        "commodity": {
            "id": dd.commodity.id,
            "name": dd.commodity.name,
            "type": dd.commodity.commodity_type.value,
        } if dd.commodity else None,
    }


def _build_commodity_breakdown(
    db: Session,
    tenant_id: str,
    dd: EUDRDueDiligence,
) -> Dict[str, Any]:
    """Build commodity volume breakdown."""
    # Get batch links with volumes
    batch_links = (
        db.query(EUDRDueDiligenceBatchLink)
        .filter(EUDRDueDiligenceBatchLink.due_diligence_id == dd.id)
        .all()
    )

    # Aggregate by origin country
    by_country = {}
    by_harvest_year = {}
    total_volume = 0.0

    for link in batch_links:
        batch = link.batch
        if not batch:
            continue

        volume = link.included_volume or batch.volume
        total_volume += volume

        # By country
        country = batch.origin_country or "Unknown"
        if country not in by_country:
            by_country[country] = {"volume": 0.0, "batch_count": 0}
        by_country[country]["volume"] += volume
        by_country[country]["batch_count"] += 1

        # By harvest year
        year = str(batch.harvest_year) if batch.harvest_year else "Unknown"
        if year not in by_harvest_year:
            by_harvest_year[year] = {"volume": 0.0, "batch_count": 0}
        by_harvest_year[year]["volume"] += volume
        by_harvest_year[year]["batch_count"] += 1

    return {
        "commodity_name": dd.commodity.name if dd.commodity else "Unknown",
        "commodity_type": dd.commodity.commodity_type.value if dd.commodity else None,
        "total_volume": total_volume,
        "volume_unit": dd.total_volume_unit or "tonne",
        "by_country": [
            {"country": k, **v}
            for k, v in sorted(by_country.items(), key=lambda x: x[1]["volume"], reverse=True)
        ],
        "by_harvest_year": [
            {"year": k, **v}
            for k, v in sorted(by_harvest_year.items())
        ],
    }


def _build_supply_chain_summary(
    db: Session,
    tenant_id: str,
    dd: EUDRDueDiligence,
) -> Dict[str, Any]:
    """Build supply chain operator and site summary."""
    # Get all batches in this DD
    batch_ids = (
        db.query(EUDRDueDiligenceBatchLink.batch_id)
        .filter(EUDRDueDiligenceBatchLink.due_diligence_id == dd.id)
        .subquery()
    )

    # Get unique supply sites from batches
    sites = (
        db.query(EUDRSupplySite)
        .join(EUDRBatch, EUDRBatch.origin_site_id == EUDRSupplySite.id)
        .filter(
            EUDRBatch.id.in_(batch_ids),
            EUDRSupplySite.tenant_id == tenant_id,
        )
        .distinct()
        .all()
    )

    # Get unique operators from sites
    operator_ids = set(site.operator_id for site in sites if site.operator_id)
    operators = (
        db.query(EUDROperator)
        .filter(
            EUDROperator.id.in_(operator_ids),
            EUDROperator.tenant_id == tenant_id,
        )
        .all()
    )

    # Aggregate by country
    sites_by_country = {}
    for site in sites:
        country = site.country or "Unknown"
        if country not in sites_by_country:
            sites_by_country[country] = 0
        sites_by_country[country] += 1

    return {
        "total_sites": len(sites),
        "total_operators": len(operators),
        "sites_by_country": sites_by_country,
        "sites_with_coordinates": sum(1 for s in sites if s.has_coordinates),
        "sites_with_polygon": sum(1 for s in sites if s.has_polygon),
        "operators": [
            {
                "id": op.id,
                "name": op.name,
                "role": op.role.value,
                "country": op.country,
            }
            for op in operators
        ],
        "sites": [
            {
                "id": site.id,
                "name": site.name,
                "country": site.country,
                "region": site.region,
                "latitude": site.latitude,
                "longitude": site.longitude,
                "area_ha": site.area_ha,
                "has_coordinates": site.has_coordinates,
            }
            for site in sites[:50]  # Limit to first 50
        ],
    }


def _build_risk_by_site(
    db: Session,
    tenant_id: str,
    dd: EUDRDueDiligence,
) -> Dict[str, Any]:
    """Build georisk assessment summary by site."""
    # Get all batches in this DD
    batch_ids = (
        db.query(EUDRDueDiligenceBatchLink.batch_id)
        .filter(EUDRDueDiligenceBatchLink.due_diligence_id == dd.id)
        .subquery()
    )

    # Get site IDs from batches
    site_ids = (
        db.query(EUDRBatch.origin_site_id)
        .filter(
            EUDRBatch.id.in_(batch_ids),
            EUDRBatch.origin_site_id.isnot(None),
        )
        .distinct()
        .all()
    )
    site_ids = [s[0] for s in site_ids]

    if not site_ids:
        return {
            "total_assessed": 0,
            "risk_distribution": {},
            "deforestation_flags": 0,
            "protected_area_overlaps": 0,
            "sites": [],
        }

    # Get latest georisk snapshot for each site
    # Subquery for max snapshot date per site
    latest_snapshot = (
        db.query(
            EUDRGeoRiskSnapshot.supply_site_id,
            func.max(EUDRGeoRiskSnapshot.snapshot_date).label("max_date"),
        )
        .filter(
            EUDRGeoRiskSnapshot.tenant_id == tenant_id,
            EUDRGeoRiskSnapshot.supply_site_id.in_(site_ids),
        )
        .group_by(EUDRGeoRiskSnapshot.supply_site_id)
        .subquery()
    )

    snapshots = (
        db.query(EUDRGeoRiskSnapshot)
        .join(
            latest_snapshot,
            (EUDRGeoRiskSnapshot.supply_site_id == latest_snapshot.c.supply_site_id) &
            (EUDRGeoRiskSnapshot.snapshot_date == latest_snapshot.c.max_date),
        )
        .filter(EUDRGeoRiskSnapshot.tenant_id == tenant_id)
        .all()
    )

    # Aggregate risk distribution
    risk_dist = {"low": 0, "medium": 0, "high": 0, "unassessed": 0}
    deforestation_count = 0
    protected_count = 0

    site_risks = []
    for snap in snapshots:
        site = snap.supply_site
        level = snap.risk_level.value if snap.risk_level else "unassessed"
        risk_dist[level] = risk_dist.get(level, 0) + 1

        if snap.deforestation_flag:
            deforestation_count += 1
        if snap.protected_area_overlap:
            protected_count += 1

        site_risks.append({
            "site_id": snap.supply_site_id,
            "site_name": site.name if site else "Unknown",
            "country": site.country if site else None,
            "risk_level": level,
            "risk_score": snap.risk_score_raw,
            "deforestation_flag": snap.deforestation_flag,
            "tree_cover_loss_ha": snap.tree_cover_loss_ha,
            "protected_area_overlap": snap.protected_area_overlap,
            "snapshot_date": snap.snapshot_date.isoformat() if snap.snapshot_date else None,
            "source": snap.source.value if snap.source else None,
        })

    # Add unassessed sites
    assessed_site_ids = set(s.supply_site_id for s in snapshots)
    unassessed_count = len(site_ids) - len(assessed_site_ids)
    risk_dist["unassessed"] = unassessed_count

    return {
        "total_sites": len(site_ids),
        "total_assessed": len(snapshots),
        "risk_distribution": risk_dist,
        "deforestation_flags": deforestation_count,
        "protected_area_overlaps": protected_count,
        "average_risk_score": (
            sum(s.risk_score_raw or 0 for s in snapshots) / len(snapshots)
            if snapshots else None
        ),
        "sites": sorted(site_risks, key=lambda x: x.get("risk_score") or 0, reverse=True),
    }


def _build_supply_chain_graph(
    db: Session,
    tenant_id: str,
    dd: EUDRDueDiligence,
) -> Dict[str, Any]:
    """Build supply chain graph data for visualization."""
    # Get all batches in this DD
    batch_links = (
        db.query(EUDRDueDiligenceBatchLink)
        .filter(EUDRDueDiligenceBatchLink.due_diligence_id == dd.id)
        .all()
    )
    batch_ids = [bl.batch_id for bl in batch_links]

    if not batch_ids:
        return {"nodes": [], "edges": []}

    # Get supply chain links involving these batches
    links = (
        db.query(EUDRSupplyChainLink)
        .filter(
            EUDRSupplyChainLink.tenant_id == tenant_id,
            (
                EUDRSupplyChainLink.from_batch_id.in_(batch_ids) |
                EUDRSupplyChainLink.to_batch_id.in_(batch_ids)
            ),
        )
        .all()
    )

    # Build nodes (operators and batches)
    nodes = []
    node_ids = set()

    # Add operator nodes
    operator_ids = set()
    for link in links:
        operator_ids.add(link.from_operator_id)
        operator_ids.add(link.to_operator_id)

    operators = (
        db.query(EUDROperator)
        .filter(
            EUDROperator.id.in_(operator_ids),
            EUDROperator.tenant_id == tenant_id,
        )
        .all()
    )

    for op in operators:
        node_id = f"operator_{op.id}"
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                "id": node_id,
                "type": "operator",
                "label": op.name,
                "role": op.role.value,
                "country": op.country,
            })

    # Add batch nodes
    batches = (
        db.query(EUDRBatch)
        .filter(
            EUDRBatch.tenant_id == tenant_id,
            EUDRBatch.id.in_(batch_ids),
        )
        .all()
    )

    for batch in batches:
        node_id = f"batch_{batch.id}"
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                "id": node_id,
                "type": "batch",
                "label": batch.batch_reference,
                "volume": batch.volume,
                "unit": batch.volume_unit,
                "origin_country": batch.origin_country,
            })

    # Build edges
    edges = []
    for link in links:
        edges.append({
            "id": f"link_{link.id}",
            "source": f"operator_{link.from_operator_id}",
            "target": f"operator_{link.to_operator_id}",
            "link_type": link.link_type.value if link.link_type else None,
            "from_batch": f"batch_{link.from_batch_id}" if link.from_batch_id else None,
            "to_batch": f"batch_{link.to_batch_id}" if link.to_batch_id else None,
        })

    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def _build_compliance_checklist(dd: EUDRDueDiligence) -> List[Dict[str, Any]]:
    """Build EUDR compliance checklist."""
    checks = [
        {
            "requirement": "Commodity identification",
            "status": "complete" if dd.commodity_id else "incomplete",
            "description": "Commodity type identified per EUDR Annex I",
        },
        {
            "requirement": "Geographic traceability",
            "status": "complete" if dd.batch_count and dd.batch_count > 0 else "incomplete",
            "description": "Plot of land coordinates or polygons collected",
        },
        {
            "requirement": "Deforestation-free verification",
            "status": "complete" if dd.overall_risk_level else "incomplete",
            "description": "Verified no deforestation after 31 Dec 2020 cutoff",
        },
        {
            "requirement": "Legal compliance",
            "status": "review_required",
            "description": "Compliance with country of production laws verified",
        },
        {
            "requirement": "Risk assessment",
            "status": "complete" if dd.overall_risk_score is not None else "incomplete",
            "description": "Risk assessment conducted and documented",
        },
        {
            "requirement": "Risk mitigation",
            "status": "complete" if dd.justification_summary else "incomplete",
            "description": "Mitigation measures for identified risks",
        },
    ]
    return checks


# =============================================================================
# Export Functions
# =============================================================================

def export_eudr_report_csv(
    db: Session,
    tenant_id: str,
    due_diligence_id: int,
) -> str:
    """
    Export EUDR due diligence report as CSV.

    Returns CSV content as string.
    """
    report = generate_eudr_due_diligence_report(db, tenant_id, due_diligence_id)

    output = StringIO()
    writer = csv.writer(output)

    # Header info
    dd = report["due_diligence"]
    writer.writerow(["EUDR Due Diligence Report"])
    writer.writerow(["Reference", dd.get("reference", "")])
    writer.writerow(["Status", dd.get("status", "")])
    writer.writerow(["Period", f"{dd.get('period_start', '')} to {dd.get('period_end', '')}"])
    writer.writerow(["Overall Risk Level", dd.get("overall_risk_level", "")])
    writer.writerow(["Total Volume", f"{dd.get('total_volume', 0)} {dd.get('total_volume_unit', 'tonne')}"])
    writer.writerow([])

    # Commodity breakdown by country
    writer.writerow(["Commodity Breakdown by Country"])
    writer.writerow(["Country", "Volume", "Batch Count"])
    for item in report["commodity_breakdown"].get("by_country", []):
        writer.writerow([item["country"], item["volume"], item["batch_count"]])
    writer.writerow([])

    # Risk by site
    writer.writerow(["Risk Assessment by Site"])
    writer.writerow([
        "Site Name", "Country", "Risk Level", "Risk Score",
        "Deforestation Flag", "Tree Cover Loss (ha)", "Protected Area Overlap"
    ])
    for site in report["risk_by_site"].get("sites", []):
        writer.writerow([
            site.get("site_name", ""),
            site.get("country", ""),
            site.get("risk_level", ""),
            site.get("risk_score", ""),
            "Yes" if site.get("deforestation_flag") else "No",
            site.get("tree_cover_loss_ha", ""),
            "Yes" if site.get("protected_area_overlap") else "No",
        ])

    return output.getvalue()


def generate_eudr_pdf(
    db: Session,
    tenant_id: str,
    due_diligence_id: int,
) -> bytes:
    """
    Generate EUDR due diligence report as PDF.

    Returns PDF as bytes.
    """
    from app.services.pdf_generator import PDFGenerator
    from xml.sax.saxutils import escape as xml_escape

    report = generate_eudr_due_diligence_report(db, tenant_id, due_diligence_id)
    dd = report["due_diligence"]

    # Build XHTML for PDF conversion
    risk_rows = []
    for site in report["risk_by_site"].get("sites", [])[:20]:  # Limit to 20
        risk_class = f"risk-{site.get('risk_level', 'unknown')}"
        risk_rows.append(f"""
            <tr class="{risk_class}">
                <td>{xml_escape(str(site.get('site_name', '')))}</td>
                <td>{xml_escape(str(site.get('country', '')))}</td>
                <td>{site.get('risk_level', 'N/A')}</td>
                <td class="numeric">{site.get('risk_score', 'N/A')}</td>
                <td>{'Yes' if site.get('deforestation_flag') else 'No'}</td>
            </tr>
        """)

    country_rows = []
    for item in report["commodity_breakdown"].get("by_country", []):
        country_rows.append(f"""
            <tr>
                <td>{xml_escape(item['country'])}</td>
                <td class="numeric">{item['volume']:,.2f}</td>
                <td class="numeric">{item['batch_count']}</td>
            </tr>
        """)

    xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>EUDR Due Diligence Report - {xml_escape(dd.get('reference', 'N/A'))}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 2rem; }}
        h1 {{ color: #1a5f2a; border-bottom: 2px solid #2d8a3e; padding-bottom: 0.5rem; }}
        h2 {{ color: #1a5f2a; margin-top: 2rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid #e2e8f0; padding: 0.75rem; text-align: left; }}
        th {{ background-color: #1a5f2a; color: white; }}
        .numeric {{ text-align: right; font-family: monospace; }}
        .risk-low {{ background-color: #d4edda; }}
        .risk-medium {{ background-color: #fff3cd; }}
        .risk-high {{ background-color: #f8d7da; }}
        .summary-box {{ background-color: #f0fdf4; border: 1px solid #86efac; padding: 1rem; margin: 1rem 0; border-radius: 4px; }}
        .metadata {{ color: #718096; font-size: 0.875rem; margin-top: 2rem; }}
    </style>
</head>
<body>
    <h1>EUDR Due Diligence Report</h1>

    <section class="summary-box">
        <p><strong>Reference:</strong> {xml_escape(dd.get('reference', 'N/A'))}</p>
        <p><strong>Status:</strong> {dd.get('status', 'N/A').upper()}</p>
        <p><strong>Period:</strong> {dd.get('period_start', 'N/A')} to {dd.get('period_end', 'N/A')}</p>
        <p><strong>Overall Risk Level:</strong> {dd.get('overall_risk_level', 'N/A')}</p>
        <p><strong>Total Volume:</strong> {dd.get('total_volume', 0):,.2f} {dd.get('total_volume_unit', 'tonne')}</p>
        <p><strong>Batch Count:</strong> {dd.get('batch_count', 0)}</p>
    </section>

    <h2>Commodity Breakdown by Country</h2>
    <table>
        <thead>
            <tr>
                <th>Country</th>
                <th class="numeric">Volume ({dd.get('total_volume_unit', 'tonne')})</th>
                <th class="numeric">Batches</th>
            </tr>
        </thead>
        <tbody>
            {''.join(country_rows) if country_rows else '<tr><td colspan="3">No data</td></tr>'}
        </tbody>
    </table>

    <h2>Risk Assessment by Site</h2>
    <p><strong>Sites Assessed:</strong> {report['risk_by_site'].get('total_assessed', 0)} / {report['risk_by_site'].get('total_sites', 0)}</p>
    <p><strong>Deforestation Flags:</strong> {report['risk_by_site'].get('deforestation_flags', 0)}</p>
    <p><strong>Protected Area Overlaps:</strong> {report['risk_by_site'].get('protected_area_overlaps', 0)}</p>
    <table>
        <thead>
            <tr>
                <th>Site</th>
                <th>Country</th>
                <th>Risk Level</th>
                <th class="numeric">Score</th>
                <th>Deforestation</th>
            </tr>
        </thead>
        <tbody>
            {''.join(risk_rows) if risk_rows else '<tr><td colspan="5">No site data</td></tr>'}
        </tbody>
    </table>

    <h2>Supply Chain Summary</h2>
    <p><strong>Total Sites:</strong> {report['supply_chain_summary'].get('total_sites', 0)}</p>
    <p><strong>Total Operators:</strong> {report['supply_chain_summary'].get('total_operators', 0)}</p>
    <p><strong>Sites with Coordinates:</strong> {report['supply_chain_summary'].get('sites_with_coordinates', 0)}</p>

    <footer class="metadata">
        <p>Generated by FactorTrace on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        <p>This document is for EUDR due diligence purposes under EU Regulation 2023/1115.</p>
    </footer>
</body>
</html>"""

    generator = PDFGenerator(
        company_name=dd.get("operator", {}).get("name", "FactorTrace"),
        include_page_numbers=True,
    )

    return generator.generate_pdf(xhtml, title=f"EUDR Due Diligence - {dd.get('reference', 'Report')}")
