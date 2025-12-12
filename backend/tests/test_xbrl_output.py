# tests/test_xbrl_output.py
"""
iXBRL Output Validation Tests
=============================
Comprehensive tests for ESRS E1 iXBRL generation and validation.

Tests verify:
1. ESRS E1 taxonomy mappings are correct
2. iXBRL document structure is valid
3. Context and unit references are properly linked
4. Required ESRS E1 elements are present
5. Calculation results map to correct tags
6. Output structure matches ESRS 2024 taxonomy
"""

import pytest
from datetime import date
from xml.etree import ElementTree as ET

from app.services.xbrl_exporter import (
    ESRS_E1_Taxonomy,
    ESRSE1EmissionsData,
    IXBRLGenerator,
    XBRLValidationError,
    XBRLValidationResult,
    validate_ixbrl_output,
    generate_esrs_e1_report,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def valid_emissions_data() -> ESRSE1EmissionsData:
    """Create valid emissions data for testing."""
    return ESRSE1EmissionsData(
        entity_name="Acme Steel Corporation",
        lei="5493001KJTIIGC8Y1R12",  # Valid 20-char LEI
        reporting_year=2024,
        scope_1_emissions=1500.25,
        scope_2_location_based=750.50,
        scope_2_market_based=680.00,
        scope_3_emissions=2250.75,
        scope_3_categories={
            "purchased_goods_services": 1200.00,
            "upstream_transportation": 500.00,
            "business_travel": 300.75,
            "employee_commuting": 250.00,
        },
        data_quality_score=85,
        calculation_count=42,
        datasets_used=["DEFRA_2024", "EXIOBASE_2020"],
    )


@pytest.fixture
def minimal_emissions_data() -> ESRSE1EmissionsData:
    """Create minimal valid emissions data."""
    return ESRSE1EmissionsData(
        entity_name="Minimal Corp",
        lei="MINIMAL1234567890123",  # Valid 20-char LEI (exactly 20 chars)
        reporting_year=2024,
        scope_1_emissions=100.0,
        scope_2_location_based=50.0,
        scope_3_emissions=150.0,
    )


@pytest.fixture
def generator() -> IXBRLGenerator:
    """Create an iXBRL generator instance."""
    return IXBRLGenerator()


# =============================================================================
# DATA VALIDATION TESTS
# =============================================================================

class TestESRSE1EmissionsDataValidation:
    """Tests for emissions data validation."""

    def test_valid_data_passes_validation(self, valid_emissions_data):
        """Valid emissions data should pass validation."""
        result = valid_emissions_data.validate()
        assert result.valid is True
        assert len(result.errors) == 0

    def test_empty_entity_name_fails(self):
        """Empty entity name should fail validation."""
        data = ESRSE1EmissionsData(
            entity_name="",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
        )
        result = data.validate()
        assert result.valid is False
        assert any("entity_name" in e for e in result.errors)

    def test_missing_lei_fails(self):
        """Missing LEI should fail validation."""
        data = ESRSE1EmissionsData(
            entity_name="Test Corp",
            lei="",
            reporting_year=2024,
        )
        result = data.validate()
        assert result.valid is False
        assert any("lei" in e.lower() for e in result.errors)

    def test_invalid_lei_format_fails(self):
        """Invalid LEI format should fail validation."""
        # LEI must be 20 alphanumeric characters
        invalid_leis = [
            "12345",  # Too short
            "12345678901234567890123",  # Too long
            "1234567890123456789!",  # Invalid character
        ]
        for lei in invalid_leis:
            data = ESRSE1EmissionsData(
                entity_name="Test Corp",
                lei=lei,
                reporting_year=2024,
            )
            result = data.validate()
            assert result.valid is False, f"LEI '{lei}' should be invalid"

    def test_valid_lei_formats_pass(self):
        """Valid LEI formats should pass validation."""
        valid_leis = [
            "5493001KJTIIGC8Y1R12",
            "ABCD12345678901234EF",
            "12345678901234567890",
        ]
        for lei in valid_leis:
            data = ESRSE1EmissionsData(
                entity_name="Test Corp",
                lei=lei,
                reporting_year=2024,
            )
            result = data.validate()
            assert result.valid is True, f"LEI '{lei}' should be valid"

    def test_negative_emissions_fail(self):
        """Negative emissions values should fail validation."""
        data = ESRSE1EmissionsData(
            entity_name="Test Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1_emissions=-100.0,
        )
        result = data.validate()
        assert result.valid is False
        assert any("negative" in e for e in result.errors)

    def test_zero_emissions_generates_warning(self):
        """Zero emissions should generate a warning, not an error."""
        data = ESRSE1EmissionsData(
            entity_name="Test Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1_emissions=0.0,
            scope_2_location_based=0.0,
        )
        result = data.validate()
        assert result.valid is True
        assert any("zero" in w.lower() for w in result.warnings)

    def test_scope_3_without_categories_warning(self):
        """Scope 3 without category breakdown should generate a warning."""
        data = ESRSE1EmissionsData(
            entity_name="Test Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_3_emissions=1000.0,
            scope_3_categories={},  # No breakdown
        )
        result = data.validate()
        assert result.valid is True
        assert any("category" in w.lower() for w in result.warnings)

    def test_scope_3_category_mismatch_warning(self):
        """Mismatched Scope 3 total and category sum should warn."""
        data = ESRSE1EmissionsData(
            entity_name="Test Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_3_emissions=1000.0,  # Total
            scope_3_categories={"purchased_goods_services": 500.0},  # Only 500
        )
        result = data.validate()
        assert result.valid is True  # Not an error
        assert any("match" in w.lower() for w in result.warnings)

    def test_total_emissions_calculation(self, valid_emissions_data):
        """Total emissions should equal sum of scopes."""
        expected = (
            valid_emissions_data.scope_1_emissions +
            valid_emissions_data.scope_2_location_based +
            valid_emissions_data.scope_3_emissions
        )
        assert valid_emissions_data.total_emissions == expected

    def test_default_period_from_year(self):
        """Period should default to full year when not specified."""
        data = ESRSE1EmissionsData(
            entity_name="Test Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
        )
        assert data.period_start == date(2024, 1, 1)
        assert data.period_end == date(2024, 12, 31)


# =============================================================================
# iXBRL GENERATION TESTS
# =============================================================================

class TestIXBRLGeneration:
    """Tests for iXBRL document generation."""

    def test_generates_valid_xml(self, generator, valid_emissions_data):
        """Generated output should be valid XML."""
        xhtml = generator.generate(valid_emissions_data)

        # Should not raise an exception
        try:
            ET.fromstring(xhtml)
        except ET.ParseError as e:
            pytest.fail(f"Generated XHTML is not valid XML: {e}")

    def test_contains_xml_declaration(self, generator, valid_emissions_data):
        """Output should start with XML declaration."""
        xhtml = generator.generate(valid_emissions_data)
        assert xhtml.startswith('<?xml version="1.0" encoding="UTF-8"?>')

    def test_contains_required_namespaces(self, generator, valid_emissions_data):
        """Output should declare all required namespaces."""
        xhtml = generator.generate(valid_emissions_data)

        required_namespaces = [
            'xmlns="http://www.w3.org/1999/xhtml"',
            'xmlns:ix="http://www.xbrl.org/2013/inlineXBRL"',
            'xmlns:xbrli="http://www.xbrl.org/2003/instance"',
            'xmlns:esrs="https://xbrl.efrag.org/taxonomy/esrs/2023-12-22"',
        ]
        for ns in required_namespaces:
            assert ns in xhtml, f"Missing namespace: {ns}"

    def test_contains_ix_header(self, generator, valid_emissions_data):
        """Output should contain ix:header element."""
        xhtml = generator.generate(valid_emissions_data)
        assert '<ix:header>' in xhtml

    def test_contains_schema_reference(self, generator, valid_emissions_data):
        """Output should reference ESRS schema."""
        xhtml = generator.generate(valid_emissions_data)
        assert 'link:schemaRef' in xhtml
        assert 'esrs_cor.xsd' in xhtml

    def test_contains_context(self, generator, valid_emissions_data):
        """Output should contain xbrli:context element."""
        xhtml = generator.generate(valid_emissions_data)
        assert '<xbrli:context id="ctx_period">' in xhtml
        assert '<xbrli:entity>' in xhtml
        assert '<xbrli:period>' in xhtml

    def test_context_contains_lei(self, generator, valid_emissions_data):
        """Context should contain the LEI identifier."""
        xhtml = generator.generate(valid_emissions_data)
        assert valid_emissions_data.lei in xhtml

    def test_context_contains_period_dates(self, generator, valid_emissions_data):
        """Context should contain period start and end dates."""
        xhtml = generator.generate(valid_emissions_data)
        assert '<xbrli:startDate>2024-01-01</xbrli:startDate>' in xhtml
        assert '<xbrli:endDate>2024-12-31</xbrli:endDate>' in xhtml

    def test_contains_unit_definition(self, generator, valid_emissions_data):
        """Output should contain xbrli:unit element for tCO2e."""
        xhtml = generator.generate(valid_emissions_data)
        assert '<xbrli:unit id="unit_tCO2e">' in xhtml
        assert '<xbrli:measure>esrs:tCO2e</xbrli:measure>' in xhtml

    def test_invalid_data_raises_exception(self, generator):
        """Generator should raise exception for invalid data."""
        invalid_data = ESRSE1EmissionsData(
            entity_name="",  # Invalid
            lei="invalid",  # Invalid
            reporting_year=2024,
        )
        with pytest.raises(XBRLValidationError):
            generator.generate(invalid_data)


# =============================================================================
# ESRS E1 TAXONOMY ELEMENT TESTS
# =============================================================================

class TestESRSE1TaxonomyElements:
    """Tests for correct ESRS E1 taxonomy element usage."""

    def test_scope_1_element(self, generator, valid_emissions_data):
        """Scope 1 should use correct ESRS element."""
        xhtml = generator.generate(valid_emissions_data)
        assert 'name="esrs:GrossScope1GreenhouseGasEmissions"' in xhtml

    def test_scope_2_location_element(self, generator, valid_emissions_data):
        """Scope 2 location-based should use correct ESRS element."""
        xhtml = generator.generate(valid_emissions_data)
        assert 'name="esrs:GrossLocationBasedScope2GreenhouseGasEmissions"' in xhtml

    def test_scope_2_market_element(self, generator, valid_emissions_data):
        """Scope 2 market-based should use correct ESRS element."""
        xhtml = generator.generate(valid_emissions_data)
        # Market-based is optional but should be present in valid_emissions_data
        assert 'name="esrs:GrossMarketBasedScope2GreenhouseGasEmissions"' in xhtml

    def test_scope_3_element(self, generator, valid_emissions_data):
        """Scope 3 should use correct ESRS element."""
        xhtml = generator.generate(valid_emissions_data)
        assert 'name="esrs:GrossScope3GreenhouseGasEmissions"' in xhtml

    def test_total_emissions_element(self, generator, valid_emissions_data):
        """Total emissions should use correct ESRS element."""
        xhtml = generator.generate(valid_emissions_data)
        assert 'name="esrs:TotalGHGEmissions"' in xhtml

    def test_scope_3_category_elements(self, generator, valid_emissions_data):
        """Scope 3 categories should use correct ESRS elements."""
        xhtml = generator.generate(valid_emissions_data)

        # Check categories that are in the test data
        assert 'name="esrs:Scope3Category1PurchasedGoodsAndServices"' in xhtml
        assert 'name="esrs:Scope3Category4UpstreamTransportation"' in xhtml
        assert 'name="esrs:Scope3Category6BusinessTravel"' in xhtml
        assert 'name="esrs:Scope3Category7EmployeeCommuting"' in xhtml

    def test_emission_values_are_formatted(self, generator, valid_emissions_data):
        """Emission values should be formatted with commas and decimals."""
        xhtml = generator.generate(valid_emissions_data)
        # Check for properly formatted numbers (with commas)
        assert '1,500.25' in xhtml  # Scope 1
        assert '750.50' in xhtml  # Scope 2 location
        assert '2,250.75' in xhtml  # Scope 3

    def test_ix_non_fraction_attributes(self, generator, valid_emissions_data):
        """ix:nonFraction elements should have required attributes."""
        xhtml = generator.generate(valid_emissions_data)

        # Should have contextRef
        assert 'contextRef="ctx_period"' in xhtml
        # Should have unitRef
        assert 'unitRef="unit_tCO2e"' in xhtml
        # Should have decimals
        assert 'decimals="2"' in xhtml


# =============================================================================
# OUTPUT VALIDATION TESTS
# =============================================================================

class TestOutputValidation:
    """Tests for iXBRL output validation."""

    def test_validate_valid_output(self, generator, valid_emissions_data):
        """Valid output should pass validation."""
        xhtml = generator.generate(valid_emissions_data)
        result = validate_ixbrl_output(xhtml)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_validate_detects_missing_xml_declaration(self):
        """Validation should detect missing XML declaration."""
        invalid_xhtml = "<html><body>No XML declaration</body></html>"
        result = validate_ixbrl_output(invalid_xhtml)

        # Should either fail or have a warning
        assert not result.valid or len(result.warnings) > 0

    def test_validate_counts_facts(self, generator, valid_emissions_data):
        """Validation should count facts in output."""
        xhtml = generator.generate(valid_emissions_data)
        result = validate_ixbrl_output(xhtml)

        # Should have multiple numeric facts
        assert result.info.get('numeric_fact_count', 0) >= 4  # At least Scope 1,2,3,Total

    def test_validate_identifies_contexts(self, generator, valid_emissions_data):
        """Validation should identify context definitions."""
        xhtml = generator.generate(valid_emissions_data)
        result = validate_ixbrl_output(xhtml)

        assert 'ctx_period' in result.info.get('context_ids', [])

    def test_validate_identifies_units(self, generator, valid_emissions_data):
        """Validation should identify unit definitions."""
        xhtml = generator.generate(valid_emissions_data)
        result = validate_ixbrl_output(xhtml)

        assert 'unit_tCO2e' in result.info.get('unit_ids', [])

    def test_validate_reports_esrs_elements(self, generator, valid_emissions_data):
        """Validation should report which ESRS elements are found."""
        xhtml = generator.generate(valid_emissions_data)
        result = validate_ixbrl_output(xhtml)

        esrs_found = result.info.get('esrs_elements_found', {})
        assert esrs_found.get('GrossScope1GreenhouseGasEmissions') is True
        assert esrs_found.get('GrossLocationBasedScope2GreenhouseGasEmissions') is True
        assert esrs_found.get('GrossScope3GreenhouseGasEmissions') is True
        assert esrs_found.get('TotalGHGEmissions') is True


# =============================================================================
# CONVENIENCE FUNCTION TESTS
# =============================================================================

class TestGenerateESRSE1Report:
    """Tests for the generate_esrs_e1_report convenience function."""

    def test_generates_complete_report(self):
        """Function should generate complete report dict."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
        )

        assert 'content' in result
        assert 'validation' in result
        assert 'filename' in result
        assert 'total_emissions' in result

    def test_calculates_total_correctly(self):
        """Total emissions should be calculated correctly."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
        )

        assert result['total_emissions'] == 3000.0

    def test_validation_passes_for_valid_data(self):
        """Validation should pass for valid input."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
        )

        assert result['validation']['valid'] is True
        assert len(result['validation']['errors']) == 0

    def test_generates_filename(self):
        """Function should generate appropriate filename."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
        )

        assert result['filename'] == "esrs_e1_test_corporation_2024.xhtml"

    def test_accepts_optional_scope_2_market(self):
        """Function should accept optional market-based Scope 2."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
            scope_2_market=450.0,
        )

        assert 'GrossMarketBasedScope2GreenhouseGasEmissions' in result['content']

    def test_accepts_scope_3_categories(self):
        """Function should accept Scope 3 category breakdown."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
            scope_3_categories={
                "purchased_goods_services": 1000.0,
                "business_travel": 500.0,
            },
        )

        assert 'Scope3Category1PurchasedGoodsAndServices' in result['content']
        assert 'Scope3Category6BusinessTravel' in result['content']

    def test_accepts_additional_kwargs(self):
        """Function should accept additional optional fields."""
        result = generate_esrs_e1_report(
            entity_name="Test Corporation",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1=1000.0,
            scope_2_location=500.0,
            scope_3=1500.0,
            ghg_removals=100.0,
            carbon_credits_retired=50.0,
            internal_carbon_price=85.0,
        )

        assert 'GreenhouseGasRemovalsFromOwnOperations' in result['content']
        assert 'CarbonCreditsRetired' in result['content']
        assert 'InternalCarbonPrice' in result['content']


# =============================================================================
# TAXONOMY CLASS TESTS
# =============================================================================

class TestESRSE1Taxonomy:
    """Tests for ESRS E1 taxonomy constants."""

    def test_namespace_is_correct(self):
        """Taxonomy namespace should be correct EFRAG namespace."""
        assert "xbrl.efrag.org" in ESRS_E1_Taxonomy.NAMESPACE
        assert "esrs" in ESRS_E1_Taxonomy.NAMESPACE

    def test_all_scope_elements_defined(self):
        """All scope elements should be defined."""
        assert ESRS_E1_Taxonomy.GROSS_SCOPE_1_GHG.startswith("esrs:")
        assert ESRS_E1_Taxonomy.GROSS_SCOPE_2_LOCATION.startswith("esrs:")
        assert ESRS_E1_Taxonomy.GROSS_SCOPE_2_MARKET.startswith("esrs:")
        assert ESRS_E1_Taxonomy.GROSS_SCOPE_3_GHG.startswith("esrs:")
        assert ESRS_E1_Taxonomy.TOTAL_GHG_EMISSIONS.startswith("esrs:")

    def test_all_scope_3_categories_defined(self):
        """All 15 Scope 3 categories should be defined."""
        scope_3_attrs = [
            'SCOPE_3_CAT_1_PURCHASED',
            'SCOPE_3_CAT_2_CAPITAL',
            'SCOPE_3_CAT_3_FUEL_ENERGY',
            'SCOPE_3_CAT_4_UPSTREAM_TRANSPORT',
            'SCOPE_3_CAT_5_WASTE',
            'SCOPE_3_CAT_6_BUSINESS_TRAVEL',
            'SCOPE_3_CAT_7_COMMUTING',
            'SCOPE_3_CAT_8_UPSTREAM_LEASED',
            'SCOPE_3_CAT_9_DOWNSTREAM_TRANSPORT',
            'SCOPE_3_CAT_10_PROCESSING',
            'SCOPE_3_CAT_11_USE',
            'SCOPE_3_CAT_12_END_OF_LIFE',
            'SCOPE_3_CAT_13_DOWNSTREAM_LEASED',
            'SCOPE_3_CAT_14_FRANCHISES',
            'SCOPE_3_CAT_15_INVESTMENTS',
        ]
        for attr in scope_3_attrs:
            assert hasattr(ESRS_E1_Taxonomy, attr), f"Missing {attr}"
            value = getattr(ESRS_E1_Taxonomy, attr)
            assert value.startswith("esrs:"), f"{attr} should start with esrs:"

    def test_lei_scheme_is_correct(self):
        """LEI scheme should be correct."""
        assert "lei" in ESRS_E1_Taxonomy.LEI_SCHEME.lower()


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_very_large_emissions(self, generator):
        """Should handle very large emission values."""
        data = ESRSE1EmissionsData(
            entity_name="Large Emitter Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1_emissions=999999999.99,
            scope_2_location_based=888888888.88,
            scope_3_emissions=777777777.77,
        )
        xhtml = generator.generate(data)
        result = validate_ixbrl_output(xhtml)
        assert result.valid is True

    def test_very_small_emissions(self, generator):
        """Should handle very small emission values."""
        data = ESRSE1EmissionsData(
            entity_name="Small Emitter Corp",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1_emissions=0.01,
            scope_2_location_based=0.02,
            scope_3_emissions=0.03,
        )
        xhtml = generator.generate(data)
        result = validate_ixbrl_output(xhtml)
        assert result.valid is True

    def test_entity_name_with_special_chars(self, generator):
        """Should handle entity names with special characters."""
        data = ESRSE1EmissionsData(
            entity_name="Company & Sons <Ltd>",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            scope_1_emissions=100.0,
            scope_2_location_based=50.0,
            scope_3_emissions=150.0,
        )
        xhtml = generator.generate(data)
        result = validate_ixbrl_output(xhtml)
        assert result.valid is True
        # Should be escaped
        assert '&amp;' in xhtml
        assert '&lt;' in xhtml

    def test_custom_reporting_period(self, generator):
        """Should handle custom reporting periods."""
        data = ESRSE1EmissionsData(
            entity_name="Q1 Reporter",
            lei="5493001KJTIIGC8Y1R12",
            reporting_year=2024,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 3, 31),  # Q1 only
            scope_1_emissions=100.0,
            scope_2_location_based=50.0,
            scope_3_emissions=150.0,
        )
        xhtml = generator.generate(data)
        assert '2024-01-01' in xhtml
        assert '2024-03-31' in xhtml

    def test_no_css_option(self, valid_emissions_data):
        """Should work without CSS when disabled."""
        generator = IXBRLGenerator(include_css=False)
        xhtml = generator.generate(valid_emissions_data)

        assert '<style' not in xhtml
        result = validate_ixbrl_output(xhtml)
        assert result.valid is True

    def test_no_methodology_option(self, valid_emissions_data):
        """Should work without methodology section when disabled."""
        generator = IXBRLGenerator(include_methodology=False)
        xhtml = generator.generate(valid_emissions_data)

        assert 'Methodology Notes' not in xhtml
        result = validate_ixbrl_output(xhtml)
        assert result.valid is True


# =============================================================================
# REGRESSION TESTS
# =============================================================================

class TestRegression:
    """Regression tests for known issues."""

    def test_e1_7_section_only_when_data_present(self, generator, minimal_emissions_data):
        """E1-7 section should only appear when removals/credits data present."""
        xhtml = generator.generate(minimal_emissions_data)
        assert 'E1-7' not in xhtml  # Should not be present

        # Add removals
        minimal_emissions_data.ghg_removals = 50.0
        xhtml = generator.generate(minimal_emissions_data)
        assert 'E1-7' in xhtml  # Should now be present

    def test_e1_8_section_only_when_data_present(self, generator, minimal_emissions_data):
        """E1-8 section should only appear when internal carbon price present."""
        xhtml = generator.generate(minimal_emissions_data)
        assert 'E1-8' not in xhtml  # Should not be present

        # Add carbon price
        minimal_emissions_data.internal_carbon_price = 85.0
        xhtml = generator.generate(minimal_emissions_data)
        assert 'E1-8' in xhtml  # Should now be present

    def test_scope_3_detail_only_when_categories_present(self, generator, minimal_emissions_data):
        """Scope 3 detail section should only appear when categories present."""
        xhtml = generator.generate(minimal_emissions_data)
        assert 'scope3-detail' not in xhtml  # Should not be present

        # Add categories
        minimal_emissions_data.scope_3_categories = {"purchased_goods_services": 100.0}
        xhtml = generator.generate(minimal_emissions_data)
        assert 'scope3-detail' in xhtml  # Should now be present


# =============================================================================
# SECURITY MARKER
# =============================================================================

pytestmark = pytest.mark.security


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
