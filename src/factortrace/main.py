from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from factortrace.routes.admin import admin_router, templates
from factortrace.api.routes_voucher import router as voucher_router

app = FastAPI(title="FactorTrace Scope 3 API")

app.include_router(admin_router)
app.include_router(voucher_router, prefix="/api/v1")

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    return templates.TemplateResponse("error.html", {
        "request": request,
        "status_code": exc.status_code,
        "detail": exc.detail
    }, status_code=exc.status_code)
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from factortrace.routes.admin import admin_router, templates
from cli.generate_report import generate_compliance_report

if __name__ == "__main__":
    generate_compliance_report()

app = FastAPI()
app.include_router(admin_router)

@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    status = exc.status_code
    if status == HTTP_500_INTERNAL_SERVER_ERROR:
        # maybe add special logging or a different template
        return templates.TemplateResponse("500.html", {
            "request": request,
            "status_code": status,
            "detail": exc.detail,
        }, status_code=status)
    return templates.TemplateResponse("error.html", {
        "request": request,
        "status_code": status,
        "detail": exc.detail,
    }, status_code=status)

from fastapi import FastAPI
from factortrace.api.routes_voucher import router as voucher_router

app = FastAPI(title="FactorTrace Scope 3 API")
app.include_router(voucher_router, prefix="/api/v1")

from factortrace.compliance_engine import main

if __name__ == "__main__":
    main()

from generator.xhtml_generator import generate_ixbrl

generate_ixbrl(
    voucher_data={"lei": "LEI:898998123ABC456"},
    output_path="output/compliance_report.xhtml"
