from fastapi import APIRouter
from fastapi.responses import FileResponse
from factortrace.models.emissions_voucher import EmissionVoucher
from factortrace.exporters.xhtml_exporter import generate_ixbrl
from uuid import uuid4
from pathlib import Path

router = APIRouter()

@router.post("/export", response_class=FileResponse)
def export_ixbrl(voucher: EmissionVoucher):
    output_path = Path("output") / f"{uuid4()}.xhtml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generate_ixbrl(voucher, output_path=str(output_path))
    return FileResponse(path=output_path, media_type="application/xhtml+xml", filename=output_path.name)

