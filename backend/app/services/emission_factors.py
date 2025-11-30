# app/services/emission_factors.py
"""
Centralized Emission Factor Service - Database-Backed Version

Provides a strict, type-safe architecture for emission factor lookups.
All factor lookups should go through this service.

Lookup Strategy (simple, no waterfall):
1. Base filter: scope, category, activity_type, year
2. If dataset provided: try with dataset first, then without
3. Country handling: try country_code first, then GLOBAL fallback
4. No logic based on method, regulation, or validity periods (future use)
"""
import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Type alias for emission factor lookup key
FactorKey = tuple[str, str, str, str, int, str | None]


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


def _query_factor(
    db: Session,
    scope: str,
    category: str,
    activity_type: str,
    country_code: str,
    year: int,
    dataset: str | None = None,
) -> float | None:
    """
    Internal helper to query a single factor from the database.
    Returns the factor value if found, None otherwise.
    """
    from app.models.emission_factor import EmissionFactor

    query = db.query(EmissionFactor).filter(
        EmissionFactor.scope == scope,
        EmissionFactor.category == category,
        EmissionFactor.activity_type == activity_type,
        EmissionFactor.country_code == country_code,
        EmissionFactor.year == year,
    )

    if dataset is not None:
        query = query.filter(EmissionFactor.dataset == dataset)

    record = query.first()
    return record.factor if record else None


def get_factor(
    db: Session,
    *,
    scope: int | str,
    category: str,
    activity_type: str,
    country_code: str | None = None,
    year: int = 2024,
    dataset: str | None = None,
) -> float | None:
    """
    Look up emission factor from database.

    Lookup Strategy (simple, no waterfall):
    1. Base filter: scope, category, activity_type, year
    2. If dataset provided: try with dataset first, then without
    3. Country handling: try country_code first, then GLOBAL fallback
    4. Return None if nothing found

    Args:
        db: SQLAlchemy database session (required, keyword-only)
        scope: Emission scope (1, 2, 3 or "SCOPE_1", "SCOPE_2", "SCOPE_3")
        category: Emission category (e.g., "electricity")
        activity_type: Activity type (e.g., "Electricity - Grid Average")
        country_code: ISO country code (e.g., "DE", "FR") or None for GLOBAL
        year: Year for the factor (default 2024)
        dataset: Dataset name (e.g., "MASTER", "DEFRA_2024") - optional

    Returns:
        Emission factor (kgCO2e/unit) if found, None otherwise
    """
    # Normalize inputs
    scope_normalized = normalize_scope(scope)
    country_normalized = normalize_country_code(country_code)

    # Build lookup key for logging
    key: FactorKey = (scope_normalized, category, activity_type, country_normalized, year, dataset)
    logger.debug(f"Factor lookup: {key}")

    # STEP 1: If dataset is provided, try exact match with dataset first
    if dataset is not None:
        factor = _query_factor(db, scope_normalized, category, activity_type, country_normalized, year, dataset)
        if factor is not None:
            logger.debug(f"Factor found (exact + dataset={dataset}): {factor}")
            return factor

        # STEP 1b: Dataset provided but not found - try without dataset filter
        factor = _query_factor(db, scope_normalized, category, activity_type, country_normalized, year, None)
        if factor is not None:
            logger.debug(f"Factor found (no dataset filter): {factor}")
            return factor
    else:
        # STEP 2: No dataset provided - try exact match on country
        factor = _query_factor(db, scope_normalized, category, activity_type, country_normalized, year, None)
        if factor is not None:
            logger.debug(f"Factor found (exact): {factor}")
            return factor

    # STEP 3: Fallback to GLOBAL if country-specific not found
    if country_normalized != "GLOBAL":
        logger.debug(f"Trying GLOBAL fallback for {key}")

        # If dataset was provided, try GLOBAL + dataset first
        if dataset is not None:
            factor = _query_factor(db, scope_normalized, category, activity_type, "GLOBAL", year, dataset)
            if factor is not None:
                logger.debug(f"Factor found (GLOBAL + dataset={dataset}): {factor}")
                return factor

        # Try GLOBAL without dataset filter
        factor = _query_factor(db, scope_normalized, category, activity_type, "GLOBAL", year, None)
        if factor is not None:
            logger.debug(f"Factor found (GLOBAL fallback): {factor}")
            return factor

    # STEP 4: Not found
    logger.warning(f"No emission factor found for key: {key}")
    return None


def get_factor_strict(
    db: Session,
    *,
    scope: int | str,
    category: str,
    activity_type: str,
    country_code: str | None = None,
    year: int = 2024,
    dataset: str | None = None,
) -> float:
    """
    Look up emission factor - raises ValueError if not found.

    Same as get_factor but raises exception instead of returning None.
    Includes all lookup key fields in error message for debugging.
    """
    factor = get_factor(
        db,
        scope=scope,
        category=category,
        activity_type=activity_type,
        country_code=country_code,
        year=year,
        dataset=dataset,
    )
    if factor is None:
        key = {
            "scope": normalize_scope(scope),
            "category": category,
            "activity_type": activity_type,
            "country_code": normalize_country_code(country_code),
            "year": year,
            "dataset": dataset,
        }
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
            "dataset": f.dataset,
            "external_id": f.external_id,
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
