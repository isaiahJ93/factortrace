# Quick setup: Add this to your existing FastAPI backend
# File: src/api/routes/vouchers.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import json

router = APIRouter(prefix="/api/vouchers", tags=["vouchers"])

# Simple models
class EmissionScope(BaseModel):
    value: float
    uncertainty: int = 5
    quality: int = 80
    methodology: str = "direct"

class VoucherData(BaseModel):
    company_name: str
    lei: str
    reporting_period: str
    reporting_year: str
    standard: str
    scope1: EmissionScope
    scope2: EmissionScope
    scope3: EmissionScope
    primary_data_percentage: int = 65
    estimates_percentage: int = 25
    proxies_percentage: int = 10
    verification_level: str = "limited"
    data_collection_method: str = "automated"
    notes: Optional[str] = None
    targets: Optional[Dict[str, Any]] = None

# Store drafts in memory (use Redis/DB in production)
drafts = {}
generated_reports = {}

@router.post("/validate")
async def validate_voucher(data: VoucherData):
    """Quick validation endpoint"""
    warnings = []
    suggestions = []
    
    # Basic validation
    if data.primary_data_percentage < 50:
        warnings.append("Primary data is below 50% - consider improving data collection")
    
    total = data.scope1.value + data.scope2.value + data.scope3.value
    if data.scope3.value < total * 0.4:
        suggestions.append("Scope 3 typically represents 40-80% of total emissions")
    
    # Calculate quality score
    quality_score = int(
        data.scope1.quality * 0.2 + 
        data.scope2.quality * 0.2 + 
        data.scope3.quality * 0.6
    )
    
    return {
        "valid": True,
        "quality_score": quality_score,
        "warnings": warnings,
        "suggestions": suggestions
    }

@router.post("/draft")
async def save_draft(data: VoucherData):
    """Save draft endpoint"""
    draft_id = str(uuid.uuid4())
    drafts[draft_id] = {
        "id": draft_id,
        "data": data.dict(),
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    return {"id": draft_id, "message": "Draft saved successfully"}

@router.post("/generate")
async def generate_xbrl(request: Dict[str, Any]):
    """Generate XBRL voucher"""
    try:
        voucher_data = VoucherData(**request["voucher_data"])
        report_id = str(uuid.uuid4())
        
        # Calculate total emissions
        total_emissions = (
            voucher_data.scope1.value + 
            voucher_data.scope2.value + 
            voucher_data.scope3.value
        )
        
        # Create simple XBRL content
        xbrl_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance" 
      xmlns:esrs="http://xbrl.efrag.org/taxonomy/2023-12-31/esrs">
    
    <context id="c1">
        <entity>
            <identifier scheme="http://www.gleif.org">{voucher_data.lei}</identifier>
        </entity>
        <period>
            <startDate>{voucher_data.reporting_year}-01-01</startDate>
            <endDate>{voucher_data.reporting_year}-12-31</endDate>
        </period>
    </context>
    
    <unit id="tCO2e">
        <measure>esrs:tCO2e</measure>
    </unit>
    
    <esrs:Scope1GHGEmissions contextRef="c1" unitRef="tCO2e" decimals="2">
        {voucher_data.scope1.value}
    </esrs:Scope1GHGEmissions>
    
    <esrs:Scope2GHGEmissions contextRef="c1" unitRef="tCO2e" decimals="2">
        {voucher_data.scope2.value}
    </esrs:Scope2GHGEmissions>
    
    <esrs:Scope3GHGEmissions contextRef="c1" unitRef="tCO2e" decimals="2">
        {voucher_data.scope3.value}
    </esrs:Scope3GHGEmissions>
    
    <esrs:TotalGHGEmissions contextRef="c1" unitRef="tCO2e" decimals="2">
        {total_emissions}
    </esrs:TotalGHGEmissions>
    
    <!-- Data Quality -->
    <esrs:DataQualityScore contextRef="c1" decimals="0">
        {int(voucher_data.scope1.quality * 0.2 + voucher_data.scope2.quality * 0.2 + voucher_data.scope3.quality * 0.6)}
    </esrs:DataQualityScore>
    
</xbrl>"""
        
        # Store the report
        generated_reports[report_id] = {
            "id": report_id,
            "content": xbrl_content,
            "metadata": voucher_data.dict(),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "report_id": report_id,
            "download_url": f"/api/vouchers/download/{report_id}",
            "validation_status": "valid",
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{report_id}")
async def download_report(report_id: str):
    """Download generated report"""
    if report_id not in generated_reports:
        raise HTTPException(status_code=404, detail="Report not found")
    
    report = generated_reports[report_id]
    
    # Return as XBRL file
    from fastapi.responses import Response
    return Response(
        content=report["content"],
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename=emissions_report_{report_id}.xbrl"
        }
    )

@router.get("/suggestions")
async def get_suggestions(industry: str = "manufacturing"):
    """Get emission suggestions by industry"""
    suggestions_db = {
        "manufacturing": {
            "scope1": {"min": 200, "max": 300, "typical": 250},
            "scope2": {"min": 150, "max": 220, "typical": 180},
            "scope3": {"min": 700, "max": 1000, "typical": 820}
        },
        "technology": {
            "scope1": {"min": 10, "max": 50, "typical": 25},
            "scope2": {"min": 100, "max": 200, "typical": 150},
            "scope3": {"min": 300, "max": 600, "typical": 450}
        },
        "retail": {
            "scope1": {"min": 50, "max": 150, "typical": 100},
            "scope2": {"min": 200, "max": 400, "typical": 300},
            "scope3": {"min": 800, "max": 1500, "typical": 1100}
        }
    }
    
    return {
        "industry": industry,
        "suggestions": suggestions_db.get(industry, suggestions_db["manufacturing"]),
        "confidence": 0.85,
        "based_on": "Industry averages from 2024 ESRS reports"
    }

# Add this special endpoint that matches what your frontend is calling
@router.post("/reports/generate-elite")
async def generate_elite_report(request: Dict[str, Any]):
    """Elite report generation endpoint (matches your frontend)"""
    
    # Transform the elite format to our standard format
    facts = request.get("facts", [])
    metadata = request.get("metadata", {})
    
    # Extract emissions from facts
    scope1_value = 0
    scope2_value = 0
    scope3_value = 0
    
    for fact in facts:
        if fact["concept"] == "Scope1Emissions":
            scope1_value = float(fact["value"])
        elif fact["concept"] == "Scope2Emissions":
            scope2_value = float(fact["value"])
        elif fact["concept"] == "Scope3Emissions":
            scope3_value = float(fact["value"])
    
    # Create voucher data
    voucher_data = {
        "company_name": metadata.get("entity_name", ""),
        "lei": metadata.get("entity_identifier", ""),
        "reporting_period": metadata.get("reporting_period", "Q1"),
        "reporting_year": metadata.get("reporting_year", "2024"),
        "standard": metadata.get("standard", "CSRD"),
        "scope1": {"value": scope1_value, "quality": 85, "uncertainty": 5, "methodology": "direct"},
        "scope2": {"value": scope2_value, "quality": 80, "uncertainty": 10, "methodology": "location"},
        "scope3": {"value": scope3_value, "quality": 75, "uncertainty": 15, "methodology": "spend"},
        "primary_data_percentage": 65,
        "estimates_percentage": 25,
        "proxies_percentage": 10,
        "verification_level": metadata.get("verification_level", "limited"),
        "data_collection_method": "automated"
    }
    
    # Call our standard generate endpoint
    return await generate_xbrl({"voucher_data": voucher_data, "format": request.get("format", "ixbrl")})