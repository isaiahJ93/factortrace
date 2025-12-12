# tests/test_supplier_portal.py
"""
Tests for Supplier Self-Serve Portal.

Tests the complete supplier flow:
1. Pay (checkout) → 2. Complete wizard → 3. Get report emailed → 4. Download again anytime

Note: Stripe integration tests are mocked since we don't want to hit real Stripe APIs.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, AsyncMock
import json
import uuid

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db, Base, engine
from app.models.tenant import Tenant
from app.models.voucher import Voucher, VoucherStatus
from app.models.payment import Payment
from app.models.wizard import ComplianceWizardSession, WizardStatus, IndustryTemplate


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)

    from sqlalchemy.orm import sessionmaker
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_tenant(db_session):
    """Create a test tenant with unique ID."""
    unique_id = str(uuid.uuid4())[:8]
    tenant = Tenant(
        id=f"supplier-tenant-{unique_id}",
        name="Test Supplier Co",
        slug=f"test-supplier-{unique_id}",
        is_active=True,
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def test_voucher(db_session, test_tenant):
    """Create a test voucher with unique code."""
    unique_id = str(uuid.uuid4())[:8]
    voucher = Voucher(
        tenant_id=test_tenant.id,
        code=f"FT-2024-TEST-{unique_id}",
        company_email="supplier@test.com",
        company_name="Test Supplier Co",
        valid_until=datetime.utcnow() + timedelta(days=365),
        is_used=False,
        status=VoucherStatus.VALID,
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


@pytest.fixture
def completed_wizard_session(db_session, test_tenant, test_voucher):
    """Create a completed wizard session with emissions."""
    # Mark voucher as used
    test_voucher.is_used = True
    test_voucher.status = VoucherStatus.USED
    test_voucher.used_at = datetime.utcnow()

    session = ComplianceWizardSession(
        tenant_id=test_tenant.id,
        voucher_id=test_voucher.id,
        status=WizardStatus.COMPLETED,
        current_step="completed",
        company_profile={
            "name": "Test Supplier Co",
            "country": "DE",
            "reporting_year": 2024,
            "contact_email": "supplier@test.com",
        },
        activity_data={
            "electricity_kwh": 100000,
            "natural_gas_m3": 5000,
        },
        calculated_emissions={
            "scope1_tco2e": 10.5,
            "scope2_tco2e": 45.2,
            "scope3_tco2e": 25.8,
            "total_tco2e": 81.5,
            "methodology_notes": "Calculated using DEFRA 2024",
        },
        completed_at=datetime.utcnow(),
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture
def client(db_session):
    """Create test client with database override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# =============================================================================
# PRODUCT LISTING TESTS (PUBLIC ENDPOINT)
# =============================================================================

class TestPublicEndpoints:
    """Tests for public portal endpoints."""

    def test_list_products(self, client):
        """Test listing available products."""
        response = client.get("/api/v1/portal/products")

        assert response.status_code == 200
        products = response.json()
        assert len(products) >= 1

        # Check CSRD report product exists
        csrd_product = next((p for p in products if p["id"] == "csrd_report"), None)
        assert csrd_product is not None
        assert csrd_product["price_cents"] == 50000
        assert csrd_product["currency"] == "eur"

    def test_checkout_invalid_product(self, client):
        """Test checkout with invalid product fails."""
        response = client.post(
            "/api/v1/portal/checkout",
            json={
                "email": "test@test.com",
                "company_name": "Test Co",
                "product": "invalid_product",
                "success_url": "https://test.com/success",
                "cancel_url": "https://test.com/cancel",
            },
        )

        assert response.status_code == 400
        assert "Unknown product" in response.json()["detail"]


# =============================================================================
# EMAIL SERVICE TESTS
# =============================================================================

class TestEmailService:
    """Tests for email service functionality."""

    @pytest.mark.asyncio
    async def test_send_report_complete_email(self):
        """Test sending report completion email (mocked)."""
        from app.services.email_service import EmailService

        service = EmailService()

        # SendGrid not configured, so it should log and return True
        result = await service.send_report_complete(
            to_email="test@example.com",
            company_name="Test Company",
            total_emissions=100.5,
            scope1_emissions=20.0,
            scope2_emissions=50.0,
            scope3_emissions=30.5,
            pdf_url="https://example.com/report.pdf",
            xbrl_url="https://example.com/report.xbrl",
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_send_voucher_email(self):
        """Test sending voucher email."""
        from app.services.email_service import EmailService

        service = EmailService()

        result = await service.send_voucher_email(
            to_email="test@example.com",
            company_name="Test Company",
            voucher_code="FT-2024-TESTXYZ",
            valid_until=datetime.utcnow() + timedelta(days=365),
        )

        assert result is True


# =============================================================================
# SUPPLIER PORTAL AUTHENTICATED TESTS
# =============================================================================

class TestSupplierPortalAuth:
    """Tests for authenticated supplier portal endpoints."""

    def test_list_my_sessions_with_data(self, client, test_tenant, completed_wizard_session, db_session):
        """Test listing sessions returns correct data."""
        from app.core.auth import get_current_user
        from app.schemas.auth_schemas import CurrentUser

        mock_user = CurrentUser(
            id="user-1",
            email="test@supplier.com",
            tenant_id=test_tenant.id,
            is_active=True,
        )

        def override_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_current_user

        try:
            response = client.get("/api/v1/portal/my-sessions")

            assert response.status_code == 200
            sessions = response.json()
            assert len(sessions) == 1
            assert sessions[0]["status"] == "completed"
            assert sessions[0]["total_tco2e"] == 81.5
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_list_my_reports(self, client, test_tenant, completed_wizard_session, db_session):
        """Test listing completed reports."""
        from app.core.auth import get_current_user
        from app.schemas.auth_schemas import CurrentUser

        mock_user = CurrentUser(
            id="user-1",
            email="test@supplier.com",
            tenant_id=test_tenant.id,
            is_active=True,
        )

        def override_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_current_user

        try:
            response = client.get("/api/v1/portal/my-reports")

            assert response.status_code == 200
            reports = response.json()
            assert len(reports) == 1
            assert reports[0]["total_tco2e"] == 81.5
            assert reports[0]["scope1_tco2e"] == 10.5
            assert reports[0]["pdf_url"] is not None
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_download_report_json(self, client, test_tenant, completed_wizard_session, db_session):
        """Test downloading report as JSON."""
        from app.core.auth import get_current_user
        from app.schemas.auth_schemas import CurrentUser

        mock_user = CurrentUser(
            id="user-1",
            email="test@supplier.com",
            tenant_id=test_tenant.id,
            is_active=True,
        )

        def override_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_current_user

        try:
            response = client.get(
                f"/api/v1/portal/my-reports/{completed_wizard_session.id}/download?format=json"
            )

            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == completed_wizard_session.id
            assert "company_profile" in data
            assert "emissions" in data
            assert data["emissions"]["total_tco2e"] == 81.5
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    def test_download_report_not_found(self, client, test_tenant, db_session):
        """Test downloading non-existent report returns 404."""
        from app.core.auth import get_current_user
        from app.schemas.auth_schemas import CurrentUser

        mock_user = CurrentUser(
            id="user-1",
            email="test@supplier.com",
            tenant_id=test_tenant.id,
            is_active=True,
        )

        def override_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_current_user

        try:
            response = client.get("/api/v1/portal/my-reports/99999/download?format=json")
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)


# =============================================================================
# MULTI-TENANT ISOLATION TESTS
# =============================================================================

class TestMultiTenantIsolation:
    """Tests ensuring tenant isolation is enforced."""

    def test_cannot_access_other_tenant_sessions(self, client, test_tenant, completed_wizard_session, db_session):
        """Verify tenant A cannot see tenant B's sessions."""
        from app.core.auth import get_current_user
        from app.schemas.auth_schemas import CurrentUser

        # Create another tenant with unique ID
        unique_id = str(uuid.uuid4())[:8]
        other_tenant = Tenant(
            id=f"other-tenant-{unique_id}",
            name="Other Supplier",
            slug=f"other-supplier-{unique_id}",
            is_active=True,
        )
        db_session.add(other_tenant)
        db_session.commit()

        # Auth as other tenant
        mock_user = CurrentUser(
            id="user-2",
            email="other@supplier.com",
            tenant_id=other_tenant.id,
            is_active=True,
        )

        def override_current_user():
            return mock_user

        app.dependency_overrides[get_current_user] = override_current_user

        try:
            # Try to list sessions - should be empty
            response = client.get("/api/v1/portal/my-sessions")
            assert response.status_code == 200
            assert response.json() == []

            # Try to download the other tenant's report - should 404
            response = client.get(
                f"/api/v1/portal/my-reports/{completed_wizard_session.id}/download?format=json"
            )
            assert response.status_code == 404
        finally:
            app.dependency_overrides.pop(get_current_user, None)


# =============================================================================
# STRIPE CHECKOUT SERVICE UNIT TESTS
# =============================================================================

class TestStripeCheckoutService:
    """Unit tests for Stripe checkout service functions."""

    def test_products_configured(self):
        """Verify products are properly configured."""
        from app.services.stripe_checkout import PRODUCTS

        assert "csrd_report" in PRODUCTS
        assert PRODUCTS["csrd_report"]["price_cents"] == 50000
        assert PRODUCTS["csrd_report"]["currency"] == "eur"

        assert "csrd_basic" in PRODUCTS
        assert PRODUCTS["csrd_basic"]["price_cents"] == 25000

    def test_voucher_code_generation(self):
        """Test voucher code generation format."""
        from app.services.stripe_checkout import _generate_voucher_code

        code = _generate_voucher_code()
        assert code.startswith("FT-")
        assert len(code) > 10  # Should have year and random part


# =============================================================================
# MODULE IMPORT TESTS
# =============================================================================

class TestModuleImports:
    """Tests to verify all modules can be imported correctly."""

    def test_import_stripe_checkout(self):
        """Test stripe_checkout module imports."""
        from app.services.stripe_checkout import (
            create_checkout_session,
            get_checkout_session_status,
            handle_checkout_complete,
            verify_webhook_signature,
            PRODUCTS,
        )
        assert PRODUCTS is not None

    def test_import_email_service(self):
        """Test email_service module imports."""
        from app.services.email_service import (
            EmailService,
            get_email_service,
            send_report_complete_email,
        )
        assert EmailService is not None

    def test_import_supplier_portal(self):
        """Test supplier_portal endpoint imports."""
        from app.api.v1.endpoints.supplier_portal import router
        assert router is not None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "TestPublicEndpoints",
    "TestEmailService",
    "TestSupplierPortalAuth",
    "TestMultiTenantIsolation",
    "TestStripeCheckoutService",
    "TestModuleImports",
]
