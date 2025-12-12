# tests/test_wizard.py
"""
Self-Serve Compliance Wizard Tests.

Tests for the "€500 magic moment" - voucher to compliance report in 10 minutes.

Tests cover:
1. Session management (create, update, list, abandon)
2. Company profile and activity data collection
3. Emissions calculation
4. Industry templates and smart defaults
5. Multi-tenant isolation (CRITICAL)
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.models.voucher import Voucher, VoucherStatus
from app.models.wizard import ComplianceWizardSession, IndustryTemplate, WizardStatus
from app.models.emission_factor import EmissionFactor


# =============================================================================
# WIZARD FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def valid_voucher_a(db_session: Session, tenant_a: Tenant) -> Voucher:
    """Create a valid voucher for Tenant A wizard testing."""
    voucher = Voucher(
        tenant_id=tenant_a.id,
        code="WIZARD-TEST-A-001",
        valid_until=datetime.utcnow() + timedelta(days=90),
        status=VoucherStatus.VALID,
        is_used=False,
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


@pytest.fixture(scope="function")
def valid_voucher_b(db_session: Session, tenant_b: Tenant) -> Voucher:
    """Create a valid voucher for Tenant B wizard testing."""
    voucher = Voucher(
        tenant_id=tenant_b.id,
        code="WIZARD-TEST-B-001",
        valid_until=datetime.utcnow() + timedelta(days=90),
        status=VoucherStatus.VALID,
        is_used=False,
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


@pytest.fixture(scope="function")
def expired_voucher(db_session: Session, tenant_a: Tenant) -> Voucher:
    """Create an expired voucher for testing."""
    voucher = Voucher(
        tenant_id=tenant_a.id,
        code="WIZARD-EXPIRED-001",
        valid_until=datetime.utcnow() - timedelta(days=1),  # Expired
        status=VoucherStatus.VALID,
        is_used=False,
    )
    db_session.add(voucher)
    db_session.commit()
    db_session.refresh(voucher)
    return voucher


@pytest.fixture(scope="function")
def industry_template(db_session: Session) -> IndustryTemplate:
    """Create an industry template for testing."""
    template = IndustryTemplate(
        id="test_manufacturing",
        name="Test Manufacturing Template",
        nace_codes=["C10", "C11", "C12"],
        description="Test template for manufacturing",
        company_size="small",
        activity_categories=[
            "electricity_kwh",
            "natural_gas_m3",
            "diesel_l",
            "waste_kg",
        ],
        smart_defaults={
            "electricity_kwh": 75000,
            "natural_gas_m3": 5000,
            "diesel_l": 2000,
            "waste_kg": 15000,
        },
        recommended_datasets={
            "scope1": "DEFRA_2024",
            "scope2": "DEFRA_2024",
            "scope3": "EXIOBASE_2020",
        },
        display_order=10,
        is_active=1,
    )
    db_session.add(template)
    db_session.commit()
    db_session.refresh(template)
    return template


@pytest.fixture(scope="function")
def wizard_session_a(db_session: Session, tenant_a: Tenant) -> ComplianceWizardSession:
    """Create a wizard session for Tenant A."""
    session = ComplianceWizardSession(
        tenant_id=tenant_a.id,
        status=WizardStatus.DRAFT,
        current_step="company_profile",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture(scope="function")
def wizard_session_b(db_session: Session, tenant_b: Tenant) -> ComplianceWizardSession:
    """Create a wizard session for Tenant B."""
    session = ComplianceWizardSession(
        tenant_id=tenant_b.id,
        status=WizardStatus.DRAFT,
        current_step="company_profile",
    )
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)
    return session


@pytest.fixture(scope="function")
def test_emission_factors(db_session: Session):
    """Create test emission factors for calculations."""
    factors = [
        # Scope 2 - Electricity
        EmissionFactor(
            scope="SCOPE_2",
            category="electricity",
            activity_type="Electricity - Grid Average",
            country_code="GB",
            year=2024,
            factor=0.207,  # kgCO2e/kWh
            unit="kgCO2e/kWh",
            source="DEFRA_2024",
            method="average_data",
        ),
        EmissionFactor(
            scope="SCOPE_2",
            category="electricity",
            activity_type="Electricity - Grid Average",
            country_code="GLOBAL",
            year=2024,
            factor=0.420,  # kgCO2e/kWh
            unit="kgCO2e/kWh",
            source="DEFRA_2024",
            method="average_data",
        ),
        # Scope 1 - Natural Gas
        EmissionFactor(
            scope="SCOPE_1",
            category="fuels",
            activity_type="Natural Gas",
            country_code="GLOBAL",
            year=2024,
            factor=2.02,  # kgCO2e/m3
            unit="kgCO2e/m3",
            source="DEFRA_2024",
            method="average_data",
        ),
        # Scope 1 - Diesel
        EmissionFactor(
            scope="SCOPE_1",
            category="fuels",
            activity_type="Diesel",
            country_code="GLOBAL",
            year=2024,
            factor=2.51,  # kgCO2e/litre
            unit="kgCO2e/litre",
            source="DEFRA_2024",
            method="average_data",
        ),
        # Scope 3 - Waste
        EmissionFactor(
            scope="SCOPE_3",
            category="waste",
            activity_type="Waste - General",
            country_code="GLOBAL",
            year=2024,
            factor=0.58,  # kgCO2e/kg
            unit="kgCO2e/kg",
            source="DEFRA_2024",
            method="average_data",
        ),
    ]
    for f in factors:
        db_session.add(f)
    db_session.commit()
    return factors


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================

class TestWizardSessionManagement:
    """Tests for wizard session CRUD operations."""

    def test_create_session_without_voucher(
        self, client_a: TestClient, tenant_a: Tenant
    ):
        """Test creating a wizard session without a voucher."""
        response = client_a.post(
            "/api/v1/wizard/sessions",
            json={}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tenant_id"] == tenant_a.id
        assert data["status"] == "draft"
        assert data["current_step"] == "company_profile"
        assert data["voucher_id"] is None

    def test_create_session_with_valid_voucher(
        self, client_a: TestClient, tenant_a: Tenant, valid_voucher_a: Voucher
    ):
        """Test creating a wizard session with a valid voucher."""
        response = client_a.post(
            "/api/v1/wizard/sessions",
            json={"voucher_code": valid_voucher_a.code}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["tenant_id"] == tenant_a.id
        assert data["voucher_id"] == valid_voucher_a.id

    def test_create_session_with_invalid_voucher(
        self, client_a: TestClient
    ):
        """Test creating a session with an invalid voucher code."""
        response = client_a.post(
            "/api/v1/wizard/sessions",
            json={"voucher_code": "INVALID-VOUCHER-CODE"}
        )
        assert response.status_code == 400
        assert "Invalid or expired voucher" in response.json()["detail"]

    def test_create_session_with_expired_voucher(
        self, client_a: TestClient, expired_voucher: Voucher
    ):
        """Test creating a session with an expired voucher."""
        response = client_a.post(
            "/api/v1/wizard/sessions",
            json={"voucher_code": expired_voucher.code}
        )
        assert response.status_code == 400

    def test_create_session_with_template(
        self, client_a: TestClient, industry_template: IndustryTemplate
    ):
        """Test creating a session with an industry template."""
        response = client_a.post(
            "/api/v1/wizard/sessions",
            json={"template_id": industry_template.id}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["template_id"] == industry_template.id
        # Template should pre-populate activity data
        assert data["activity_data"] is not None
        assert data["activity_data"]["electricity_kwh"] == 75000

    def test_list_sessions(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test listing wizard sessions."""
        response = client_a.get("/api/v1/wizard/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        session_ids = [s["id"] for s in data]
        assert wizard_session_a.id in session_ids

    def test_get_session(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test getting a specific session."""
        response = client_a.get(f"/api/v1/wizard/sessions/{wizard_session_a.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == wizard_session_a.id

    def test_abandon_session(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test abandoning a wizard session."""
        response = client_a.delete(f"/api/v1/wizard/sessions/{wizard_session_a.id}")
        assert response.status_code == 204


# =============================================================================
# COMPANY PROFILE TESTS
# =============================================================================

class TestCompanyProfile:
    """Tests for company profile collection (Step 1)."""

    def test_update_company_profile(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test updating company profile."""
        profile = {
            "name": "Test Manufacturing Co",
            "country": "GB",
            "industry_nace": "C10.1",
            "employees": 50,
            "annual_revenue_eur": 5000000,
            "reporting_year": 2024,
            "contact_email": "test@example.com",
        }
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/company-profile",
            json=profile
        )
        assert response.status_code == 200
        data = response.json()
        assert data["company_profile"]["name"] == "Test Manufacturing Co"
        assert data["company_profile"]["country"] == "GB"
        assert data["current_step"] == "activity_data"

    def test_company_profile_validates_country(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test that country code is validated."""
        profile = {
            "name": "Test Co",
            "country": "INVALID",  # Invalid country code
            "reporting_year": 2024,
        }
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/company-profile",
            json=profile
        )
        assert response.status_code == 422

    def test_company_profile_validates_nace(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test that NACE code is validated."""
        profile = {
            "name": "Test Co",
            "country": "GB",
            "industry_nace": "INVALID",  # Invalid NACE format
            "reporting_year": 2024,
        }
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/company-profile",
            json=profile
        )
        assert response.status_code == 422


# =============================================================================
# ACTIVITY DATA TESTS
# =============================================================================

class TestActivityData:
    """Tests for activity data collection (Step 2)."""

    def test_update_activity_data(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test updating activity data."""
        activity = {
            "electricity_kwh": 100000,
            "natural_gas_m3": 5000,
            "diesel_l": 2000,
            "waste_kg": 10000,
        }
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/activity-data",
            json=activity
        )
        assert response.status_code == 200
        data = response.json()
        assert data["activity_data"]["electricity_kwh"] == 100000
        assert data["current_step"] == "calculate"

    def test_activity_data_allows_partial(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test that partial activity data is allowed."""
        activity = {
            "electricity_kwh": 50000,
        }
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/activity-data",
            json=activity
        )
        assert response.status_code == 200

    def test_activity_data_validates_non_negative(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test that negative values are rejected."""
        activity = {
            "electricity_kwh": -100,  # Invalid negative
        }
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/activity-data",
            json=activity
        )
        assert response.status_code == 422


# =============================================================================
# EMISSIONS CALCULATION TESTS
# =============================================================================

class TestEmissionsCalculation:
    """Tests for emissions calculation."""

    def test_calculate_emissions(
        self,
        client_a: TestClient,
        db_session: Session,
        wizard_session_a: ComplianceWizardSession,
        test_emission_factors,
    ):
        """Test emissions calculation."""
        # First set up company profile
        wizard_session_a.company_profile = {
            "name": "Test Co",
            "country": "GB",
            "reporting_year": 2024,
        }
        wizard_session_a.activity_data = {
            "electricity_kwh": 100000,  # Should use 0.207 factor
            "natural_gas_m3": 5000,  # Should use 2.02 factor
        }
        db_session.commit()

        response = client_a.post(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/calculate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["emissions"] is not None

        # Verify calculations:
        # Electricity: 100,000 kWh * 0.207 = 20,700 kgCO2e = 20.7 tCO2e
        # Natural Gas: 5,000 m3 * 2.02 = 10,100 kgCO2e = 10.1 tCO2e
        emissions = data["emissions"]
        assert emissions["scope2_tco2e"] > 0
        assert emissions["scope1_tco2e"] > 0
        assert emissions["total_tco2e"] > 0

    def test_calculate_emissions_no_data(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test calculation with no activity data."""
        response = client_a.post(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/calculate"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "No activity data" in data["errors"][0]


# =============================================================================
# INDUSTRY TEMPLATES TESTS
# =============================================================================

class TestIndustryTemplates:
    """Tests for industry templates."""

    def test_list_templates(
        self, client_a: TestClient, industry_template: IndustryTemplate
    ):
        """Test listing industry templates."""
        response = client_a.get("/api/v1/wizard/templates")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        template_ids = [t["id"] for t in data]
        assert industry_template.id in template_ids

    def test_get_template(
        self, client_a: TestClient, industry_template: IndustryTemplate
    ):
        """Test getting a specific template."""
        response = client_a.get(f"/api/v1/wizard/templates/{industry_template.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == industry_template.id
        assert data["name"] == industry_template.name

    def test_filter_templates_by_size(
        self, client_a: TestClient, industry_template: IndustryTemplate
    ):
        """Test filtering templates by company size."""
        response = client_a.get("/api/v1/wizard/templates?company_size=small")
        assert response.status_code == 200
        data = response.json()
        for template in data:
            assert template["company_size"] == "small"


# =============================================================================
# SMART DEFAULTS TESTS
# =============================================================================

class TestSmartDefaults:
    """Tests for smart defaults calculation."""

    def test_smart_defaults_by_employees(
        self, client_a: TestClient
    ):
        """Test smart defaults based on employee count."""
        response = client_a.post(
            "/api/v1/wizard/smart-defaults",
            json={
                "country": "GB",
                "employees": 50,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "defaults" in data
        assert "electricity_kwh" in data["defaults"]
        # 50 employees * 2500 kWh = 125,000 kWh
        assert data["defaults"]["electricity_kwh"] == 125000

    def test_smart_defaults_with_template(
        self, client_a: TestClient, industry_template: IndustryTemplate
    ):
        """Test smart defaults from template."""
        response = client_a.post(
            "/api/v1/wizard/smart-defaults",
            json={
                "country": "GB",
                "template_id": industry_template.id,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["confidence"] == "high"
        # Should use template defaults
        assert data["defaults"]["electricity_kwh"] == 75000


# =============================================================================
# MULTI-TENANT ISOLATION TESTS (CRITICAL)
# =============================================================================

class TestWizardTenantIsolation:
    """Critical tests for multi-tenant isolation."""

    def test_tenant_cannot_access_other_tenant_session(
        self,
        client_a: TestClient,
        client_b: TestClient,
        wizard_session_a: ComplianceWizardSession,
        wizard_session_b: ComplianceWizardSession,
    ):
        """Test that Tenant A cannot access Tenant B's sessions."""
        # Tenant A tries to access Tenant B's session
        response = client_a.get(f"/api/v1/wizard/sessions/{wizard_session_b.id}")
        assert response.status_code == 404  # Returns 404, not 403 (no enumeration)

        # Tenant B tries to access Tenant A's session
        response = client_b.get(f"/api/v1/wizard/sessions/{wizard_session_a.id}")
        assert response.status_code == 404

    def test_tenant_cannot_update_other_tenant_session(
        self,
        client_a: TestClient,
        wizard_session_b: ComplianceWizardSession,
    ):
        """Test that Tenant A cannot update Tenant B's session."""
        response = client_a.put(
            f"/api/v1/wizard/sessions/{wizard_session_b.id}/company-profile",
            json={
                "name": "Hacked Company",
                "country": "GB",
                "reporting_year": 2024,
            }
        )
        assert response.status_code == 404

    def test_tenant_cannot_delete_other_tenant_session(
        self,
        client_a: TestClient,
        wizard_session_b: ComplianceWizardSession,
    ):
        """Test that Tenant A cannot delete Tenant B's session."""
        response = client_a.delete(f"/api/v1/wizard/sessions/{wizard_session_b.id}")
        assert response.status_code == 404

    def test_list_sessions_only_returns_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        tenant_a: Tenant,
        tenant_b: Tenant,
        wizard_session_a: ComplianceWizardSession,
        wizard_session_b: ComplianceWizardSession,
    ):
        """Test that listing sessions only returns own tenant's sessions."""
        # Client A should only see session A
        response = client_a.get("/api/v1/wizard/sessions")
        assert response.status_code == 200
        data = response.json()
        for session in data:
            assert session["tenant_id"] == tenant_a.id

        # Client B should only see session B
        response = client_b.get("/api/v1/wizard/sessions")
        assert response.status_code == 200
        data = response.json()
        for session in data:
            assert session["tenant_id"] == tenant_b.id

    def test_tenant_cannot_use_other_tenant_voucher(
        self,
        client_a: TestClient,
        valid_voucher_b: Voucher,
    ):
        """Test that Tenant A cannot use Tenant B's voucher."""
        response = client_a.post(
            "/api/v1/wizard/sessions",
            json={"voucher_code": valid_voucher_b.code}
        )
        assert response.status_code == 400
        assert "Invalid or expired voucher" in response.json()["detail"]


# =============================================================================
# REPORT GENERATION TESTS
# =============================================================================

class TestReportGeneration:
    """Tests for report generation."""

    def test_generate_report_requires_emissions(
        self, client_a: TestClient, wizard_session_a: ComplianceWizardSession
    ):
        """Test that report generation requires calculated emissions."""
        response = client_a.post(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/generate-report",
            json={
                "format": "pdf",
                "include_methodology": True,
                "include_breakdown": True,
            }
        )
        assert response.status_code == 400
        assert "must be calculated" in response.json()["detail"]

    def test_generate_report_with_emissions(
        self,
        client_a: TestClient,
        db_session: Session,
        wizard_session_a: ComplianceWizardSession,
    ):
        """Test generating a report after emissions are calculated."""
        # Set up the session with calculated emissions
        wizard_session_a.company_profile = {
            "name": "Test Co",
            "country": "GB",
            "reporting_year": 2024,
        }
        wizard_session_a.activity_data = {
            "electricity_kwh": 100000,
        }
        wizard_session_a.calculated_emissions = {
            "scope1_tco2e": 0,
            "scope2_tco2e": 20.7,
            "scope3_tco2e": 0,
            "total_tco2e": 20.7,
            "breakdown": [],
        }
        db_session.commit()

        response = client_a.post(
            f"/api/v1/wizard/sessions/{wizard_session_a.id}/generate-report",
            json={
                "format": "pdf",
                "include_methodology": True,
                "include_breakdown": True,
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["format"] == "pdf"
