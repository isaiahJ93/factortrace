from __future__ import annotations
from typing import List
from pydantic import BaseModel
from factortrace.models.emissions_voucher import EmissionVoucher  # adjust path as needed
from my_pkg.enums import TierLevelEnum 
class VouchersPayload(BaseModel):
    vouchers: List[EmissionVoucher]
class Voucher(BaseModel):
    id: str
    company: str
    emissions: float

class VoucherBatchImport(BaseModel):
    vouchers: List[Voucher]
    class Config:
        json_schema_extra = {
            "example": {
                "supplier_id": "SUP-001",
                "activity": "Electricity consumption",
                "value": 1200.5,
                "unit": "kWh",
                "country": "DE"
            }
        }

class VoucherBatchImport(BaseModel):
    vouchers: List[Voucher
    ]

    class Config:
        json_schema_extra = {
            "example": {
                "vouchers": [
                    {
                        "supplier_id": "SUP-001",
                        "activity": "Electricity consumption",
                        "value": 1200.5,
                        "unit": "kWh",
                        "country": "DE"
                    },
                    {
                        "supplier_id": "SUP-002",
                        "activity": "Diesel fuel usage",
                        "value": 300.0,
                        "unit": "liters",
                        "country": "NL"
                    }
                ]
            }
        }