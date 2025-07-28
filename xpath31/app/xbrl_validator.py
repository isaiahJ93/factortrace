import os
import sys
from pathlib import Path
from lxml import etree
import json
from typing import Dict, List, Any

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class XBRLSchemaValidator:
    """Validates data against XBRL taxonomy schemas"""
    
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.voucher_schema_path = self.base_path / "voucher-taxonomy-v1.0" / "schemas"
        self.schemas = self._load_schemas()
        
    def _load_schemas(self) -> Dict[str, etree.XMLSchema]:
        """Load all XBRL schemas"""
        schemas = {}
        
        # Load voucher schema
        voucher_xsd = self.voucher_schema_path / "voucher.xsd"
        if voucher_xsd.exists():
            try:
                doc = etree.parse(str(voucher_xsd))
                schemas['voucher'] = etree.XMLSchema(doc)
                print(f"✅ Loaded voucher schema from {voucher_xsd}")
            except Exception as e:
                print(f"❌ Error loading voucher schema: {e}")
        
        # Load calculation linkbase
        calc_xml = self.voucher_schema_path / "voucher-calculation.xml"
        if calc_xml.exists():
            schemas['calculations'] = etree.parse(str(calc_xml))
            print(f"✅ Loaded calculation linkbase from {calc_xml}")
            
        # Load presentation linkbase
        pres_xml = self.voucher_schema_path / "voucher-presentation.xml"
        if pres_xml.exists():
            schemas['presentation'] = etree.parse(str(pres_xml))
            print(f"✅ Loaded presentation linkbase from {pres_xml}")
            
        return schemas
    
    def validate_voucher_code(self, code: str) -> Dict[str, Any]:
        """Validate voucher code against schema"""
        # For now, basic validation
        # TODO: Implement full XSD validation
        
        if len(code) != 16:
            return {
                "valid": False,
                "errors": ["Voucher code must be 16 characters"]
            }
        
        # Check if it matches pattern (alphanumeric)
        if not code.isalnum():
            return {
                "valid": False,
                "errors": ["Voucher code must be alphanumeric"]
            }
        
        return {
            "valid": True,
            "permissions": {
                "maxReports": 10,
                "taxonomyAccess": ["emissions", "financial", "social"],
                "exportFormats": ["pdf", "xlsx", "xbrl", "ixbrl", "json"]
            }
        }
    
    def validate_fact_data(self, fact_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate XBRL fact data against taxonomy"""
        errors = []
        warnings = []
        
        # Validate each fact
        for concept, fact in fact_data.items():
            # Check if concept exists in taxonomy
            if not self._is_valid_concept(concept):
                errors.append({
                    "field": concept,
                    "message": f"Unknown concept: {concept}",
                    "severity": "error"
                })
            
            # Validate data type
            if "value" in fact:
                validation = self._validate_fact_value(concept, fact["value"])
                if not validation["valid"]:
                    errors.append({
                        "field": concept,
                        "message": validation["message"],
                        "severity": "error"
                    })
        
        # Validate calculations
        calc_errors = self._validate_calculations(fact_data)
        errors.extend(calc_errors)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _is_valid_concept(self, concept: str) -> bool:
        """Check if concept exists in taxonomy"""
        # List of valid concepts from your taxonomy
        valid_concepts = [
            "scope1-emissions",
            "scope2-location",
            "scope2-market", 
            "scope3-upstream",
            "scope3-downstream",
            "total-emissions",
            "energy-consumed",
            "renewable-energy",
            "carbon-intensity",
            "emission-reduction-target"
        ]
        return concept in valid_concepts
    
    def _validate_fact_value(self, concept: str, value: Any) -> Dict[str, Any]:
        """Validate fact value against data type"""
        # Numeric concepts
        numeric_concepts = [
            "scope1-emissions", "scope2-location", "scope2-market",
            "scope3-upstream", "scope3-downstream", "total-emissions",
            "energy-consumed", "renewable-energy", "carbon-intensity"
        ]
        
        if concept in numeric_concepts:
            try:
                float_val = float(value)
                if float_val < 0:
                    return {
                        "valid": False,
                        "message": "Emission values cannot be negative"
                    }
                return {"valid": True}
            except ValueError:
                return {
                    "valid": False,
                    "message": f"Value must be numeric for {concept}"
                }
        
        return {"valid": True}
    
    def _validate_calculations(self, fact_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate calculation relationships"""
        errors = []
        
        # Example: Total emissions = Scope 1 + Scope 2 + Scope 3
        scope1 = self._get_numeric_value(fact_data, "scope1-emissions")
        scope2_loc = self._get_numeric_value(fact_data, "scope2-location")
        scope3_up = self._get_numeric_value(fact_data, "scope3-upstream")
        scope3_down = self._get_numeric_value(fact_data, "scope3-downstream")
        total = self._get_numeric_value(fact_data, "total-emissions")
        
        if all(v is not None for v in [scope1, scope2_loc, scope3_up, scope3_down, total]):
            calculated_total = scope1 + scope2_loc + scope3_up + scope3_down
            if abs(calculated_total - total) > 0.01:
                errors.append({
                    "field": "total-emissions",
                    "message": f"Total emissions ({total}) doesn't match sum of scopes ({calculated_total})",
                    "severity": "error"
                })
        
        return errors
    
    def _get_numeric_value(self, fact_data: Dict, concept: str) -> float:
        """Extract numeric value from fact data"""
        if concept in fact_data and "value" in fact_data[concept]:
            try:
                return float(fact_data[concept]["value"])
            except:
                return None
        return None
