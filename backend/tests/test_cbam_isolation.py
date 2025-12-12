# tests/test_cbam_isolation.py
"""
CBAM Cross-Tenant Isolation Security Tests
===========================================
Tests to verify multi-tenant data isolation for CBAM (Carbon Border Adjustment Mechanism).

CRITICAL: These tests verify that:
1. Tenant A cannot see Tenant B's declarations
2. Tenant A cannot see Tenant B's installations
3. Declaration lines are scoped via parent declaration
4. Calculate endpoint respects tenant boundary

Any failure in these tests indicates a critical security vulnerability.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.models.cbam import (
    CBAMDeclaration,
    CBAMDeclarationStatus,
    CBAMInstallation,
    CBAMProductSector,
    CBAMDeclarationLine,
    CBAMProduct,
)


# =============================================================================
# CBAM-SPECIFIC FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def cbam_product(db_session: Session) -> CBAMProduct:
    """Create a shared CBAM product reference (not tenant-owned)."""
    product = CBAMProduct(
        cn_code="72061000",
        description="Iron and non-alloy steel ingots",
        sector=CBAMProductSector.IRON_STEEL,
        unit="tonne",
        is_active=True,
    )
    db_session.add(product)
    db_session.commit()
    db_session.refresh(product)
    return product


@pytest.fixture(scope="function")
def declaration_a(db_session: Session, tenant_a: Tenant, user_a: User) -> CBAMDeclaration:
    """Create a CBAM declaration for Tenant A."""
    declaration = CBAMDeclaration(
        tenant_id=tenant_a.id,
        declaration_reference="CBAM-ALPHA-2024-001",
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        status=CBAMDeclarationStatus.DRAFT,
        importer_name="Alpha Steel Imports Ltd",
        importer_eori="GB123456789000",
        importer_country="GB",
        total_embedded_emissions_tco2e=150.5,
        total_quantity=100.0,
        created_by_user_id=user_a.id,
    )
    db_session.add(declaration)
    db_session.commit()
    db_session.refresh(declaration)
    return declaration


@pytest.fixture(scope="function")
def declaration_b(db_session: Session, tenant_b: Tenant, user_b: User) -> CBAMDeclaration:
    """Create a CBAM declaration for Tenant B."""
    declaration = CBAMDeclaration(
        tenant_id=tenant_b.id,
        declaration_reference="CBAM-BETA-2024-001",
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        status=CBAMDeclarationStatus.SUBMITTED,
        importer_name="Beta Aluminium GmbH",
        importer_eori="DE987654321000",
        importer_country="DE",
        total_embedded_emissions_tco2e=500.0,
        total_quantity=200.0,
        created_by_user_id=user_b.id,
    )
    db_session.add(declaration)
    db_session.commit()
    db_session.refresh(declaration)
    return declaration


@pytest.fixture(scope="function")
def declaration_line_a(
    db_session: Session,
    declaration_a: CBAMDeclaration,
    cbam_product: CBAMProduct,
) -> CBAMDeclarationLine:
    """Create a declaration line for Tenant A's declaration."""
    line = CBAMDeclarationLine(
        declaration_id=declaration_a.id,
        cbam_product_id=cbam_product.id,
        country_of_origin="CN",
        facility_name="Baosteel Works",
        quantity=50.0,
        quantity_unit="tonne",
        embedded_emissions_tco2e=75.25,
        emission_factor_value=1.505,
        emission_factor_unit="tCO2e/tonne",
    )
    db_session.add(line)
    db_session.commit()
    db_session.refresh(line)
    return line


@pytest.fixture(scope="function")
def installation_a(db_session: Session, tenant_a: Tenant) -> CBAMInstallation:
    """Create a CBAM installation for Tenant A."""
    installation = CBAMInstallation(
        tenant_id=tenant_a.id,
        installation_id="CN-BAOSTEEL-001",
        name="Baosteel Shanghai Works",
        country="CN",
        region="Shanghai",
        operator_name="Baosteel Group",
        sector=CBAMProductSector.IRON_STEEL,
        specific_emission_factor=1.505,
        specific_factor_unit="tCO2e/tonne",
        is_verified=True,
        is_active=True,
    )
    db_session.add(installation)
    db_session.commit()
    db_session.refresh(installation)
    return installation


@pytest.fixture(scope="function")
def installation_b(db_session: Session, tenant_b: Tenant) -> CBAMInstallation:
    """Create a CBAM installation for Tenant B."""
    installation = CBAMInstallation(
        tenant_id=tenant_b.id,
        installation_id="RU-RUSAL-001",
        name="RUSAL Krasnoyarsk",
        country="RU",
        region="Krasnoyarsk",
        operator_name="RUSAL",
        sector=CBAMProductSector.ALUMINIUM,
        specific_emission_factor=2.1,
        specific_factor_unit="tCO2e/tonne",
        is_verified=False,
        is_active=True,
    )
    db_session.add(installation)
    db_session.commit()
    db_session.refresh(installation)
    return installation


# =============================================================================
# DECLARATION ISOLATION TESTS
# =============================================================================

class TestCBAMDeclarationTenantIsolation:
    """Test tenant isolation for CBAM declaration endpoints."""

    def test_list_declarations_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        declaration_a: CBAMDeclaration,
        declaration_b: CBAMDeclaration,
    ):
        """
        SECURITY TEST: GET /api/v1/cbam/declarations returns only own tenant's declarations.
        """
        # Tenant A sees only their declarations
        response_a = client_a.get("/api/v1/cbam/declarations")

        if response_a.status_code == status.HTTP_200_OK:
            declarations = response_a.json()
            # Handle both list and paginated responses
            items = declarations if isinstance(declarations, list) else declarations.get("items", declarations)

            declaration_ids = [d.get("id") for d in items]
            assert declaration_a.id in declaration_ids, "Tenant A should see their own declaration"
            assert declaration_b.id not in declaration_ids, "SECURITY: Tenant A sees Tenant B's declaration!"

        # Tenant B sees only their declarations
        response_b = client_b.get("/api/v1/cbam/declarations")

        if response_b.status_code == status.HTTP_200_OK:
            declarations = response_b.json()
            items = declarations if isinstance(declarations, list) else declarations.get("items", declarations)

            declaration_ids = [d.get("id") for d in items]
            assert declaration_b.id in declaration_ids, "Tenant B should see their own declaration"
            assert declaration_a.id not in declaration_ids, "SECURITY: Tenant B sees Tenant A's declaration!"

    def test_get_declaration_by_id_denies_cross_tenant(
        self,
        client_a: TestClient,
        declaration_b: CBAMDeclaration,
    ):
        """
        SECURITY TEST: GET /api/v1/cbam/declarations/{id} denies access to other tenant's declaration.
        """
        response = client_a.get(f"/api/v1/cbam/declarations/{declaration_b.id}")

        # Should return 404, NOT 403 (to prevent enumeration)
        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's declaration! "
            f"Got status {response.status_code}"
        )

    def test_update_declaration_denies_cross_tenant(
        self,
        client_a: TestClient,
        declaration_b: CBAMDeclaration,
    ):
        """
        SECURITY TEST: PUT /api/v1/cbam/declarations/{id} denies updating other tenant's declaration.
        """
        response = client_a.put(
            f"/api/v1/cbam/declarations/{declaration_b.id}",
            json={"declaration_reference": "MALICIOUS-UPDATE"}
        )

        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED], (
            f"SECURITY: Tenant A can update Tenant B's declaration! "
            f"Got status {response.status_code}"
        )

    def test_delete_declaration_denies_cross_tenant(
        self,
        client_a: TestClient,
        declaration_b: CBAMDeclaration,
        db_session: Session,
    ):
        """
        SECURITY TEST: DELETE /api/v1/cbam/declarations/{id} denies deleting other tenant's declaration.
        """
        original_count = db_session.query(CBAMDeclaration).filter(
            CBAMDeclaration.id == declaration_b.id
        ).count()

        response = client_a.delete(f"/api/v1/cbam/declarations/{declaration_b.id}")

        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED], (
            f"SECURITY: Tenant A can delete Tenant B's declaration! "
            f"Got status {response.status_code}"
        )

        # Verify declaration still exists
        post_count = db_session.query(CBAMDeclaration).filter(
            CBAMDeclaration.id == declaration_b.id
        ).count()
        assert post_count == original_count, "SECURITY: Declaration was deleted by wrong tenant!"


# =============================================================================
# INSTALLATION ISOLATION TESTS
# =============================================================================

class TestCBAMInstallationTenantIsolation:
    """Test tenant isolation for CBAM installation endpoints."""

    def test_list_installations_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        installation_a: CBAMInstallation,
        installation_b: CBAMInstallation,
    ):
        """
        SECURITY TEST: GET /api/v1/cbam/installations returns only own tenant's installations.
        """
        response_a = client_a.get("/api/v1/cbam/installations")

        if response_a.status_code == status.HTTP_200_OK:
            installations = response_a.json()
            items = installations if isinstance(installations, list) else installations.get("items", installations)

            installation_ids = [i.get("id") for i in items]
            assert installation_a.id in installation_ids, "Tenant A should see their own installation"
            assert installation_b.id not in installation_ids, "SECURITY: Tenant A sees Tenant B's installation!"

    def test_get_installation_by_id_denies_cross_tenant(
        self,
        client_a: TestClient,
        installation_b: CBAMInstallation,
    ):
        """
        SECURITY TEST: GET /api/v1/cbam/installations/{id} denies access to other tenant's installation.
        """
        response = client_a.get(f"/api/v1/cbam/installations/{installation_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's installation! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# DECLARATION LINE ISOLATION TESTS
# =============================================================================

class TestCBAMDeclarationLineTenantIsolation:
    """Test tenant isolation for declaration lines (scoped via parent declaration)."""

    def test_declaration_lines_scoped_via_parent(
        self,
        client_a: TestClient,
        declaration_a: CBAMDeclaration,
        declaration_b: CBAMDeclaration,
        declaration_line_a: CBAMDeclarationLine,
    ):
        """
        SECURITY TEST: Declaration lines are accessed via parent declaration.

        Tenant A should only see lines belonging to their declarations.
        """
        # Access Tenant A's declaration lines - should succeed
        response_a = client_a.get(f"/api/v1/cbam/declarations/{declaration_a.id}/lines")

        if response_a.status_code == status.HTTP_200_OK:
            lines = response_a.json()
            items = lines if isinstance(lines, list) else lines.get("items", lines)
            assert len(items) >= 1, "Tenant A should see their declaration lines"

        # Try to access Tenant B's declaration lines - should fail
        response_b = client_a.get(f"/api/v1/cbam/declarations/{declaration_b.id}/lines")
        assert response_b.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's declaration lines! "
            f"Got status {response_b.status_code}"
        )


# =============================================================================
# CALCULATE ENDPOINT ISOLATION TESTS
# =============================================================================

class TestCBAMCalculateEndpointIsolation:
    """Test tenant isolation for CBAM calculation endpoints."""

    def test_calculate_respects_tenant_boundary(
        self,
        client_a: TestClient,
        declaration_a: CBAMDeclaration,
        declaration_b: CBAMDeclaration,
    ):
        """
        SECURITY TEST: Calculate endpoint only processes own tenant's declarations.
        """
        # Try to trigger calculation on Tenant B's declaration
        response = client_a.post(
            f"/api/v1/cbam/declarations/{declaration_b.id}/calculate"
        )

        # Should return 404 (not found for this tenant) or 405 (method not allowed)
        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED], (
            f"SECURITY: Tenant A can calculate Tenant B's declaration! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# SHARED REFERENCE DATA TESTS
# =============================================================================

class TestCBAMSharedReferenceData:
    """Test that shared reference data (products, factor sources) is accessible by all."""

    def test_products_accessible_to_all_tenants(
        self,
        client_a: TestClient,
        client_b: TestClient,
        cbam_product: CBAMProduct,
    ):
        """
        Reference test: CBAM products are shared and accessible to all tenants.
        """
        response_a = client_a.get("/api/v1/cbam/products")
        response_b = client_b.get("/api/v1/cbam/products")

        # Both should succeed
        assert response_a.status_code == status.HTTP_200_OK
        assert response_b.status_code == status.HTTP_200_OK

    def test_factor_sources_accessible_to_all_tenants(
        self,
        client_a: TestClient,
        client_b: TestClient,
    ):
        """
        Reference test: CBAM factor sources are shared and accessible to all tenants.
        """
        response_a = client_a.get("/api/v1/cbam/factor-sources")
        response_b = client_b.get("/api/v1/cbam/factor-sources")

        # Both should succeed
        assert response_a.status_code == status.HTTP_200_OK
        assert response_b.status_code == status.HTTP_200_OK


# =============================================================================
# MARKER FOR SECURITY TESTS
# =============================================================================

pytestmark = pytest.mark.security


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
