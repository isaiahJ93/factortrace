from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class EmissionScope(BaseModel):
    value: float = Field(..., gt=0, description="Emission value in tCO2e")
    uncertainty: int = Field(default=5, ge=0, le=100)
    quality: int = Field(default=80, ge=0, le=100)
    methodology: str

class VerificationLevel(str, Enum):
    NONE = "none"
    LIMITED = "limited"
    REASONABLE = "reasonable"

class ComplianceStandard(str, Enum):
    CSRD = "CSRD"
    ESRS_E1 = "ESRS E1"
    CBAM = "CBAM"
    SBTI = "SBTi"

class VoucherCreateRequest(BaseModel):
    # Basic Information
    company_name: str = Field(..., min_length=1, max_length=200)
    lei: str = Field(..., regex="^[A-Z0-9]{20}$")
    reporting_period: str = Field(..., regex="^(Q[1-4]|FY)$")
    reporting_year: str = Field(..., regex="^20[2-9][0-9]$")
    standard: ComplianceStandard
    
    # Emissions Data
    scope1: EmissionScope
    scope2: EmissionScope
    scope3: EmissionScope
    
    # Data Quality
    primary_data_percentage: int = Field(default=65, ge=0, le=100)
    estimates_percentage: int = Field(default=25, ge=0, le=100)
    proxies_percentage: int = Field(default=10, ge=0, le=100)
    verification_level: VerificationLevel = VerificationLevel.LIMITED
    data_collection_method: str = "automated"
    
    # Additional Info
    notes: Optional[str] = None
    targets: Optional[Dict[str, Any]] = None
    
    @validator('proxies_percentage')
    def validate_percentages(cls, v, values):
        if 'primary_data_percentage' in values and 'estimates_percentage' in values:
            total = values['primary_data_percentage'] + values['estimates_percentage'] + v
            if total != 100:
                raise ValueError(f'Percentages must sum to 100, got {total}')
        return v

class VoucherDraft(BaseModel):
    id: str
    user_id: str
    data: VoucherCreateRequest
    created_at: datetime
    updated_at: datetime
    step_completed: int = 0

class XBRLGenerationRequest(BaseModel):
    voucher_data: VoucherCreateRequest
    format: str = "ixbrl"
    include_signature: bool = True

class XBRLGenerationResponse(BaseModel):
    report_id: str
    download_url: str
    validation_status: str
    xbrl_content: Optional[str] = None
    generated_at: datetime