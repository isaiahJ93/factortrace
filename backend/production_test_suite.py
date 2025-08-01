#!/usr/bin/env python3
"""Production test suite for iXBRL generation"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work"""
    try:
        from app.api.v1.endpoints.esrs_e1_full import (
            create_enhanced_xbrl_tag,
            create_proper_ixbrl_report
        )
        print("✅ Imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except SyntaxError as e:
        print(f"❌ Syntax error: {e}")
        return False

def test_xbrl_generation():
    """Test XBRL generation"""
    try:
        from app.api.v1.endpoints.esrs_e1_full import create_proper_ixbrl_report
        
        test_data = {
            "company_name": "Production Test Corp",
            "lei": "12345678901234567890",
            "reporting_period": "2024",
            "emissions": {"scope1": 1000, "scope2": 2000, "scope3": 3000}
        }
        
        result = create_proper_ixbrl_report(test_data)
        
        # Basic validation
        assert "<html" in result
        assert "xmlns:ix" in result
        assert "esrs:" in result
        
        print("✅ XBRL generation successful")
        print(f"   Generated {len(result)} characters")
        
        # Save output
        with open("production_test.xhtml", "w") as f:
            f.write(result)
        print("✅ Saved to production_test.xhtml")
        
        return True
    except Exception as e:
        print(f"❌ Generation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 PRODUCTION TEST SUITE")
    print("=" * 40)
    
    if test_imports() and test_xbrl_generation():
        print("\n✅ ALL TESTS PASSED - READY FOR PRODUCTION!")
    else:
        print("\n❌ Tests failed - check errors above")

if __name__ == "__main__":
    main()
