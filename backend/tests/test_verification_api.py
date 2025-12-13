# tests/test_verification_api.py
"""
Tests for the report verification API endpoints.

Tests the public verification endpoint that validates
signed compliance reports.

See docs/features/verification-layer.md
"""
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from fastapi.testclient import TestClient


class TestVerificationEndpoint:
    """Tests for the /verify/{report_id} endpoint."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def mock_wizard_session(self):
        """Create a mock completed wizard session with signing."""
        session = MagicMock()
        session.id = 123
        session.tenant_id = "tenant-abc"
        session.status = MagicMock()
        session.status.value = "completed"
        session.company_profile = {
            "name": "Test Company",
            "country": "DE",
            "industry_nace": "C25",
        }
        session.activity_data = {
            "electricity_kwh": 50000,
            "natural_gas_m3": 1000,
        }
        session.calculated_emissions = {
            "total_tco2e": 25.5,
            "scope1_tco2e": 5.0,
            "scope2_tco2e": 10.5,
            "scope3_tco2e": 10.0,
            "reporting_period": "2024",
        }
        session.completed_at = datetime(2024, 12, 13, 10, 0, 0)
        session.report_hash = "a" * 64
        session.signature = "b" * 128
        session.signed_at = datetime(2024, 12, 13, 10, 0, 1)
        session.verification_url = "https://factortrace.com/verify/123"
        return session

    def test_verify_report_not_found(self):
        """Test verification returns NOT_FOUND for non-existent report."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db

            client = TestClient(app)
            response = client.get("/verify/99999")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.NOT_FOUND.value
            assert data["report_id"] == "99999"

    def test_verify_report_invalid_id_format(self):
        """Test verification returns NOT_FOUND for invalid ID format."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db:
            mock_get_db.return_value = MagicMock()

            client = TestClient(app)
            response = client.get("/verify/not-a-number")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.NOT_FOUND.value
            assert "Invalid report ID format" in data["message"]

    def test_verify_report_not_signed(self, mock_wizard_session):
        """Test verification returns NOT_SIGNED for unsigned report."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from app.models.wizard import WizardStatus
        from fastapi import FastAPI

        # Remove signature
        mock_wizard_session.report_hash = None
        mock_wizard_session.signature = None
        mock_wizard_session.status = WizardStatus.COMPLETED

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_wizard_session
            mock_get_db.return_value = mock_db

            client = TestClient(app)
            response = client.get("/verify/123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.NOT_SIGNED.value
            assert data["hash_verified"] is False
            assert data["signature_verified"] is False

    def test_verify_report_not_completed(self, mock_wizard_session):
        """Test verification returns NOT_FOUND for incomplete report."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from app.models.wizard import WizardStatus
        from fastapi import FastAPI

        mock_wizard_session.status = WizardStatus.IN_PROGRESS

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_wizard_session
            mock_get_db.return_value = mock_db

            client = TestClient(app)
            response = client.get("/verify/123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.NOT_FOUND.value
            assert "not yet completed" in data["message"]

    def test_verify_report_success(self, mock_wizard_session):
        """Test successful report verification."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from app.models.wizard import WizardStatus
        from fastapi import FastAPI

        mock_wizard_session.status = WizardStatus.COMPLETED

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db, \
             patch("app.api.v1.endpoints.verify.get_crypto_service") as mock_crypto:

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_wizard_session
            mock_get_db.return_value = mock_db

            # Mock crypto service to return valid verification
            mock_service = MagicMock()
            mock_service.verify_report.return_value = True
            mock_service.get_public_key_hex.return_value = "c" * 64
            mock_crypto.return_value = mock_service

            client = TestClient(app)
            response = client.get("/verify/123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.VERIFIED.value
            assert data["hash_verified"] is True
            assert data["signature_verified"] is True
            assert data["company"]["name"] == "Test Company"
            assert data["emissions_summary"]["total_tco2e"] == 25.5

    def test_verify_report_failed_verification(self, mock_wizard_session):
        """Test verification failure (tampered data)."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from app.models.wizard import WizardStatus
        from fastapi import FastAPI

        mock_wizard_session.status = WizardStatus.COMPLETED

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db, \
             patch("app.api.v1.endpoints.verify.get_crypto_service") as mock_crypto:

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_wizard_session
            mock_get_db.return_value = mock_db

            # Mock crypto service to return failed verification
            mock_service = MagicMock()
            mock_service.verify_report.return_value = False
            mock_crypto.return_value = mock_service

            client = TestClient(app)
            response = client.get("/verify/123")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.FAILED.value
            assert data["hash_verified"] is False


class TestVerificationBadge:
    """Tests for the /verify/{report_id}/badge endpoint."""

    def test_badge_verified(self):
        """Test badge returns VERIFIED status."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from app.models.wizard import WizardStatus
        from fastapi import FastAPI

        mock_session = MagicMock()
        mock_session.id = 123
        mock_session.tenant_id = "tenant-abc"
        mock_session.status = WizardStatus.COMPLETED
        mock_session.company_profile = {"name": "Test"}
        mock_session.activity_data = {}
        mock_session.calculated_emissions = {"total_tco2e": 10}
        mock_session.completed_at = datetime.utcnow()
        mock_session.report_hash = "a" * 64
        mock_session.signature = "b" * 128
        mock_session.signed_at = datetime.utcnow()
        mock_session.verification_url = "https://factortrace.com/verify/123"

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db, \
             patch("app.api.v1.endpoints.verify.get_crypto_service") as mock_crypto:

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            mock_get_db.return_value = mock_db

            mock_service = MagicMock()
            mock_service.verify_report.return_value = True
            mock_service.get_public_key_hex.return_value = "c" * 64
            mock_crypto.return_value = mock_service

            client = TestClient(app)
            response = client.get("/verify/123/badge")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.VERIFIED.value
            assert data["badge_text"] == "VERIFIED"
            assert data["color"] == "green"

    def test_badge_not_found(self):
        """Test badge returns NOT_FOUND status."""
        from app.api.v1.endpoints.verify import router, VerificationStatus
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db

            client = TestClient(app)
            response = client.get("/verify/99999/badge")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == VerificationStatus.NOT_FOUND.value
            assert data["badge_text"] == "NOT FOUND"
            assert data["color"] == "red"


class TestVerificationQR:
    """Tests for the /verify/{report_id}/qr endpoint."""

    def test_qr_code_generation(self):
        """Test QR code endpoint returns PNG image."""
        from app.api.v1.endpoints.verify import router
        from app.models.wizard import WizardStatus
        from fastapi import FastAPI

        mock_session = MagicMock()
        mock_session.id = 123
        mock_session.status = WizardStatus.COMPLETED

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db, \
             patch("app.api.v1.endpoints.verify.generate_verification_qr") as mock_qr:

            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_session
            mock_get_db.return_value = mock_db

            # Return fake PNG data
            mock_qr.return_value = b"\x89PNG\r\n\x1a\n" + b"fake png data"

            client = TestClient(app)
            response = client.get("/verify/123/qr")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/png"
            assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    def test_qr_code_not_found(self):
        """Test QR code endpoint returns 404 for non-existent report."""
        from app.api.v1.endpoints.verify import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_db") as mock_get_db:
            mock_db = MagicMock()
            mock_db.query.return_value.filter.return_value.first.return_value = None
            mock_get_db.return_value = mock_db

            client = TestClient(app)
            response = client.get("/verify/99999/qr")

            assert response.status_code == 404


class TestPublicKeyEndpoint:
    """Tests for the /verify/public-key endpoint."""

    def test_get_public_key(self):
        """Test public key endpoint returns key info."""
        from app.api.v1.endpoints.verify import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_crypto_service") as mock_crypto:
            mock_service = MagicMock()
            mock_service.get_public_key_hex.return_value = "d" * 64
            mock_crypto.return_value = mock_service

            client = TestClient(app)
            response = client.get("/verify/public-key")

            assert response.status_code == 200
            data = response.json()
            assert data["algorithm"] == "Ed25519"
            assert data["public_key_hex"] == "d" * 64
            assert "usage" in data

    def test_get_public_key_not_configured(self):
        """Test public key endpoint returns 503 when not configured."""
        from app.api.v1.endpoints.verify import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/verify")

        with patch("app.api.v1.endpoints.verify.get_crypto_service") as mock_crypto:
            mock_service = MagicMock()
            mock_service.get_public_key_hex.return_value = None
            mock_crypto.return_value = mock_service

            client = TestClient(app)
            response = client.get("/verify/public-key")

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"]
