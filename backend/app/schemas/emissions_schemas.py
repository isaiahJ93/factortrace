from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel
from app.models.emissions_voucher import EmissionVoucher  # adjust path as needed
from my_pkg.enums import TierLevelEnum
from datetime import datetime
from enum import Enum

class EmissionScope(int, Enum):
    SCOPE_1 = 1
    SCOPE_2 = 2
    SCOPE_3 = 3

class EmissionCategory(str, Enum):
    PURCHASED_GOODS = "purchased_goods"
    CAPITAL_GOODS = "capital_goods"
    FUEL_ENERGY = "fuel_energy"
    TRANSPORTATION = "transportation"
    WASTE = "waste"
    BUSINESS_TRAVEL = "business_travel"
    EMPLOYEE_COMMUTING = "employee_commuting"
    LEASED_ASSETS = "leased_assets"

class EmissionCreate(BaseModel):
    scope: EmissionScope
    category: EmissionCategory
    subcategory: Optional[str] = None
    activity_data: float = Field(..., gt=0)
    unit_conversion: Optional[float] = 1.0
    region: Optional[str] = "global"
    data_source: Optional[str] = None

class EmissionResponse(BaseModel):
    id: int
    scope: int
    category: str
    activity_data: float
    emission_factor: float
    amount: float
    unit: str
    metadata: Optional[Dict] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class EmissionsSummary(BaseModel):
    scope1_total: float = 0
    scope2_total: float = 0
    scope3_total: float = 0
    total_emissions: float = 0
    category_breakdown: Dict[str, Dict[str, float]] = {}
    insights: List[Dict] = []


class VouchersListResponse(BaseModel):
    vouchers: List[EmissionVoucher]


class Voucher(BaseModel):
    id: str
    company: str
    emissions: float


class VoucherList(BaseModel):
    vouchers: List[Voucher]
    class Config:
        # 🔧 REVIEW: possible unclosed bracket -> json_schema_extra = {}
        json_schema_extra = {
            # 🔧 REVIEW: possible unclosed bracket -> "example"
            "example": {
                "supplier_id": "SUP-001",
                "activity": "Electricity consumption",
                "value": 1000,
                "unit": "kWh",
                "country": "DE"
            }
        }


class VoucherListWithExample(BaseModel):
    vouchers: List[Voucher]

    class Config:
        # 🔧 REVIEW: possible unclosed bracket -> json_schema_extra = {}
        json_schema_extra = {
            # 🔧 REVIEW: possible unclosed bracket -> "example"
            "example": {
                # 🔧 REVIEW: possible unclosed bracket -> "vouchers"
                "vouchers": [
                    # 🔧 REVIEW: possible unclosed bracket -> {}
                    {
                        "supplier_id": "SUP-001",
                        "activity": "Electricity consumption",
                        "value": 1000,
                        "unit": "kWh",
                        "country": "DE"
                    },
                    # 🔧 REVIEW: possible unclosed bracket -> {}
                    {
                        "supplier_id": "SUP-002",
                        "activity": "Diesel fuel usage",
                        "value": 500,
                        "unit": "liters",
                        "country": "NL"
                    }
                ]
            }
        }