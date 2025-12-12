# app/utils/units.py
"""
Unit validation and conversion utilities using Pint.

Per CLAUDE.md: Use the Pint library for unit normalization.
Internal canonical units:
  - Energy: kWh, MJ
  - Distance: km
  - Mass: kg
  - Volume: L

Usage:
    from app.utils.units import validate_unit, convert_to_canonical, UnitError

    # Validate a unit string
    is_valid = validate_unit("kWh")  # True

    # Convert to canonical unit
    canonical_value, canonical_unit = convert_to_canonical(1000, "Wh", "energy")
    # Returns (1.0, "kWh")
"""
from typing import Optional, Tuple, Dict, List
import logging

try:
    import pint
    PINT_AVAILABLE = True
    ureg = pint.UnitRegistry()
    # Define some custom units that might appear in emissions data
    ureg.define("tonne = 1000 * kg = t = metric_ton")
    ureg.define("kgCO2e = kg")
    ureg.define("tCO2e = tonne")
except ImportError:
    PINT_AVAILABLE = False
    ureg = None

logger = logging.getLogger(__name__)


class UnitError(ValueError):
    """Raised when a unit is invalid or cannot be converted."""
    pass


# Canonical units by dimension
CANONICAL_UNITS: Dict[str, str] = {
    "energy": "kWh",
    "distance": "km",
    "mass": "kg",
    "volume": "L",
    "area": "m**2",
    "time": "hour",
    "currency": "EUR",  # For spend-based calculations
}

# Common unit aliases (case-insensitive mapping)
UNIT_ALIASES: Dict[str, str] = {
    # Energy
    "kwh": "kWh",
    "mwh": "MWh",
    "gwh": "GWh",
    "wh": "Wh",
    "mj": "MJ",
    "gj": "GJ",
    "kj": "kJ",
    "j": "J",
    "therm": "therm",
    "btu": "BTU",
    # Mass
    "kg": "kg",
    "g": "g",
    "mg": "mg",
    "t": "tonne",
    "tonne": "tonne",
    "tonnes": "tonne",
    "ton": "ton",
    "tons": "ton",
    "lb": "lb",
    "lbs": "lb",
    "oz": "oz",
    # Distance
    "km": "km",
    "m": "m",
    "cm": "cm",
    "mm": "mm",
    "mi": "mile",
    "mile": "mile",
    "miles": "mile",
    "ft": "ft",
    "yd": "yard",
    # Volume
    "l": "L",
    "litre": "L",
    "liter": "L",
    "litres": "L",
    "liters": "L",
    "ml": "mL",
    "m3": "m**3",
    "m³": "m**3",
    "gal": "gallon",
    "gallon": "gallon",
    "gallons": "gallon",
    # Area
    "m2": "m**2",
    "m²": "m**2",
    "sqm": "m**2",
    "sqft": "ft**2",
    "ha": "hectare",
    "acre": "acre",
    # Time
    "h": "hour",
    "hr": "hour",
    "hour": "hour",
    "hours": "hour",
    "day": "day",
    "days": "day",
    "year": "year",
    "years": "year",
    # Compound units (common in emissions)
    "tonne-km": "tonne * km",
    "tkm": "tonne * km",
    "passenger-km": "km",  # Simplified - person is dimensionless
    "pkm": "km",
    "vehicle-km": "km",
    "vkm": "km",
}

# Known valid units that Pint might not recognize
PASSTHROUGH_UNITS: List[str] = [
    "EUR", "USD", "GBP",  # Currencies
    "kgCO2e", "tCO2e",    # CO2 equivalent
    "nights",             # Hotel stays
    "passenger-km",       # Travel
    "tonne-km",           # Freight
    "vehicle-km",
    "m²-year",
    "unit",
    "unit-year",
    "user-year",
]


def normalize_unit_string(unit: str) -> str:
    """
    Normalize a unit string to a consistent format.

    Args:
        unit: The unit string to normalize

    Returns:
        Normalized unit string
    """
    if not unit:
        return unit

    # Strip whitespace
    unit_clean = unit.strip()

    # Check aliases (case-insensitive)
    unit_lower = unit_clean.lower()
    if unit_lower in UNIT_ALIASES:
        return UNIT_ALIASES[unit_lower]

    return unit_clean


def validate_unit(unit: str, strict: bool = False) -> bool:
    """
    Validate that a unit string is recognized.

    Args:
        unit: The unit string to validate
        strict: If True, require Pint to parse it. If False, accept passthrough units.

    Returns:
        True if unit is valid, False otherwise

    Examples:
        validate_unit("kWh") -> True
        validate_unit("invalid_unit") -> False
        validate_unit("EUR") -> True (passthrough)
    """
    if not unit:
        return False

    normalized = normalize_unit_string(unit)

    # Check passthrough units first
    if normalized in PASSTHROUGH_UNITS:
        return True

    if not PINT_AVAILABLE:
        # Without Pint, accept any normalized unit
        logger.warning("Pint not available - unit validation limited")
        return True

    try:
        ureg.parse_expression(normalized)
        return True
    except (pint.UndefinedUnitError, pint.DimensionalityError):
        if strict:
            return False
        # Allow unknown units in non-strict mode
        logger.debug(f"Unknown unit '{unit}', accepting in non-strict mode")
        return True
    except Exception as e:
        logger.warning(f"Error parsing unit '{unit}': {e}")
        return not strict


def get_unit_dimension(unit: str) -> Optional[str]:
    """
    Get the dimension category of a unit.

    Args:
        unit: The unit string

    Returns:
        Dimension name (energy, mass, distance, volume, etc.) or None
    """
    if not PINT_AVAILABLE or not unit:
        return None

    normalized = normalize_unit_string(unit)

    # Check passthrough units
    if normalized in ["EUR", "USD", "GBP"]:
        return "currency"
    if normalized in ["kgCO2e", "tCO2e"]:
        return "mass"  # CO2e treated as mass

    try:
        quantity = ureg.parse_expression(normalized)
        dimensionality = quantity.dimensionality

        # Map Pint dimensionality to our categories
        dim_str = str(dimensionality)

        if "[length] ** 2" in dim_str:
            return "area"
        if "[length]" in dim_str:
            return "distance"
        if "[mass]" in dim_str:
            return "mass"
        if "[time]" in dim_str:
            return "time"

        # Energy is mass * length^2 / time^2
        if "[mass]" in dim_str and "[length]" in dim_str and "[time]" in dim_str:
            return "energy"

        # Volume is length^3
        if dim_str == "[length] ** 3":
            return "volume"

        return None

    except Exception:
        return None


def convert_to_canonical(
    value: float,
    from_unit: str,
    dimension: Optional[str] = None
) -> Tuple[float, str]:
    """
    Convert a value to its canonical unit.

    Args:
        value: The numeric value
        from_unit: The source unit
        dimension: Optional dimension hint (energy, mass, distance, volume)

    Returns:
        Tuple of (converted_value, canonical_unit)

    Raises:
        UnitError: If conversion fails

    Examples:
        convert_to_canonical(1000, "Wh", "energy") -> (1.0, "kWh")
        convert_to_canonical(1, "tonne", "mass") -> (1000.0, "kg")
    """
    if not PINT_AVAILABLE:
        logger.warning("Pint not available - returning value unchanged")
        return value, normalize_unit_string(from_unit)

    normalized_unit = normalize_unit_string(from_unit)

    # Handle passthrough units
    if normalized_unit in PASSTHROUGH_UNITS:
        return value, normalized_unit

    # Determine canonical unit
    if dimension and dimension in CANONICAL_UNITS:
        target_unit = CANONICAL_UNITS[dimension]
    else:
        # Try to infer dimension
        inferred_dim = get_unit_dimension(normalized_unit)
        if inferred_dim and inferred_dim in CANONICAL_UNITS:
            target_unit = CANONICAL_UNITS[inferred_dim]
        else:
            # Can't convert, return as-is
            return value, normalized_unit

    try:
        # Create Pint quantity and convert
        quantity = value * ureg.parse_expression(normalized_unit)
        converted = quantity.to(target_unit)
        return float(converted.magnitude), target_unit

    except pint.DimensionalityError as e:
        raise UnitError(f"Cannot convert {from_unit} to {target_unit}: {e}")
    except Exception as e:
        raise UnitError(f"Conversion error for {from_unit}: {e}")


def convert_units(
    value: float,
    from_unit: str,
    to_unit: str
) -> float:
    """
    Convert a value between two units.

    Args:
        value: The numeric value
        from_unit: The source unit
        to_unit: The target unit

    Returns:
        Converted value

    Raises:
        UnitError: If conversion fails

    Examples:
        convert_units(1, "km", "m") -> 1000.0
        convert_units(1, "kWh", "MJ") -> 3.6
    """
    if not PINT_AVAILABLE:
        raise UnitError("Pint library not available for unit conversion")

    from_normalized = normalize_unit_string(from_unit)
    to_normalized = normalize_unit_string(to_unit)

    try:
        quantity = value * ureg.parse_expression(from_normalized)
        converted = quantity.to(to_normalized)
        return float(converted.magnitude)

    except pint.DimensionalityError as e:
        raise UnitError(f"Cannot convert {from_unit} to {to_unit}: incompatible dimensions")
    except pint.UndefinedUnitError as e:
        raise UnitError(f"Unknown unit: {e}")
    except Exception as e:
        raise UnitError(f"Conversion error: {e}")


def get_known_units() -> Dict[str, List[str]]:
    """
    Get a dictionary of known units organized by dimension.

    Returns:
        Dict mapping dimension names to lists of unit strings
    """
    return {
        "energy": ["kWh", "MWh", "GWh", "Wh", "MJ", "GJ", "kJ", "J", "therm", "BTU"],
        "mass": ["kg", "g", "mg", "tonne", "ton", "lb", "oz", "kgCO2e", "tCO2e"],
        "distance": ["km", "m", "cm", "mm", "mile", "ft", "yard"],
        "volume": ["L", "mL", "m**3", "gallon"],
        "area": ["m**2", "ft**2", "hectare", "acre"],
        "time": ["hour", "day", "year"],
        "currency": ["EUR", "USD", "GBP"],
        "compound": ["tonne-km", "passenger-km", "vehicle-km", "m²-year", "unit-year"],
    }
