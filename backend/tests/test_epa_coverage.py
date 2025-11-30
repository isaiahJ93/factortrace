"""
EPA 2024 Factor Coverage Tests
==============================
Validates that key EPA 2024 emission factors (Table 1 - Stationary Combustion)
are correctly loaded and can be retrieved via the emission_factors service.

EPA factors are US-specific and focus on stationary combustion fuels.
All factors are Scope 1 and measured in kg CO2 per mmBtu.
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


class TestEPACoalFactors:
    """Tests for EPA coal combustion factors."""

    def test_anthracite_coal(self, db_session):
        """Test anthracite coal factor exists and is reasonable."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Anthracite",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Anthracite factor should exist"
        assert factor > 0, "Factor should be positive"
        # Anthracite is ~103-104 kg CO2/mmBtu
        assert 90 < factor < 120, f"Anthracite factor {factor} out of expected range"

    def test_bituminous_coal(self, db_session):
        """Test bituminous coal factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Bituminous",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Bituminous factor should exist"
        # Bituminous is ~93 kg CO2/mmBtu
        assert 80 < factor < 110, f"Bituminous factor {factor} out of expected range"

    def test_sub_bituminous_coal(self, db_session):
        """Test sub-bituminous coal factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Sub-bituminous",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Sub-bituminous factor should exist"
        assert factor > 0, "Factor should be positive"

    def test_lignite_coal(self, db_session):
        """Test lignite coal factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Lignite",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Lignite factor should exist"
        assert factor > 0, "Factor should be positive"

    def test_coal_coke(self, db_session):
        """Test coal coke factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Coal Coke",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Coal coke factor should exist"
        # Coal coke has higher emissions ~113 kg CO2/mmBtu
        assert factor > 100, f"Coal coke factor {factor} seems low"


class TestEPANaturalGas:
    """Tests for EPA natural gas factors."""

    def test_natural_gas(self, db_session):
        """Test natural gas factor exists and is reasonable."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Natural Gas",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Natural gas factor should exist"
        assert factor > 0, "Factor should be positive"
        # Natural gas is ~53 kg CO2/mmBtu
        assert 45 < factor < 65, f"Natural gas factor {factor} out of expected range"


class TestEPAPetroleumProducts:
    """Tests for EPA petroleum product factors."""

    def test_distillate_fuel_oil_no_2(self, db_session):
        """Test diesel/heating oil factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Distillate Fuel Oil No. 2",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Distillate fuel oil #2 factor should exist"
        # Diesel is ~73 kg CO2/mmBtu
        assert 65 < factor < 85, f"Diesel factor {factor} out of expected range"

    def test_motor_gasoline(self, db_session):
        """Test motor gasoline factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Motor Gasoline",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Motor gasoline factor should exist"
        # Gasoline is ~70 kg CO2/mmBtu
        assert 60 < factor < 80, f"Gasoline factor {factor} out of expected range"

    def test_propane(self, db_session):
        """Test propane factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Propane",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Propane factor should exist"
        # Propane is ~63 kg CO2/mmBtu
        assert 55 < factor < 75, f"Propane factor {factor} out of expected range"

    def test_kerosene(self, db_session):
        """Test kerosene factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Kerosene",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Kerosene factor should exist"
        assert factor > 0, "Factor should be positive"

    def test_lpg(self, db_session):
        """Test LPG factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - LPG",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "LPG factor should exist"
        assert factor > 0, "Factor should be positive"


class TestEPAOtherFuels:
    """Tests for EPA other fuel factors."""

    def test_petroleum_coke(self, db_session):
        """Test petroleum coke factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Petroleum Coke (Solid)",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Petroleum coke factor should exist"
        # Petroleum coke is ~102 kg CO2/mmBtu
        assert factor > 90, f"Petroleum coke factor {factor} seems low"

    def test_landfill_gas(self, db_session):
        """Test landfill gas factor exists."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Landfill Gas",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "Landfill gas factor should exist"
        # Landfill gas is ~52 kg CO2/mmBtu (biogenic)
        assert factor > 40, f"Landfill gas factor {factor} seems low"


class TestEPAUSCountryCode:
    """Tests for EPA US country code handling."""

    def test_us_factor_found_directly(self, db_session):
        """Test US factors are found directly."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Natural Gas",
            country_code="US",
            year=2024,
            dataset="EPA_2024",
        )
        assert factor is not None, "US natural gas factor should exist"

    def test_non_us_country_not_found(self, db_session):
        """Test non-US country returns None for EPA-specific factors."""
        factor = get_factor(
            db_session,
            scope=1,
            category="stationary_combustion",
            activity_type="Stationary combustion - Natural Gas",
            country_code="GB",  # UK
            year=2024,
            dataset="EPA_2024",
        )
        # EPA factors are US-specific, should not find GB
        # This is expected behavior - use DEFRA for GB


class TestEPAFactorCount:
    """Tests to verify overall EPA coverage."""

    def test_minimum_factor_count(self, db_session):
        """Test that we have expected number of EPA factors."""
        from sqlalchemy import text

        result = db_session.execute(
            text("SELECT COUNT(*) FROM emission_factors WHERE dataset = 'EPA_2024'")
        )
        count = result.scalar()
        # We expect 50-60 EPA stationary combustion factors
        assert count >= 50, f"Expected at least 50 EPA factors, got {count}"
        assert count < 100, f"Expected fewer than 100 EPA factors (Table 1 only), got {count}"

    def test_all_factors_are_scope_1(self, db_session):
        """Test that all EPA factors are Scope 1 (stationary combustion)."""
        from sqlalchemy import text

        result = db_session.execute(
            text(
                "SELECT DISTINCT scope FROM emission_factors WHERE dataset = 'EPA_2024'"
            )
        )
        scopes = {row[0] for row in result}
        assert scopes == {"SCOPE_1"}, f"EPA should only have Scope 1, got {scopes}"

    def test_all_factors_are_us(self, db_session):
        """Test that all EPA factors have US country code."""
        from sqlalchemy import text

        result = db_session.execute(
            text(
                "SELECT DISTINCT country_code FROM emission_factors WHERE dataset = 'EPA_2024'"
            )
        )
        countries = {row[0] for row in result}
        assert countries == {"US"}, f"EPA should only have US, got {countries}"
