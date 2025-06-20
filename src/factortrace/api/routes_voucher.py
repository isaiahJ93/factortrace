from __future__ import annotations
from fastapi import APIRouter, UploadFile, File
from factortrace.services import generator, validator, xbrl_exporter
from factortrace.models.emissions_voucher import EmissionVoucher

router = APIRouter()

@router.post("/voucher/generate", response_model=EmissionVoucher)
async def generate_voucher(file: UploadFile = File(...)):
    return await generator.create_voucher(file)

@router.post("/voucher/validate", response_model=EmissionVoucher)
async def validate_voucher(file: UploadFile = File(...)):
    return await validator.run_validation(file)

@router.get("/voucher/export/xbrl/{voucher_id}")
async def export_xbrl(voucher_id: str):
    return await xbrl_exporter.export(voucher_id)
