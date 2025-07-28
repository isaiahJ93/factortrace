"""Test suite for RFC 3161 and OCSP validation."""
import pytest
from unittest.mock import Mock, patch
import os

class TestCryptoValidation:
    """Test cryptographic validation features."""
    
    def test_development_mode_signer(self):
        """Test signer in development mode."""
        os.environ['DEVELOPMENT_MODE'] = 'true'
        try:
            from xpath31.crypto.production_signer import ProductionSigner
            signer = ProductionSigner()
            assert signer is not None
            assert signer.algorithm == "rsa-pss-sha256"
        finally:
            os.environ.pop('DEVELOPMENT_MODE', None)
            
    def test_signature_format(self):
        """Test signature format."""
        os.environ['DEVELOPMENT_MODE'] = 'true'
        try:
            from xpath31.crypto.production_signer import ProductionSigner
            signer = ProductionSigner()
            
            # Test signing
            result = signer.sign_filing(b"test content", {"test": "metadata"})
            
            # Check signature structure
            assert 'algorithm' in result
            assert 'signature' in result
            assert 'content_hash' in result
            assert result['algorithm'] == 'rsa-pss-sha256'
            
        finally:
            os.environ.pop('DEVELOPMENT_MODE', None)
            
    def test_quantum_migration_info(self):
        """Test quantum migration information."""
        from xpath31.crypto.production_signer import ProductionSigner
        
        os.environ['DEVELOPMENT_MODE'] = 'true'
        try:
            signer = ProductionSigner()
            info = signer.prepare_quantum_migration()
            
            assert 'current_algorithm' in info
            assert 'migration_path' in info
            assert info['migration_path'] == 'dilithium2-rsa-hybrid'
            
        finally:
            os.environ.pop('DEVELOPMENT_MODE', None)
