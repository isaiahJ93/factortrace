from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import json
from datetime import datetime
from app.xbrl_validator import XBRLSchemaValidator
from app.report_generator import ReportGenerator

# Initialize validators
xbrl_validator = XBRLSchemaValidator()
report_generator = ReportGenerator()


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
