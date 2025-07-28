# pdf_export.py - FastAPI PDF Export Endpoint for GHG Calculator
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Dict, Any, List, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
import io
from pydantic import BaseModel

# Data models
class CompanyInfo(BaseModel):
    name: str
    id: str

class EmissionsSummary(BaseModel):
    total_emissions_tons_co2e: float
    scope1_emissions: float
    scope2_location_based: float
    scope2_market_based: Optional[float] = None
    scope3_emissions: float

class Activity(BaseModel):
    name: str
    amount: float
    unit: str
    factor: float
    emissions_tons: Optional[float] = None
    category: Optional[str] = None
    scope: Optional[str] = None

class PDFExportRequest(BaseModel):
    company_info: CompanyInfo
    reporting_period: str
    summary: EmissionsSummary
    activities: List[Activity]
    data_quality: Optional[Dict[str, Any]] = None
    evidence_files: Optional[List[Dict[str, Any]]] = []
    uncertainty_analysis: Optional[Dict[str, Any]] = None
    emissions_data: Optional[List[Dict[str, Any]]] = []
    category_totals: Optional[List[Dict[str, Any]]] = []
    metadata: Optional[Dict[str, Any]] = {}
    results: Optional[Dict[str, Any]] = {}

router = APIRouter()

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom styles for the PDF"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a2e'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Subtitle style
        self.styles.add(ParagraphStyle(
            name='Subtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#16213e'),
            spaceAfter=20
        ))
        
        # Data style
        self.styles.add(ParagraphStyle(
            name='DataText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333')
        ))
    
    def generate_pdf(self, data: PDFExportRequest) -> bytes:
        """Generate PDF report from emissions data"""
        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Build story (content)
        story = []
        
        # Title Page
        story.append(Paragraph(f"{data.company_info.name}", self.styles['CustomTitle']))
        story.append(Paragraph("GHG Emissions Report", self.styles['Subtitle']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(f"Reporting Period: {data.reporting_period}", self.styles['Normal']))
        story.append(Spacer(1, 2*cm))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", self.styles['Heading1']))
        story.append(Spacer(1, 0.5*cm))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value (tCO₂e)', 'Percentage'],
            ['Total Emissions', f"{data.summary.total_emissions_tons_co2e:.2f}", '100%'],
            ['Scope 1 (Direct)', f"{data.summary.scope1_emissions/1000:.2f}", 
             f"{(data.summary.scope1_emissions/1000/data.summary.total_emissions_tons_co2e*100):.1f}%"],
            ['Scope 2 (Energy)', f"{data.summary.scope2_location_based/1000:.2f}", 
             f"{(data.summary.scope2_location_based/1000/data.summary.total_emissions_tons_co2e*100):.1f}%"],
            ['Scope 3 (Value Chain)', f"{data.summary.scope3_emissions/1000:.2f}", 
             f"{(data.summary.scope3_emissions/1000/data.summary.total_emissions_tons_co2e*100):.1f}%"]
        ]
        
        summary_table = Table(summary_data, colWidths=[8*cm, 4*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 1*cm))
        
        # Data Quality Score
        if data.data_quality:
            story.append(Paragraph("Data Quality Assessment", self.styles['Heading2']))
            quality_score = data.data_quality.get('overallScore', 0)
            story.append(Paragraph(f"Overall Data Quality Score: {quality_score:.0f}%", self.styles['Normal']))
            story.append(Spacer(1, 0.5*cm))
        
        # Page break before detailed breakdown
        story.append(PageBreak())
        
        # Detailed Activity Breakdown
        story.append(Paragraph("Detailed Activity Breakdown", self.styles['Heading1']))
        story.append(Spacer(1, 0.5*cm))
        
        # Activities table
        if data.activities:
            activity_data = [['Activity', 'Amount', 'Unit', 'Factor', 'Emissions (tCO₂e)']]
            
            for activity in data.activities:
                emissions = (activity.amount * activity.factor) / 1000
                activity_data.append([
                    activity.name,
                    f"{activity.amount:.2f}",
                    activity.unit,
                    f"{activity.factor:.3f}",
                    f"{emissions:.3f}"
                ])
            
            activity_table = Table(activity_data, colWidths=[6*cm, 3*cm, 2*cm, 3*cm, 3*cm])
            activity_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#16213e')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            
            story.append(activity_table)
        
        # Uncertainty Analysis
        if data.uncertainty_analysis:
            story.append(PageBreak())
            story.append(Paragraph("Uncertainty Analysis", self.styles['Heading1']))
            story.append(Spacer(1, 0.5*cm))
            
            ua = data.uncertainty_analysis
            if ua.get('confidence_interval_95'):
                lower, upper = ua['confidence_interval_95']
                story.append(Paragraph(
                    f"95% Confidence Interval: {lower/1000:.2f} - {upper/1000:.2f} tCO₂e",
                    self.styles['Normal']
                ))
            
            if ua.get('relative_uncertainty_percent'):
                story.append(Paragraph(
                    f"Relative Uncertainty: ±{ua['relative_uncertainty_percent']:.1f}%",
                    self.styles['Normal']
                ))
        
        # Methodology
        story.append(PageBreak())
        story.append(Paragraph("Methodology", self.styles['Heading1']))
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph(
            "This inventory has been prepared in accordance with:",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.3*cm))
        methodology = [
            "• The Greenhouse Gas Protocol: A Corporate Accounting and Reporting Standard",
            "• European Sustainability Reporting Standards (ESRS) E1 Climate Change",
            "• ISO 14064-1:2018 Greenhouse gases"
        ]
        for item in methodology:
            story.append(Paragraph(item, self.styles['Normal']))
            story.append(Spacer(1, 0.2*cm))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.read()

@router.post("/api/v1/ghg-calculator/export/pdf")
async def export_pdf(request: PDFExportRequest):
    """Generate PDF report for GHG emissions"""
    try:
        # Initialize PDF generator
        pdf_generator = PDFGenerator()
        
        # Generate PDF
        pdf_content = pdf_generator.generate_pdf(request)
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=GHG_Report_{request.reporting_period}.pdf"
            }
        )
        
    except Exception as e:
        print(f"PDF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")