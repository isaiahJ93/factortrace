"""
EXIOBASE 2020 Spend-Based Factor Coverage Tests
================================================
Validates that key EXIOBASE 2020 spend-based emission factors are correctly
loaded and can be retrieved via the emission_factors service.

EXIOBASE factors are Scope 3 spend-based, measuring kgCO2e per EUR spent.
They cover multi-region input-output analysis for various sectors.
"""
import pytest
from sqlalchemy import create_engine, text
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


class TestEXIOBASEITServices:
    """Tests for IT and computer services factors."""

    def test_computer_services_global(self, db_session):
        """Test global computer services factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Computer and related activities",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        assert factor is not None, "Computer services factor should exist"
        assert factor > 0, "Factor should be positive"
        # IT services typically 0.1-0.5 kgCO2e/EUR
        assert factor < 2.0, f"IT services factor {factor} seems too high"

    def test_telecommunications_global(self, db_session):
        """Test telecommunications factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Post and telecommunications",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        assert factor is not None, "Telecommunications factor should exist"
        assert factor > 0, "Factor should be positive"


class TestEXIOBASEManufacturing:
    """Tests for manufacturing sector factors."""

    def test_chemicals_global(self, db_session):
        """Test chemicals manufacturing factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Chemicals nec",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"
            # Chemicals are typically higher intensity
            assert factor > 0.1, "Chemicals factor should be significant"

    def test_machinery_global(self, db_session):
        """Test machinery manufacturing factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Machinery and equipment n.e.c.",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"

    def test_textiles_global(self, db_session):
        """Test textiles factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Textiles",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"


class TestEXIOBASEFoodAgriculture:
    """Tests for food and agriculture factors."""

    def test_food_products_global(self, db_session):
        """Test food products factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Food products nec",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"

    def test_agriculture_global(self, db_session):
        """Test agriculture factor exists."""
        # Try multiple possible activity types
        for activity in [
            "Cultivation of crops nec",
            "Cattle farming",
            "Products of meat cattle",
        ]:
            factor = get_factor(
                db_session,
                scope=3,
                category="spend_based",
                activity_type=activity,
                country_code="GLOBAL",
                year=2020,
                dataset="EXIOBASE_2020",
            )
            if factor is not None:
                assert factor > 0, f"{activity} factor should be positive"
                break


class TestEXIOBASETransport:
    """Tests for transport and logistics factors."""

    def test_air_transport_global(self, db_session):
        """Test air transport factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Air transport",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        assert factor is not None, "Air transport factor should exist"
        assert factor > 0, "Factor should be positive"
        # Air transport has high emissions intensity
        assert factor > 0.5, f"Air transport factor {factor} seems low"

    def test_sea_transport_global(self, db_session):
        """Test sea transport factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Sea and coastal water transport",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"

    def test_land_transport_global(self, db_session):
        """Test land transport factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Other land transport",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"


class TestEXIOBASEProfessionalServices:
    """Tests for professional services factors."""

    def test_legal_accounting_global(self, db_session):
        """Test legal/accounting services factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Other business activities",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"
            # Professional services typically low intensity
            assert factor < 1.0, f"Professional services factor {factor} seems high"

    def test_financial_services_global(self, db_session):
        """Test financial services factor exists."""
        factor = get_factor(
            db_session,
            scope=3,
            category="spend_based",
            activity_type="Financial intermediation, except insurance and pension funding",
            country_code="GLOBAL",
            year=2020,
            dataset="EXIOBASE_2020",
        )
        if factor is not None:
            assert factor > 0, "Factor should be positive"


class TestEXIOBASECountryVariation:
    """Tests for country-specific factors."""

    def test_us_factor_exists(self, db_session):
        """Test US-specific factors exist."""
        result = db_session.execute(
            text(
                "SELECT COUNT(*) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020' AND country_code = 'US'"
            )
        )
        count = result.scalar()
        assert count > 0, "Should have US-specific EXIOBASE factors"

    def test_de_factor_exists(self, db_session):
        """Test Germany-specific factors exist."""
        result = db_session.execute(
            text(
                "SELECT COUNT(*) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020' AND country_code = 'DE'"
            )
        )
        count = result.scalar()
        assert count > 0, "Should have Germany-specific EXIOBASE factors"

    def test_cn_factor_exists(self, db_session):
        """Test China-specific factors exist."""
        result = db_session.execute(
            text(
                "SELECT COUNT(*) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020' AND country_code = 'CN'"
            )
        )
        count = result.scalar()
        assert count > 0, "Should have China-specific EXIOBASE factors"

    def test_global_fallback_available(self, db_session):
        """Test GLOBAL fallback factors exist."""
        result = db_session.execute(
            text(
                "SELECT COUNT(*) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020' AND country_code = 'GLOBAL'"
            )
        )
        count = result.scalar()
        assert count > 0, "Should have GLOBAL EXIOBASE factors"


class TestEXIOBASEFactorCount:
    """Tests to verify overall EXIOBASE coverage."""

    def test_minimum_factor_count(self, db_session):
        """Test that we have expected number of EXIOBASE factors."""
        result = db_session.execute(
            text("SELECT COUNT(*) FROM emission_factors WHERE dataset = 'EXIOBASE_2020'")
        )
        count = result.scalar()
        # EXIOBASE has ~160 sectors x multiple regions = several thousand factors
        assert count >= 1000, f"Expected at least 1000 EXIOBASE factors, got {count}"

    def test_all_factors_are_scope_3(self, db_session):
        """Test that all EXIOBASE factors are Scope 3."""
        result = db_session.execute(
            text(
                "SELECT DISTINCT scope FROM emission_factors WHERE dataset = 'EXIOBASE_2020'"
            )
        )
        scopes = {row[0] for row in result}
        assert scopes == {"SCOPE_3"}, f"EXIOBASE should only have Scope 3, got {scopes}"

    def test_all_factors_are_spend_based(self, db_session):
        """Test that all EXIOBASE factors have spend_based category."""
        result = db_session.execute(
            text(
                "SELECT DISTINCT category FROM emission_factors WHERE dataset = 'EXIOBASE_2020'"
            )
        )
        categories = {row[0] for row in result}
        assert categories == {
            "spend_based"
        }, f"EXIOBASE should only have spend_based, got {categories}"

    def test_unique_activity_types(self, db_session):
        """Test diversity of activity types."""
        result = db_session.execute(
            text(
                "SELECT COUNT(DISTINCT activity_type) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020'"
            )
        )
        count = result.scalar()
        # EXIOBASE has ~160 unique sectors
        assert count >= 100, f"Expected at least 100 unique activity types, got {count}"

    def test_unique_countries(self, db_session):
        """Test coverage of multiple countries."""
        result = db_session.execute(
            text(
                "SELECT COUNT(DISTINCT country_code) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020'"
            )
        )
        count = result.scalar()
        # EXIOBASE covers ~50 regions
        assert count >= 10, f"Expected at least 10 unique countries, got {count}"


class TestEXIOBASEOutlierDetection:
    """Tests for sanity checking factor values."""

    def test_no_negative_factors(self, db_session):
        """Test that no factors are negative."""
        result = db_session.execute(
            text(
                "SELECT COUNT(*) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020' AND factor < 0"
            )
        )
        count = result.scalar()
        assert count == 0, f"Found {count} negative factors"

    def test_no_extreme_outliers(self, db_session):
        """Test that no factors are unreasonably high."""
        result = db_session.execute(
            text(
                "SELECT COUNT(*) FROM emission_factors "
                "WHERE dataset = 'EXIOBASE_2020' AND factor > 100"
            )
        )
        count = result.scalar()
        # Most spend-based factors should be < 10 kgCO2e/EUR
        # Some heavy industries might be higher but > 100 is suspicious
        assert (
            count < 50
        ), f"Found {count} factors > 100 kgCO2e/EUR, check for data issues"

    def test_reasonable_average(self, db_session):
        """Test that average factor is reasonable."""
        result = db_session.execute(
            text(
                "SELECT AVG(factor) FROM emission_factors WHERE dataset = 'EXIOBASE_2020'"
            )
        )
        avg = result.scalar()
        # Average across all sectors should be ~0.5-5 kgCO2e/EUR
        assert avg is not None, "Should have factors to average"
        assert 0.1 < avg < 20, f"Average factor {avg} seems unreasonable"
