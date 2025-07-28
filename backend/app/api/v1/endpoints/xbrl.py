"""XBRL validation and generation endpoints"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.services.xbrl_validator import validate_xbrl_document
from typing import Dict, Any
import xmlschema
import lxml.etree as ET
from pathlib import Path

from app.core.config import settings
from app.core.auth import get_current_user
from app.models.user import User


router = APIRouter()

XSD_SCHEMAS = {}

def load_xsd_schemas():
    """Load XSD schemas for validation"""
    xsd_path = Path(settings.xsd_base_path)
    if xsd_path.exists():
        for xsd_file in xsd_path.glob("*.xsd"):
            schema_name = xsd_file.stem
            try:
                XSD_SCHEMAS[schema_name] = xmlschema.XMLSchema(str(xsd_file))
                print(f"✅ Loaded XSD schema: {schema_name}")
            except Exception as e:
                print(f"❌ Failed to load {schema_name}: {e}")

# Load schemas on module import
load_xsd_schemas()

@router.post("/validate")
async def validate_xbrl(
    file: UploadFile = File(...),
    schema_name: str = "voucher",
    current_user: User = Depends(get_current_user)
):
    """Validate an XBRL/XML file against XSD schema"""
    
    if schema_name not in XSD_SCHEMAS:
        raise HTTPException(
            status_code=400, 
            detail=f"Schema '{schema_name}' not found. Available: {list(XSD_SCHEMAS.keys())}"
        )
    
    # Read file content
    content = await file.read()
    
    try:
        # Parse XML
        doc = ET.fromstring(content)
        
        # Validate against schema
        schema = XSD_SCHEMAS[schema_name]
        schema.validate(doc)
        
        return {
            "valid": True,
            "message": "Document is valid according to schema",
            "schema": schema_name
        }
        
    except xmlschema.XMLSchemaException as e:
        return {
            "valid": False,
            "message": "Validation failed",
            "errors": str(e),
            "schema": schema_name
        }
    except ET.XMLSyntaxError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid XML syntax: {str(e)}"
        )

@router.post("/generate")
async def generate_xbrl(
    data: Dict[str, Any],
    template: str = "emissions_report",
    current_user: User = Depends(get_current_user)
):
    """Generate XBRL document from data"""
    
    # This would use your existing XBRL generation logic
    # For now, a simple example:
    
    root = ET.Element("xbrl")
    
    # Add emission data
    for emission in data.get("emissions", []):
        elem = ET.SubElement(root, "emission")
        elem.set("scope", str(emission["scope"]))
        elem.set("amount", str(emission["amount"]))
        elem.set("unit", emission["unit"])
        elem.text = emission.get("description", "")
    
    # Convert to string
    xbrl_string = ET.tostring(root, pretty_print=True, encoding="unicode")
    
    return {
        "xbrl": xbrl_string,
        "template": template
    }


@router.post("/validate")
async def validate_xbrl(file: UploadFile = File(...)):
    """Validate XBRL document against schemas"""
    content = await file.read()
    result = validate_xbrl_document(content)
    return {"valid": result.is_valid, "errors": result.errors}
