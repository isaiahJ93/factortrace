"""
FactorTrace Models - Multi-tenant enabled.

All tenant-owned models include tenant_id for isolation.
"""
from __future__ import annotations

from app.models.enums import (
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
)
from app.models.types import EmissionFactor, EmissionsRecord
from app.models.emission_data import EmissionData
from app.models.emissions_voucher import EmissionVoucher
from app.models.emissions_voucher import GHGBreakdown, DataQuality
from app.models.materiality import MaterialityAssessment, MaterialityType
from app.models.uncertainty_model import UncertaintyAssessment

# Core tenant-owned models (all have tenant_id)
from app.models.tenant import Tenant
from app.models.user import User
from app.models.emission import Emission
from app.models.voucher import Voucher
from app.models.payment import Payment
from app.models.data_quality import DataQualityScore
from app.models.evidence_document import EvidenceDocument

# CBAM regime models
from app.models.cbam import (
    CBAMFactorSource,
    CBAMProduct,
    CBAMDeclaration,
    CBAMDeclarationLine,
    CBAMInstallation,
    CBAMDeclarationStatus,
    CBAMFactorDataset,
    CBAMProductSector,
)

# EUDR regime models
from app.models.eudr import (
    EUDRCommodity,
    EUDROperator,
    EUDRSupplySite,
    EUDRBatch,
    EUDRSupplyChainLink,
    EUDRGeoRiskSnapshot,
    EUDRDueDiligence,
    EUDRDueDiligenceBatchLink,
    EUDRCommodityType,
    EUDROperatorRole,
    EUDRSupplyChainLinkType,
    EUDRRiskLevel,
    EUDRDueDiligenceStatus,
    EUDRGeoRiskSource,
)


__all__ = [
    # Core multi-tenant models
    "Tenant",
    "User",
    "Emission",
    "Voucher",
    "Payment",
    "DataQualityScore",
    "EvidenceDocument",
    # CBAM regime models
    "CBAMFactorSource",
    "CBAMProduct",
    "CBAMDeclaration",
    "CBAMDeclarationLine",
    "CBAMInstallation",
    "CBAMDeclarationStatus",
    "CBAMFactorDataset",
    "CBAMProductSector",
    # EUDR regime models
    "EUDRCommodity",
    "EUDROperator",
    "EUDRSupplySite",
    "EUDRBatch",
    "EUDRSupplyChainLink",
    "EUDRGeoRiskSnapshot",
    "EUDRDueDiligence",
    "EUDRDueDiligenceBatchLink",
    "EUDRCommodityType",
    "EUDROperatorRole",
    "EUDRSupplyChainLinkType",
    "EUDRRiskLevel",
    "EUDRDueDiligenceStatus",
    "EUDRGeoRiskSource",
    # Pydantic/domain models
    "EmissionFactor",
    "EmissionsRecord",
    "UncertaintyAssessment",
    "EmissionData",
    "GHGBreakdown",
    "DataQuality",
    "MaterialityAssessment",
    "MaterialityType",
    # Enums
    "GasTypeEnum",
    "TierLevelEnum",
    "UncertaintyDistributionEnum",
    "ValueChainStageEnum",
    "ScopeLevelEnum",
    "Scope3CategoryEnum",
    "GWPVersionEnum",
    "ConsolidationMethodEnum",
    "DataQualityTierEnum",
    "VerificationLevelEnum",
    "TemporalGranularityEnum",
]