"""Test suite for message imprint and digest validation."""
import pytest
import hashlib

class TestMessageImprint:
    """Test message imprint cross-validation."""
    
    def test_sha256_hashing(self):
        """Test SHA256 hashing."""
        data = b"test data"
        hash_result = hashlib.sha256(data).hexdigest()
        assert len(hash_result) == 64  # SHA256 produces 64 hex chars
        assert hash_result == hashlib.sha256(data).hexdigest()  # Deterministic
        
    def test_message_imprint_format(self):
        """Test message imprint format."""
        test_data = b"Test XBRL content"
        imprint = hashlib.sha256(test_data).digest()
        
        assert len(imprint) == 32  # SHA256 produces 32 bytes
        assert isinstance(imprint, bytes)
        
    def test_hash_consistency(self):
        """Test hash consistency."""
        data1 = b"test"
        data2 = b"test"
        data3 = b"different"
        
        assert hashlib.sha256(data1).digest() == hashlib.sha256(data2).digest()
        assert hashlib.sha256(data1).digest() != hashlib.sha256(data3).digest()
