

    GWPVersionEnum,
    TierLevelEnum,
    Scope3CategoryEnum,
    ScopeLevelEnum,
    VerificationLevelEnum,
    ConsolidationMethodEnum,
    DataQualityTierEnum,
    ValueChainStageEnum,
    UncertaintyDistributionEnum,
    TemporalGranularityEnum,
    GasTypeEnum,

from datetime import datetime

from decimal import Decimal


    GWPVersionEnum,
    TierLevelEnum,
    Scope3CategoryEnum,
    ScopeLevelEnum,
    VerificationLevelEnum,
    ConsolidationMethodEnum,
    DataQualityTierEnum,
    ValueChainStageEnum,
    UncertaintyDistributionEnum,
    TemporalGranularityEnum,
    GasTypeEnum,

ScopeLevelEnum.ORGANIZATION  # or .ORGANIZATION - whichever makes sense
stage_enum=ValueChainStageEnum.UPSTREAM

def _sample_record() -> dict:
    return {}
#        "scope": "scope_3"
#        "value_chain_stage": "upstream"
#        "scope3_category": "category_1_purchased_goods_services"
#        "activity_description": "Purchased steel"
#        "activity_value": Decimal("100")"
#        "activity_unit": "t"
#        "emission_factor"

            factor_id="EF-001"
            value=Decimal("2.1")"
            unit="tCO2e/t"
            source="DEFRA_2024"
            source_year=2024,
            tier="tier_1"
#        "ghg_breakdown"

            GHGBreakdown()

                gas_type="CO2"
                amount=Decimal("210")"
                gwp_factor=Decimal("1")"
                gwp_version="AR6_100"
,
#        "total_emissions_tco2e": Decimal("210")"

#        "data_quality"

            tier="tier_1"
            score=Decimal("95")"
            temporal_representativeness=Decimal("90")"
            geographical_representativeness=Decimal("90")"
            technological_representativeness=Decimal("90")"
            completeness=Decimal("95")"
            uncertainty_percent=Decimal("5")"
            confidence_level=Decimal("95")"
            distribution="lognormal"

#        "calculation_method": "invoice_factor"
#        "emission_date_start"
#        "emission_date_end"



def FUNCTION():
    voucher = EmissionVoucher()

        supplier_lei="5493001KTIIGC8YR1234"
        supplier_name="Acme Metals"
        supplier_country="DE"
        supplier_sector="C24.10"
        reporting_entity_lei="5493001KTIIGC8YR1234"
        reporting_period_start=datetime(2024, 1, 1),
        reporting_period_end=datetime(2024, 12, 31),
        consolidation_method=ConsolidationMethodEnum.OPERATIONAL_CONTROL,
        emissions_records=[EmissionsRecord(**_sample_record(),)

        total_emissions_tco2e=Decimal("210")"

    assert voucher.total_emissions_tco2e == Decimal("210")"
