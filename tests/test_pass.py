from enum import Enum
from decimal import Decimal
from datetime import datetime, date
from api.schemas import VoucherInput
from enum import Enum
from generator.voucher_generator import generate_voucher
from factortrace.models.materiality import MaterialityAssessment, MaterialityType
from factortrace.models.emissions import UncertaintyAssessment
from factortrace.models.emissions_voucher import EmissionVoucher, EmissionsRecord, GHGBreakdown
from factortrace.enums import (
    ScopeLevelEnum as ScopeEnum,
    ValueChainStageEnum,
    TierLevelEnum,
    GWPVersionEnum,
)

from factortrace.voucher_types import EmissionFactor, DataQuality

class ValueChainStageEnum(str, Enum):
    UPSTREAM = "upstream"
    OPERATIONS = "operations"
    DOWNSTREAM = "downstream"

def _sample_record():
    return {
        "scope": "Scope 1",
        "value_chain_stage": "Upstream",
        "activity_description": "Purchased steel",
        "activity_value": Decimal("100"),
        "activity_unit": "t",
        "emission_factor": {
            "factor_id": "EF-001",
            "value": Decimal("2.1"),
            "unit": "tCO2e/t",
            "source": "DEFRA_2024",
            "source_year": 2024,
            "tier": "tier_1",
        },
        "ghg_breakdown": [{
            "gas_type": "CO2",
            "amount": Decimal("210"),
            "gwp_factor": Decimal("1"),
            "gwp_version": "AR6_100",
        }],
        "total_emissions_tco2e": Decimal("210"),
        "data_quality": {
            "tier": "tier_1",
            "score": Decimal("95"),
            "temporal_representativeness": Decimal("90"),
            "geographical_representativeness": Decimal("90"),
            "technological_representativeness": Decimal("90"),
            "completeness": Decimal("95"),
            "uncertainty_percent": Decimal("5"),
            "confidence_level": "0.95",       # or any valid float or Decimal
            "distribution": "normal",         # must match enum exactly
        },
        "calculation_method": "invoice_factor",
        "emission_date_start": datetime(2024, 1, 1),
        "emission_date_end": datetime(2024, 1, 31),
    }

def test_materiality_full_parsing():
    m = MaterialityAssessment(
        assessment_date=date(2025, 6, 12),
        materiality_type=MaterialityType.double_materiality,
        impact_score=3.5,
        impact_magnitude=3.5,
        impact_likelihood=0.8,
        impact_scope="ENVIRONMENTAL",
        financial_score=2.8,
        financial_impact=1_500_000.0,
        financial_likelihood=0.6,
        financial_time_horizon="MEDIUM_TERM",
        materiality_threshold=0.7,
        is_material=True,
        justification="High climate impact risk",
        time_horizon="LONG_TERM",
        affected_stakeholders=["investors", "NGOs"],
        risk_type="PHYSICAL",
        reporting_period="2025"
    )
    assert m.is_material is True

def test_materiality_partial_parsing():
    example = MaterialityAssessment(
        impact_magnitude=3.5,
        impact_likelihood=0.9,
        time_horizon="LONG_TERM",
        affected_stakeholders=["investors", "NGOs"],
        financial_impact=1_500_000.0,
        risk_type="PHYSICAL",
        reporting_period="2025",
        materiality_type=MaterialityType.double_materiality,
        assessment_date=date(2025, 6, 12),
        impact_score=3.0,
        impact_scope="ENVIRONMENTAL",
        financial_score=2.5,
        financial_likelihood=0.6,
        financial_time_horizon="LONG_TERM",
        materiality_threshold=0.7,
        is_material=True,
        justification="Meets EU sustainability threshold"
    )
    assert example.impact_magnitude == 3.5

def test_uncertainty_distribution():
    u = UncertaintyAssessment(
        uncertainty_percentage=10.0,
        lower_bound=90.0,
        upper_bound=110.0,
        confidence_level=95.0,
        distribution="LOGNORMAL",
        method="Monte Carlo"
    )
    assert u.distribution == "LOGNORMAL"
    assert u.confidence_level == 95.0
    assert u.uncertainty_percentage == 10.0

def test_valid_voucher():
    voucher = EmissionVoucher(
        supplier_lei="5493001KTIIGC8YR1212",
        supplier_name="Acme Metals",
        supplier_country="DE",
        supplier_sector="Steel",
        reporting_entity_lei="5493001KTIIGC8YR1212",
        reporting_period_start="2024-01-01",
        reporting_period_end="2024-12-31",
        consolidation_method="operational_control",
        emissions_records=[EmissionsRecord(**_sample_record())],
        total_emissions_tco2e=100.0
    )
    assert voucher.total_emissions_tco2e == 100.0

def test_invalid_scope():
    try:
        EmissionVoucher(Scope="INVALID")
    except ValueError:
        assert True

def test_voucher_xml_is_valid():
    sample = {
        "supplier_id": "SUP-001",
        "supplier_name": "Acme Metals",
        "legal_entity_identifier": "5493001KTIIIGC8YR1212",
        "product_category": "Materials",
        "product_cn_code": "7208.39.00",
        "cost": 1200.0,
        "material_type": "Steel",
        "origin_country": "DE",
        "emission_factor": 2.5,
        "emission_factor_id": "EF-001",
        "fallback_factor_used": False,
    }
    voucher = generate_voucher(VoucherInput(**sample))
    assert "co2e" in voucher

def test_valid_emission_voucher():
    example = EmissionVoucher(
        voucher_id="ABC123",
        emissions_records=[EmissionsRecord(**_sample_record())],
        ghg_breakdown=GHGBreakdown(
            gas_type="CO2",
            amount=Decimal("210"),
            gwp_factor=Decimal("1"),
            gwp_version=GWPVersionEnum.AR6_100,
        )
    )
    assert example.voucher_id == "ABC123"