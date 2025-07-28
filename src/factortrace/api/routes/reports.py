# src/factortrace/api/routes/reports.py
from fastapi import APIRouter, Response, HTTPException
from factortrace.generator.xhtml_generator import (
    XHTMLiXBRLGenerator, EmissionReportData
)

router = APIRouter(tags=["Reports"])

@router.post("/reports/xhtml", response_class=Response)
async def generate_xhtml_report(payload: EmissionReportData):
    try:
        gen = XHTMLiXBRLGenerator()
        xhtml = gen.render(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Option A – just stream it back
    return Response(
        content=xhtml,
        media_type="application/xhtml+xml",
        headers={
            "Content-Disposition": "attachment; filename=report.xhtml"
        },
    )
