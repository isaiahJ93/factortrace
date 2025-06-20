from __future__ import annotations
from factortrace.shared_enums import (
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

from enum import Enum
from factortrace.emissions_voucher import generate_voucher
from factortrace.emissions_calculator import calculate_emissions
from factortrace.compliance_engine import generate_ixbrl_report
from factortrace.factor_loader import load_factors
# src/cli/generate_report.py
import json
from decimal import Decimal

from factortrace.shared_enums import (
    ScopeLevelEnum,
    ValueChainStageEnum,
    Scope3CategoryEnum,

from factortrace.models.emissions_voucher import EmissionData


def generate_voucher(file_path: str, scope_enum: ScopeLevelEnum) -> EmissionData:
    with open(file_path) as f:
        data = json.load(f)

    return EmissionData(
        supplier_id=data.get("supplier_id", "SUP-DEFAULT"),
        scope=scope_enum,
        value_chain_stage=ValueChainStageEnum.UPSTREAM,
        scope3_category=Scope3CategoryEnum.CATEGORY_1,
        emissions_amount=Decimal(str(data.get("emissions_amount", "0.0"))),
        unit=data.get("unit", "tCO2e"),


def generate_compliance_report() -> None:
    file_path = "src/data/input_data.json"      # ← ensure this exists
    scope_enum = ScopeLevelEnum.scope_3

    voucher = generate_voucher(file_path, scope_enum)
    print("✅ Voucher generated:")
    print(voucher.model_dump_json(indent=2))


class ScopeLevelEnum(str, Enum):
    SCOPE_1 = "SCOPE_1"
    SCOPE_2 = "SCOPE_2"
)
    SCOPE_3 = "SCOPE_3")
