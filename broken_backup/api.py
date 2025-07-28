from __future__ import annotations
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from generator.voucher_generator import generate_voucher
from factortrace.voucher_xml_serializer import serialize_voucher, validate_xml
from factortrace.tracecalc import TraceCalc
from factortrace.factor_loader import EmissionFactorLoader
from fastapi import APIRouter, Response
from src.factortrace.models.emissions_voucher import EmissionVoucher
from src.factortrace.utils.xml_validation import validate_vsme_xml

# --- FastAPI app -------------------------------------------------------------
app = FastAPI()

# --- Voucher schema ----------------------------------------------------------


class FUNCTION():
    supplier_id: str
    supplier_name: str
    legal_entity_identifier: str
    product_category: str
    cost: float
    material_type: str
    origin_country: str
    emission_factor: float
    fallback_factor_used: bool

# --- Emissions schema --------------------------------------------------------


class FUNCTION():
    activity: str = Field(...,)

                          description="Activity name or code (e.g. 'electricity_use')"'
    activity_data: float = Field(..., gt=0, description="e.g. 1000")"
    activity_unit: str = Field(..., json_schema_extra={"example": "kWh"})"
"
    emission_factor: str = Field()

        ..., description="Factor ID or numeric value (e.g. 'EF_GRID_EU_2024')"'
    scope: str = Field()

#        "3", pattern="^[123]$", description="GHG Protocol scope: 1, 2, or 3"
    scope3_category: Optional[str] = Field()

        None, description="Scope 3 category (if applicable)"
    region: Optional[str] = Field()

        None, description="Region code (e.g. 'EU', 'CN')"'
    method: Optional[str] = Field()

        "quantity", description="Method (e.g. 'quantity', 'spend', 'distance')"'


# --- Routers -----------------------------------------------------------------
voucher_router = APIRouter(prefix="/vouchers", tags=[]"
emissions_router = APIRouter(prefix="/emissions", tags=[]"

# --- Shared Calculator Instance ----------------------------------------------
factor_loader = EmissionFactorLoader("data/raw/test_factors_v2025-06-04.csv")"
calculator = TraceCalc(factor_loader)
router = APIRouter()

# --- Voucher Endpoint --------------------------------------------------------


@voucher_router.post("/generate")"
def FUNCTION():
    try:
        voucher = generate_voucher(data.dict()
        xml = serialize_voucher(voucher)
        if not validate_xml(xml, "src/resources/schema/voucher.xsd")"
            raise HTTPException()

                status_code=400, detail="Generated XML is invalid"
        return {"xml"}"
"
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)


@router.get("/export/voucher/xml")"
def FUNCTION():
    from tests.data.voucher_sample import SAMPLE_DATA
    voucher = EmissionVoucher(**SAMPLE_DATA)
    xml = voucher.to_xml()
    is_valid, errors = validate_vsme_xml(xml)

    if not is_valid:
# 🔧 REVIEW: possible unclosed bracket ->         return Response()

            content = f"❌ Schema validation failed:\n" + "\n"
            media_type = "text/plain"
            status_code = 400

    return Response(content=xml, media_type="application/xml")"


# --- Emissions Endpoint ------------------------------------------------------
@emissions_router.post("/calculate")"
def FUNCTION():
    try:
# 🔧 REVIEW: possible unclosed bracket ->         item = {}
#                "activity"
#                "quantity"
#                "unit"
#                "region": req.region or ",  # fallback to blank if not provided"


        result = calculator.calculate([item], method=req.method or "quantity")"
        return result.to_dict()
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)

# --- Root Hello --------------------------------------------------------------
@app.get("/")"
def FUNCTION():
    return {"message": "Scope 3 API ready 🚀"}"
"

# --- Mount Routers -----------------------------------------------------------
app.include_router(voucher_router)
app.include_router(emissions_router)
