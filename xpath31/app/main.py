from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from datetime import datetime

app = FastAPI(title="XBRL Validation API", version="1.0.0")

# CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class VoucherValidation(BaseModel):
    code: str
    user_id: Optional[str] = None

class VoucherResponse(BaseModel):
    status: str
    remaining_uses: Optional[int] = None
    permissions: Dict

# Basic routes
@app.get("/")
async def root():
    return {"message": "XBRL Validation API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/vouchers/validate")
async def validate_voucher(voucher: VoucherValidation):
    """Validate voucher code"""
    # For now, accept any 16-character code for testing
    if len(voucher.code) == 16:
        return VoucherResponse(
            status="valid",
            remaining_uses=10,
            permissions={
                "maxReports": 10,
                "taxonomyAccess": ["emissions", "financial"],
                "exportFormats": ["pdf", "xlsx", "xbrl", "ixbrl", "json"]
            }
        )
    else:
        return VoucherResponse(
            status="invalid",
            permissions={}
        )

@app.post("/api/xbrl/validate")
async def validate_xbrl_data(data: Dict):
    """Validate XBRL data"""
    return {
        "status": "processing",
        "session_id": data.get("session_id", "test-session"),
        "message": "Validation started"
    }

@app.get("/api/ixbrl/templates")
async def get_ixbrl_templates():
    """Get available iXBRL templates"""
    return {
        "templates": [
            {
                "id": "sustainability_report",
                "name": "ESRS Sustainability Report",
                "description": "Full sustainability disclosure report",
                "sections": ["E1", "E2", "E3", "S1", "S2", "G1"]
            },
            {
                "id": "emissions_summary",
                "name": "GHG Emissions Summary",
                "description": "Focused emissions reporting",
                "sections": ["Scope 1", "Scope 2", "Scope 3"]
            }
        ]
    }



# Add this to the end of your app/main.py file

# Handle the double /api prefix issue
@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/api/health")
@app.get("/api/api/health/")
async def double_api_health():
    """Handle frontend's double API prefix"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Frontend is using double /api prefix - consider fixing the base URL"
    }

# Add validation endpoints
@app.post("/api/xbrl/validate-facts")
async def validate_facts(data: Dict):
    """Validate XBRL fact data"""
    fact_data = data.get("fact_data", {})
    errors = []
    
    # Validate calculations
    total = float(fact_data.get("total-emissions", {}).get("value", 0))
    scope1 = float(fact_data.get("scope1-emissions", {}).get("value", 0))
    scope2 = float(fact_data.get("scope2-location", {}).get("value", 0))
    scope3_up = float(fact_data.get("scope3-upstream", {}).get("value", 0))
    scope3_down = float(fact_data.get("scope3-downstream", {}).get("value", 0))
    
    calculated = scope1 + scope2 + scope3_up + scope3_down
    if abs(calculated - total) > 0.01:
        errors.append({
            "field": "total-emissions",
            "message": f"Total {total} doesn't match sum {calculated}",
            "severity": "error"
        })
    
    # Check for negative values
    for concept, fact in fact_data.items():
        if "emissions" in concept and "value" in fact:
            value = float(fact["value"])
            if value < 0:
                errors.append({
                    "field": concept,
                    "message": "Emission values cannot be negative",
                    "severity": "error"
                })
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": []
    }

@app.post("/api/reports/generate-test")
async def generate_test_report(request: Dict):
    """Generate test report in various formats"""
    format = request.get("format", "json")
    fact_data = request.get("fact_data", {})
    
    if format == "json":
        return {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "format": "json",
                "version": "1.0"
            },
            "entity": {
                "name": "Test Company",
                "id": "TEST-001"
            },
            "reporting_period": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            },
            "facts": fact_data,
            "calculations": {
                "total_emissions": sum(
                    float(fact_data.get(k, {}).get("value", 0))
                    for k in ["scope1-emissions", "scope2-location", 
                              "scope3-upstream", "scope3-downstream"]
                ),
                "scope_1_2_total": sum(
                    float(fact_data.get(k, {}).get("value", 0))
                    for k in ["scope1-emissions", "scope2-location"]
                ),
                "scope_3_total": sum(
                    float(fact_data.get(k, {}).get("value", 0))
                    for k in ["scope3-upstream", "scope3-downstream"]
                )
            }
        }
    elif format == "xbrl":
        # Generate simple XBRL
        xbrl = f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance">
    <context id="c1">
        <entity><identifier>TEST-001</identifier></entity>
        <period><startDate>2024-01-01</startDate><endDate>2024-12-31</endDate></period>
    </context>
    <unit id="u1"><measure>tCO2e</measure></unit>
"""
        for concept, fact in fact_data.items():
            if "value" in fact:
                xbrl += f'    <{concept} contextRef="c1" unitRef="u1">{fact["value"]}</{concept}>\n'
        xbrl += "</xbrl>"
        
        return {
            "format": "xbrl",
            "content_type": "application/xml",
            "preview": xbrl[:500] + "..." if len(xbrl) > 500 else xbrl
        }
    elif format == "ixbrl":
        # Generate simple iXBRL
        html = """<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
<head><title>Sustainability Report</title></head>
<body>
<h1>Sustainability Report</h1>
<h2>Emissions Data</h2>
<table border="1">
<tr><th>Metric</th><th>Value (tCO2e)</th></tr>
"""
        for concept, fact in fact_data.items():
            if "value" in fact:
                html += f"""<tr>
    <td>{concept.replace('-', ' ').title()}</td>
    <td><ix:nonFraction name="{concept}" contextRef="c1" unitRef="u1">{fact['value']}</ix:nonFraction></td>
</tr>
"""
        html += "</table></body></html>"
        
        return {
            "format": "ixbrl",
            "content_type": "text/html",
            "preview": html[:500] + "..." if len(html) > 500 else html
        }
    else:
        return {
            "format": format,
            "content_type": f"application/{format}",
            "preview": f"{format.upper()} report generation would happen here. Install additional libraries for full {format} support."
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Handle the double /api prefix issue
@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/api/health")
@app.get("/api/api/health/")
async def double_api_health():
    """Handle frontend double API prefix"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

# Add validation endpoints
@app.post("/api/xbrl/validate-facts")
async def validate_facts(data: Dict):
    """Validate XBRL fact data"""
    fact_data = data.get("fact_data", {})
    errors = []
    
    # Validate calculations
    total = float(fact_data.get("total-emissions", {}).get("value", 0))
    scope1 = float(fact_data.get("scope1-emissions", {}).get("value", 0))
    scope2 = float(fact_data.get("scope2-location", {}).get("value", 0))
    scope3_up = float(fact_data.get("scope3-upstream", {}).get("value", 0))
    scope3_down = float(fact_data.get("scope3-downstream", {}).get("value", 0))
    
    calculated = scope1 + scope2 + scope3_up + scope3_down
    if abs(calculated - total) > 0.01:
        errors.append({
            "field": "total-emissions",
            "message": f"Total {total} doesn't match sum {calculated}",
            "severity": "error"
        })
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": []
    }

@app.post("/api/reports/generate-test")
async def generate_test_report(request: Dict):
    """Generate test report"""
    format = request.get("format", "json")
    fact_data = request.get("fact_data", {})
    
    if format == "json":
        return {
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "format": "json"
            },
            "facts": fact_data,
            "calculations": {
                "total_emissions": sum(
                    float(fact_data.get(k, {}).get("value", 0))
                    for k in ["scope1-emissions", "scope2-location", 
                              "scope3-upstream", "scope3-downstream"]
                )
            }
        }
    else:
        return {
            "format": format,
            "preview": f"{format.upper()} report would be generated here"
        }
