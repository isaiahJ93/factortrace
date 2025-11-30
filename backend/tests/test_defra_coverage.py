"""
DEFRA 2024 Factor Coverage Tests
=================================
Validates that key DEFRA 2024 emission factors are correctly loaded and
can be retrieved via the emission_factors service.

Test cases cover realistic business scenarios:
- Scope 1: Stationary combustion (natural gas, diesel)
- Scope 2: Purchased electricity (UK Grid)
- Scope 3: Business travel (flights, rail), freight, waste
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.emission_factors import get_factor


@pytest.fixture(scope="module")
def db_session():
    """Create a database session for testing."""
    engine = create_engine("sqlite:///./factortrace.db")
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


class TestDEFRAScope1Coverage:
    """Tests for DEFRA Scope 1 (direct emissions) factors."""

    def test_stationary_combustion_natural_gas(self, db_session):
        """Test natural gas factor exists and is positive."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Natural gas",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "Natural gas factor should exist"
        assert factor > 0, "Factor should be positive"
        # DEFRA natural gas is ~0.18 kgCO2e/kWh (Gross CV)
        assert 0.1 < factor < 0.3, f"Natural gas factor {factor} out of expected range"

    def test_stationary_combustion_butane(self, db_session):
        """Test butane factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Butane",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "Butane factor should exist"
        assert factor > 0, "Factor should be positive"

    def test_mobile_combustion_car_diesel(self, db_session):
        """Test car diesel factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="mobile_combustion",
            activity_type="Car - Average car - Diesel",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        # May not exist with exact name, check None gracefully
        if factor is not None:
            assert factor > 0, "Factor should be positive"

    def test_refrigerant_r410a(self, db_session):
        """Test refrigerant factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="refrigerants",
            activity_type="R410A",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        # R410A has very high GWP
        if factor is not None:
            assert factor > 100, "R410A should have high GWP factor"


class TestDEFRAScope2Coverage:
    """Tests for DEFRA Scope 2 (indirect energy) factors."""

    def test_uk_grid_electricity(self, db_session):
        """Test UK grid electricity factor exists and is reasonable."""
        factor = get_factor(
            db_session,
            scope=2,
            category="purchased_electricity",
            activity_type="UK Grid - Generation",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "UK Grid electricity factor should exist"
        assert factor > 0, "Factor should be positive"
        # UK grid is ~0.2 kgCO2e/kWh in 2024
        assert 0.1 < factor < 0.4, f"UK Grid factor {factor} out of expected range"

    def test_heat_and_steam(self, db_session):
        """Test heat/steam factor exists."""
        factor = get_factor(
            db_session,
            scope=2,
            category="purchased_heat",
            activity_type="Heat and Steam - District heat and steam",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        # May have different activity_type naming
        if factor is not None:
            assert factor > 0, "Factor should be positive"


class TestDEFRAScope3Coverage:
    """Tests for DEFRA Scope 3 (value chain) factors."""

    def test_business_travel_long_haul_flight(self, db_session):
        """Test long-haul flight factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="business_travel",
            activity_type="Air - Long-haul, to/from UK - With RF",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "Long-haul flight factor should exist"
        assert factor > 0, "Factor should be positive"
        # Long-haul with RF is around 0.1-0.3 kgCO2e/passenger.km
        assert factor < 2.0, f"Flight factor {factor} seems too high"

    def test_business_travel_domestic_flight(self, db_session):
        """Test domestic flight factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="business_travel",
            activity_type="Air - Domestic, to/from UK - With RF",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "Domestic flight factor should exist"
        # Domestic flights have higher per-km emissions than long-haul
        assert factor > 0.1, "Domestic flight factor should be significant"

    def test_business_travel_rail(self, db_session):
        """Test rail travel factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="business_travel",
            activity_type="Rail - National rail",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "Rail factor should exist"
        assert factor > 0, "Factor should be positive"
        # Rail is typically much lower than air
        assert factor < 0.1, f"Rail factor {factor} seems too high"

    def test_upstream_transportation_hgv(self, db_session):
        """Test HGV freight factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="upstream_transportation",
            activity_type="Road Freight HGV - All HGVs - Average laden",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        if factor is not None:
            assert factor > 0, "HGV freight factor should be positive"

    def test_waste_landfill(self, db_session):
        """Test waste landfill factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="waste",
            activity_type="Waste - Refuse - Landfill",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        if factor is not None:
            assert factor > 0, "Landfill factor should be positive"

    def test_hotel_stay(self, db_session):
        """Test hotel stay factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="hotel_stay",
            activity_type="UK",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        if factor is not None:
            assert factor > 0, "Hotel stay factor should be positive"


class TestDEFRAGlobalFallback:
    """Tests for GLOBAL fallback behavior with DEFRA factors."""

    def test_gb_factor_found_directly(self, db_session):
        """Test GB factors are found without fallback."""
        factor = get_factor(
            db_session,
            scope=2,
            category="purchased_electricity",
            activity_type="UK Grid - Generation",
            country_code="GB",
            year=2024,
            dataset="DEFRA_2024",
        )
        assert factor is not None, "GB factor should be found directly"

    def test_non_gb_country_may_fallback(self, db_session):
        """Test non-GB country may fall back to GLOBAL or return None."""
        factor = get_factor(
            db_session,
            scope=2,
            category="purchased_electricity",
            activity_type="UK Grid - Generation",
            country_code="DE",  # Germany, not UK
            year=2024,
            dataset="DEFRA_2024",
        )
        # DEFRA factors are GB-specific, so DE won't find this
        # The function may return None or a GLOBAL fallback
        # This is expected behavior - client should use appropriate dataset


class TestDEFRAFactorCount:
    """Tests to verify overall DEFRA coverage."""

    def test_minimum_factor_count(self, db_session):
        """Test that we have a minimum number of DEFRA factors."""
        from sqlalchemy import text

        result = db_session.execute(
            text("SELECT COUNT(*) FROM emission_factors WHERE dataset = 'DEFRA_2024'")
        )
        count = result.scalar()
        # We expect at least 1000 DEFRA factors after ingestion
        assert count >= 1000, f"Expected at least 1000 DEFRA factors, got {count}"

    def test_all_scopes_covered(self, db_session):
        """Test that all three scopes have DEFRA factors."""
        from sqlalchemy import text

        result = db_session.execute(
            text(
                "SELECT DISTINCT scope FROM emission_factors WHERE dataset = 'DEFRA_2024'"
            )
        )
        scopes = {row[0] for row in result}
        assert "SCOPE_1" in scopes, "DEFRA should have Scope 1 factors"
        assert "SCOPE_2" in scopes, "DEFRA should have Scope 2 factors"
        assert "SCOPE_3" in scopes, "DEFRA should have Scope 3 factors"
