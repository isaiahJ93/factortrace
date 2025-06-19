from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
import os
import json

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/admin/voucher/{voucher_id}/report.xhtml", response_class=Response)
def export_xhtml_report(voucher_id: str, request: Request):
    voucher_path = f"data/vouchers/{voucher_id}.json"
    
    if not os.path.exists(voucher_path):
        raise HTTPException(status_code=404, detail="Voucher not found")
    
    with open(voucher_path, "r") as f:
        voucher = json.load(f)
    
    # If needed, inject taxonomy version
    voucher["taxonomy_version"] = "2025-draft"

    rendered = templates.get_template("report.xhtml.j2").render(
        request=request,
        voucher=voucher
    )

    return Response(content=rendered, media_type="application/xhtml+xml")

