"""
Test Suite for Unified Calculation API
======================================
Tests for POST /api/v1/emissions/calculate endpoint.

Covers:
1. Activity-based calculations (DEFRA, EPA)
2. Spend-based calculations (EXIOBASE)
3. Dataset auto-selection based on country
4. Error handling for missing factors
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Import the FastAPI app
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestActivityBasedCalculation:
    """Tests for activity-based emission calculations (DEFRA/EPA)."""

    def test_activity_based_with_mocked_factor(self, client):
        """Test activity-based calculation with mocked database factor."""
        # Mock the get_factor function to return a known value
        with patch("app.api.v1.endpoints.emissions.get_factor") as mock_get_factor:
            mock_get_factor.return_value = 0.233  # kgCO2e/kWh

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "activity_data",
                    "dataset": "AUTO",
                    "scope": 2,
                    "country_code": "GB",
                    "amount": "10000",
                    "unit": "kWh",
                    "category": "electricity",
                    "activity_type": "Electricity - Grid Average"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["method_used"] == "activity_data"
            assert data["dataset_used"] == "DEFRA_2024"
            assert data["scope"] == 2
            assert data["country_code"] == "GB"
            assert data["activity_type_used"] == "Electricity - Grid Average"
            # 10000 * 0.233 = 2330 kgCO2e
            assert abs(data["emissions_kg_co2e"] - 2330.0) < 0.01
            assert data["factor_value"] == 0.233

    def test_auto_dataset_selects_defra_for_gb(self, client):
        """Test that AUTO dataset selection picks DEFRA for GB."""
        with patch("app.api.v1.endpoints.emissions.get_factor") as mock_get_factor:
            mock_get_factor.return_value = 0.35

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "activity_data",
                    "dataset": "AUTO",
                    "scope": 2,
                    "country_code": "GB",
                    "amount": "1000",
                    "unit": "kWh",
                    "category": "electricity",
                    "activity_type": "Electricity"
                }
            )

            assert response.status_code == 200
            assert response.json()["dataset_used"] == "DEFRA_2024"

    def test_auto_dataset_selects_epa_for_us(self, client):
        """Test that AUTO dataset selection picks EPA for US."""
        with patch("app.api.v1.endpoints.emissions.get_factor") as mock_get_factor:
            mock_get_factor.return_value = 0.42

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "activity_data",
                    "dataset": "AUTO",
                    "scope": 1,
                    "country_code": "US",
                    "amount": "500",
                    "unit": "liters",
                    "category": "stationary_combustion",
                    "activity_type": "Natural Gas"
                }
            )

            assert response.status_code == 200
            assert response.json()["dataset_used"] == "EPA_2024"

    def test_factor_not_found_returns_422_with_lookup_key(self, client):
        """Test that missing factor returns 422 with lookup key details."""
        with patch("app.api.v1.endpoints.emissions.get_factor") as mock_get_factor:
            mock_get_factor.return_value = None  # No factor found

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "activity_data",
                    "dataset": "AUTO",
                    "scope": 2,
                    "country_code": "XX",
                    "amount": "1000",
                    "unit": "kWh",
                    "category": "unknown_category",
                    "activity_type": "Unknown Activity"
                }
            )

            assert response.status_code == 422
            data = response.json()
            assert "detail" in data
            assert data["detail"]["error"] == "FACTOR_NOT_FOUND"
            assert "lookup_key" in data["detail"]
            assert data["detail"]["lookup_key"]["country_code"] == "XX"
            assert data["detail"]["lookup_key"]["category"] == "unknown_category"

    def test_missing_category_returns_422(self, client):
        """Test that missing category field returns validation error."""
        response = client.post(
            "/api/v1/emissions/calculate",
            json={
                "method": "activity_data",
                "scope": 2,
                "country_code": "DE",
                "amount": "1000",
                "unit": "kWh",
                # Missing: category and activity_type
            }
        )

        assert response.status_code == 422


class TestSpendBasedCalculation:
    """Tests for spend-based emission calculations (EXIOBASE)."""

    def test_spend_based_with_sector_label(self, client):
        """Test spend-based calculation using sector_label."""
        with patch("app.api.v1.endpoints.emissions.calculate_spend_based_emissions") as mock_calc:
            # Create mock result
            mock_result = MagicMock()
            mock_result.emissions_kg_co2e = 3500.0
            mock_result.factor_value = 0.07
            mock_result.factor_unit = "kgCO2e_per_EUR"
            mock_result.dataset = "EXIOBASE_2020"
            mock_result.country_code_used = "DE"
            mock_result.activity_type_used = "Computer and related services (72)"
            mock_result.factor_outlier_warning = False
            mock_calc.return_value = mock_result

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "spend_based",
                    "scope": 3,
                    "country_code": "DE",
                    "amount": "50000",
                    "unit": "EUR",
                    "sector_label": "IT Services"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["method_used"] == "spend_based"
            assert data["dataset_used"] == "EXIOBASE_2020"
            assert data["emissions_kg_co2e"] == 3500.0
            assert data["sector_used"] == "Computer and related services (72)"

    def test_spend_based_with_exiobase_activity_type(self, client):
        """Test spend-based calculation using exact exiobase_activity_type."""
        with patch("app.api.v1.endpoints.emissions.calculate_spend_based_emissions") as mock_calc:
            mock_result = MagicMock()
            mock_result.emissions_kg_co2e = 11000.0
            mock_result.factor_value = 0.22
            mock_result.factor_unit = "kgCO2e_per_EUR"
            mock_result.dataset = "EXIOBASE_2020"
            mock_result.country_code_used = "FR"
            mock_result.activity_type_used = "Motor vehicles, trailers and semi-trailers (34)"
            mock_result.factor_outlier_warning = False
            mock_calc.return_value = mock_result

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "spend_based",
                    "scope": 3,
                    "country_code": "FR",
                    "amount": "50000",
                    "unit": "EUR",
                    "exiobase_activity_type": "Motor vehicles, trailers and semi-trailers (34)"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["method_used"] == "spend_based"
            assert data["sector_used"] == "Motor vehicles, trailers and semi-trailers (34)"

    def test_spend_based_with_outlier_warning(self, client):
        """Test that outlier factors include warning in notes."""
        with patch("app.api.v1.endpoints.emissions.calculate_spend_based_emissions") as mock_calc:
            mock_result = MagicMock()
            mock_result.emissions_kg_co2e = 15000.0
            mock_result.factor_value = 150.0  # Above 100 threshold
            mock_result.factor_unit = "kgCO2e_per_EUR"
            mock_result.dataset = "EXIOBASE_2020"
            mock_result.country_code_used = "DE"
            mock_result.activity_type_used = "Mining sector"
            mock_result.factor_outlier_warning = True
            mock_calc.return_value = mock_result

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "spend_based",
                    "scope": 3,
                    "country_code": "DE",
                    "amount": "100",
                    "unit": "EUR",
                    "sector_label": "Mining"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["notes"] is not None
            assert "outlier" in data["notes"].lower()
            assert "150" in data["notes"]

    def test_spend_based_missing_sector_returns_422(self, client):
        """Test that spend-based without sector info returns 422."""
        response = client.post(
            "/api/v1/emissions/calculate",
            json={
                "method": "spend_based",
                "scope": 3,
                "country_code": "DE",
                "amount": "50000",
                "unit": "EUR"
                # Missing: sector_label and exiobase_activity_type
            }
        )

        assert response.status_code == 422
        data = response.json()
        assert data["detail"]["error"] == "MISSING_SECTOR"


class TestValidation:
    """Tests for request validation."""

    def test_invalid_amount_zero(self, client):
        """Test that zero amount is rejected."""
        response = client.post(
            "/api/v1/emissions/calculate",
            json={
                "method": "activity_data",
                "scope": 2,
                "country_code": "DE",
                "amount": "0",
                "unit": "kWh",
                "category": "electricity",
                "activity_type": "Electricity"
            }
        )

        assert response.status_code == 422

    def test_invalid_amount_negative(self, client):
        """Test that negative amount is rejected."""
        response = client.post(
            "/api/v1/emissions/calculate",
            json={
                "method": "activity_data",
                "scope": 2,
                "country_code": "DE",
                "amount": "-100",
                "unit": "kWh",
                "category": "electricity",
                "activity_type": "Electricity"
            }
        )

        assert response.status_code == 422

    def test_missing_required_fields(self, client):
        """Test that missing required fields return 422."""
        # Missing method
        response = client.post(
            "/api/v1/emissions/calculate",
            json={
                "scope": 2,
                "country_code": "DE",
                "amount": "1000",
                "unit": "kWh"
            }
        )
        assert response.status_code == 422

    def test_country_code_normalization(self, client):
        """Test that country codes are normalized to uppercase."""
        with patch("app.api.v1.endpoints.emissions.get_factor") as mock_get_factor:
            mock_get_factor.return_value = 0.35

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "activity_data",
                    "scope": 2,
                    "country_code": "de",  # lowercase
                    "amount": "1000",
                    "unit": "kWh",
                    "category": "electricity",
                    "activity_type": "Electricity"
                }
            )

            assert response.status_code == 200
            assert response.json()["country_code"] == "DE"


class TestResponseStructure:
    """Tests for response structure and content."""

    def test_activity_response_has_all_fields(self, client):
        """Test that activity-based response has all required fields."""
        with patch("app.api.v1.endpoints.emissions.get_factor") as mock_get_factor:
            mock_get_factor.return_value = 0.35

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "activity_data",
                    "scope": 2,
                    "country_code": "DE",
                    "amount": "1000",
                    "unit": "kWh",
                    "category": "electricity",
                    "activity_type": "Electricity"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check all required fields are present
            assert "emissions_kg_co2e" in data
            assert "factor_value" in data
            assert "factor_unit" in data
            assert "dataset_used" in data
            assert "method_used" in data
            assert "scope" in data
            assert "country_code" in data
            assert "activity_type_used" in data
            assert "sector_used" in data
            assert "notes" in data

    def test_spend_response_has_all_fields(self, client):
        """Test that spend-based response has all required fields."""
        with patch("app.api.v1.endpoints.emissions.calculate_spend_based_emissions") as mock_calc:
            mock_result = MagicMock()
            mock_result.emissions_kg_co2e = 3500.0
            mock_result.factor_value = 0.07
            mock_result.factor_unit = "kgCO2e_per_EUR"
            mock_result.dataset = "EXIOBASE_2020"
            mock_result.country_code_used = "DE"
            mock_result.activity_type_used = "Computer and related services (72)"
            mock_result.factor_outlier_warning = False
            mock_calc.return_value = mock_result

            response = client.post(
                "/api/v1/emissions/calculate",
                json={
                    "method": "spend_based",
                    "scope": 3,
                    "country_code": "DE",
                    "amount": "50000",
                    "unit": "EUR",
                    "sector_label": "IT Services"
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check all required fields are present
            assert "emissions_kg_co2e" in data
            assert "factor_value" in data
            assert "factor_unit" in data
            assert "dataset_used" in data
            assert "method_used" in data
            assert "scope" in data
            assert "country_code" in data
            assert "sector_used" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
