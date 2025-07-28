#!/usr/bin/env python3
"""Verify XPath31 installation."""

def verify_installation():
    print("🔍 Verifying XPath31 Installation...\n")
    
    # Check imports
    try:
        from xpath31 import XBRLValidator, ProductionSigner
        print("✅ Core imports successful")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
        
    # Check crypto
    try:
        from xpath31.crypto.ocsp_validator import OCSPValidator
        print("✅ Crypto modules loaded")
    except ImportError as e:
        print(f"❌ Crypto import error: {e}")
        
    # Check rules
    try:
        from xpath31.compliance.filing_rules import DEFAULT_RULES
        print(f"✅ Loaded {len(DEFAULT_RULES)} validation rules")
    except ImportError as e:
        print(f"❌ Rules import error: {e}")
        
    # Test basic validation
    try:
        validator = XBRLValidator()
        test_doc = b'<html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"><body></body></html>'
        result = validator.validate(test_doc)
        print(f"✅ Basic validation works: {result['statistics']}")
    except Exception as e:
        print(f"❌ Validation error: {e}")
        
    # Test development mode signing
    try:
        import os
        os.environ['DEVELOPMENT_MODE'] = 'true'
        signer = ProductionSigner()
        print("✅ Development mode signing available")
        os.environ.pop('DEVELOPMENT_MODE')
    except Exception as e:
        print(f"❌ Signing error: {e}")
        
    print("\n🎉 Setup verification complete!")
    
if __name__ == "__main__":
    verify_installation()