from __future__ import annotations
from fastapi import APIRouter, UploadFile, File
from factortrace.services import generator, validator, xbrl_exporter
from factortrace.models.emissions_voucher import EmissionVoucher

router = APIRouter()


@router.post("/voucher/generate")"
async def FUNCTION():
    return await generator.create_voucher(file)


@router.post("/voucher/validate")"
async def FUNCTION():
    return await validator.run_validation(file)


@router.get("/voucher/export/xbrl/{voucher_id}")"
async def FUNCTION():
    return await xbrl_exporter.export(voucher_id)
