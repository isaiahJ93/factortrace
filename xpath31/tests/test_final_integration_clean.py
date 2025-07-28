# tests/test_final_integration.py - Final integration tests
"""Integration tests validating all components work together."""
import pytest
from pathlib import Path
import tempfile
import json
import subprocess
import os
from datetime import datetime
from lxml import etree

from xpath31.validator import XBRLValidator
from xpath31.crypto.production_signer import ProductionSigner
from xpath31.compliance.filing_rules import UnitHarmonizationRule, WhitespaceNormalizationRule

class TestFinalIntegration:
    """Test complete system integration."""
    
    @pytest.fixture
    def sample_filing_with_issues(self):
        """Create filing with various issues to fix."""
        return """<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns="http://www.w3.org/1999/xhtml" 
              xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"
              xmlns:xbrli="http://www.xbrl.org/2003/instance">
        <head>
            <title>Test Filing with Issues</title>
        </head>
        <body>
            <!-- Mixed units issue -->
            <xbrli:unit id="tCO2e">
                <xbrli:measure>unit:tCO2e</xbrli:measure>
            </xbrli:unit>
            <xbrli:unit id="kgCO2e">
                <xbrli:measure>unit:kgCO2e</xbrli:measure>
            </xbrli:unit>
            
            <div>
                <ix:nonFraction name="esrs-e1:GHGEmissionsScope3Cat01" 
                               contextRef="current" unitRef="tCO2e">1000</ix:nonFraction>
                <ix:nonFraction name="esrs-e1:GHGEmissionsScope3Cat02" 
                               contextRef="current" unitRef="kgCO2e">500000</ix:nonFraction>
                <ix:nonFraction name="esrs-e1:GHGEmissionsScope3Cat03" 
                               contextRef="current" unitRef="tCO2e">2000</ix:nonFraction>
                               
                <!-- Unicode whitespace issue (NBSP) -->
                <ix:nonFraction name="esrs-e1:Revenue" 
                               contextRef="current" unitRef="EUR">1 234 567</ix:nonFraction>
            </div>
        </body>
        </html>""".replace(' ', '\u00A0')  # Replace space with NBSP in revenue
        
    def test_complete_validation_flow(self, sample_filing_with_issues):
        """Test complete validation workflow."""
        validator = XBRLValidator()
        
        # Validate
        results = validator.validate(sample_filing_with_issues.encode('utf-8'))
        
        # Should find both issues
        errors = [r for r in results['validation_results'] if r['severity'] == 'ERROR']
        assert len(errors) >= 2
        
        # Check unit harmonization error
        unit_errors = [e for e in errors if e['rule_id'] == 'UNIT.02']
        assert len(unit_errors) >= 1
        assert 'suggested_value' in unit_errors[0]['context']
        assert unit_errors[0]['context']['suggested_value'] == 500.0  # 500000 kg = 500 t
        
        # Check whitespace error
        ws_errors = [e for e in errors if e['rule_id'] == 'WHITESPACE.01']
        assert len(ws_errors) >= 1
        assert 'normalized_value' in ws_errors[0]['context']
        
    def test_auto_fix_generation(self, sample_filing_with_issues):
        """Test auto-fix generation for issues."""
        doc = etree.fromstring(sample_filing_with_issues.encode('utf-8'))
        
        # Test unit harmonization auto-fix
        unit_rule = UnitHarmonizationRule()
        xslt_fix = unit_rule.generate_auto_fix(doc)
        assert xslt_fix is not None
        assert 'GHGEmissionsScope3Cat02' in xslt_fix
        assert '500.00' in xslt_fix  # Converted value
        
        # Test whitespace auto-fix
        ws_rule = WhitespaceNormalizationRule()
        sed_fix = ws_rule.generate_auto_fix(doc)
        assert sed_fix is not None
        assert '\\240' in sed_fix  # Octal for NBSP
        
    def test_cli_integration(self, tmp_path):
        """Test CLI commands work correctly."""
        # Write test filing
        test_file = tmp_path / "test.xhtml"
        test_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
            <body>
                <ix:nonFraction name="test:Revenue" contextRef="c1">1000000</ix:nonFraction>
            </body>
        </html>""")
        
        # Test validation command
        result = subprocess.run(
            ["xpath31", "validate", str(test_file), "-o", "json"],
            capture_output=True,
            text=True
        )
        
        # Should succeed (no major errors in simple filing)
        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert 'validation_results' in output
        
        # Test quantum-plan command
        result = subprocess.run(
            ["xpath31", "quantum-plan", "--json"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        plan = json.loads(result.stdout)
        assert plan['migration_path'] == 'dilithium2-rsa-hybrid'
        assert plan['implementation_status']['placeholder_removed'] is True
        
    def test_signing_with_validation(self, tmp_path):
        """Test signing workflow with validation."""
        # Create test filing
        filing_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
            <body>
                <ix:nonFraction name="esrs-e1:Revenue">1000000</ix:nonFraction>
            </body>
        </html>"""
        
        # Validate first
        validator = XBRLValidator()
        results = validator.validate(filing_content)
        
        # Only sign if valid
        if results['statistics'].get('errors', 0) == 0:
            os.environ['DEVELOPMENT_MODE'] = 'true'
            
            try:
                signer = ProductionSigner()
                
                metadata = {
                    'validation_results': results['statistics'],
                    'validated_at': datetime.utcnow().isoformat()
                }
                
                signature = signer.sign_filing(filing_content, metadata)
                
                # Verify signature structure
                assert signature['algorithm'] == 'rsa-pss-sha256'
                assert signature['timestamp_token_format'] == 'RFC3161_DER'
                assert signature['timestamp_message_imprint'] is not None
                assert signature['quantum_ready'] is False
                
                # Save signature
                sig_file = tmp_path / "signature.json"
                with open(sig_file, 'w') as f:
                    json.dump(signature, f, indent=2)
                    
                assert sig_file.exists()
                
            finally:
                os.environ.pop('DEVELOPMENT_MODE', None)
                
    def test_certificate_info_display(self):
        """Test certificate information display."""
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        try:
            signer = ProductionSigner()
            info = signer.get_certificate_info()
            
            # Development mode info
            assert info['status'] == "No certificate loaded (development mode)"
            
        finally:
            os.environ.pop('DEVELOPMENT_MODE', None)
            
    @pytest.mark.integration
    def test_full_production_simulation(self, tmp_path):
        """Simulate full production workflow."""
        # 1. Create filing
        filing = tmp_path / "q4-2024.xhtml"
        filing.write_bytes(b"""<?xml version="1.0" encoding="UTF-8"?>
        <html xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
            <head><title>Q4 2024 ESRS Report</title></head>
            <body>
                <ix:nonFraction name="esrs-e1:GHGEmissionsScope1" 
                               contextRef="2024Q4" unitRef="tCO2e">5000</ix:nonFraction>
                <ix:nonFraction name="esrs-e1:GHGEmissionsScope2" 
                               contextRef="2024Q4" unitRef="tCO2e">3000</ix:nonFraction>
                <ix:nonFraction name="esrs-e1:GHGEmissionsScope3Total" 
                               contextRef="2024Q4" unitRef="tCO2e">12000</ix:nonFraction>
            </body>
        </html>""")
        
        # 2. Validate
        validator = XBRLValidator()
        with open(filing, 'rb') as f:
            results = validator.validate(f.read())
            
        assert results['statistics'].get('errors', 0) == 0
        
        # 3. Sign (would use real keys in production)
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        try:
            signer = ProductionSigner()
            
            with open(filing, 'rb') as f:
                signature = signer.sign_filing(
                    f.read(),
                    metadata={
                        'report_period': '2024-Q4',
                        'entity': 'Test Corp',
                        'validation_status': 'passed'
                    }
                )
                
            # 4. Save signature package
            sig_package = tmp_path / "q4-2024-signature.json"
            with open(sig_package, 'w') as f:
                json.dump(signature, f, indent=2)
                
            # 5. Create submission package
            submission = {
                'filing': str(filing),
                'signature': str(sig_package),
                'metadata': {
                    'submitted_at': datetime.utcnow().isoformat(),
                    'submission_type': 'quarterly',
                    'taxonomy_version': 'esrs_v1.0'
                }
            }
            
            submission_file = tmp_path / "submission.json"
            with open(submission_file, 'w') as f:
                json.dump(submission, f, indent=2)
                
            # Verify all artifacts created
            assert filing.exists()
            assert sig_package.exists()
            assert submission_file.exists()
            
        finally:
            os.environ.pop('DEVELOPMENT_MODE', None)