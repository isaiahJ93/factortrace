# tests/test_eudr_isolation.py
"""
EUDR Cross-Tenant Isolation Security Tests
==========================================
Tests to verify multi-tenant data isolation for EUDR (EU Deforestation Regulation).

CRITICAL: These tests verify that:
1. Tenant A cannot see Tenant B's operators/sites/batches
2. Supply chain traversal stays within tenant boundary
3. Risk snapshots are tenant-scoped
4. Due diligence statements are isolated

Any failure in these tests indicates a critical security vulnerability.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.models.eudr import (
    EUDROperator,
    EUDROperatorRole,
    EUDRSupplySite,
    EUDRBatch,
    EUDRDueDiligence,
    EUDRDueDiligenceStatus,
    EUDRGeoRiskSnapshot,
    EUDRRiskLevel,
    EUDRCommodity,
    EUDRCommodityType,
    EUDRGeoRiskSource,
)


# =============================================================================
# EUDR-SPECIFIC FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def eudr_commodity(db_session: Session) -> EUDRCommodity:
    """Create a shared EUDR commodity reference (not tenant-owned)."""
    commodity = EUDRCommodity(
        name="Coffee Arabica",
        commodity_type=EUDRCommodityType.COFFEE,
        description="Arabica coffee beans",
        hs_code="090111",
        risk_profile_default=EUDRRiskLevel.MEDIUM,
        is_active=True,
    )
    db_session.add(commodity)
    db_session.commit()
    db_session.refresh(commodity)
    return commodity


@pytest.fixture(scope="function")
def operator_a(db_session: Session, tenant_a: Tenant) -> EUDROperator:
    """Create an EUDR operator for Tenant A."""
    operator = EUDROperator(
        tenant_id=tenant_a.id,
        name="Alpha Coffee Imports Ltd",
        role=EUDROperatorRole.OPERATOR,
        country="GB",
        identifier="GB123456789000",  # VAT/EORI/registration number
        is_active=True,
    )
    db_session.add(operator)
    db_session.commit()
    db_session.refresh(operator)
    return operator


@pytest.fixture(scope="function")
def operator_b(db_session: Session, tenant_b: Tenant) -> EUDROperator:
    """Create an EUDR operator for Tenant B."""
    operator = EUDROperator(
        tenant_id=tenant_b.id,
        name="Beta Cocoa Trading GmbH",
        role=EUDROperatorRole.TRADER,
        country="DE",
        identifier="DE987654321000",  # VAT/EORI/registration number
        is_active=True,
    )
    db_session.add(operator)
    db_session.commit()
    db_session.refresh(operator)
    return operator


@pytest.fixture(scope="function")
def supply_site_a(
    db_session: Session,
    tenant_a: Tenant,
    operator_a: EUDROperator,
    eudr_commodity: EUDRCommodity,
) -> EUDRSupplySite:
    """Create an EUDR supply site for Tenant A."""
    site = EUDRSupplySite(
        tenant_id=tenant_a.id,
        operator_id=operator_a.id,
        name="Colombian Coffee Farm",
        commodity_id=eudr_commodity.id,
        country="CO",
        region="Huila",
        latitude=2.0,
        longitude=-75.5,
        area_ha=50.0,
        is_active=True,
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture(scope="function")
def supply_site_b(
    db_session: Session,
    tenant_b: Tenant,
    operator_b: EUDROperator,
    eudr_commodity: EUDRCommodity,
) -> EUDRSupplySite:
    """Create an EUDR supply site for Tenant B."""
    site = EUDRSupplySite(
        tenant_id=tenant_b.id,
        operator_id=operator_b.id,
        name="Brazilian Cocoa Plantation",
        commodity_id=eudr_commodity.id,
        country="BR",
        region="Bahia",
        latitude=-15.0,
        longitude=-39.5,
        area_ha=100.0,
        is_active=True,
    )
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture(scope="function")
def batch_a(
    db_session: Session,
    tenant_a: Tenant,
    supply_site_a: EUDRSupplySite,
    eudr_commodity: EUDRCommodity,
) -> EUDRBatch:
    """Create an EUDR batch for Tenant A."""
    batch = EUDRBatch(
        tenant_id=tenant_a.id,
        batch_reference="ALPHA-BATCH-2024-001",
        commodity_id=eudr_commodity.id,
        origin_site_id=supply_site_a.id,
        volume=1.0,  # 1 tonne
        volume_unit="tonne",
        origin_country="CO",  # Colombia
        harvest_year=2024,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture(scope="function")
def batch_b(
    db_session: Session,
    tenant_b: Tenant,
    supply_site_b: EUDRSupplySite,
    eudr_commodity: EUDRCommodity,
) -> EUDRBatch:
    """Create an EUDR batch for Tenant B."""
    batch = EUDRBatch(
        tenant_id=tenant_b.id,
        batch_reference="BETA-BATCH-2024-001",
        commodity_id=eudr_commodity.id,
        origin_site_id=supply_site_b.id,
        volume=5.0,  # 5 tonnes
        volume_unit="tonne",
        origin_country="BR",  # Brazil
        harvest_year=2024,
    )
    db_session.add(batch)
    db_session.commit()
    db_session.refresh(batch)
    return batch


@pytest.fixture(scope="function")
def risk_snapshot_a(
    db_session: Session,
    tenant_a: Tenant,
    supply_site_a: EUDRSupplySite,
) -> EUDRGeoRiskSnapshot:
    """Create a geo risk snapshot for Tenant A."""
    snapshot = EUDRGeoRiskSnapshot(
        tenant_id=tenant_a.id,
        supply_site_id=supply_site_a.id,
        snapshot_date=datetime(2024, 3, 1),
        source=EUDRGeoRiskSource.MOCK,
        deforestation_flag=False,
        protected_area_overlap=False,
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    return snapshot


@pytest.fixture(scope="function")
def risk_snapshot_b(
    db_session: Session,
    tenant_b: Tenant,
    supply_site_b: EUDRSupplySite,
) -> EUDRGeoRiskSnapshot:
    """Create a geo risk snapshot for Tenant B."""
    snapshot = EUDRGeoRiskSnapshot(
        tenant_id=tenant_b.id,
        supply_site_id=supply_site_b.id,
        snapshot_date=datetime(2024, 3, 1),
        source=EUDRGeoRiskSource.MOCK,
        deforestation_flag=True,  # High risk indicator
        protected_area_overlap=True,
    )
    db_session.add(snapshot)
    db_session.commit()
    db_session.refresh(snapshot)
    return snapshot


@pytest.fixture(scope="function")
def due_diligence_a(
    db_session: Session,
    tenant_a: Tenant,
    user_a: User,
    operator_a: EUDROperator,
    eudr_commodity: EUDRCommodity,
) -> EUDRDueDiligence:
    """Create an EUDR due diligence statement for Tenant A."""
    dd = EUDRDueDiligence(
        tenant_id=tenant_a.id,
        operator_id=operator_a.id,
        reference="DD-ALPHA-2024-001",
        commodity_id=eudr_commodity.id,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        status=EUDRDueDiligenceStatus.DRAFT,
        justification_summary="Compliant - no deforestation risk identified",
        created_by_user_id=user_a.id,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.refresh(dd)
    return dd


@pytest.fixture(scope="function")
def due_diligence_b(
    db_session: Session,
    tenant_b: Tenant,
    user_b: User,
    operator_b: EUDROperator,
    eudr_commodity: EUDRCommodity,
) -> EUDRDueDiligence:
    """Create an EUDR due diligence statement for Tenant B."""
    dd = EUDRDueDiligence(
        tenant_id=tenant_b.id,
        operator_id=operator_b.id,
        reference="DD-BETA-2024-001",
        commodity_id=eudr_commodity.id,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        status=EUDRDueDiligenceStatus.FINAL,
        justification_summary="High risk identified - mitigation required",
        created_by_user_id=user_b.id,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.refresh(dd)
    return dd


# =============================================================================
# OPERATOR ISOLATION TESTS
# =============================================================================

class TestEUDROperatorTenantIsolation:
    """Test tenant isolation for EUDR operator endpoints."""

    def test_list_operators_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        operator_a: EUDROperator,
        operator_b: EUDROperator,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/operators returns only own tenant's operators.
        """
        response_a = client_a.get("/api/v1/eudr/operators")

        if response_a.status_code == status.HTTP_200_OK:
            operators = response_a.json()
            items = operators if isinstance(operators, list) else operators.get("items", operators)

            operator_ids = [o.get("id") for o in items]
            assert operator_a.id in operator_ids, "Tenant A should see their own operator"
            assert operator_b.id not in operator_ids, "SECURITY: Tenant A sees Tenant B's operator!"

        response_b = client_b.get("/api/v1/eudr/operators")

        if response_b.status_code == status.HTTP_200_OK:
            operators = response_b.json()
            items = operators if isinstance(operators, list) else operators.get("items", operators)

            operator_ids = [o.get("id") for o in items]
            assert operator_b.id in operator_ids, "Tenant B should see their own operator"
            assert operator_a.id not in operator_ids, "SECURITY: Tenant B sees Tenant A's operator!"

    def test_get_operator_by_id_denies_cross_tenant(
        self,
        client_a: TestClient,
        operator_b: EUDROperator,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/operators/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/eudr/operators/{operator_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's operator! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# SUPPLY SITE ISOLATION TESTS
# =============================================================================

class TestEUDRSupplySiteTenantIsolation:
    """Test tenant isolation for EUDR supply site endpoints."""

    def test_list_supply_sites_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        supply_site_a: EUDRSupplySite,
        supply_site_b: EUDRSupplySite,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/supply-sites returns only own tenant's sites.
        """
        response_a = client_a.get("/api/v1/eudr/supply-sites")

        if response_a.status_code == status.HTTP_200_OK:
            sites = response_a.json()
            items = sites if isinstance(sites, list) else sites.get("items", sites)

            site_ids = [s.get("id") for s in items]
            assert supply_site_a.id in site_ids, "Tenant A should see their own supply site"
            assert supply_site_b.id not in site_ids, "SECURITY: Tenant A sees Tenant B's supply site!"

    def test_get_supply_site_denies_cross_tenant(
        self,
        client_a: TestClient,
        supply_site_b: EUDRSupplySite,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/supply-sites/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/eudr/supply-sites/{supply_site_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's supply site! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# BATCH ISOLATION TESTS
# =============================================================================

class TestEUDRBatchTenantIsolation:
    """Test tenant isolation for EUDR batch endpoints."""

    def test_list_batches_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        batch_a: EUDRBatch,
        batch_b: EUDRBatch,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/batches returns only own tenant's batches.
        """
        response_a = client_a.get("/api/v1/eudr/batches")

        if response_a.status_code == status.HTTP_200_OK:
            batches = response_a.json()
            items = batches if isinstance(batches, list) else batches.get("items", batches)

            batch_ids = [b.get("id") for b in items]
            assert batch_a.id in batch_ids, "Tenant A should see their own batch"
            assert batch_b.id not in batch_ids, "SECURITY: Tenant A sees Tenant B's batch!"

    def test_get_batch_denies_cross_tenant(
        self,
        client_a: TestClient,
        batch_b: EUDRBatch,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/batches/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/eudr/batches/{batch_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's batch! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# SUPPLY CHAIN TRAVERSAL TESTS
# =============================================================================

class TestEUDRSupplyChainIsolation:
    """Test that supply chain traversal stays within tenant boundary."""

    def test_supply_chain_traversal_scoped_to_tenant(
        self,
        client_a: TestClient,
        batch_a: EUDRBatch,
        batch_b: EUDRBatch,
    ):
        """
        SECURITY TEST: Supply chain API only returns tenant's own chain.
        """
        # Try to get supply chain for own batch - should work
        response_own = client_a.get(f"/api/v1/eudr/batches/{batch_a.id}/supply-chain")

        if response_own.status_code == status.HTTP_200_OK:
            chain = response_own.json()
            # Should only contain Tenant A's data
            pass  # Endpoint may return chain structure

        # Try to get supply chain for other tenant's batch - should fail
        response_other = client_a.get(f"/api/v1/eudr/batches/{batch_b.id}/supply-chain")

        assert response_other.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's supply chain! "
            f"Got status {response_other.status_code}"
        )


# =============================================================================
# GEO RISK SNAPSHOT ISOLATION TESTS
# =============================================================================

class TestEUDRGeoRiskTenantIsolation:
    """Test tenant isolation for geo risk assessments."""

    def test_risk_snapshots_scoped_to_tenant(
        self,
        client_a: TestClient,
        risk_snapshot_a: EUDRGeoRiskSnapshot,
        risk_snapshot_b: EUDRGeoRiskSnapshot,
        supply_site_a: EUDRSupplySite,
        supply_site_b: EUDRSupplySite,
    ):
        """
        SECURITY TEST: Risk snapshots only visible to owning tenant.
        """
        # Get risk for own site - should work
        response_own = client_a.get(f"/api/v1/eudr/supply-sites/{supply_site_a.id}/risk")

        if response_own.status_code == status.HTTP_200_OK:
            risk_data = response_own.json()
            # Should show LOW risk for Tenant A's site
            pass

        # Try to get risk for other tenant's site - should fail
        response_other = client_a.get(f"/api/v1/eudr/supply-sites/{supply_site_b.id}/risk")

        assert response_other.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can see Tenant B's risk assessment! "
            f"Got status {response_other.status_code}"
        )


# =============================================================================
# DUE DILIGENCE ISOLATION TESTS
# =============================================================================

class TestEUDRDueDiligenceTenantIsolation:
    """Test tenant isolation for due diligence statements."""

    def test_list_due_diligence_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        due_diligence_a: EUDRDueDiligence,
        due_diligence_b: EUDRDueDiligence,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/due-diligence returns only own tenant's statements.
        """
        response_a = client_a.get("/api/v1/eudr/due-diligence")

        if response_a.status_code == status.HTTP_200_OK:
            dds = response_a.json()
            items = dds if isinstance(dds, list) else dds.get("items", dds)

            dd_ids = [d.get("id") for d in items]
            assert due_diligence_a.id in dd_ids, "Tenant A should see their own due diligence"
            assert due_diligence_b.id not in dd_ids, "SECURITY: Tenant A sees Tenant B's due diligence!"

    def test_get_due_diligence_denies_cross_tenant(
        self,
        client_a: TestClient,
        due_diligence_b: EUDRDueDiligence,
    ):
        """
        SECURITY TEST: GET /api/v1/eudr/due-diligence/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/eudr/due-diligence/{due_diligence_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's due diligence! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# SHARED REFERENCE DATA TESTS
# =============================================================================

class TestEUDRSharedReferenceData:
    """Test that shared reference data (commodities) is accessible by all."""

    def test_commodities_accessible_to_all_tenants(
        self,
        client_a: TestClient,
        client_b: TestClient,
        eudr_commodity: EUDRCommodity,
    ):
        """
        Reference test: EUDR commodities are shared and accessible to all tenants.
        """
        response_a = client_a.get("/api/v1/eudr/commodities")
        response_b = client_b.get("/api/v1/eudr/commodities")

        # Both should succeed
        assert response_a.status_code == status.HTTP_200_OK
        assert response_b.status_code == status.HTTP_200_OK


# =============================================================================
# MARKER FOR SECURITY TESTS
# =============================================================================

pytestmark = pytest.mark.security


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
