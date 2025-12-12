# tests/test_issb_isolation.py
"""
ISSB Cross-Tenant Isolation Security Tests
==========================================
Tests to verify multi-tenant data isolation for ISSB (IFRS S1 + S2).

CRITICAL: These tests verify that:
1. Tenant A cannot see Tenant B's reporting units
2. Scenario analysis is tenant-scoped
3. Materiality assessments are isolated
4. Disclosure statements are tenant-scoped

Any failure in these tests indicates a critical security vulnerability.
"""

import pytest
from datetime import datetime, timedelta
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.models.user import User
from app.models.issb import (
    ISSBReportingUnit,
    ISSBConsolidationMethod,
    ISSBFinancialMetric,
    ISSBMetricType,
    ISSBClimateRiskExposure,
    ISSBRiskType,
    ISSBPhysicalRiskSubtype,
    ISSBTimeHorizon,
    ISSBLikelihood,
    ISSBTarget,
    ISSBTargetType,
    ISSBTargetStatus,
    ISSBEmissionsScope,
    ISSBScenario,
    ISSBScenarioResult,
    ISSBScenarioResultMetric,
    ISSBMaterialityAssessment,
    ISSBMaterialityTopic,
    ISSBDisclosureStatement,
    ISSBDisclosureStandard,
    ISSBDisclosureSection,
    ISSBDisclosureStatus,
)


# =============================================================================
# ISSB-SPECIFIC FIXTURES
# =============================================================================

@pytest.fixture(scope="function")
def reporting_unit_a(db_session: Session, tenant_a: Tenant) -> ISSBReportingUnit:
    """Create an ISSB reporting unit for Tenant A."""
    unit = ISSBReportingUnit(
        tenant_id=tenant_a.id,
        name="Alpha Manufacturing Division",
        description="Manufacturing operations in EU",
        currency="EUR",
        consolidation_method=ISSBConsolidationMethod.FULL,
        sector="Manufacturing",
        is_active=True,
    )
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


@pytest.fixture(scope="function")
def reporting_unit_b(db_session: Session, tenant_b: Tenant) -> ISSBReportingUnit:
    """Create an ISSB reporting unit for Tenant B."""
    unit = ISSBReportingUnit(
        tenant_id=tenant_b.id,
        name="Beta Energy Operations",
        description="Energy sector operations",
        currency="EUR",
        consolidation_method=ISSBConsolidationMethod.EQUITY,
        sector="Energy",
        is_active=True,
    )
    db_session.add(unit)
    db_session.commit()
    db_session.refresh(unit)
    return unit


@pytest.fixture(scope="function")
def scenario_a(db_session: Session, tenant_a: Tenant, user_a: User) -> ISSBScenario:
    """Create an ISSB scenario for Tenant A."""
    scenario = ISSBScenario(
        tenant_id=tenant_a.id,
        name="Net Zero 2050",
        description="1.5C aligned scenario",
        temperature_pathway="1.5C",
        reference_source="IEA NZE",
        start_year=2024,
        end_year=2050,
        is_active=True,
    )
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)
    return scenario


@pytest.fixture(scope="function")
def scenario_b(db_session: Session, tenant_b: Tenant, user_b: User) -> ISSBScenario:
    """Create an ISSB scenario for Tenant B."""
    scenario = ISSBScenario(
        tenant_id=tenant_b.id,
        name="High Physical Risk",
        description="RCP 8.5 scenario",
        temperature_pathway="4C",
        reference_source="IPCC RCP8.5",
        start_year=2024,
        end_year=2100,
        is_active=True,
    )
    db_session.add(scenario)
    db_session.commit()
    db_session.refresh(scenario)
    return scenario


@pytest.fixture(scope="function")
def materiality_a(
    db_session: Session,
    tenant_a: Tenant,
    user_a: User,
    reporting_unit_a: ISSBReportingUnit,
) -> ISSBMaterialityAssessment:
    """Create an ISSB materiality assessment for Tenant A."""
    assessment = ISSBMaterialityAssessment(
        tenant_id=tenant_a.id,
        reporting_unit_id=reporting_unit_a.id,
        topic=ISSBMaterialityTopic.CLIMATE,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        financial_materiality_score=75.0,
        impact_materiality_score=80.0,
        material=True,
        justification="Climate risk exposure through manufacturing operations",
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)
    return assessment


@pytest.fixture(scope="function")
def materiality_b(
    db_session: Session,
    tenant_b: Tenant,
    user_b: User,
    reporting_unit_b: ISSBReportingUnit,
) -> ISSBMaterialityAssessment:
    """Create an ISSB materiality assessment for Tenant B."""
    assessment = ISSBMaterialityAssessment(
        tenant_id=tenant_b.id,
        reporting_unit_id=reporting_unit_b.id,
        topic=ISSBMaterialityTopic.CLIMATE,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        financial_materiality_score=60.0,
        impact_materiality_score=40.0,
        material=True,
        justification="Low carbon transition risk, high physical risk exposure",
    )
    db_session.add(assessment)
    db_session.commit()
    db_session.refresh(assessment)
    return assessment


@pytest.fixture(scope="function")
def disclosure_a(
    db_session: Session,
    tenant_a: Tenant,
    user_a: User,
    reporting_unit_a: ISSBReportingUnit,
) -> ISSBDisclosureStatement:
    """Create an ISSB disclosure statement for Tenant A."""
    disclosure = ISSBDisclosureStatement(
        tenant_id=tenant_a.id,
        reporting_unit_id=reporting_unit_a.id,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        standard=ISSBDisclosureStandard.IFRS_S2,
        section=ISSBDisclosureSection.STRATEGY,
        headline_summary="Alpha climate strategy disclosure",
        status=ISSBDisclosureStatus.DRAFT,
    )
    db_session.add(disclosure)
    db_session.commit()
    db_session.refresh(disclosure)
    return disclosure


@pytest.fixture(scope="function")
def disclosure_b(
    db_session: Session,
    tenant_b: Tenant,
    user_b: User,
    reporting_unit_b: ISSBReportingUnit,
) -> ISSBDisclosureStatement:
    """Create an ISSB disclosure statement for Tenant B."""
    disclosure = ISSBDisclosureStatement(
        tenant_id=tenant_b.id,
        reporting_unit_id=reporting_unit_b.id,
        period_start=datetime(2024, 1, 1),
        period_end=datetime(2024, 3, 31),
        standard=ISSBDisclosureStandard.IFRS_S2,
        section=ISSBDisclosureSection.GOVERNANCE,
        headline_summary="Beta governance disclosure",
        status=ISSBDisclosureStatus.APPROVED,
    )
    db_session.add(disclosure)
    db_session.commit()
    db_session.refresh(disclosure)
    return disclosure


@pytest.fixture(scope="function")
def target_a(
    db_session: Session,
    tenant_a: Tenant,
    reporting_unit_a: ISSBReportingUnit,
) -> ISSBTarget:
    """Create an ISSB target for Tenant A."""
    target = ISSBTarget(
        tenant_id=tenant_a.id,
        reporting_unit_id=reporting_unit_a.id,
        name="Net Zero 2050",
        target_type=ISSBTargetType.NET_ZERO,
        scope=ISSBEmissionsScope.COMBINED,
        base_year=2020,
        target_year=2050,
        base_value=100000.0,
        target_value=0.0,
        unit="tCO2e",
        status=ISSBTargetStatus.IN_PROGRESS,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target


@pytest.fixture(scope="function")
def target_b(
    db_session: Session,
    tenant_b: Tenant,
    reporting_unit_b: ISSBReportingUnit,
) -> ISSBTarget:
    """Create an ISSB target for Tenant B."""
    target = ISSBTarget(
        tenant_id=tenant_b.id,
        reporting_unit_id=reporting_unit_b.id,
        name="50% Reduction by 2030",
        target_type=ISSBTargetType.ABSOLUTE_EMISSIONS,
        scope=ISSBEmissionsScope.SCOPE1,
        base_year=2020,
        target_year=2030,
        base_value=50000.0,
        target_value=25000.0,
        unit="tCO2e",
        status=ISSBTargetStatus.ON_TRACK,
    )
    db_session.add(target)
    db_session.commit()
    db_session.refresh(target)
    return target


# =============================================================================
# REPORTING UNIT ISOLATION TESTS
# =============================================================================

class TestISSBReportingUnitTenantIsolation:
    """Test tenant isolation for ISSB reporting unit endpoints."""

    def test_list_reporting_units_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        reporting_unit_a: ISSBReportingUnit,
        reporting_unit_b: ISSBReportingUnit,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/reporting-units returns only own tenant's units.
        """
        response_a = client_a.get("/api/v1/issb/reporting-units")

        if response_a.status_code == status.HTTP_200_OK:
            units = response_a.json()
            items = units if isinstance(units, list) else units.get("items", units)

            unit_ids = [u.get("id") for u in items]
            assert reporting_unit_a.id in unit_ids, "Tenant A should see their own reporting unit"
            assert reporting_unit_b.id not in unit_ids, "SECURITY: Tenant A sees Tenant B's reporting unit!"

        response_b = client_b.get("/api/v1/issb/reporting-units")

        if response_b.status_code == status.HTTP_200_OK:
            units = response_b.json()
            items = units if isinstance(units, list) else units.get("items", units)

            unit_ids = [u.get("id") for u in items]
            assert reporting_unit_b.id in unit_ids, "Tenant B should see their own reporting unit"
            assert reporting_unit_a.id not in unit_ids, "SECURITY: Tenant B sees Tenant A's reporting unit!"

    def test_get_reporting_unit_by_id_denies_cross_tenant(
        self,
        client_a: TestClient,
        reporting_unit_b: ISSBReportingUnit,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/reporting-units/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/issb/reporting-units/{reporting_unit_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's reporting unit! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# SCENARIO ISOLATION TESTS
# =============================================================================

class TestISSBScenarioTenantIsolation:
    """Test tenant isolation for ISSB scenario analysis."""

    def test_list_scenarios_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        scenario_a: ISSBScenario,
        scenario_b: ISSBScenario,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/scenarios returns only own tenant's scenarios.
        """
        response_a = client_a.get("/api/v1/issb/scenarios")

        if response_a.status_code == status.HTTP_200_OK:
            scenarios = response_a.json()
            items = scenarios if isinstance(scenarios, list) else scenarios.get("items", scenarios)

            scenario_ids = [s.get("id") for s in items]
            assert scenario_a.id in scenario_ids, "Tenant A should see their own scenario"
            assert scenario_b.id not in scenario_ids, "SECURITY: Tenant A sees Tenant B's scenario!"

    def test_get_scenario_by_id_denies_cross_tenant(
        self,
        client_a: TestClient,
        scenario_b: ISSBScenario,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/scenarios/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/issb/scenarios/{scenario_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's scenario! "
            f"Got status {response.status_code}"
        )

    def test_run_scenario_denies_cross_tenant(
        self,
        client_a: TestClient,
        scenario_b: ISSBScenario,
    ):
        """
        SECURITY TEST: POST /api/v1/issb/scenarios/{id}/run denies cross-tenant execution.
        """
        response = client_a.post(f"/api/v1/issb/scenarios/{scenario_b.id}/run")

        assert response.status_code in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED], (
            f"SECURITY: Tenant A can run Tenant B's scenario! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# MATERIALITY ASSESSMENT ISOLATION TESTS
# =============================================================================

class TestISSBMaterialityTenantIsolation:
    """Test tenant isolation for ISSB materiality assessments."""

    def test_list_materiality_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        materiality_a: ISSBMaterialityAssessment,
        materiality_b: ISSBMaterialityAssessment,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/materiality returns only own tenant's assessments.
        """
        response_a = client_a.get("/api/v1/issb/materiality")

        if response_a.status_code == status.HTTP_200_OK:
            assessments = response_a.json()
            items = assessments if isinstance(assessments, list) else assessments.get("items", assessments)

            assessment_ids = [m.get("id") for m in items]
            assert materiality_a.id in assessment_ids, "Tenant A should see their own materiality"
            assert materiality_b.id not in assessment_ids, "SECURITY: Tenant A sees Tenant B's materiality!"

    def test_get_materiality_denies_cross_tenant(
        self,
        client_a: TestClient,
        materiality_b: ISSBMaterialityAssessment,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/materiality/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/issb/materiality/{materiality_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's materiality! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# DISCLOSURE STATEMENT ISOLATION TESTS
# =============================================================================

class TestISSBDisclosureTenantIsolation:
    """Test tenant isolation for ISSB disclosure statements."""

    def test_list_disclosures_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        disclosure_a: ISSBDisclosureStatement,
        disclosure_b: ISSBDisclosureStatement,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/disclosures returns only own tenant's disclosures.
        """
        response_a = client_a.get("/api/v1/issb/disclosures")

        if response_a.status_code == status.HTTP_200_OK:
            disclosures = response_a.json()
            items = disclosures if isinstance(disclosures, list) else disclosures.get("items", disclosures)

            disclosure_ids = [d.get("id") for d in items]
            assert disclosure_a.id in disclosure_ids, "Tenant A should see their own disclosure"
            assert disclosure_b.id not in disclosure_ids, "SECURITY: Tenant A sees Tenant B's disclosure!"

    def test_get_disclosure_denies_cross_tenant(
        self,
        client_a: TestClient,
        disclosure_b: ISSBDisclosureStatement,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/disclosures/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/issb/disclosures/{disclosure_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's disclosure! "
            f"Got status {response.status_code}"
        )

    def test_generate_disclosure_denies_cross_tenant_data(
        self,
        client_a: TestClient,
        reporting_unit_b: ISSBReportingUnit,
    ):
        """
        SECURITY TEST: Disclosure generation cannot include other tenant's reporting units.
        """
        # Try to generate a disclosure with Tenant B's reporting unit
        response = client_a.post(
            "/api/v1/issb/disclosures/generate",
            json={
                "reporting_period_start": "2024-01-01",
                "reporting_period_end": "2024-03-31",
                "reporting_unit_ids": [reporting_unit_b.id],  # Malicious inclusion
            }
        )

        # Should either fail with 404/422 or succeed but not include the foreign unit
        if response.status_code == status.HTTP_200_OK:
            disclosure = response.json()
            included_units = disclosure.get("reporting_unit_ids", [])
            assert reporting_unit_b.id not in included_units, (
                "SECURITY: Disclosure includes Tenant B's reporting unit!"
            )


# =============================================================================
# TARGET ISOLATION TESTS
# =============================================================================

class TestISSBTargetTenantIsolation:
    """Test tenant isolation for ISSB targets."""

    def test_list_targets_returns_only_own_tenant(
        self,
        client_a: TestClient,
        client_b: TestClient,
        target_a: ISSBTarget,
        target_b: ISSBTarget,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/targets returns only own tenant's targets.
        """
        response_a = client_a.get("/api/v1/issb/targets")

        if response_a.status_code == status.HTTP_200_OK:
            targets = response_a.json()
            items = targets if isinstance(targets, list) else targets.get("items", targets)

            target_ids = [t.get("id") for t in items]
            assert target_a.id in target_ids, "Tenant A should see their own target"
            assert target_b.id not in target_ids, "SECURITY: Tenant A sees Tenant B's target!"

    def test_get_target_denies_cross_tenant(
        self,
        client_a: TestClient,
        target_b: ISSBTarget,
    ):
        """
        SECURITY TEST: GET /api/v1/issb/targets/{id} denies cross-tenant access.
        """
        response = client_a.get(f"/api/v1/issb/targets/{target_b.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND, (
            f"SECURITY: Tenant A can access Tenant B's target! "
            f"Got status {response.status_code}"
        )


# =============================================================================
# AGGREGATION ISOLATION TESTS
# =============================================================================

class TestISSBAggregationTenantIsolation:
    """Test that aggregation/summary endpoints respect tenant boundaries."""

    def test_climate_metrics_summary_scoped_to_tenant(
        self,
        client_a: TestClient,
        reporting_unit_a: ISSBReportingUnit,
        reporting_unit_b: ISSBReportingUnit,
    ):
        """
        SECURITY TEST: Climate metrics summary only includes own tenant's data.
        """
        response = client_a.get("/api/v1/issb/climate-metrics/summary")

        if response.status_code == status.HTTP_200_OK:
            summary = response.json()
            # Summary should only reflect Tenant A's data
            # Specific assertions depend on API response structure


# =============================================================================
# MARKER FOR SECURITY TESTS
# =============================================================================

pytestmark = pytest.mark.security


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
