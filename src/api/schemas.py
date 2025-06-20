from __future__ import annotations
from typing import Optional, Any, Dict
from enum import Enum

# ------------------------------------------------------------------
# Pydantic v2 exposes ConfigDict; v1 doesn’t.  This shim makes it
# available either way so test collection never explodes.
# ------------------------------------------------------------------
try:
    from pydantic import BaseModel, Field, ConfigDict  # v2.x
except ImportError:                                   # v1.x fallback
    from pydantic import BaseModel, Field              # type: ignore

    def ConfigDict(**kwargs: Any) -> Dict[str, Any]:   # noqa: N802
        """Minimal stand-in so `model_config = ConfigDict(...)` works on v1."""
        return kwargs
    

class EmissionRequest(BaseModel):
    activity_data: float = Field(..., gt=0, description="e.g. 1000")
    activity_unit: str = Field(..., json_schema_extra={"example": "kWh"})
    emission_factor: str = Field(
        ...,
        description="Factor ID or numeric value; ID preferred (e.g. 'EF_GRID_EU_2024')"
    scope: str = Field("3", pattern="^[123]$", description="GHG Protocol scope: 1, 2, or 3")
    scope3_category: Optional[str] = Field(
        ..., description="Scope 3 category (if applicable)"

class VoucherInput(BaseModel):
    supplier_id: str
    emission_factor_id: Optional[str] = None
    supplier_name: str
    legal_entity_identifier: str
    product_category: str
    cost: float
    material_type: str
    origin_country: str
    installation_country: Optional[str] = None
    emission_factor: float
    product_cn_code: str = Field(alias="product_cn_code")
    use_fallback_factor: bool = Field(alias="fallback_factor_used")
    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)