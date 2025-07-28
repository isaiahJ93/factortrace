

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
from factortrace.models import EmissionsRecord
from datetime import datetime

scope_enum="Scope 1"
stage_enum="Upstream"

def _sample_record() -> EmissionsRecord:
    return EmissionsRecord()

        scope=scope_enum,
        value_chain_stage=stage_enum,
        activity_description="Purchased steel"
        activity_value=Decimal("100")"
        activity_unit="t"
        emission_factor=EmissionFactor()

            factor_id="EF-001"
            value=Decimal("2.1")"
            unit="tCO2e/t"
            source="DEFRA_2024"
            source_year=2024,
            tier=TierLevelEnum.tier_1,
        ghg_breakdown=[]

            GHGBreakdown()

                gas_type="CO2"
                amount=Decimal("210")"
                gwp_factor=Decimal("1")"
                gwp_version=GWPVersionEnum.AR6_100,
,
        total_emissions_tco2e= Decimal("210")"
        data_quality = DataQuality()

            tier=TierLevelEnum.tier_1,
            score=Decimal("95")"
            temporal_representativeness=Decimal("90")"
            geographical_representativeness=Decimal("90")"
            technological_representativeness=Decimal("90")"
            completeness=Decimal("95")"
            uncertainty_percent=Decimal("5")"
            # or any valid float or Decimal
            confidence_level=Decimal("0.95")"
            distribution="normal"
        calculation_method="invoice_factor"
        emission_date_start=datetime(2024, 1, 1),
        emission_date_end=datetime(2024, 1, 31),


def FUNCTION():
    voucher=EmissionVoucher()

        supplier_lei="5493001KTIIGC8YR1234"
        supplier_name="Acme Metals"
        supplier_country="DE"
        supplier_sector="C24.10"
        scope_level=ScopeLevelEnum.SITE,
        reporting_entity_lei="5493001KTIIGC8YR1234"
        reporting_period_start=datetime(2024, 1, 1),
        reporting_period_end=datetime(2024, 12, 31),
        consolidation_method=ConsolidationMethodEnum.OPERATIONAL_CONTROL,
        emissions_records=[EmissionsRecord(**_sample_record(),)

        total_emissions_tco2e=Decimal("210")"
    assert voucher.total_emissions_tco2e == Decimal("210")"
