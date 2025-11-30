"""
Spend-Based Calculation Service
================================
Implements EXIOBASE 3 spend-based emission factor lookup and calculation.
Uses kgCO2e per EUR factors from the EXIOBASE_2020 dataset.
"""
import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.emission_factor import EmissionFactor
from app.services.exiobase_mapping import (
    resolve_exiobase_sector,
    get_country_fallback_chain,
)

logger = logging.getLogger(__name__)

# Outlier threshold for EXIOBASE factors (kgCO2e per EUR)
# Factors above this are likely MRIO artifacts from low-activity country-sectors
# TODO: This is a temporary safeguard. Replace with a more sophisticated
#       outlier detection policy (e.g., percentile-based caps, sector-specific limits)
EXIOBASE_FACTOR_OUTLIER_THRESHOLD = 100.0  # kgCO2e per EUR


@dataclass
class SpendBasedResult:
    """Result of a spend-based emission calculation."""
    emissions_kg_co2e: float
    factor_value: float
    factor_unit: str
    country_code_used: str
    activity_type_used: str
    dataset: str
    method: str
    source: str
    regulation: str
    factor_outlier_warning: bool = False
    uncertainty_percentage: float = 20.0  # Default uncertainty for spend-based


class SpendBasedCalculationError(Exception):
    """Raised when spend-based calculation fails."""
    pass


def calculate_spend_based_emissions(
    db: Session,
    spend_amount_eur: float,
    country_code: str,
    exiobase_sector: Optional[str] = None,
    sector_label: Optional[str] = None,
    activity_type: Optional[str] = None,
) -> SpendBasedResult:
    """
    Calculate emissions using spend-based EXIOBASE factors.

    Args:
        db: Database session
        spend_amount_eur: Spend amount in EUR
        country_code: ISO2 country code (e.g., "DE", "US")
        exiobase_sector: Direct EXIOBASE sector name (highest priority)
        sector_label: User-friendly sector label to map (second priority)
        activity_type: Activity type to try mapping (fallback)

    Returns:
        SpendBasedResult with calculated emissions and metadata

    Raises:
        SpendBasedCalculationError: If no matching factor found or validation fails
    """
    # Validate inputs
    if spend_amount_eur <= 0:
        raise SpendBasedCalculationError(
            f"spend_amount_eur must be positive, got {spend_amount_eur}"
        )

    # Resolve the EXIOBASE sector
    resolved_sector = resolve_exiobase_sector(
        exiobase_sector=exiobase_sector,
        sector_label=sector_label,
        activity_type=activity_type,
    )

    if not resolved_sector:
        raise SpendBasedCalculationError(
            f"Could not resolve EXIOBASE sector from: "
            f"exiobase_sector={exiobase_sector}, sector_label={sector_label}, "
            f"activity_type={activity_type}. "
            "Please provide a valid exiobase_sector or sector_label."
        )

    # Get country fallback chain
    country_chain = get_country_fallback_chain(country_code)
    logger.debug(f"Country fallback chain for {country_code}: {country_chain}")

    # Try to find a factor using the country fallback chain
    factor = None
    country_used = None

    for try_country in country_chain:
        factor = (
            db.query(EmissionFactor)
            .filter(
                EmissionFactor.dataset == "EXIOBASE_2020",
                EmissionFactor.method == "spend_based",
                EmissionFactor.year == 2020,
                EmissionFactor.category == "spend_based",
                EmissionFactor.country_code == try_country,
                EmissionFactor.activity_type == resolved_sector,
            )
            .first()
        )

        if factor:
            country_used = try_country
            logger.debug(f"Found EXIOBASE factor for {try_country}/{resolved_sector}")
            break

    if not factor:
        raise SpendBasedCalculationError(
            f"No EXIOBASE_2020 emission factor found for sector '{resolved_sector}' "
            f"in countries {country_chain}. "
            f"Check that the sector name matches an EXIOBASE activity_type exactly."
        )

    # Check for outlier
    factor_outlier_warning = False
    factor_value = factor.factor

    if factor_value > EXIOBASE_FACTOR_OUTLIER_THRESHOLD:
        logger.warning(
            f"EXIOBASE factor outlier detected: {factor_value} kgCO2e/EUR "
            f"for {country_used}/{resolved_sector} (threshold: {EXIOBASE_FACTOR_OUTLIER_THRESHOLD}). "
            "This may be an MRIO artifact. Consider capping or excluding."
        )
        factor_outlier_warning = True
        # TODO: Decide whether to cap at threshold or return error
        # For now, we calculate but flag the warning
        # factor_value = min(factor_value, EXIOBASE_FACTOR_OUTLIER_THRESHOLD)

    # Calculate emissions
    emissions_kg_co2e = spend_amount_eur * factor_value

    return SpendBasedResult(
        emissions_kg_co2e=emissions_kg_co2e,
        factor_value=factor_value,
        factor_unit=factor.unit or "kgCO2e_per_EUR",
        country_code_used=country_used,
        activity_type_used=resolved_sector,
        dataset="EXIOBASE_2020",
        method="spend_based",
        source=factor.source or "EXIOBASE 3.9.4 IOT_2020_pxp",
        regulation=factor.regulation or "EXIOBASE",
        factor_outlier_warning=factor_outlier_warning,
        uncertainty_percentage=20.0,  # Higher uncertainty for spend-based
    )


def get_available_exiobase_sectors(db: Session, country_code: str = "DE") -> list[str]:
    """
    Get list of available EXIOBASE sectors for a country.

    Useful for frontend autocomplete/dropdown population.

    Args:
        db: Database session
        country_code: ISO2 country code (default: DE for full coverage)

    Returns:
        List of sector names available for the country
    """
    sectors = (
        db.query(EmissionFactor.activity_type)
        .filter(
            EmissionFactor.dataset == "EXIOBASE_2020",
            EmissionFactor.country_code == country_code,
        )
        .distinct()
        .all()
    )

    return sorted([s[0] for s in sectors if s[0]])


def get_exiobase_factor_info(
    db: Session,
    country_code: str,
    sector: str,
) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about an EXIOBASE factor.

    Useful for previewing factor before calculation.

    Args:
        db: Database session
        country_code: ISO2 country code
        sector: EXIOBASE sector name

    Returns:
        Dict with factor details or None if not found
    """
    country_chain = get_country_fallback_chain(country_code)

    for try_country in country_chain:
        factor = (
            db.query(EmissionFactor)
            .filter(
                EmissionFactor.dataset == "EXIOBASE_2020",
                EmissionFactor.country_code == try_country,
                EmissionFactor.activity_type == sector,
            )
            .first()
        )

        if factor:
            return {
                "factor": factor.factor,
                "unit": factor.unit,
                "country_code": try_country,
                "country_requested": country_code,
                "used_fallback": try_country != country_code,
                "activity_type": sector,
                "dataset": factor.dataset,
                "year": factor.year,
                "source": factor.source,
                "is_outlier": factor.factor > EXIOBASE_FACTOR_OUTLIER_THRESHOLD,
            }

    return None
