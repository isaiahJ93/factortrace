# app/services/emission_factors.py
"""
Centralized Emission Factor Service - Database-Backed Version

Provides a strict, type-safe architecture for emission factor lookups.
All factor lookups should go through this service.

This version uses the database (EmissionFactor model) as the primary source,
with fallback logic for country-specific to GLOBAL factors.
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Type alias for emission factor lookup key
FactorKey = tuple[str, str, str, str]


def normalize_scope(scope: int | str) -> str:
    """Normalize scope to string format (e.g., 1 -> 'SCOPE_1', 2 -> 'SCOPE_2')"""
    if isinstance(scope, int):
        return f"SCOPE_{scope}"
    if isinstance(scope, str):
        scope_upper = scope.upper().strip()
        if scope_upper.startswith("SCOPE_"):
            return scope_upper
        if scope_upper.isdigit():
            return f"SCOPE_{scope_upper}"
        return scope_upper
    return str(scope)


def normalize_country_code(country_code: str | None) -> str:
    """Normalize country code to uppercase, default to GLOBAL"""
    if not country_code:
        return "GLOBAL"
    return country_code.upper().strip()


def get_factor(
    scope: int | str,
    category: str,
    activity_type: str,
    country_code: str | None = None,
    db: Session | None = None,
    year: int = 2024
) -> float | None:
    """
    Look up emission factor from database.

    Logic:
    1. Try exact match on (scope, category, activity_type, country_code, year)
    2. If not found, try match on (scope, category, activity_type, 'GLOBAL', year)
    3. Return factor or None

    Args:
        scope: Emission scope (1, 2, 3 or "SCOPE_1", "SCOPE_2", "SCOPE_3")
        category: Emission category (e.g., "Purchased Electricity")
        activity_type: Activity type (e.g., "Electricity", "Flight")
        country_code: ISO country code (e.g., "DE", "FR") or None for GLOBAL
        db: SQLAlchemy database session (required)
        year: Year for the factor (default 2024)

    Returns:
        Emission factor (kgCO2e/unit) if found, None otherwise
    """
    # Normalize inputs
    scope_normalized = normalize_scope(scope)
    country_normalized = normalize_country_code(country_code)

    # Build lookup key for logging
    key: FactorKey = (scope_normalized, category, activity_type, country_normalized)

    # If no database session provided, return None
    if db is None:
        logger.warning(f"No database session provided for factor lookup: {key}")
        return None

    # Import here to avoid circular imports
    from app.models.emission_factor import EmissionFactor

    # STEP 1: Try exact match on (scope, category, activity_type, country_code, year)
    factor_record = db.query(EmissionFactor).filter(
        EmissionFactor.scope == scope_normalized,
        EmissionFactor.category == category,
        EmissionFactor.activity_type == activity_type,
        EmissionFactor.country_code == country_normalized,
        EmissionFactor.year == year
    ).first()

    if factor_record:
        logger.debug(f"Factor found for {key}: {factor_record.factor}")
        return factor_record.factor

    # STEP 2: Fallback to GLOBAL if country-specific not found
    if country_normalized != "GLOBAL":
        global_key: FactorKey = (scope_normalized, category, activity_type, "GLOBAL")
        global_record = db.query(EmissionFactor).filter(
            EmissionFactor.scope == scope_normalized,
            EmissionFactor.category == category,
            EmissionFactor.activity_type == activity_type,
            EmissionFactor.country_code == "GLOBAL",
            EmissionFactor.year == year
        ).first()

        if global_record:
            logger.debug(f"Using GLOBAL fallback for {key}: {global_record.factor}")
            return global_record.factor

    # STEP 3: Not found
    logger.warning(f"No emission factor found for key: {key}")
    return None


def get_factor_strict(
    scope: int | str,
    category: str,
    activity_type: str,
    country_code: str | None = None,
    db: Session | None = None,
    year: int = 2024
) -> float:
    """
    Look up emission factor - raises ValueError if not found.

    Same as get_factor but raises exception instead of returning None.
    """
    factor = get_factor(scope, category, activity_type, country_code, db, year)
    if factor is None:
        key = (normalize_scope(scope), category, activity_type, normalize_country_code(country_code))
        raise ValueError(f"No emission factor found for key: {key}")
    return factor


def list_available_factors(db: Session) -> list[dict]:
    """List all available emission factors from database"""
    from app.models.emission_factor import EmissionFactor

    factors = db.query(EmissionFactor).all()

    return [
        {
            "id": f.id,
            "scope": f.scope,
            "category": f.category,
            "activity_type": f.activity_type,
            "country_code": f.country_code,
            "year": f.year,
            "factor": f.factor,
            "unit": f.unit,
            "source": f.source,
            "method": f.method,
            "regulation": f.regulation,
        }
        for f in factors
    ]


# Export list
__all__ = [
    "FactorKey",
    "get_factor",
    "get_factor_strict",
    "normalize_scope",
    "normalize_country_code",
    "list_available_factors",
]
