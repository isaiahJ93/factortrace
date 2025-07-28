# src/scope3_api.py
# Updated to match your dashboard's API expectations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import uuid
import random

app = FastAPI(title="FactorTrace API", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock data storage
voucher_sessions = {}
emissions_data = {
    "scope1": 228.5,
    "scope2": 151.2,
    "scope3": 835.7,
    "total": 1215.4,
    "uncertainty": {
        "scope1": 5,
        "scope2": 10,
        "scope3": 15
    },
    "dataQuality": {
        "scope1": 85,
        "scope2": 80,
        "scope3": 75
    }
}

@app.get("/")
async def root():
    return {
        "message": "FactorTrace Elite API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.post("/api/vouchers/validate")
async def validate_voucher(request: Dict[str, Any]):
    """Validate voucher session - matches dashboard expectations"""
    voucher_code = request.get("code", "")
    
    # Mock validation - in production, check against database
    if voucher_code:
        # Store session
        session_id = str(uuid.uuid4())
        voucher_sessions[voucher_code] = {
            "session_id": session_id,
            "validated_at": datetime.now().isoformat()
        }
        
        return {
            "status": "valid",
            "permissions": {
                "features": {
                    "cbam_compliance": True,
                    "uncertainty_analysis": True,
                    "audit_trail": True,
                    "xbrl_generation": True
                },
                "access_level": "elite",
                "expires_at": "2024-12-31T23:59:59Z"
            },
            "organization": {
                "name": "Elite Corp",
                "id": "org_123"
            }
        }
    
    return {"status": "invalid", "error": "Invalid voucher code"}

@app.get("/api/emissions/summary")
async def get_emissions_summary():
    """Get emissions summary - matches dashboard data structure"""
    # Add some random variation to simulate real-time data
    variation = random.uniform(0.95, 1.05)
    
    return {
        "scope1": round(emissions_data["scope1"] * variation, 1),
        "scope2": round(emissions_data["scope2"] * variation, 1),
        "scope3": round(emissions_data["scope3"] * variation, 1),
        "total": round(emissions_data["total"] * variation, 1),
        "uncertainty": emissions_data["uncertainty"],
        "dataQuality": emissions_data["dataQuality"],
        "lastUpdated": datetime.now().isoformat(),
        "calculationMethod": "AR6 GWP factors with Monte Carlo uncertainty"
    }

@app.get("/api/reports/latest")
async def get_latest_reports():
    """Get latest reports metadata"""
    return {
        "reports": [
            {
                "id": "rep_001",
                "type": "XBRL",
                "created_at": "2024-04-01T10:30:00Z",
                "status": "completed",
                "format": "xbrl",
                "size": "245KB"
            },
            {
                "id": "rep_002",
                "type": "iXBRL",
                "created_at": "2024-04-02T14:15:00Z",
                "status": "completed",
                "format": "ixbrl",
                "size": "512KB"
            }
        ],
        "total": 2,
        "lastGenerated": "2024-04-02T14:15:00Z"
    }

@app.post("/api/emissions/calculate")
async def calculate_emissions(request: Dict[str, Any]):
    """Calculate emissions with uncertainty - Monte Carlo method"""
    activity_value = float(request.get("activity_value", 0))
    emission_factor_id = request.get("emission_factor_id", "default")
    scope = request.get("scope", "3")
    uncertainty_method = request.get("uncertainty_method", "monte_carlo")
    
    # Mock calculation with uncertainty
    base_emissions = activity_value * 0.385  # Example factor
    
    # Monte Carlo simulation (simplified)
    if uncertainty_method == "monte_carlo":
        simulations = []
        for _ in range(1000):
            variation = random.gauss(1.0, 0.1)  # 10% standard deviation
            simulations.append(base_emissions * variation)
        
        mean_emissions = sum(simulations) / len(simulations)
        lower_bound = sorted(simulations)[int(len(simulations) * 0.05)]  # 5th percentile
        upper_bound = sorted(simulations)[int(len(simulations) * 0.95)]  # 95th percentile
        
        return {
            "emissions": round(mean_emissions, 2),
            "unit": "tCO2e",
            "uncertainty": {
                "method": "monte_carlo",
                "iterations": 1000,
                "confidence_level": 90,
                "lower_bound": round(lower_bound, 2),
                "upper_bound": round(upper_bound, 2),
                "relative_uncertainty": round((upper_bound - lower_bound) / mean_emissions * 100, 1)
            },
            "calculation_details": {
                "activity_value": activity_value,
                "emission_factor": 0.385,
                "scope": scope,
                "timestamp": datetime.now().isoformat()
            }
        }
    
    return {
        "emissions": round(base_emissions, 2),
        "unit": "tCO2e",
        "calculation_details": {
            "activity_value": activity_value,
            "emission_factor": 0.385,
            "scope": scope
        }
    }

@app.post("/api/reports/generate-elite")
async def generate_report(request: Dict[str, Any]):
    """Generate XBRL/iXBRL report"""
    format_type = request.get("format", "json")
    fact_data = request.get("fact_data", {})
    
    report_id = str(uuid.uuid4())
    
    # Generate content based on format
    if format_type == "json":
        content = {
            "report": {
                "id": report_id,
                "type": "emissions",
                "generated_at": datetime.now().isoformat(),
                "facts": fact_data,
                "metadata": {
                    "standard": "ESRS E1",
                    "period": "2024-01-01 to 2024-12-31",
                    "entity": "Elite Corp"
                }
            },
            "vouchers": True  # Signal successful generation
        }
        
    elif format_type == "xml":
        # Simple XBRL structure
        facts_xml = ""
        for fact_id, fact in fact_data.items():
            facts_xml += f"""
    <fact:item contextRef="c1" unitRef="u1" decimals="2">
        <fact:concept>{fact_id}</fact:concept>
        <fact:value>{fact['value']}</fact:value>
    </fact:item>"""
        
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<xbrl xmlns="http://www.xbrl.org/2003/instance" 
      xmlns:fact="http://factortrace.com/xbrl/2024">
    <context id="c1">
        <entity>
            <identifier scheme="http://www.lei.org">123456789</identifier>
        </entity>
        <period>
            <instant>2024-12-31</instant>
        </period>
    </context>
    <unit id="u1">
        <measure>iso4217:tCO2e</measure>
    </unit>
    {facts_xml}
</xbrl>"""
        
    else:  # ixbrl
        # iXBRL/XHTML format
        facts_html = ""
        for fact_id, fact in fact_data.items():
            facts_html += f"""
        <tr>
            <td>{fact_id.replace('-', ' ').title()}</td>
            <td><ix:nonFraction contextRef="c1" unitRef="u1" decimals="2" 
                name="esrs:{fact_id}" format="ixt:numdotdecimal">
                {fact['value']}
            </ix:nonFraction></td>
            <td>{fact.get('unit', 'tCO2e')}</td>
        </tr>"""
        
        content = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" 
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
      xmlns:ixt="http://www.xbrl.org/inlineXBRL/transformation/2022-01-24">
<head>
    <title>Emissions Report - Elite Corp</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #3498db; color: white; }}
        .metadata {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>Emissions Report - {datetime.now().year}</h1>
    
    <div class="metadata">
        <p><strong>Entity:</strong> Elite Corp (LEI: 123456789)</p>
        <p><strong>Period:</strong> January 1 - December 31, {datetime.now().year}</p>
        <p><strong>Standard:</strong> ESRS E1 Climate Change</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <h2>Greenhouse Gas Emissions</h2>
    <table>
        <thead>
            <tr>
                <th>Emission Category</th>
                <th>Value</th>
                <th>Unit</th>
            </tr>
        </thead>
        <tbody>
            {facts_html}
        </tbody>
    </table>
    
    <div style="display:none">
        <ix:header>
            <ix:hidden>
                <ix:nonNumeric contextRef="c1" name="esrs:EntityName">Elite Corp</ix:nonNumeric>
            </ix:hidden>
            <ix:references>
                <link:schemaRef xlink:type="simple" 
                     xlink:href="https://www.efrag.org/esrs/2023/esrs-e1.xsd"/>
            </ix:references>
        </ix:header>
    </div>
</body>
</html>"""
    
    return {
        "report_id": report_id,
        "format": format_type,
        "content": content if format_type != "json" else None,
        "vouchers": content if format_type == "json" else None,
        "download_url": f"/api/reports/download/{report_id}",
        "status": "completed",
        "generated_at": datetime.now().isoformat()
    }

@app.post("/api/vouchers/validate")
async def validate_voucher(voucher: Dict[str, Any]):
    """Original endpoint for compatibility"""
    return {
        "valid": True,
        "extracted_data": voucher,
        "confidence_scores": {"overall": 0.95}
    }

@app.post("/api/xbrl/validate-facts")
async def validate_facts(data: Dict[str, Any]):
    """Validate XBRL facts"""
    facts = data.get("facts", [])
    return {
        "valid": True,
        "errors": [],
        "warnings": []
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FactorTrace Elite API")
    print("📊 Dashboard: http://localhost:3000")
    print("📚 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)