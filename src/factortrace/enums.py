from factortrace.models.common_enums import (
    Scope3CategoryEnum,
    VerificationLevelEnum,
    AuditActionEnum,
    ConsolidationMethodEnum,
    TargetTypeEnum,
    GWPVersionEnum,
)

from enum import Enum

class MaterialityTypeEnum(str, Enum):
    FINANCIAL = "financial"
    IMPACT = "impact"