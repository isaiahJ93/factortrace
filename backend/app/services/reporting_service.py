"""
Reporting Service for GHG Protocol Scope 3 Calculator
Generates compliance reports (CDP, TCFD, CSRD)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
import json
import io
import logging

import boto3
from jinja2 import Template
import xlsxwriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

from app.models.ghg_protocol_models import (
    Organization, Scope3Category, Scope3Inventory
)
from app.repositories import (
    CalculationResultRepository, OrganizationRepository
)

logger = logging.getLogger(__name__)


class ReportingService:
    """Service for generating compliance reports"""
    
    def __init__(
        self,
        calc_repo: CalculationResultRepository,
        org_repo: OrganizationRepository,
        s3_client: boto3.client
    ):
        self.calc_repo = calc_repo
        self.org_repo = org_repo
        self.s3_client = s3_client
        self.report_templates = self._load_templates()
        
    async def generate_report(
        self,
        organization_id: UUID,
        report_type: str,
        year: int,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        
        # Get organization and inventory
        organization = await self.org_repo.get(organization_id)
        inventory = await self._get_inventory(organization_id, year)
        
        if not inventory:
            raise ValueError(f"No inventory data for year {year}")
            
        # Generate report based on type
        if report_type == "CDP":
            report_data = await self._generate_cdp_report(organization, inventory, options)
        elif report_type == "TCFD":
            report_data = await self._generate_tcfd_report(organization, inventory, options)
        elif report_type == "CSRD":
            report_data = await self._generate_csrd_report(organization, inventory, options)
        else:
            raise ValueError(f"Unsupported report type: {report_type}")
            
        # Save to S3
        report_id = uuid4()
        file_key = f"reports/{organization_id}/{report_id}.{report_data['format']}"
        
        await self._save_to_s3(report_data["content"], file_key)
        
        return {
            "id": report_id,
            "report_type": report_type,
            "file_key": file_key,
            "expires_at": datetime.utcnow() + timedelta(days=30)
        }
        
    async def get_report(
        self,
        report_id: UUID,
        organization_id: UUID,
        format: str
    ) -> Optional[bytes]:
        """Retrieve report content"""
        # Implementation would fetch from S3
        pass
        
    async def _generate_cdp_report(
        self,
        organization: Organization,
        inventory: Scope3Inventory,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate CDP Climate Change report"""
        
        # Create PDF document
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph(
            f"CDP Climate Change 2024 - {organization.name}",
            styles['Title']
        ))
        
        # C6.5 Scope 3 Emissions Data
        story.append(Paragraph("C6.5 Account for your organization's gross global Scope 3 emissions", styles['Heading2']))
        
        # Create emissions table
        data = [["Scope 3 Category", "Metric tons CO2e", "Evaluation Status"]]
        
        for category in Scope3Category:
            if category in inventory.category_results:
                result = inventory.category_results[category]
                emissions_mt = float(result.emissions.value) / 1000  # Convert kg to metric tons
                data.append([
                    category.value.replace("_", " ").title(),
                    f"{emissions_mt:,.2f}",
                    "Relevant, calculated"
                ])
            else:
                data.append([
                    category.value.replace("_", " ").title(),
                    "0",
                    "Not relevant, explanation provided"
                ])
                
        # Add total
        total_mt = float(inventory.total_emissions.value) / 1000
        data.append(["Total Scope 3", f"{total_mt:,.2f}", ""])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return {
            "content": buffer.getvalue(),
            "format": "pdf",
            "filename": f"CDP_Climate_{organization.name}_{inventory.reporting_year}.pdf"
        }
        
    async def _generate_tcfd_report(
        self,
        organization: Organization,
        inventory: Scope3Inventory,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate TCFD-aligned report"""
        
        # Create Excel report for TCFD metrics
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        # Metrics & Targets worksheet
        metrics_sheet = workbook.add_worksheet("Metrics & Targets")
        
        # Formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        number_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        
        # Headers
        headers = ["GHG Emissions", "Value (tCO2e)", "% of Total", "Data Quality Score"]
        for col, header in enumerate(headers):
            metrics_sheet.write(0, col, header, header_format)
            
        # Data
        row = 1
        for category, result in inventory.category_results.items():
            emissions_t = float(result.emissions.value) / 1000
            percentage = (emissions_t / (float(inventory.total_emissions.value) / 1000)) * 100
            
            metrics_sheet.write(row, 0, category.value.replace("_", " ").title())
            metrics_sheet.write(row, 1, emissions_t, number_format)
            metrics_sheet.write(row, 2, f"{percentage:.1f}%")
            metrics_sheet.write(row, 3, result.data_quality_score)
            row += 1
            
        # Total
        total_t = float(inventory.total_emissions.value) / 1000
        metrics_sheet.write(row, 0, "Total Scope 3", header_format)
        metrics_sheet.write(row, 1, total_t, number_format)
        
        # Risk Assessment worksheet
        risk_sheet = workbook.add_worksheet("Climate Risks")
        risk_sheet.write(0, 0, "Transition Risks from Scope 3", header_format)
        
        # Add risk analysis based on categories
        risks = self._analyze_transition_risks(inventory)
        row = 2
        for risk in risks:
            risk_sheet.write(row, 0, risk["category"])
            risk_sheet.write(row, 1, risk["risk_level"])
            risk_sheet.write(row, 2, risk["description"])
            row += 1
            
        workbook.close()
        output.seek(0)
        
        return {
            "content": output.getvalue(),
            "format": "xlsx",
            "filename": f"TCFD_Metrics_{organization.name}_{inventory.reporting_year}.xlsx"
        }
        
    async def _generate_csrd_report(
        self,
        organization: Organization,
        inventory: Scope3Inventory,
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate CSRD/ESRS E1 compliant report"""
        
        # JSON format for XBRL tagging
        esrs_data = {
            "reportingEntity": {
                "name": organization.name,
                "lei": organization.metadata.get("lei"),  # Legal Entity Identifier
                "reportingPeriod": inventory.reporting_year
            },
            "e1_climateChange": {
                "ghgEmissions": {
                    "scope3": {
                        "total": {
                            "value": float(inventory.total_emissions.value),
                            "unit": "kgCO2e",
                            "uncertainty": {
                                "lower": float(inventory.total_emissions.uncertainty_lower) if inventory.total_emissions.uncertainty_lower else None,
                                "upper": float(inventory.total_emissions.uncertainty_upper) if inventory.total_emissions.uncertainty_upper else None
                            }
                        },
                        "categories": {}
                    }
                },
                "dataQuality": {
                    "scope3AverageScore": inventory.average_data_quality,
                    "methodology": "GHG Protocol Corporate Value Chain Standard",
                    "assurance": {
                        "level": "limited" if inventory.third_party_verified else "none",
                        "provider": inventory.verification_statement
                    }
                }
            }
        }
        
        # Add category details
        for category, result in inventory.category_results.items():
            esrs_data["e1_climateChange"]["ghgEmissions"]["scope3"]["categories"][category.value] = {
                "value": float(result.emissions.value),
                "unit": "kgCO2e",
                "calculationMethod": result.methodology.value,
                "dataQualityScore": result.data_quality_score,
                "activityDataPoints": result.activity_data_count
            }
            
        return {
            "content": json.dumps(esrs_data, indent=2).encode(),
            "format": "json",
            "filename": f"ESRS_E1_{organization.name}_{inventory.reporting_year}.json"
        }
        
    def _analyze_transition_risks(self, inventory: Scope3Inventory) -> List[Dict[str, str]]:
        """Analyze transition risks from Scope 3 emissions"""
        risks = []
        
        # High emission categories pose carbon pricing risk
        for category, result in inventory.category_results.items():
            emissions_t = float(result.emissions.value) / 1000
            percentage = (emissions_t / (float(inventory.total_emissions.value) / 1000)) * 100
            
            if percentage > 20:
                risks.append({
                    "category": category.value,
                    "risk_level": "High",
                    "description": f"Represents {percentage:.1f}% of Scope 3 emissions - high exposure to carbon pricing"
                })
            elif percentage > 10:
                risks.append({
                    "category": category.value,
                    "risk_level": "Medium",
                    "description": f"Material emissions source at {percentage:.1f}% - monitor policy developments"
                })
                
        return risks
        
    async def _save_to_s3(self, content: bytes, key: str):
        """Save report to S3"""
        self.s3_client.put_object(
            Bucket="ghg-reports",
            Key=key,
            Body=content,
            ServerSideEncryption="AES256"
        )
        
    def _load_templates(self) -> Dict[str, Template]:
        """Load report templates"""
        # In production, load from files
        return {}
        
    async def _get_inventory(self, organization_id: UUID, year: int) -> Scope3Inventory:
        """Get inventory (simplified)"""
        # Would use CalculationService.get_inventory
        from app.services.calculation_service import CalculationService
        # Implementation would properly inject dependencies
        pass
