# app/utils/format.py
"""
Number and format sanitization utilities for CSRD compliance.

Handles EU (1.234,56) vs US (1,234.56) number format normalization.
This is critical for CSV imports from different locales.

Usage:
    from app.utils.format import sanitize_number, detect_number_format

    # Auto-detect and convert
    value = sanitize_number("1.234,56")  # Returns 1234.56

    # Explicit format
    value = sanitize_number("1,234.56", locale="US")
"""
from typing import Union, Optional
import re
import logging

logger = logging.getLogger(__name__)


class NumberFormatError(ValueError):
    """Raised when a number cannot be parsed."""
    pass


def detect_number_format(value: str) -> str:
    """
    Detect if a number string is EU or US format.

    EU format: 1.234,56 (period as thousands separator, comma as decimal)
    US format: 1,234.56 (comma as thousands separator, period as decimal)

    Args:
        value: Number string to analyze

    Returns:
        "EU", "US", or "AMBIGUOUS"

    Examples:
        "1.234,56" -> "EU"
        "1,234.56" -> "US"
        "1234" -> "AMBIGUOUS"
        "1234.5" -> "US" (single decimal point, no thousands)
        "1234,5" -> "EU" (single comma, no thousands)
    """
    value = value.strip()

    # Remove currency symbols and whitespace
    value = re.sub(r'[€$£¥\s]', '', value)

    # Check for both comma and period
    has_comma = ',' in value
    has_period = '.' in value

    if has_comma and has_period:
        # Both present - check which comes last (that's the decimal separator)
        last_comma = value.rfind(',')
        last_period = value.rfind('.')

        if last_comma > last_period:
            return "EU"  # Comma is decimal separator
        else:
            return "US"  # Period is decimal separator

    elif has_comma and not has_period:
        # Only comma - check if it's thousands or decimal
        # EU decimal: single comma with 1-2 digits after
        # US thousands: comma with 3 digits after (or multiple commas)
        parts = value.split(',')
        if len(parts) == 2 and len(parts[1]) <= 2:
            return "EU"  # Likely decimal separator
        elif len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3):
            return "US"  # Likely thousands separator
        else:
            return "AMBIGUOUS"

    elif has_period and not has_comma:
        # Only period - check if it's thousands or decimal
        # EU thousands: period with 3 digits after (or multiple periods)
        # US decimal: single period
        parts = value.split('.')
        if len(parts) > 2 or (len(parts) == 2 and len(parts[1]) == 3 and len(parts[0]) <= 3):
            return "EU"  # Likely thousands separator (e.g., "1.234.567")
        else:
            return "US"  # Likely decimal separator

    else:
        # No separators - just digits
        return "AMBIGUOUS"


def sanitize_number(
    value: Union[str, int, float, None],
    locale: Optional[str] = None,
    strict: bool = False
) -> Optional[float]:
    """
    Sanitize and convert a number string to float.

    Handles EU (1.234,56) and US (1,234.56) number formats.
    If locale is not specified, auto-detects the format.

    Args:
        value: The value to sanitize (string, int, float, or None)
        locale: Force a specific locale ("EU", "US", or None for auto-detect)
        strict: If True, raise error on ambiguous formats. If False, assume US.

    Returns:
        Float value, or None if input is None/empty

    Raises:
        NumberFormatError: If value cannot be parsed (and strict=True for ambiguous)

    Examples:
        sanitize_number("1.234,56") -> 1234.56  (EU format detected)
        sanitize_number("1,234.56") -> 1234.56  (US format detected)
        sanitize_number("1234.56") -> 1234.56   (US format, no thousands)
        sanitize_number("1234,56", locale="EU") -> 1234.56
        sanitize_number(1234.56) -> 1234.56     (passthrough)
        sanitize_number(None) -> None
        sanitize_number("") -> None
    """
    # Handle None and empty
    if value is None:
        return None

    # Passthrough numeric types
    if isinstance(value, (int, float)):
        return float(value)

    # Convert to string and strip
    value_str = str(value).strip()

    if not value_str:
        return None

    # Remove currency symbols, whitespace, and plus signs
    value_str = re.sub(r'[€$£¥\s+]', '', value_str)

    # Handle negative numbers (preserve the sign)
    is_negative = value_str.startswith('-') or value_str.startswith('(')
    value_str = value_str.lstrip('-').strip('()')

    # If no separators, just try to convert
    if ',' not in value_str and '.' not in value_str:
        try:
            result = float(value_str)
            return -result if is_negative else result
        except ValueError:
            raise NumberFormatError(f"Cannot parse number: {value}")

    # Detect or use specified locale
    detected_locale = locale or detect_number_format(value_str)

    if detected_locale == "AMBIGUOUS":
        if strict:
            raise NumberFormatError(
                f"Ambiguous number format: {value}. "
                "Specify locale='EU' or locale='US'"
            )
        # Default to US format for ambiguous cases
        detected_locale = "US"
        logger.debug(f"Ambiguous number format '{value}', defaulting to US")

    # Convert based on locale
    try:
        if detected_locale == "EU":
            # EU: Remove thousands separator (period), replace decimal (comma) with period
            normalized = value_str.replace('.', '').replace(',', '.')
        else:  # US
            # US: Remove thousands separator (comma), keep decimal (period)
            normalized = value_str.replace(',', '')

        result = float(normalized)
        return -result if is_negative else result

    except ValueError:
        raise NumberFormatError(f"Cannot parse number: {value}")


def format_number(
    value: Union[float, int, None],
    locale: str = "US",
    decimals: int = 2,
    thousands_separator: bool = True
) -> str:
    """
    Format a number for display in the specified locale.

    Args:
        value: Number to format
        locale: "EU" or "US"
        decimals: Number of decimal places
        thousands_separator: Whether to include thousands separator

    Returns:
        Formatted string

    Examples:
        format_number(1234.56, locale="US") -> "1,234.56"
        format_number(1234.56, locale="EU") -> "1.234,56"
    """
    if value is None:
        return ""

    # Format with US locale first
    if thousands_separator:
        formatted = f"{value:,.{decimals}f}"
    else:
        formatted = f"{value:.{decimals}f}"

    # Convert to EU if needed
    if locale == "EU":
        # Swap comma and period
        formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')

    return formatted


def sanitize_csv_row_numbers(
    row: dict,
    numeric_fields: list,
    locale: Optional[str] = None
) -> dict:
    """
    Sanitize all numeric fields in a CSV row.

    Args:
        row: Dictionary of field -> value from CSV
        numeric_fields: List of field names that should be numeric
        locale: Force a specific locale, or None for auto-detect per field

    Returns:
        Dictionary with numeric fields converted to floats

    Example:
        row = {"amount": "1.234,56", "unit": "kWh", "factor": "0,5"}
        result = sanitize_csv_row_numbers(row, ["amount", "factor"], locale="EU")
        # result = {"amount": 1234.56, "unit": "kWh", "factor": 0.5}
    """
    result = row.copy()

    for field in numeric_fields:
        if field in result and result[field] is not None:
            try:
                result[field] = sanitize_number(result[field], locale=locale)
            except NumberFormatError as e:
                logger.warning(f"Failed to sanitize field '{field}': {e}")
                # Keep original value for error reporting upstream
                pass

    return result
