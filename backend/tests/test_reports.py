"""
Test Suite for CSRD Reports API
================================
Tests for POST /api/v1/reports/csrd-summary endpoint.

Covers:
1. Basic report generation
2. XHTML content validation
3. iXBRL tag presence
4. Error handling
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import date

# Import the FastAPI app
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestCSRDSummaryEndpoint:
    """Tests for CSRD summary report generation."""

    def test_csrd_summary_basic(self, client):
        """Test basic CSRD summary report generation."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company GmbH",
                "reporting_year": 2024,
                "include_methodology_notes": True
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert data["organization_name"] == "Test Company GmbH"
        assert data["reporting_year"] == 2024
        assert "total_emissions_kg_co2e" in data
        assert "total_emissions_tonnes_co2e" in data
        assert "scope_breakdown" in data
        assert "xhtml_content" in data
        assert "generated_at" in data

    def test_csrd_summary_with_lei(self, client):
        """Test CSRD summary with LEI included."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Acme Corporation",
                "reporting_year": 2024,
                "lei": "5493001KJTIIGC8Y1R12"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["lei"] == "5493001KJTIIGC8Y1R12"
        assert "5493001KJTIIGC8Y1R12" in data["xhtml_content"]

    def test_csrd_summary_custom_period(self, client):
        """Test CSRD summary with custom reporting period."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Corp",
                "reporting_year": 2024,
                "reporting_period_start": "2024-04-01",
                "reporting_period_end": "2025-03-31"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reporting_period_start"] == "2024-04-01"
        assert data["reporting_period_end"] == "2025-03-31"


class TestXHTMLContent:
    """Tests for XHTML content structure."""

    def test_xhtml_contains_ixbrl_tags(self, client):
        """Test that XHTML contains iXBRL tags."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        xhtml = response.json()["xhtml_content"]

        # Check for iXBRL namespace
        assert "xmlns:ix=" in xhtml
        assert "http://www.xbrl.org/2013/inlineXBRL" in xhtml

        # Check for ESRS namespace
        assert "xmlns:esrs=" in xhtml

        # Check for required iXBRL elements
        assert "ix:nonFraction" in xhtml
        assert "ix:context" in xhtml
        assert "ix:header" in xhtml

    def test_xhtml_contains_scope_emissions(self, client):
        """Test that XHTML contains scope emission tags."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        xhtml = response.json()["xhtml_content"]

        # Check for ESRS E1 emission tags
        assert "esrs:GrossScope1GHGEmissions" in xhtml
        assert "esrs:GrossScope2GHGEmissions" in xhtml
        assert "esrs:GrossScope3GHGEmissions" in xhtml
        assert "esrs:TotalGHGEmissions" in xhtml

    def test_xhtml_contains_organization_name(self, client):
        """Test that XHTML contains organization name in iXBRL tag."""
        org_name = "Unique Test Organization ABC"
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": org_name,
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        xhtml = response.json()["xhtml_content"]

        # Check organization name is in XHTML
        assert org_name in xhtml
        assert "esrs:ReportingEntityName" in xhtml

    def test_xhtml_contains_methodology_notes(self, client):
        """Test that methodology notes are included when requested."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2024,
                "include_methodology_notes": True
            }
        )

        assert response.status_code == 200
        xhtml = response.json()["xhtml_content"]

        # Check methodology section
        assert "Methodology Notes" in xhtml
        assert "GHG Protocol" in xhtml

    def test_xhtml_excludes_methodology_when_disabled(self, client):
        """Test that methodology notes are excluded when disabled."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2024,
                "include_methodology_notes": False
            }
        )

        assert response.status_code == 200
        xhtml = response.json()["xhtml_content"]

        # Methodology section should not be present
        assert "Methodology Notes" not in xhtml


class TestXHTMLDownload:
    """Tests for XHTML file download endpoint."""

    def test_xhtml_download_returns_file(self, client):
        """Test that XHTML download returns a file."""
        response = client.post(
            "/api/v1/reports/csrd-summary/xhtml",
            json={
                "organization_name": "Download Test Corp",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/xhtml+xml"
        assert "attachment" in response.headers.get("content-disposition", "")
        assert "Download_Test_Corp" in response.headers.get("content-disposition", "")
        assert ".xhtml" in response.headers.get("content-disposition", "")

    def test_xhtml_download_content_is_valid(self, client):
        """Test that downloaded XHTML content is valid."""
        response = client.post(
            "/api/v1/reports/csrd-summary/xhtml",
            json={
                "organization_name": "Test Corp",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        content = response.text

        # Check basic XHTML structure
        assert "<?xml version=" in content
        assert "<!DOCTYPE html>" in content
        assert "<html" in content
        assert "</html>" in content


class TestValidation:
    """Tests for request validation."""

    def test_missing_organization_name(self, client):
        """Test that missing organization name returns 422."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "reporting_year": 2024
            }
        )

        assert response.status_code == 422

    def test_missing_reporting_year(self, client):
        """Test that missing reporting year returns 422."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company"
            }
        )

        assert response.status_code == 422

    def test_invalid_reporting_year_too_low(self, client):
        """Test that reporting year before 2020 is rejected."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2019
            }
        )

        assert response.status_code == 422

    def test_invalid_reporting_year_too_high(self, client):
        """Test that reporting year after 2100 is rejected."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2101
            }
        )

        assert response.status_code == 422

    def test_empty_organization_name(self, client):
        """Test that empty organization name is rejected."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 422


class TestResponseStructure:
    """Tests for response structure."""

    def test_response_has_all_fields(self, client):
        """Test that response has all required fields."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Complete Test Corp",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        data = response.json()

        # Check all required fields
        required_fields = [
            "organization_name",
            "reporting_year",
            "reporting_period_start",
            "reporting_period_end",
            "total_emissions_kg_co2e",
            "total_emissions_tonnes_co2e",
            "scope_breakdown",
            "calculation_count",
            "datasets_used",
            "xhtml_content",
            "generated_at",
            "factortrace_version"
        ]

        for field in required_fields:
            assert field in data, f"Missing field: {field}"

    def test_scope_breakdown_structure(self, client):
        """Test that scope breakdown has correct structure."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        scope = response.json()["scope_breakdown"]

        assert "scope_1_kg_co2e" in scope
        assert "scope_2_kg_co2e" in scope
        assert "scope_3_kg_co2e" in scope

        # All values should be numbers
        assert isinstance(scope["scope_1_kg_co2e"], (int, float))
        assert isinstance(scope["scope_2_kg_co2e"], (int, float))
        assert isinstance(scope["scope_3_kg_co2e"], (int, float))

    def test_emissions_conversion_correct(self, client):
        """Test that kg to tonnes conversion is correct."""
        response = client.post(
            "/api/v1/reports/csrd-summary",
            json={
                "organization_name": "Test Company",
                "reporting_year": 2024
            }
        )

        assert response.status_code == 200
        data = response.json()

        # tonnes = kg / 1000
        expected_tonnes = data["total_emissions_kg_co2e"] / 1000
        assert abs(data["total_emissions_tonnes_co2e"] - expected_tonnes) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
