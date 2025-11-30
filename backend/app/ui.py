# app/ui.py
"""
FactorTrace UI Routes
=====================
Simple template-based UI for demos and manual testing.
"""
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

# Setup templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

ui_router = APIRouter(tags=["UI"])


@ui_router.get("/demo/calculator", response_class=HTMLResponse)
async def demo_calculator(request: Request):
    """
    Demo calculator UI for testing the unified emission calculation API.

    This is a simple, production-grade UI for:
    - Activity-based calculations (DEFRA/EPA)
    - Spend-based calculations (EXIOBASE)

    Suitable for Loom demos and manual testing.
    """
    return templates.TemplateResponse("calculator.html", {"request": request})
