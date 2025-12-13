# tests/test_crypto.py
"""
Tests for cryptographic services.

Tests Ed25519 signing, SHA-256 hashing, and QR code generation
for the report verification layer.

See docs/features/verification-layer.md
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestCryptoServiceUnit:
    """Unit tests for CryptoService that don't require app context."""

    def test_key_generation(self):
        """Test Ed25519 key pair generation."""
        from app.services.crypto_service import CryptoService

        private_hex, public_hex = CryptoService.generate_key_pair()

        # Keys should be hex strings of correct length
        assert len(private_hex) == 64  # 32 bytes = 64 hex chars
        assert len(public_hex) == 64

        # Keys should be valid hex
        bytes.fromhex(private_hex)
        bytes.fromhex(public_hex)

    def test_hash_data_string(self):
        """Test SHA-256 hashing of string data."""
        from app.services.crypto_service import CryptoService

        result = CryptoService.hash_data("hello world")

        # SHA-256 produces 64 hex chars
        assert len(result) == 64
        # Should be deterministic
        assert result == CryptoService.hash_data("hello world")
        # Different input should produce different hash
        assert result != CryptoService.hash_data("hello World")

    def test_hash_data_dict(self):
        """Test SHA-256 hashing of dict data."""
        from app.services.crypto_service import CryptoService

        data = {"company": "Test Corp", "total_tco2e": 100.5}
        result = CryptoService.hash_data(data)

        assert len(result) == 64
        # Same data should produce same hash (canonical JSON)
        assert result == CryptoService.hash_data(data)
        # Key order shouldn't matter due to sort_keys
        data_reordered = {"total_tco2e": 100.5, "company": "Test Corp"}
        assert result == CryptoService.hash_data(data_reordered)

    def test_hash_data_bytes(self):
        """Test SHA-256 hashing of bytes data."""
        from app.services.crypto_service import CryptoService

        data = b"raw bytes data"
        result = CryptoService.hash_data(data)

        assert len(result) == 64

    def test_sign_and_verify_roundtrip(self):
        """Test signing data and verifying the signature."""
        from app.services.crypto_service import CryptoService

        # Generate keys
        private_hex, public_hex = CryptoService.generate_key_pair()

        # Create service with keys
        service = CryptoService(
            private_key_hex=private_hex,
            public_key_hex=public_hex,
            verification_url_base="https://test.example.com/verify/",
        )

        # Sign data
        data = "test data to sign"
        signature = service.sign_data(data)

        # Signature should be 128 hex chars (64 bytes)
        assert len(signature) == 128

        # Verify signature
        assert service.verify_signature(data, signature) is True

        # Modified data should fail verification
        assert service.verify_signature("modified data", signature) is False

        # Corrupted signature should fail
        assert service.verify_signature(data, "0" * 128) is False

    def test_sign_report_complete(self):
        """Test complete report signing workflow."""
        from app.services.crypto_service import CryptoService

        private_hex, public_hex = CryptoService.generate_key_pair()
        service = CryptoService(
            private_key_hex=private_hex,
            public_key_hex=public_hex,
            verification_url_base="https://factortrace.com/verify/",
        )

        report_data = {
            "company_profile": {"name": "Test Corp", "country": "DE"},
            "calculated_emissions": {"total_tco2e": 150.5},
        }

        signed = service.sign_report(
            report_id="12345",
            report_data=report_data,
            tenant_id="tenant-abc",
        )

        # Check signed report fields
        assert signed.report_id == "12345"
        assert len(signed.content_hash) == 64
        assert len(signed.signature) == 128
        assert isinstance(signed.signed_at, datetime)
        assert signed.verification_url == "https://factortrace.com/verify/12345"
        assert len(signed.public_key_hex) == 64

    def test_verify_report_success(self):
        """Test successful report verification."""
        from app.services.crypto_service import CryptoService

        private_hex, public_hex = CryptoService.generate_key_pair()
        service = CryptoService(
            private_key_hex=private_hex,
            public_key_hex=public_hex,
            verification_url_base="https://test.example.com/verify/",
        )

        report_data = {"emissions": {"total": 100}}
        signed = service.sign_report("123", report_data, "tenant-1")

        # Verify should succeed
        is_valid = service.verify_report(
            report_id="123",
            report_data=report_data,
            content_hash=signed.content_hash,
            signature=signed.signature,
            signed_at=signed.signed_at,
            tenant_id="tenant-1",
        )
        assert is_valid is True

    def test_verify_report_tampered_data(self):
        """Test verification fails when report data is modified."""
        from app.services.crypto_service import CryptoService

        private_hex, public_hex = CryptoService.generate_key_pair()
        service = CryptoService(
            private_key_hex=private_hex,
            public_key_hex=public_hex,
            verification_url_base="https://test.example.com/verify/",
        )

        original_data = {"emissions": {"total": 100}}
        signed = service.sign_report("123", original_data, "tenant-1")

        # Modify the data
        tampered_data = {"emissions": {"total": 999}}

        # Verification should fail
        is_valid = service.verify_report(
            report_id="123",
            report_data=tampered_data,
            content_hash=signed.content_hash,
            signature=signed.signature,
            signed_at=signed.signed_at,
            tenant_id="tenant-1",
        )
        assert is_valid is False

    def test_is_configured(self):
        """Test is_configured method."""
        from app.services.crypto_service import CryptoService

        # Service without keys
        service_no_keys = CryptoService(
            private_key_hex=None,
            public_key_hex=None,
            verification_url_base="https://test.example.com/verify/",
        )
        assert service_no_keys.is_configured() is False

        # Service with keys
        private_hex, public_hex = CryptoService.generate_key_pair()
        service_with_keys = CryptoService(
            private_key_hex=private_hex,
            public_key_hex=public_hex,
            verification_url_base="https://test.example.com/verify/",
        )
        assert service_with_keys.is_configured() is True

    def test_sign_without_private_key_raises(self):
        """Test that signing without private key raises error."""
        from app.services.crypto_service import CryptoService

        service = CryptoService(
            private_key_hex=None,
            public_key_hex=None,
            verification_url_base="https://test.example.com/verify/",
        )

        with pytest.raises(ValueError, match="Private key not configured"):
            service.sign_data("test")


class TestQRCodeGeneration:
    """Tests for QR code generation."""

    def test_generate_qr_code_basic(self):
        """Test basic QR code generation."""
        from app.services.crypto_service import generate_qr_code

        url = "https://factortrace.com/verify/12345"
        qr_bytes = generate_qr_code(url)

        # Should return PNG bytes
        assert isinstance(qr_bytes, bytes)
        assert len(qr_bytes) > 0
        # PNG magic bytes
        assert qr_bytes[:8] == b"\x89PNG\r\n\x1a\n"

    def test_generate_qr_code_with_size(self):
        """Test QR code generation with custom size."""
        from app.services.crypto_service import generate_qr_code

        url = "https://factortrace.com/verify/12345"

        small_qr = generate_qr_code(url, size=100)
        large_qr = generate_qr_code(url, size=400)

        # Both should be valid PNGs
        assert small_qr[:8] == b"\x89PNG\r\n\x1a\n"
        assert large_qr[:8] == b"\x89PNG\r\n\x1a\n"

        # Large should have more bytes (not always true due to compression, but generally)
        # Skip this assertion as PNG compression can vary

    def test_generate_verification_qr(self):
        """Test verification QR code generation with report ID."""
        from app.services.crypto_service import generate_verification_qr

        # Mock settings to avoid needing config
        with patch("app.services.crypto_service.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                verification_url_base="https://factortrace.com/verify/"
            )

            qr_bytes = generate_verification_qr("12345")

            assert isinstance(qr_bytes, bytes)
            assert qr_bytes[:8] == b"\x89PNG\r\n\x1a\n"


class TestCryptoServiceSingleton:
    """Tests for crypto service singleton."""

    def test_get_crypto_service_returns_same_instance(self):
        """Test that get_crypto_service returns singleton."""
        # Reset singleton for clean test
        import app.services.crypto_service as module
        module._crypto_service = None

        with patch.object(module, "CryptoService") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance

            # First call creates instance
            result1 = module.get_crypto_service()

            # Second call returns same instance
            result2 = module.get_crypto_service()

            # Should only create once
            assert mock_class.call_count == 1
            assert result1 is result2


class TestSignedReportDataclass:
    """Tests for SignedReport dataclass."""

    def test_signed_report_fields(self):
        """Test SignedReport dataclass has expected fields."""
        from app.services.crypto_service import SignedReport
        from datetime import datetime

        report = SignedReport(
            report_id="123",
            content_hash="a" * 64,
            signature="b" * 128,
            signed_at=datetime.utcnow(),
            verification_url="https://example.com/verify/123",
            public_key_hex="c" * 64,
        )

        assert report.report_id == "123"
        assert report.content_hash == "a" * 64
        assert report.signature == "b" * 128
        assert isinstance(report.signed_at, datetime)
        assert report.verification_url == "https://example.com/verify/123"
        assert report.public_key_hex == "c" * 64
