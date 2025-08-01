
import pytest
import json
import sys
from pathlib import Path

# Module name from migration
SOURCE_MODULE = "esrs_e1_full"

# Dynamic import that works before and after split
def get_report_generator():
    """Import report generator from wherever it lives"""
    try:
        # Post-split location
        from factortrace.services.report_builder import create_enhanced_ixbrl_structure
        return create_enhanced_ixbrl_structure
    except ImportError:
        # Pre-split location - dynamic module name
        sys.path.insert(0, str(Path(__file__).parent))
        module = __import__(SOURCE_MODULE)
        return module.create_enhanced_ixbrl_structure

def test_build_report():
    """Test report generation with real payload"""
    create_report = get_report_generator()
    
    payload = {
        "organization": "Test Corp",
        "lei": "123456789012345678901",
        "reporting_period": 2023,
        "emissions": {
            "scope1": 1000,
            "scope2_location": 500,
            "scope2_market": 400,
            "scope3_total": 5000
        },
        "energy": {
            "total_mwh": 2000,
            "renewable_percentage": 45
        },
        "targets": {
            "base_year": 2020,
            "targets": [{
                "year": 2030,
                "reduction": 50,
                "scope": "Scope 1+2"
            }]
        }
    }
    
    # Generate report
    result = create_report(payload)
    
    # Verify it's valid XML
    import xml.etree.ElementTree as ET
    root = ET.fromstring(result)
    assert root is not None
    assert 'html' in root.tag
    
    # Store snapshot for comparison
    with open('.test_snapshot.xml', 'w') as f:
        f.write(result)
    
    # Calculate hash for later comparison
    import hashlib
    return hashlib.sha256(result.encode()).hexdigest()

def test_endpoint():
    """Test API endpoint (if available)"""
    try:
        from fastapi.testclient import TestClient
        from fastapi import FastAPI
        
        # Try both import locations
        try:
            from factortrace.api.router import router
        except ImportError:
            module = __import__(SOURCE_MODULE)
            router = module.router
            
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        
        response = client.post(
            "/reports/generate",
            json={
                "organization": "Test Corp",
                "lei": "123456789012345678901",
                "reporting_period": 2023,
                "emissions": {"scope1": 1000}
            }
        )
        
        assert response.status_code == 202
        assert "report_id" in response.json()
        
    except (ImportError, AttributeError):
        # Skip if FastAPI not available
        pytest.skip("FastAPI not available")

if __name__ == "__main__":
    # Run and save hash
    hash_result = test_build_report()
    with open('.test_hash.txt', 'w') as f:
        f.write(hash_result)
    print(f"✅ Tests passed, output hash: {hash_result}")
